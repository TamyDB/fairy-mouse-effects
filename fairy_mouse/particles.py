"""Simulação limitada, independente do toolkit e com relógio fornecido pelo chamador."""
from collections import deque
from dataclasses import dataclass
from math import hypot
from random import Random


@dataclass(frozen=True, slots=True)
class Particle:
    x: float
    y: float
    born: float
    lifetime: float
    size: float
    vx: float
    vy: float
    burst: bool = False
    output: str | None = None

    def sample(self, now):
        age = max(0.0, now - self.born)
        opacity = max(0.0, 1.0 - age / self.lifetime)
        return self.x + self.vx * age, self.y + self.vy * age, opacity


class ParticleSystem:
    def __init__(self, limit=48, intensity=1.0, seed=None):
        if not 1 <= limit <= 256:
            raise ValueError('O limite deve estar entre 1 e 256.')
        if not 0.1 <= intensity <= 2.0:
            raise ValueError('A intensidade deve estar entre 0.1 e 2.')
        self.particles = deque(maxlen=limit)
        self.intensity = intensity
        self.random = Random(seed)
        self.last_position = None
        self.last_emission = float('-inf')

    def move(self, x, y, now, output=None):
        if self.last_position is not None:
            distance = hypot(x - self.last_position[0], y - self.last_position[1])
            if distance < 5 or now - self.last_emission < 1 / 30:
                return False
        self.last_position = (x, y)
        self.last_emission = now
        for _ in range(max(1, round(2 * self.intensity))):
            self.particles.append(Particle(
                x + self.random.uniform(-3, 3), y + self.random.uniform(-3, 3),
                now, self.random.uniform(.25, .6), self.random.uniform(1.5, 3),
                self.random.uniform(-8, 8), self.random.uniform(5, 16), output=output))
        return True

    def click(self, x, y, now, output=None):
        from math import cos, sin, tau
        count = max(4, round(10 * self.intensity))
        for i in range(count):
            angle = tau * i / count
            self.particles.append(Particle(
                x, y, now, .22, 3.5, cos(angle) * 90, sin(angle) * 90, True, output))

    def update(self, now):
        # A duração varia: não basta remover apenas o primeiro item da fila.
        alive = [p for p in self.particles if now - p.born < p.lifetime]
        self.particles.clear()
        self.particles.extend(alive)
        return bool(self.particles)

    def reset_position(self):
        self.last_position = None
