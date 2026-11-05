"""Sobreposição com rastreamento por metadados do cursor no Sway padrão."""
import logging
import math
import signal
import time
import threading
from pathlib import Path

from .events import MAX_MESSAGE, PointerEvent, parse_message
from .cursor import CursorClient, LatestPosition
from .clicks import ClickWatcher
from .particles import ParticleSystem
from .rendering import draw_particles
from .runtime import event_socket
from .gtk_runtime import load_background_gtk

LOG = logging.getLogger(__name__)


def run(args):
    Gdk, Gio, GLib, Gtk, Layer = load_background_gtk()
    import cairo

    Gtk.init_check()
    display = Gdk.Display.get_default()
    if display is None:
        raise RuntimeError('Não foi possível abrir a sessão gráfica do Sway.')
    if not Layer.is_supported():
        raise RuntimeError(
            f'Gtk4LayerShell não ficou disponível no backend {display.__gtype__.name}. '
            'Verifique layer_shell_preloaded e layer_shell_protocol_version em --diagnose')

    class Background(Gtk.Application):
        def __init__(self, server):
            super().__init__(application_id='com.tamy.fairymouse.background',
                             flags=Gio.ApplicationFlags.NON_UNIQUE)
            self.server = server
            self.system = ParticleSystem(args.particles, args.intensity)
            self.views = {}
            self.timer = 0
            self.watch = 0
            self.output = None
            self.monitors = display.get_monitors()
            self.monitor_handler = 0
            self.signal_sources = []
            self.client = None
            self.reader = None
            self.stopping = threading.Event()
            self.failed = False
            self.positions_seen = False
            self.clicks = None
            self.input_monitor = None
            self.rescan_source = 0
            self.bridge = LatestPosition(
                lambda callback: GLib.timeout_add(math.ceil(1000 / args.fps), callback),
                self.cursor_position)

        def prepare_cursor(self):
            if not args.external_events:
                self.client = CursorClient(self.bridge.put, seat=args.seat,
                                           on_leave=self.bridge.invalidate).connect()

        def read_cursor(self):
            try:
                self.client.listen()
            except (OSError, RuntimeError) as exc:
                if not self.stopping.is_set():
                    GLib.idle_add(self.cursor_failed, str(exc))

        def cursor_failed(self, message):
            if not self.stopping.is_set():
                LOG.error('Rastreamento encerrado: %s', message)
                self.failed = True
                self.quit()
            return False

        def cursor_position(self, position):
            view = self.views.get(position.output)
            if view is None:
                return
            area = view[1]
            point = position.logical(area.get_width(), area.get_height())
            if point is not None:
                if not self.positions_seen:
                    LOG.info('Primeira posição real do cursor recebida em %s.', position.output)
                    self.positions_seen = True
                self.apply_event(PointerEvent('motion', position.output, *point))

        def click_at_cursor(self):
            position = self.bridge.snapshot()
            if position is None:
                return
            view = self.views.get(position.output)
            if view is not None:
                area = view[1]
                point = position.logical(area.get_width(), area.get_height())
                if point is not None:
                    self.apply_event(PointerEvent('click', position.output, *point))

        def prepare_clicks(self):
            if args.no_clicks or args.external_events:
                return
            if args.seat != 'seat0' and not args.click_device:
                LOG.warning('Para outro seat, selecione seu mouse com --click-device.')
                return
            self.clicks = ClickWatcher(GLib, self.click_at_cursor, paths=args.click_device)
            self.clicks.rescan()
            if not self.clicks.devices:
                LOG.warning('Sem dispositivo de clique legível. O rastro continua ativo; '
                            'consulte click_detection em --diagnose. Não execute como root.')
            if Path('/dev/input').is_dir():
                try:
                    self.input_monitor = Gio.File.new_for_path('/dev/input').monitor_directory(
                        Gio.FileMonitorFlags.NONE, None)
                    self.input_monitor.connect('changed', self.schedule_rescan)
                except GLib.Error as exc:
                    LOG.warning('Monitor de conexão de mouse indisponível: %s', exc)

        def schedule_rescan(self, *_):
            if not self.rescan_source:
                self.rescan_source = GLib.timeout_add(150, self.rescan_clicks)

        def rescan_clicks(self):
            self.rescan_source = 0
            if self.clicks is not None:
                self.clicks.rescan()
            return False

        def do_activate(self):
            try:
                self.activate_overlay()
            except Exception:
                LOG.exception('Falha ao ativar a sobreposição.')
                self.failed = True
                self.quit()

        def activate_overlay(self):
            self.hold()
            css = Gtk.CssProvider()
            css.load_from_data(b'window.fairy-overlay { background: transparent; }')
            Gtk.StyleContext.add_provider_for_display(
                display, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            self.rebuild()
            self.monitor_handler = self.monitors.connect('items-changed', self.rebuild)
            self.watch = GLib.io_add_watch(self.server.fileno(), GLib.IO_IN, self.receive)
            self.display_handler = display.connect('closed', lambda *_: self.quit())
            for signum in (signal.SIGINT, signal.SIGTERM):
                self.signal_sources.append(GLib.unix_signal_add(
                    GLib.PRIORITY_DEFAULT, signum, self.request_quit))
            if self.client is not None:
                self.reader = threading.Thread(target=self.read_cursor, daemon=True,
                                               name='fairy-cursor')
                self.reader.start()
                LOG.info('Rastreamento de cursor iniciado via protocolo EXT no seat %s.', args.seat)
                self.prepare_clicks()
            else:
                LOG.warning('Modo de teste: aguardando eventos externos; rastreamento desativado.')

        def request_quit(self):
            self.quit()
            # A fonte é removida no shutdown, junto com as demais.
            return True

        def rebuild(self, *_):
            for window, area in self.views.values():
                window.destroy()
            self.views.clear()
            self.system.particles.clear()
            self.system.reset_position()
            self.output = None
            for i in range(self.monitors.get_n_items()):
                monitor = self.monitors.get_item(i)
                name = monitor.get_connector()
                if not name:
                    LOG.warning('Monitor sem identificador; ignorado.')
                    continue
                window = Gtk.ApplicationWindow(application=self)
                window.add_css_class('fairy-overlay')
                window.set_decorated(False)
                window.set_can_focus(False)
                window.set_can_target(False)
                Layer.init_for_window(window)
                Layer.set_namespace(window, 'fairy-mouse')
                Layer.set_layer(window, Layer.Layer.OVERLAY)
                Layer.set_monitor(window, monitor)
                Layer.set_keyboard_mode(window, Layer.KeyboardMode.NONE)
                # Coordenadas EXT cobrem a saída inteira. Zona 0 evita painéis e
                # comprime/desloca o desenho; -1 preserva origem e extensão da saída.
                Layer.set_exclusive_zone(window, -1)
                for edge in (Layer.Edge.TOP, Layer.Edge.BOTTOM, Layer.Edge.LEFT, Layer.Edge.RIGHT):
                    Layer.set_anchor(window, edge, True)
                area = Gtk.DrawingArea()
                area.set_can_target(False)
                area.set_draw_func(self.draw, name)
                window.set_child(area)
                window.connect('realize', self.pass_input)
                window.connect('map', self.pass_input)
                self.views[name] = (window, area)
                window.set_visible(True)

        def pass_input(self, window):
            surface = window.get_surface()
            if surface:
                surface.set_input_region(cairo.Region())

        def receive(self, fd, condition):
            # Limite por despacho evita monopolizar o loop GTK em rajadas.
            for _ in range(64):
                try:
                    data = self.server.recv(MAX_MESSAGE + 1)
                except BlockingIOError:
                    break
                try:
                    event = parse_message(data)
                except ValueError:
                    continue
                if event is None:
                    self.quit()
                    return True
                self.apply_event(event)
            return True

        def apply_event(self, event):
            view = self.views.get(event.output)
            if view is None:
                return
            area = view[1]
            if not (0 <= event.x < area.get_width() and 0 <= event.y < area.get_height()):
                return
            if self.output != event.output:
                self.system.reset_position()
                self.output = event.output
            now = time.monotonic()
            if event.kind == 'motion':
                changed = self.system.move(event.x, event.y, now, event.output)
            else:
                self.system.click(event.x, event.y, now, event.output)
                changed = True
            if changed and not self.timer:
                self.timer = GLib.timeout_add(math.ceil(1000 / args.fps), self.tick)

        def tick(self):
            dirty = {p.output for p in self.system.particles}
            active = self.system.update(time.monotonic())
            for name in dirty:
                if name in self.views:
                    self.views[name][1].queue_draw()
            if not active:
                self.timer = 0
            return active

        def draw(self, area, cr, width, height, name):
            cr.set_operator(cairo.OPERATOR_SOURCE)
            cr.set_source_rgba(0, 0, 0, 0)
            cr.paint()
            cr.set_operator(cairo.OPERATOR_OVER)
            draw_particles(cr, self.system.particles, args.color, time.monotonic(), name)

        def stop_cursor(self):
            self.stopping.set()
            if self.input_monitor is not None:
                self.input_monitor.cancel()
                self.input_monitor = None
            if self.rescan_source:
                GLib.source_remove(self.rescan_source)
                self.rescan_source = 0
            if self.clicks is not None:
                self.clicks.close()
            self.bridge.close()
            if self.client is not None:
                self.client.close()
            if self.reader is not None:
                self.reader.join(timeout=1)

        def do_shutdown(self):
            self.stop_cursor()
            for source in [self.timer, self.watch, *self.signal_sources]:
                if source:
                    GLib.source_remove(source)
            if self.monitor_handler:
                self.monitors.disconnect(self.monitor_handler)
            if hasattr(self, 'display_handler'):
                display.disconnect(self.display_handler)
            for window, area in self.views.values():
                window.destroy()
            self.views.clear()
            Gtk.Application.do_shutdown(self)

    with event_socket() as server:
        app = Background(server)
        try:
            app.prepare_cursor()
            result = app.run([])
            return 1 if app.failed else result
        finally:
            app.stop_cursor()
