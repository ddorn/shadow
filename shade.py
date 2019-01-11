#!/usr/bin/env python3

from math import floor

import pygame

from maths import cast_shadow
from physics import Space, Body
from player import Player
from vfx import np_limit_visibility

pygame.init()


BLOCK_SIZE = 8
GAME_SIZE = (320, 180)
SCREEN_SIZE = (1920, 1080)
LIGHT_COLOR = (248//2, 235//2, 68//2, 255)
SHADOW_COLOR = (20, 70, 80)
SIGHT = 80
SPEED = 10


def platform(x, y, size):
    x1 = BLOCK_SIZE * (x - floor(size / 2))
    y = BLOCK_SIZE * y
    r = pygame.Rect((x1, y), (size * BLOCK_SIZE, BLOCK_SIZE))
    return r


class App:
    FPS = 60
    ENABLE_SHADOW = True
    BLIT_MODE = 0

    def __init__(self):
        self.display = pygame.display.set_mode(SCREEN_SIZE)  # type: pygame.Surface
        self.back_screen = pygame.Surface(GAME_SIZE, pygame.SRCALPHA)
        self.clock = pygame.time.Clock()
        self.walls = self.create_walls(GAME_SIZE)
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
                elif e.key == pygame.K_b:
                    self.BLIT_MODE += 1
                    self.BLIT_MODE %= 4
            self.player.event_loop(e)

    def update(self):
        i = self.frame % 60
        if i < 10:
            i //= 2
            self.sight = SIGHT + 5 * abs(i - 2)

        self.space.simulate()
        self.player.update()

    def render(self, surf):
        surf.fill(LIGHT_COLOR)
        # platforms
        for rect in self.walls[1:]:  # without the box
            surf.fill((255, 255, 255), rect)
        for rect in self.walls[1:]:
            surf.blit(self.dirt_img, rect.topleft)

        self.player.render(surf)

    def do_shadow(self):
        s = pygame.Surface(GAME_SIZE)
        s.fill(SHADOW_COLOR)

        if self.ENABLE_SHADOW:
            walls = tuple((p.topleft, p.bottomleft, p.bottomright, p.topright) for p in self.walls)
            visible_poly = cast_shadow(walls, self.player.light_pos)
            rect = np_limit_visibility(self.back_screen, visible_poly, self.player.light_pos, self.sight, self.frame // 5 % 8)
            s.blit(self.back_screen, rect.topleft, rect)
        else:
            s.blit(self.back_screen, (0, 0))

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

        return [
            pygame.Rect((0, 0), GAME_SIZE),
            platform(2, 3, 1),
            platform(6, 3, 1),
            platform(4, 4, 5),
            platform(0, 6, 1),
            platform(3, 9, 1),
            platform(9, 7, 2),
            platform(12, 4, 4),
            platform(11, 12, 4),
            platform(20, 24, 20),
        ]

    def create_space(self):

        space = Space((0, 0.1))

        for rect in self.walls[1:]:
            p = Body(rect.topleft, rect.size)
            space.add(p)

        space.add(self.player.body)
        self.player.body.space = space

        return space



if __name__ == '__main__':
    App().run()
