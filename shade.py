#!/usr/bin/env python3
from random import randint, choice

import pygame
from graphalama.maths import Pos

from maths import cast_shadow
from vfx import np_limit_visibility

pygame.init()
pygame.key.set_repeat(50, 20)

def plateforme(x, y, size):
    x1 = x - size / 2
    x2 = x + size / 2
    x3 = randint(x - int(size / 3), x + int(size / 3))
    return (
        (x1, y),
        (x2, y),
        (x3, y + size / 2)
    )

def carre(x, y, side):
    return (
        (x, y),
        (x + side, y),
        (x + side, y + side),
        (x, y + side)
    )


def main():
    """Sexy shadows"""

    wig = (0, 0)
    wiggle = ((-1, 0), (0, 1), (1, 0), (0, -1))

    while True:

        if frame % 10 == 1:
            # every 10 frame
            wig = choice(wiggle)
        mouse = Pos(pygame.mouse.get_pos()) + wig


SCREEN_SIZE = (800, 500)
SCREEN_SIZE = (1920, 1080)
LIGHT_COLOR = (200, 180, 100)
SHADOW_COLOR = (20, 70, 80)
SIGHT = 300

class App:
    FPS = 60
    ENABLE_SHADOW = True

    def __init__(self):
        self.display = pygame.display.set_mode(SCREEN_SIZE)  # type: pygame.Surface
        self.back_screen = pygame.Surface(self.display.get_size(), pygame.SRCALPHA)
        self.clock = pygame.time.Clock()
        self.walls = self.create_walls(SCREEN_SIZE)
        self.sight = SIGHT
        self.frame = 0
        self.stop = False
        self.pos = (0, 0)

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

        self.pos = pygame.mouse.get_pos()

    def update(self):
        i = self.frame % 60
        if i < 10:
            i //= 2
            self.sight = SIGHT + 5 * abs(i - 2)

    def render(self, surf):
        surf.fill(LIGHT_COLOR)
        # platforms
        for poly in self.walls[1:]:  # without the box
            pygame.draw.polygon(surf, (255, 255, 255), poly)

    def do_shadow(self):
        if self.ENABLE_SHADOW:
            visible_poly = cast_shadow(self.walls, self.pos)
            np_limit_visibility(self.back_screen, visible_poly, self.pos, self.sight, self.frame // 5 % 8)
        self.display.fill(SHADOW_COLOR)
        self.display.blit(self.back_screen, (0, 0))


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
            plateforme(100, 100, 60),
            plateforme(400, 200, 100),
            plateforme(300, 400, 80),
            plateforme(600, 300, 200)
        ]


if __name__ == '__main__':
    App().run()
