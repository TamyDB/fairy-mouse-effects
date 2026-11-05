"""Desenho compartilhado entre demonstração e sobreposição."""
import math


def draw_particles(cr, particles, color, now, output=None):
    for particle in particles:
        if particle.output != output:
            continue
        x, y, alpha = particle.sample(now)
        if alpha <= 0:
            continue
        size = particle.size * (.5 + .5 * alpha)
        cr.set_source_rgba(*color, alpha * .85)
        cr.set_line_width(max(.8, size / 2))
        cr.move_to(x - size * 2, y)
        cr.line_to(x + size * 2, y)
        cr.move_to(x, y - size * 2)
        cr.line_to(x, y + size * 2)
        cr.stroke()
        cr.set_source_rgba(1, 1, 1, alpha)
        cr.arc(x, y, size / 2, 0, math.tau)
        cr.fill()
