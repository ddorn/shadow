from collections import namedtuple
from math import cos, sin, pi, sqrt
from typing import List

import pygame

from maths import clamp


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
        return f"Pos({round(self.x, 3)}, {round(self.y, 3)})"

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
    def __init__(self, pos=(0, 0), size=(0, 0),  max_velocity=(None, None), moving=False, space=None):
        super().__init__(pos, size)
        self.velocity = Pos(0, 0)
        self.acceleration = Pos(0, 0)
        self.max_velocity = Pos(max_velocity)
        self.moving = moving
        self.space = space  # type: Space

    @property
    def pos(self):
        return Pos(self.topleft)

    def update_x(self, static_bodies):
        self.velocity.x += self.acceleration.x
        if self.max_velocity.x is not None:
            self.velocity.x = clamp(self.velocity.x, -self.max_velocity.x, self.max_velocity.x)
        self.x += self.velocity.x

        intersect = self.collidelistall(static_bodies)
        intersect = [static_bodies[i] for i in intersect]

        if self.velocity.x > 0:
            # we are going right
            for body in intersect:
                if body.left < self.right:
                    self.right = body.left
                    self.velocity.x = 0
        elif self.velocity.x < 0:
            # we are going left
            for body in intersect:
                if self.left < body.right:
                    self.left = body.right
                    self.velocity.x = 0

        self.acceleration.x = 0


    def update_y(self, static_bodies):
        self.velocity.y += self.acceleration.y
        if self.max_velocity.y is not None:
            self.velocity.y = clamp(self.velocity.y, -self.max_velocity.y, self.max_velocity.y)
        self.y += self.velocity.y

        intersect = self.collidelistall(static_bodies)
        intersect = [static_bodies[i] for i in intersect]

        if self.velocity.y > 0:
            # we are going down
            for body in intersect:
                if self.bottom > body.top:
                    self.bottom = body.top
                    self.velocity.y = 0
        elif self.velocity.y < 0:
            # we are going up
            for body in intersect:
                if body.bottom > self.top:
                    self.top = body.bottom
                    self.velocity.y = 0

        self.acceleration.y = 0

class Space:
    def __init__(self, gravity=(0, 0)):
        self.gravity = Pos(gravity)
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
            body.acceleration += self.gravity

        # check colision horizontaly
        # we don't do both at the same time because it simplifies A LOT the thing
        # plus it's accurate enough
        for body in self.moving_bodies:
            body.update_x(self.static_bodies)

        # check colision verticaly
        for body in self.moving_bodies:
            body.update_y(self.static_bodies)



