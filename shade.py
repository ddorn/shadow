#!/usr/bin/env python3
from math import floor, ceil
from random import randint, choice

import pygame
import pymunk
import pymunk.pygame_util

from maths import cast_shadow, segments
from player import Player
from vfx import np_limit_visibility

pygame.init()


def plateforme(x, y, size):
    x1 = BLOCK_SIZE * (x - floor(size / 2))
    x2 = BLOCK_SIZE * (x + floor(size / 2) + 1)
    y = BLOCK_SIZE * y
    return (
        (x1, y),
        (x2, y),
        (x2, y + BLOCK_SIZE),
        (x1, y + BLOCK_SIZE)
    )

def carre(x, y, side):
    return (
        (x, y),
        (x + side, y),
        (x + side, y + side),
        (x, y + side)
    )


BLOCK_SIZE = 8
GAME_SIZE = (320, 180)
SCREEN_SIZE = (1920, 1080)
LIGHT_COLOR = (248//2, 235//2, 68//2, 255)
SHADOW_COLOR = (20, 70, 80)
SIGHT = 80
SPEED = 10


class App:
    FPS = 60
    ENABLE_SHADOW = True
    ENABLE_DEBUG = False
    BLIT_MODE = 0

    def __init__(self):
        self.display = pygame.display.set_mode(SCREEN_SIZE)  # type: pygame.Surface
        self.back_screen = pygame.Surface(GAME_SIZE, pygame.SRCALPHA)
        self.clock = pygame.time.Clock()
        self.walls = self.create_walls(GAME_SIZE)
        for w in self.walls: print(w)
        self.sight = SIGHT
        self.frame = 0
        self.stop = False
        self.player = Player()
        self.space = self.create_space()
        self.dirt_img = pygame.image.load('assets/dirt.png').convert()

    def run(self):
        while not self.stop:
            self.frame += 1

            self.event_loop()
            self.update()

            self.render(self.back_screen)
            self.do_shadow()

            pygame.display.update()
            self.clock.tick(self.FPS)
            print("FPS:", round(self.clock.get_fps()), end='\r')

    def event_loop(self):
        for e in pygame.event.get():
            # quit
            if e.type == pygame.QUIT:
                self.stop = True
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.stop = True
                elif e.key == pygame.K_t:
                    self.ENABLE_SHADOW = not self.ENABLE_SHADOW
                elif e.key == pygame.K_p:
                    pygame.image.save(self.display, "shadows.png")
                elif e.key == pygame.K_m:
                    self.ENABLE_DEBUG = not self.ENABLE_DEBUG
                elif e.key == pygame.K_b:
                    self.BLIT_MODE += 1
                    self.BLIT_MODE %= 4
            self.player.event_loop(e)

    def update(self):
        i = self.frame % 60
        if i < 10:
            i //= 2
            self.sight = SIGHT + 5 * abs(i - 2)
        self.player.update()
        self.space.step(1/self.FPS)

    def render(self, surf):
        surf.fill(LIGHT_COLOR)
        # platforms
        for poly in self.walls[1:]:  # without the box
            pygame.draw.polygon(surf, (255, 255, 255), poly)
        for poly in self.walls[1:]:
            surf.blit(self.dirt_img, poly[0])

        self.player.render(surf)

    def do_shadow(self):
        s = pygame.Surface(GAME_SIZE)
        s.fill(SHADOW_COLOR)
        # self.display.fill(SHADOW_COLOR)
        if self.ENABLE_SHADOW:
            visible_poly = cast_shadow(self.walls, self.player.light_pos)
            rect = np_limit_visibility(self.back_screen, visible_poly, self.player.light_pos, self.sight, self.frame // 5 % 8)
            s.blit(self.back_screen, rect.topleft, rect)
        else:
            s.blit(self.back_screen, (0, 0))

        if self.ENABLE_DEBUG:
            self.draw_options.surface = s
            self.space.debug_draw(self.draw_options)

        if self.BLIT_MODE == 0:
            s = pygame.transform.scale(s, SCREEN_SIZE, self.display)
        if self.BLIT_MODE == 1:
            s = pygame.transform.smoothscale(s, SCREEN_SIZE)
        if self.BLIT_MODE >= 2:
            s = pygame.transform.scale2x(s)
            s = pygame.transform.scale2x(s)
        if self.BLIT_MODE == 3:
            s = pygame.transform.scale2x(s)

        self.display.blit(s, (0, 0))


    def create_walls(self, screensize):
        # lots of squares

        # for x in range(5):
        #     for y in range(5):
        #         topx = 200 + 80 * x
        #         topy = 50 + 80 * y
        #         walls.append(((topx, topy),
        #                      (topx + 40, topy),
        #                      (topx + 40, topy + 40),
        #                      (topx, topy + 40)))

        return [
            ((0, 0), (0, screensize[1] - 1), (screensize[0] - 1, screensize[1] - 1), (screensize[0] - 1, 0)),
            plateforme(2, 3, 1),
            # plateforme(6, 3, 1),
            plateforme(4, 4, 5),
            plateforme(0, 6, 1)
            # plateforme(3, 9, 1),
            # plateforme(9, 7, 2),
            # plateforme(12, 4, 4),
            # plateforme(11, 12, 4),
            # plateforme(20, 24, 20),
        ]

    def create_space(self):
        space = pymunk.Space()
        space.gravity = 0, 50

        for poly in self.walls[1:]:
            a, b, c, d = poly
            # b = b[0] + 1, b[1]
            # c = c[0] + 1, c[1] + 1
            # d = d[0], d[1] + 1
            p = pymunk.Poly(space.static_body, (a, b, c, d))
            # p.elasticity = 100
            p.friction = 1
            space.add(p)

        for a, b in segments(self.walls[0]):
            p = pymunk.Segment(space.static_body, a, b, 1)
            p.friction = 1
            space.add(p)


        space.add(self.player.body, *self.player.shapes)

        pymunk.pygame_util.positive_y_is_up = False
        self.draw_options = pymunk.pygame_util.DrawOptions(self.display)
        return space



if __name__ == '__main__':
    App().run()
