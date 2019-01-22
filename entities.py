from time import time

from light import RainbowLight
from maths import clamp
from physics import Body, AABB, Pos


class LightParticle(Body, RainbowLight):
    def __init__(self, center, velocity=(0, 0), life_time=None):
        hit_box = 4
        topleft = center[0] - hit_box, center[1] - hit_box
        Body.__init__(self, AABB(topleft, (hit_box, hit_box)), mass=0,
                      elasticity=1, moving=True)
        RainbowLight.__init__(self, center, range=40, variants=3)
        self.velocity = Pos(velocity)
        self.bithdate = time()
        self.life_time = life_time

    def __del__(self):
        print("Une lumière s'est éteinte !")
        try:
            self.space.moving_bodies.remove(self)
        except ValueError:
            pass

    def update(self):
        progress = (time() - self.bithdate) / self.life_time
        self.range = clamp(round((1 - progress) * 40), 0, 40)


    @property
    def topleft(self):
        return self.center - (self.range, self.range)