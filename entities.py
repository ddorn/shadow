from light import RainbowLight
from physics import Body, AABB, Pos


class LightParticle(Body, RainbowLight):
    def __init__(self, center, velocity=(0, 0)):
        hit_box = 4
        topleft = center[0] - hit_box, center[1] - hit_box
        Body.__init__(self, AABB(topleft, (hit_box, hit_box)), mass=0,
                      elasticity=1, moving=True)
        RainbowLight.__init__(self, center, range=40, variants=10)
        self.velocity = Pos(velocity)

    def __del__(self):
        print("Une lumière s'est éteinte !")
        try:
            self.space.moving_bodies.remove(self)
        except ValueError:
            pass

    @property
    def topleft(self):
        return self.center - (40, 40)