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

    def __eq__(self, other):
        return self.x == other[0] and self.y == other[1]

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

    def __radd__(self, other):
        return Pos(self.x + other[0], self.y + other[1])

    def __sub__(self, other):
        return Pos(self[0] - other[0], self[1] - other[1])

    def __rsub__(self, other):
        return Pos(other[0] - self[0], other[1] - self[1])

    def __neg__(self):
        return Pos(-self[0], -self[1])

    def __mul__(self, other):
        return Pos(self[0] * other, self[1] * other)

    def __rmul__(self, other):
        return Pos(self.x * other, self.y * other)

    def __truediv__(self, other: int):
        return Pos(self[0] / other, self[1] / other)

    def __floordiv__(self, other: int):
        return Pos(self[0] // other, self[1] // other)

    @property
    def t(self):
        """The vector as a tuple"""
        return self[0], self[1]

    @property
    def ti(self):
        """The vector as a tuple of integer (round to closest)"""
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
        return Pos(c * self[0] + s * self[1],
                   s * self[0] - c * self[1])

    def copy(self):
        return Pos(self.x, self.y)


class AABB:
    """Axis aligned rectangle: the basic shape."""

    def __init__(self, *args):
        if len(args) == 1:
            args = args[0]

        if isinstance(args, (pygame.rect.RectType, AABB)):
            tl = args.topleft
            s = args.size
        elif len(args) == 0:
            tl = 0, 0
            s = 0, 0
        elif len(args) == 2:
            tl = args[0]
            s = args[1]
        elif len(args) == 4:
            tl = args[:2]
            s = args[2:]
        else:
            raise TypeError(f"Arguments are not in a rect style: {args}")

        self.topleft = Pos(tl)
        self.size = Pos(s)

    def __repr__(self):
        return f"<AABB({self.x}, {self.y}, {self.size.x}, {self.size.y})>"

    def collide(self, other):
        return self.collide_aabb(other)

    def collide_aabb(self, other):
        """
        Check this collides with an AABB.

        Rects do collide even if they have only an edge in common.
        This is different that the pygame.colliderect function.
        So an AABB(0, 0, 4, 4) and AABB(0, 4, 4, 4) will not collide.

        :type other: AABB
        """

        # the collide in 2D if they collide on both axis
        if self.right <= other.left or other.right <= self.left:
            return False
        if self.bottom <= other.top or other.bottom <= self.top:
            # the condition is the way because the y axis is inverted
            return False

        return True

    @property
    def center(self):
        return self.topleft + self.half_size

    @center.setter
    def center(self, value):
        self.topleft = Pos(value) - self.half_size

    @property
    def half_size(self):
        return self.size / 2

    @property
    def left(self):
        return self.topleft.x

    @left.setter
    def left(self, value):
        self.topleft.x = value

    x = left

    @property
    def right(self):
        return self.topleft.x + self.size.x

    @right.setter
    def right(self, value):
        self.topleft.x = value - self.size.x

    @property
    def bottom(self):
        return self.topleft.y + self.size.y

    @bottom.setter
    def bottom(self, value):
        self.topleft.y = value - self.size.y

    @property
    def top(self):
        return self.topleft.y

    @top.setter
    def top(self, value):
        self.topleft.y = value

    y = top

    @property
    def pygame_rect(self):
        return pygame.Rect(self.topleft, self.size)


class Body:
    """A moving object."""

    def __init__(self, shape, max_velocity=(None, None), moving=False, space=None):
        self.shape = shape  # type: AABB
        self.space = space  # type: Space

        self.velocity = Pos(0, 0)
        self.max_velocity = Pos(max_velocity)
        self.acceleration = Pos(0, 0)

        self.moving = moving

        self.collide_left = False
        self.collide_down = False
        self.collide_right = False
        self.collide_top = False

    def __repr__(self):
        return f"<Body: s {self.shape}, v {self.velocity}, a {self.acceleration}>"

    @property
    def pos(self):
        return self.shape.topleft

    def update_x(self, shapes):
        """Updates the position on the x coordinate and check for collision with the shapes."""
        self.velocity.x += self.acceleration.x
        self.clamp_speed()
        self.shape.x += self.velocity.x


        intersect = [s for s in shapes if self.shape.collide(s)]

        if self.velocity.x > 0:
            # we are going right
            for body in intersect:
                if body.left < self.shape.right:
                    self.shape.right = body.left
                    self.velocity.x = 0
        elif self.velocity.x < 0:
            # we are going left
            for body in intersect:
                if self.shape.left < body.right:
                    self.shape.left = body.right
                    self.velocity.x = 0

        self.acceleration.x = 0

    def update_y(self, shapes):
        self.grounded = False

        self.velocity.y += self.acceleration.y
        self.clamp_speed()
        self.shape.y += self.velocity.y

        intersect = [s for s in shapes if self.shape.collide(s)]

        if self.velocity.y > 0:
            # we are going down
            for body in intersect:
                if self.shape.bottom > body.top:
                    self.shape.bottom = body.top
                    self.velocity.y = 0
                    self.grounded = True
        elif self.velocity.y < 0:
            # we are going up
            for body in intersect:
                if body.bottom > self.shape.top:
                    self.shape.top = body.bottom
                    self.velocity.y = 0

        self.acceleration.y = 0

    def clamp_speed(self):
        prev = self.velocity.copy()
        if self.max_velocity.x is not None:
            self.velocity.x = clamp(self.velocity.x, -self.max_velocity.x, self.max_velocity.x)
        if self.max_velocity.y is not None:
            self.velocity.y = clamp(self.velocity.y, -self.max_velocity.y, self.max_velocity.y)

        if self.velocity != prev:
            print("VELOCITY CLAMPED:", prev)

class Space:
    def __init__(self, gravity=(0, 0)):
        self.gravity = Pos(gravity)
        self.static_bodies = []  # type: List[Body]
        self.moving_bodies = []  # type: List[Body]

    def add(self, *bodies):
        for body in bodies:
            if isinstance(body, AABB):
                self.static_bodies.append(body)
            else:
                self.moving_bodies.append(body)

    def simulate(self):
        for body in self.moving_bodies:
            body.acceleration += self.gravity

        # check collision horizontally
        # we don't do both at the same time because it simplifies A LOT the thing
        # plus it's accurate enough

        for body in self.moving_bodies:
            body.update_x(self.static_bodies)

        # check collision vertically
        for body in self.moving_bodies:
            body.update_y(self.static_bodies)

if __name__ == '__main__':
    a = AABB(0, 0, 5, 5)
    b = AABB(0, 5, 5, 5)
    print(a.collide(b))