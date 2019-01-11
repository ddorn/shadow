from collections import namedtuple
from math import cos, sin, pi, sqrt

import pygame


class Pos(namedtuple("Pos", ('x', 'y'))):
    """A vector."""

    def __new__(cls, *c):
        if len(c) == 0:
            c = (0, 0)
        elif len(c) == 1:
            assert len(c[0]) == 2
            c = c[0]
        elif len(c) > 2:
            raise TypeError

        # noinspection PyArgumentList
        return tuple.__new__(cls, c)

    def __init__(self, *args):
        super().__init__(*args)

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
    def __init__(self, pos=(0, 0), size=(0, 0),  max_velocity=(None, None)):
       super().__init__(pos, size)
       self.velocity = Pos(0, 0)
       self.acceleration = Pos(0, 0)
       self.max_velocity = max_velocity

    @property
    def pos(self):
        return Pos(self.topleft)

    @pos.setter
    def pos(self, value):
        self.topleft = value

    def update_pos(self):
        self.velocity += self.acceleration
        self.pos += self.velocity


class Space:
    def __init__(self, gravity=(0, 0)):
        self.gravity = gravity

    def add(self, *bodies):
        pass

    def simulate(self):
        pass