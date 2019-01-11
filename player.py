from functools import lru_cache

import pygame
import pymunk
from graphalama.maths import clamp

from maths import Pos

MAX_SPEED = 400
MOVE_FORCE = 10000

class Player:
    def __init__(self):
        img = pygame.image.load("assets/fire.png").convert_alpha()
        self.img = pygame.transform.smoothscale(img, (55, 110))

        self.pos = Pos(400, 70)
        self.direction = [0, 0]  # (left, right)

        mass = 1
        self.body = pymunk.Body(mass, pymunk.inf)
        self.body.position = self.pos
        self.shape = pymunk.Poly(self.body, self.get_poly())
        self.shape.friction = 0

    @property
    def light_pos(self):
        r = self.get_rect()
        return r.center + Pos(0, r.h/4)

    def event_loop(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                self.body.apply_impulse_at_local_point((0, -400), self.body.center_of_gravity)
            elif e.key == pygame.K_LEFT:
                # self.body.apply_impulse_at_local_point((-400, 0), self.body.center_of_gravity)
                self.direction[0] = True
            elif e.key == pygame.K_RIGHT:
                # self.body.apply_impulse_at_local_point((400, 0), self.body.center_of_gravity)
                self.direction[1] = True

        if e.type == pygame.KEYUP:
            if e.key == pygame.K_LEFT:
                self.direction[0] = False
            elif e.key == pygame.K_RIGHT:
                self.direction[1] = False

    def update(self):
        self.pos = Pos(self.body.position)

        if self.direction[0]:
            self.body.apply_force_at_world_point((-MOVE_FORCE, 0), (0, 0))
        if self.direction[1]:
            self.body.apply_force_at_world_point((MOVE_FORCE, 0), (0, 0))
        # if not any(self.direction):
        #     self.body.velocity = (0, self.body.velocity.y)

        self.body.velocity = (clamp(self.body.velocity.x, -MAX_SPEED, MAX_SPEED),
                              clamp(self.body.velocity.y, -MAX_SPEED, MAX_SPEED))

    def get_rect(self):
        rect: pygame.Rect = self.img.get_rect()
        # rect.center = self.pos - (0, rect.h / 4)
        rect.center = self.pos
        return rect

    def render(self, display):
        display.blit(self.img, self.get_rect())

    def get_poly(self):
        r = self.get_rect()
        r.center = 0, 0
        return (r.topleft, r.bottomleft, r.bottomright, r.topright)

