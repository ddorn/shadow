#!/usr/bin/env python3
from random import randint, choice

import pygame
from graphalama.maths import Pos

from maths import cast_shadow
from vfx import limit_visibility

pygame.init()
pygame.key.set_repeat(50, 20)

SIGHT = 200

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


def create_walls(screensize):
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
        ((0, 0), (0, screensize[1]), screensize, (screensize[0], 0)),
        plateforme(100, 100, 60),
        plateforme(400, 200, 100),
        plateforme(300, 400, 80),
        plateforme(600, 300, 200)
    ]


def main():
    """Sexy shadows"""

    LIGHT_COLOR = (200, 180, 100)
    SIGHT = 300

    # pygame stuff
    screensize = (800, 500)
    display = pygame.display.set_mode(screensize)
    clock = pygame.time.Clock()

    # mygame stuff
    walls = create_walls(screensize)
    # mask = light_mask(SIGHT)

    wig = (0, 0)
    wiggle = ((-1, 0), (0, 1), (1, 0), (0, -1))

    frame = 0
    while True:
        frame += 1

        # update
        for e in pygame.event.get():
            # quit
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return

        if frame % 10 == 1:
            # every 10 frame
            wig = choice(wiggle)
        mouse = Pos(pygame.mouse.get_pos()) + wig

        # logic

        visible_poly = cast_shadow(walls, mouse)

        # surface with the what you can see
        visible = pygame.Surface(display.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(visible, LIGHT_COLOR, visible_poly)
        # blured(visible, 4)
        # blured_visi = blured(visible, 20)
        # pygame.draw.polygon(visible, (255, 165, 0), visible_poly)
        # visible.blit(blured(visible), (0, 0))
        # visible = blured_visi

        # for poly in walls[1:]:  # without the box
        #     pygame.draw.polygon(visible, (255, 255, 255), poly)

        delta = mouse - (SIGHT, SIGHT)
        # mask = limit of vision + effects
        # now limited to what you can see
        # m.blit(visible, -delta, None, pygame.BLEND_RGBA_MIN)
        # m = blured(m)

        # s.blit(mask, (0, 0), None, pygame.BLEND_RGBA_MIN)

        limit_visibility(visible, mouse, SIGHT, frame // 5 % 8)
        display.fill((20, 30, 40))
        display.blit(visible, (0, 0))

        # render
        # pygame.draw.polygon(display, (255, 165, 0), inters)
        # display.blit(m, delta)
        # display.blit(s, (mouse[0] - 150, mouse[1] - 150))
        # for poly in walls[1:]:
        #     pygame.draw.aalines(display, (255, 0, 0), True, poly)
        # for inter in inters:
        #     pygame.draw.line(display, (255, 255, 255), mouse, inter)
        pygame.display.update()
        clock.tick(60)
        print(round(clock.get_fps()))


if __name__ == '__main__':
    main()
