import unittest

try:
    import cairo
except ImportError:
    cairo = None

from fairy_mouse.particles import ParticleSystem
from fairy_mouse.rendering import draw_particles


@unittest.skipIf(cairo is None, 'Cairo não instalado neste interpretador.')
class RenderingTests(unittest.TestCase):
    def render(self, particles, output=None):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
        draw_particles(cairo.Context(surface), particles, (1, .5, 1), .1, output)
        surface.flush()
        return bytes(surface.get_data())

    def test_local_effect_is_visible_and_other_output_is_transparent(self):
        system = ParticleSystem(seed=1)
        system.move(50, 50, 0, 'eDP-1')
        self.assertTrue(any(self.render(system.particles, 'eDP-1')))
        self.assertFalse(any(self.render(system.particles, 'HDMI-A-1')))

    def test_demo_effect_remains_visible(self):
        system = ParticleSystem(seed=1)
        system.click(50, 50, 0)
        self.assertTrue(any(self.render(system.particles)))
