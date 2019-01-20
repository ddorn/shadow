#!/usr/bin/env python3
import os
from colorsys import hsv_to_rgb
from functools import lru_cache
from random import randint, random

import numpy as np
import pygame
from graphalama.draw import polygon
from graphalama.text import SimpleText
from visibility import VisibiltyCalculator

from apple import Map
from light import GlobalLightMask, Light
from maths import segments, Pos, expand_poly, clip_poly_to_rect
from physics import Space, AABB
from player import Player
from vfx import np_blit_rect, POLY

pygame.init()

BLOCK_SIZE = 16
GAME_SIZE = (480, 270)
SCREEN_SIZE = (1920, 1080)
LIGHT_COLOR = (255, 170, 100)
SKY_COLOR = (255, 255, 255)
SHADOW_COLOR = (20, 70, 80)
SHADOW_COLOR = (0, 0, 0)
SHADOW_POLY_EXTEND = 5
SPEED = 10

def random_color():
    hue = random()
    rgb = hsv_to_rgb(hue, 1, 1)
    color = [int(c * 255) for c in rgb]
    return color

@lru_cache(maxsize=None)
def random_cached_color(*args):
    return random_color()


def gen_random_lights():
    ret = []
    for i in range(5):
        pos = randint(0, GAME_SIZE[0]), randint(0, GAME_SIZE[1])
        ran = (random() + 1) * 128
        ran = int(ran // 20 * 20)

        ret.append(Light(pos, random_color(), ran))

    return ret


class App:
    FPS = 60
    ENABLE_SHADOW = True
    MOUSE_CONTROL = False
    DEBUG = False

    def __init__(self):
        self.display = pygame.display.set_mode(SCREEN_SIZE)  # type: pygame.Surface
        self.back_screen = pygame.Surface(GAME_SIZE)
        self.clock = pygame.time.Clock()
        self.map = Map.load('assets/levels/0', )
        self.walls = self.map.collision_rects()
        self.frame = 0
        self.stop = False
        self.player = Player()
        self.shadow_caster = VisibiltyCalculator(self.create_shadow_walls(GAME_SIZE))
        lights = [self.player.light]
        self.light_mask = GlobalLightMask(lights, GAME_SIZE, self.shadow_caster)
        self.space = self.create_space()
        self.fps_text = SimpleText("Coucou", (20, 20), color=(255, 180, 180))

    def run(self):
        while not self.stop:
            self.frame += 1

            self.event_loop()
            self.update()

            self.render(self.back_screen)
            self.do_shadow()
            self.fps_text.render(self.display)

            pygame.display.update()

            self.clock.tick(self.FPS)
            print("FPS:", round(self.clock.get_fps()), end='\r')
            self.fps_text.text = f"FPS: {round(self.clock.get_fps())}"

    def event_loop(self):
        for e in pygame.event.get():
            # quit
            if e.type == pygame.QUIT:
                self.stop = True
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.stop = True
                elif e.key == pygame.K_s:
                    self.ENABLE_SHADOW = not self.ENABLE_SHADOW
                elif e.key == pygame.K_p:
                    pygame.image.save(self.display, "shadows.png")
                    print(f"\033[32mScreenshot saved at '{os.path.abspath('shadows.png')}'.\033[m")
                elif e.key == pygame.K_m:
                    self.MOUSE_CONTROL = not self.MOUSE_CONTROL
                elif e.key == pygame.K_l:
                    if len(self.light_mask.lights) == 1:
                        lights = [self.player.light, *gen_random_lights()]
                    else:
                        lights = [self.player.light]
                    self.light_mask.lights = lights
                elif e.key == pygame.K_d:
                    self.DEBUG = not self.DEBUG
            self.player.event_loop(e)

    def update(self):
        self.space.simulate()

        if self.MOUSE_CONTROL:
            self.player.body.shape.center = Pos(pygame.mouse.get_pos()) // 4

        self.player.update()

    def render(self, surf):
        surf.fill(SKY_COLOR)
        # platforms
        for pos in self.map:
            img = self.map.get_chached_image_at(pos, 1)
            r = self.map.pos_to_rect(pos)
            surf.blit(img, r)

        if self.DEBUG:
            poly = POLY[0]
            tl = self.player.light.topleft
            poly = [(p[0] + tl[0], p[1] + tl[1]) for p in poly]
            pygame.draw.lines(surf, (0, 0, 0), True, poly)

            for a, b in self.map.shadow_blockers():
                color = random_cached_color(a, b)
                pygame.draw.line(surf, color, a, b)

        self.player.render(surf)

    def do_shadow(self):
        s = pygame.Surface(GAME_SIZE)

        if self.ENABLE_SHADOW:
            self.update_light_mask()
            self.back_screen.blit(self.light_mask.surf_mask, (0, 0), None,
                                  pygame.BLEND_RGB_MULT)

        s.blit(self.back_screen, (0, 0))

        pygame.transform.scale(s, SCREEN_SIZE, self.display)

    def create_shadow_walls(self, screensize):
        shadow_block = self.map.shadow_blockers()
        bound = pygame.Rect(-5, -5, screensize[0] + 10, screensize[1] + 10)
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

    def update_light_mask(self):
        if self.frame % 2 == 0:
            self.light_mask.update_mask()
        if self.frame % 6 == 0:
            for l in self.light_mask.lights:
                l.next_variant()


if __name__ == '__main__':
    App().run()
