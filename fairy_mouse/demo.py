"""Demonstração local: os eventos pertencem apenas à janela de teste."""
import math
import signal
import sys
import time

from .particles import ParticleSystem
from .rendering import draw_particles


def run(args):
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Gdk', '4.0')
    from gi.repository import Gdk, GLib, Gtk

    class Demo(Gtk.Application):
        def __init__(self):
            super().__init__(application_id='com.tamy.fairymouse.demo')
            self.system = ParticleSystem(args.particles, args.intensity)
            self.timer = 0
            self.area = None

        def do_activate(self):
            if self.area is not None:
                self.area.get_root().present()
                return
            window = Gtk.ApplicationWindow(application=self)
            window.set_title('Fairy Mouse — demonstração local')
            window.set_default_size(800, 500)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            label = Gtk.Label(label='Mova o mouse e clique na área abaixo. '
                              'Esta demonstração funciona apenas nesta janela.')
            label.set_wrap(True)
            box.append(label)
            self.area = Gtk.DrawingArea()
            self.area.set_hexpand(True)
            self.area.set_vexpand(True)
            self.area.set_draw_func(self.draw)
            motion = Gtk.EventControllerMotion()
            motion.connect('motion', self.motion)
            motion.connect('leave', lambda *_: self.system.reset_position())
            self.area.add_controller(motion)
            click = Gtk.GestureClick()
            click.set_button(Gdk.BUTTON_PRIMARY)
            click.connect('pressed', self.click)
            self.area.add_controller(click)
            box.append(self.area)
            window.set_child(box)
            window.present()

        def motion(self, controller, x, y):
            if self.system.move(x, y, time.monotonic()):
                self.wake()

        def click(self, gesture, count, x, y):
            self.system.click(x, y, time.monotonic())
            self.wake()

        def wake(self):
            if not self.timer:
                self.timer = GLib.timeout_add(math.ceil(1000 / args.fps), self.tick)

        def tick(self):
            active = self.system.update(time.monotonic())
            self.area.queue_draw()
            if not active:
                self.timer = 0
            return active

        def draw(self, area, cr, width, height):
            cr.set_source_rgb(.045, .035, .075)
            cr.paint()
            draw_particles(cr, self.system.particles, args.color, time.monotonic())

        def do_shutdown(self):
            if self.timer:
                GLib.source_remove(self.timer)
                self.timer = 0
            Gtk.Application.do_shutdown(self)

    Gtk.init_check()
    if Gdk.Display.get_default() is None:
        print('Não foi possível abrir a sessão gráfica. Execute em um terminal do Sway.',
              file=sys.stderr)
        return 1
    app = Demo()
    for signum in (signal.SIGINT, signal.SIGTERM):
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signum, lambda: (app.quit(), False)[1])
    return app.run([])
