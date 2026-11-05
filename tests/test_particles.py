import unittest

from fairy_mouse.particles import ParticleSystem


class ParticleTests(unittest.TestCase):
    def test_expiration_checks_all_particles_not_just_oldest(self):
        from fairy_mouse.particles import Particle
        system = ParticleSystem()
        system.particles.extend([
            Particle(0, 0, 0, .6, 1, 0, 0),
            Particle(0, 0, .1, .2, 1, 0, 0)])
        self.assertTrue(system.update(.4))
        self.assertEqual(len(system.particles), 1)
        self.assertFalse(system.update(.7))

    def test_click_storm_stays_bounded(self):
        system = ParticleSystem(limit=48)
        for i in range(1000):
            system.click(10, 20, i / 1000)
        self.assertEqual(len(system.particles), 48)
        self.assertFalse(system.update(2))

    def test_movement_emission_is_limited(self):
        system = ParticleSystem(seed=1)
        self.assertTrue(system.move(0, 0, 0))
        self.assertFalse(system.move(100, 0, .001))
        self.assertTrue(system.move(100, 0, .04))
        self.assertFalse(system.move(101, 0, .1))
        self.assertEqual(len(system.particles), 4)

    def test_new_visit_can_emit_at_same_position(self):
        system = ParticleSystem()
        system.move(10, 20, 0)
        system.reset_position()
        self.assertTrue(system.move(10, 20, 1))

    def test_particle_position_and_opacity_follow_time(self):
        from fairy_mouse.particles import Particle
        p = Particle(10, 20, 1, .5, 2, 4, 8)
        self.assertEqual(p.sample(1.25), (11, 22, .5))
        self.assertEqual(p.sample(2)[2], 0)

    def test_invalid_limits_rejected(self):
        for limit in (0, 257):
            with self.assertRaises(ValueError):
                ParticleSystem(limit=limit)

    def test_outputs_share_one_global_limit(self):
        system = ParticleSystem(limit=12)
        system.move(10, 20, 0, 'eDP-1')
        system.click(10, 20, .1, 'HDMI-A-1')
        system.click(10, 20, .2, 'eDP-1')
        self.assertEqual(len(system.particles), 12)
        self.assertEqual({p.output for p in system.particles}, {'eDP-1', 'HDMI-A-1'})
