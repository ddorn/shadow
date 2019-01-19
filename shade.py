#!/usr/bin/env python3

from math import floor

import pygame
from visibility import VisibiltyCalculator

from apple import Map
from maths import segments, Pos
from physics import Space, AABB
from player import Player
from vfx import np_limit_visibility

pygame.init()

BLOCK_SIZE = 16
GAME_SIZE = (480, 270)
SCREEN_SIZE = (1920, 1080)
LIGHT_COLOR = (248 // 2, 235 // 2, 68 // 2, 255)
SHADOW_COLOR = (20, 70, 80)
SIGHT = 80
SPEED = 10


class App:
    FPS = 60
    ENABLE_SHADOW = True
    BLIT_MODE = 0
    MOUSE_CONTROL = False

    def __init__(self):
        self.display = pygame.display.set_mode(SCREEN_SIZE)  # type: pygame.Surface
        self.back_screen = pygame.Surface(GAME_SIZE, pygame.SRCALPHA)
        self.clock = pygame.time.Clock()
        self.map = Map.load('assets/levels/0', )
        self.walls = self.map.collision_rects()
        self.shadow_caster = VisibiltyCalculator(self.create_shadow_walls(GAME_SIZE))
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
                    self.BLIT_MODE %= 8
                elif e.key == pygame.K_m:
                    self.MOUSE_CONTROL = not self.MOUSE_CONTROL
            self.player.event_loop(e)

    def update(self):
        i = self.frame % 60
        if i < 10:
            i //= 2
            self.sight = SIGHT + 5 * abs(i - 2)

        self.space.simulate()
        self.player.update()
        if self.MOUSE_CONTROL:
            self.player.body.shape.topleft = Pos(pygame.mouse.get_pos()) // 6

    def render(self, surf):
        surf.fill(LIGHT_COLOR)
        # platforms
        for pos in self.map:
            img = self.map.get_image_at(pos, 1)
            r = self.map.pos_to_rect(pos)
            surf.blit(img, r)

        self.player.render(surf)

    def do_shadow(self):
        s = pygame.Surface(GAME_SIZE)
        s.fill(SHADOW_COLOR)

        if self.ENABLE_SHADOW:
            visible_poly = self.shadow_caster.visible_polygon(self.player.light_pos)
            rect = np_limit_visibility(self.back_screen, visible_poly, self.player.light_pos, self.sight,
                                       self.frame // 5 % 8)
            s.blit(self.back_screen, rect.topleft, rect)
        else:
            s.blit(self.back_screen, (0, 0))

        if self.BLIT_MODE == 0:
            s = pygame.transform.scale(s, SCREEN_SIZE, self.display)
        elif self.BLIT_MODE == 1:
            s = pygame.transform.smoothscale(s, SCREEN_SIZE)
        elif self.BLIT_MODE == 2:
            # we do nothing
            pass
        elif self.BLIT_MODE == 3:
            s = pygame.transform.scale2x(s)
        elif self.BLIT_MODE == 4:
            s = pygame.transform.scale2x(s)
            s = pygame.transform.scale2x(s)
        else:
            scale = self.BLIT_MODE - 3
            s = pygame.transform.scale(s, (GAME_SIZE[0] * scale, GAME_SIZE[1] * scale))


        self.display.blit(s, (0, 0))

    def create_shadow_walls(self, screensize):
        shadow_block = self.map.unoptimized_shadow_blockers()
        bound = pygame.Rect((0, 0), GAME_SIZE)
        shadow_block.extend(segments((bound.topleft, bound.topright,
                                      bound.bottomright, bound.bottomleft)))
        return shadow_block

    def create_space(self):

        space = Space((0, 0.2))

        for rect in self.walls:
            p = AABB(rect.topleft, rect.size)
            space.add(p)

        space.add(self.player.body)
        self.player.body.space = space

        return space


if __name__ == '__main__':
    App().run()
