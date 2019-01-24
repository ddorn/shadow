#!/usr/bin/env python3

import os
from colorsys import hsv_to_rgb
from functools import lru_cache
from random import random

import pygame
from graphalama.text import SimpleText
from visibility import VisibiltyCalculator

from apple import TileMap
from light import GlobalLightMask, RainbowLight
from maths import segments, Pos
from physics import Space, AABB
from player import Player

pygame.init()

BLOCK_SIZE = 16
SCREEN_SIZE = pygame.display.list_modes()[0]
GAME_SIZE = (480, 270)
SKY_COLOR = (255, 255, 255)
SHADOW_POLY_EXTEND = 5
GRAVITY = (0, 0.2)


def random_color():
    """Return a randomly chosen color, with max brightness and saturation."""
    hue = random()
    rgb = hsv_to_rgb(hue, 1, 1)
    color = [round(c * 255) for c in rgb]
    return color


@lru_cache(maxsize=None)
def random_cached_color(*args):
    """
    Same as random_color, but return the same color, if you pass the same args
    This is useful when I want to use random colors for something but don't bother saving it.
    """
    return random_color()


class App:
    UPDATE_FPS = 60
    FPS = 600

    # Feature flags
    ENABLE_SHADOW = True  # [s] to toggle shadows
    MOUSE_CONTROL = False  # [m] so the player follow the mouse
    DEBUG = False  # [d] to maybe discover bugs

    def __init__(self):
        self.display = pygame.display.set_mode(SCREEN_SIZE)  # type: pygame.Surface
        # Everything is made on a small surface, that is then scaled to the display resolution
        # There two reasons:
        #   - Get the pixel "art" look
        #   - Performance, as I can't blur efficiently a huge surface, and the cool look of the lights
        #       comes from the blur
        self.back_screen = pygame.Surface(GAME_SIZE)
        self.clock = pygame.time.Clock()
        self.frame = 0
        self.stop = False

        # Environment
        self.map = TileMap.load('assets/levels/0')
        self.walls = self.map.collision_rects()

        # Physics
        self.player = Player()
        self.space = self.create_space()

        # Lights
        self.shadow_caster = VisibiltyCalculator(self.create_shadow_walls(GAME_SIZE))
        lights = [self.player.light]  # , *self.gen_lights()]
        self.light_mask = GlobalLightMask(lights, GAME_SIZE, self.shadow_caster, (30, 30, 30))

        # UI
        self.fps_text = SimpleText("Be love", (20, 20), color=(255, 180, 180))
        self.bg = pygame.image.load("assets/bg.gif").convert()  # type: pygame.Surface
        self.bg.fill((50,)*3, None, pygame.BLEND_RGB_ADD)

    def run(self):
        accu = 0
        while not self.stop:

            # Updating
            while accu > 1000 / self.UPDATE_FPS:
                # We want to get that stable 60 fps update whatever the rendering takes
                accu -= 1000 / self.UPDATE_FPS
                self.frame += 1
                self.event_loop()
                self.update()

            # Rendering is done in two steps
            # First we render our game as we would usualy do, on the back_screen surface
            self.render(self.back_screen)
            # But then we apply the shadows on back_screen and put the result (scaled) on the display
            self.do_shadow()
            # on top of everything else
            self.fps_text.render(self.display)

            pygame.display.update()

            # FPS
            accu += self.clock.tick(self.FPS)
            self.fps_text.text = f"FPS: {round(self.clock.get_fps())}"

    def event_loop(self):

        # Bindings:
        #   - [Esq] Quit
        #   - [s]   Toggle shadows
        #   - [p]   Screenshot
        #   - [m]   Player follow mouse
        #   - [l]   Re-generate lights
        #   - [d]   Toggle debug mode

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.stop = True
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.stop = True
                elif e.key == pygame.K_s:
                    self.ENABLE_SHADOW = not self.ENABLE_SHADOW
                elif e.key == pygame.K_p:
                    pygame.image.save(self.display, "shadows.png")
                    print(f"\033[32mScreenshot saved at '{os.path.abspath('screenshots/shadows.png')}'.\033[m")
                elif e.key == pygame.K_m:
                    self.MOUSE_CONTROL = not self.MOUSE_CONTROL
                elif e.key == pygame.K_l:
                    if len(self.light_mask.lights) == 1:
                        lights = [self.player.light, *self.gen_lights()]
                    else:
                        lights = [self.player.light]
                    self.light_mask.lights = lights
                elif e.key == pygame.K_d:
                    self.DEBUG = not self.DEBUG
            self.player.event_loop(e)

    def update(self):
        # Apply gravity / collisions and stuff
        self.space.simulate()

        if self.MOUSE_CONTROL:
            self.player.body.shape.center = Pos(pygame.mouse.get_pos()) // 4

        # Update light position, update from input etc for next frame
        # This should be before space.simulate, but I need to put it after the MOUSE_CONTROL
        # Otherwise the player is moved and is not on the mouse
        self.player.update()

    def render(self, surf):
        # surf.fill(SKY_COLOR)
        surf.blit(self.bg, (0, 0))

        # Platforms
        self.map.render(surf)

        # Player
        self.player.render(surf)

        if self.DEBUG:
            # segments that block the light
            for a, b in self.map.light_blockers():
                color = random_cached_color(a, b)
                pygame.draw.line(surf, color, a, b)

    def do_shadow(self):
        # It is not really the main part of the shadow, the interesting stuff is in light.py and vfx.py

        if self.ENABLE_SHADOW:
            self.update_light_mask()
            self.light_mask.apply_light_on(self.back_screen)

        # we scale our mini surface to the real one, with the nearest pixel (we don't want to blur
        pygame.transform.scale(self.back_screen, SCREEN_SIZE, self.display)

    def create_shadow_walls(self, screensize):
        walls = self.map.light_blockers()
        # The bounding rect of the light, shadow casting doesn't work without
        bound = pygame.Rect(-5, -5, screensize[0] + 10, screensize[1] + 10)
        walls.extend(segments((bound.topleft, bound.topright,
                               bound.bottomright, bound.bottomleft)))
        return walls

    def create_space(self):

        space = Space(GRAVITY)

        # TODO: use the tilemap for collision instead
        for rect in self.walls:
            p = AABB(rect.topleft, rect.size)
            space.add(p)

        space.add(self.player.body)

        return space

    def update_light_mask(self):
        # We update the light masks every second frame, there is no need to do it more often
        # as it means more computation for very noticeable change
        if self.frame % 2 == 0:
            self.light_mask.lights = self.player.get_all_lights()
            self.light_mask.update_mask()
        # Every 6 frames we cycle through the variants, so the edge of the lights appear wiggling (?) like a fire
        if self.frame % 6 == 0:
            for l in self.light_mask.lights:
                l.next_variant()

    def gen_lights(self):
        lights = [
            RainbowLight((100, 140), loop_time=3, range=80, variants=4),
            RainbowLight((124, 16), loop_time=7, range=150, variants=4),
            RainbowLight((210, 128), loop_time=10, range=200, variants=4),
            RainbowLight((310, 112), loop_time=6, range=100, variants=4),
            RainbowLight((400, 48), loop_time=7, range=100, variants=4),
            RainbowLight((426, 172), 0.5, loop_time=10, range=150, variants=4),
        ]

        return lights


if __name__ == '__main__':
    App().run()
