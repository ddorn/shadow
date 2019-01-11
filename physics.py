from collections import namedtuple
from math import cos, sin, pi, sqrt
from typing import List

import pygame


class Pos:
    """A vector."""

    def __init__(self, *args):
        if len(args) == 1:
            args = args[0]
        self.x = args[0]
        self.y = args[1]

    def __len__(self):
        return 2

    def __iter__(self):
        yield self.x
        yield self.y

    def __bool__(self):
        return self.x and self.y

    def __repr__(self):
        return f"Pos({self.x}, {self.y})"

    def __getitem__(self, item):
        if item == 0:
            return self.x
        elif item == 1:
            return self.y
        raise IndexError(f"Pos has no item {item}")

    def __add__(self, other):
        return Pos(self[0] + other[0], self[1] + other[1])

    __radd__ = __add__

    def __sub__(self, other):
        return Pos(self[0] - other[0], self[1] - other[1])

    def __rsub__(self, other):
        return Pos(other[0] - self[0], other[1] - self[1])

    def __neg__(self):
        return Pos(-self[0], -self[1])

    def __mul__(self, other):
        return Pos(self[0] * other, self[1] * other)

    __rmul__ = __mul__

    def __truediv__(self, other: int):
        return Pos(self[0] / other, self[1] / other)

    def __floordiv__(self, other: int):
        return Pos(self[0] // other, self[1] // other)

    @property
    def t(self):
        """The vecor as a tuple"""
        return self[0], self[1]

    @property
    def ti(self):
        """The vecor as a tuple of integer (round to closest)"""
        return round(self[0]), round(self[1])

    @property
    def i(self):
        """The vector as an integer Pos (round to closest)"""
        return Pos(round(self[0], round(self[1])))

    def squared_norm(self):
        """Return the squared norm of the vector"""
        return self[0] ** 2 + self[1] ** 2

    def norm(self):
        """Return the norm of the vector"""
        return sqrt(self.squared_norm())

    def rotate(self, degree):
        c = cos(pi / 180 * degree)
        s = sin(pi / 180 * degree)
        return Pos(c*self[0] + s*self[1],
                   s*self[0] - c*self[1])


class Body(pygame.rect.RectType):
    def __init__(self, pos=(0, 0), size=(0, 0),  max_velocity=(None, None), moving=False):
        super().__init__(pos, size)
        self.velocity = Pos(0, 0)
        self.acceleration = Pos(0, 0)
        self.max_velocity = max_velocity
        self.moving = True

    @property
    def pos(self):
        return Pos(self.topleft)

    @pos.setter
    def pos(self, value):
        self.topleft = value

    def update_pos(self):
        self.velocity += self.acceleration
        self.pos += self.velocity

    def update_x(self, static_bodies):
        self.velocity.
        indices = self.collidelist(static_bodies)


    def check_colisions_y(self, static_bodies):
        pass


class Space:
    def __init__(self, gravity=(0, 0)):
        self.gravity = gravity
        self.static_bodies = []  # type: List[Body]
        self.moving_bodies = []  # type: List[Body]

    def add(self, *bodies):
        for body in bodies:
            if body.moving:
                self.moving_bodies.append(body)
            else:
                self.static_bodies.append(body)

    def simulate(self):
        for body in self.moving_bodies:
            body.update_pos()

        # check colision horizontaly
        for body in self.moving_bodies:
            body.update_x(self.static_bodies)

        # check colision verticaly
        for body in self.moving_bodies:
            body.check_colisions_y(self.static_bodies)



