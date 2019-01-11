from functools import lru_cache

import pygame
import pymunk
from graphalama.maths import clamp

from maths import Pos, approx

MAX_SPEED = 80
MOVE_FORCE = 300
JUMP_IMPULSE = 50

class Player:
    def __init__(self):
        img = pygame.image.load("assets/fire2.png").convert()
        img.set_colorkey((255, 255, 255))
        self.img = pygame.transform.smoothscale(img, (8, 8))

        self.pos = Pos(32, 8)
        self.direction = [0, 0]  # (left, right)

        mass = 1
        self.body = pymunk.Body(mass, pymunk.inf)
        self.body.position = self.pos
        # self.shape = pymunk.Poly(self.body, self.get_poly())
        fire = pymunk.Circle(self.body, 4)
        # fire.elasticity = 1
        fire.friction = 1
        # feet = pymunk.Segment(self.body, (-4, 4), (4, 4), 0)
        self.shapes = (fire, )


    @property
    def light_pos(self):
        r = self.get_rect()
        return r.center + Pos(0, r.h/4)

    def event_loop(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                self.body.apply_impulse_at_local_point((0, -JUMP_IMPULSE), self.body.center_of_gravity)
            elif e.key == pygame.K_LEFT:
                # self.body.apply_impulse_at_local_point((-400, 0), self.body.center_of_gravity)
                self.direction[0] = True
            elif e.key == pygame.K_RIGHT:
                # self.body.apply_impulse_at_local_point((400, 0), self.body.center_of_gravity)
                self.direction[1] = True
            elif e.key == pygame.K_r:
                self.body.position = (32, 24)

        if e.type == pygame.KEYUP:
            if e.key == pygame.K_LEFT:
                self.direction[0] = False
            elif e.key == pygame.K_RIGHT:
                self.direction[1] = False

    def update(self):
        self.pos = approx(self.body.position)

        if self.direction[0]:
            # self.shapes[0].surface_velocity = MOVE_FORCE, 0
            self.body.apply_force_at_local_point((-MOVE_FORCE, 0), self.body.center_of_gravity)
        if self.direction[1]:
            # self.shapes[0].surface_velocity = -MOVE_FORCE, 0
            self.body.apply_force_at_local_point((MOVE_FORCE, 0), self.body.center_of_gravity)
        if not any(self.direction):
            # self.shapes[0].surface_velocity = 0, 0
            self.body.velocity = (self.body.velocity.x / 2, self.body.velocity.y)

        self.body.velocity = (clamp(self.body.velocity.x, -MAX_SPEED, MAX_SPEED),
                              clamp(self.body.velocity.y, -MAX_SPEED, MAX_SPEED))

    def get_rect(self):
        rect: pygame.Rect = self.img.get_rect()
        # rect.center = self.pos - (0, rect.h / 4)
        rect.center = self.pos
        return rect

    def render(self, display):
        r = self.get_rect()
        angle = approx(self.body.angle * 180 / 3.14159265358978)
        img = self.get_rotated(angle)
        rect = img.get_rect()
        rect.center = r.center
        display.blit(img, rect)

    def get_poly(self):
        r = self.get_rect()
        r.center = 0, 0
        return (r.topleft, r.bottomleft,
                r.bottomright, r.topright)

    def get_rotated(self, angle: int) -> pygame.Surface:
        return pygame.transform.rotate(self.img, angle)

