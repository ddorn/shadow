from time import time

from light import RainbowLight
from maths import clamp
from physics import Body, AABB, Pos


class LightParticle(Body, RainbowLight):
    def __init__(self, center, velocity=(0, 0), life_time=None, range=40):
        hit_box = 4
        topleft = center[0] - hit_box, center[1] - hit_box
        Body.__init__(self, AABB(topleft, (hit_box, hit_box)), mass=0,
                      elasticity=1, moving=True)
        RainbowLight.__init__(self, center, range=range, loop_time=1, variants=3)
        self.velocity = Pos(velocity)
        self.birthdate = time()
        self.life_time = life_time
        self.start_range = range

    def __del__(self):
        print("Une lumière s'est éteinte !")

    @property
    def life_time(self):
        return self._life_time

    @life_time.setter
    def life_time(self, value):
        self._life_time = value
        self.start_range = self.range
        self.birthdate = time()

    def update(self):
        if self.life_time:
            progress = (time() - self.birthdate) / self.life_time
            self.range = clamp(round((1 - progress) * self.start_range), 0, self.start_range)

    @property
    def topleft(self):
        return self.center - (self.range, self.range)