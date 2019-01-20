#!/usr/bin/env python3

import os
from colorsys import hsv_to_rgb
from functools import lru_cache
from random import randint, random

import pygame
from graphalama.text import SimpleText
from visibility import VisibiltyCalculator

from apple import Map
from light import GlobalLightMask, Light
from maths import segments, Pos
from physics import Space, AABB
from player import Player
from vfx import POLY

pygame.init()

BLOCK_SIZE = 16
GAME_SIZE = (480, 270)
SCREEN_SIZE = pygame.display.list_modes()[0]
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


def gen_random_lights(nb_lights=5):
    """Generate nb_lights with a random color, position and range"""

    ret = []
    for i in range(nb_lights):
        pos = randint(0, GAME_SIZE[0]), randint(0, GAME_SIZE[1])
        range_ = (random() + 1) * 128
        # we take them in steps of 20, to often get the same range -> less mask to calculate when we re-generate
        range_ = int(range_ // 20 * 20)

        ret.append(Light(pos, random_color(), range_))

    return ret


class App:
    FPS = 60

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
        self.map = Map.load('assets/levels/0')
        self.walls = self.map.collision_rects()

        # Physics
        self.player = Player()
        self.space = self.create_space()

        # Lights
        self.shadow_caster = VisibiltyCalculator(self.create_shadow_walls(GAME_SIZE))
        lights = [self.player.light, *gen_random_lights()]
        self.light_mask = GlobalLightMask(lights, GAME_SIZE, self.shadow_caster)

        # UI
        self.fps_text = SimpleText("Be love", (20, 20), color=(255, 180, 180))

    def run(self):
        while not self.stop:
            self.frame += 1

            # Updating
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
            self.clock.tick(self.FPS)
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
                    print(f"\033[32mScreenshot saved at '{os.path.abspath('screenshots/shadows.png')}'.\033[m")
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
        # Apply gravity / collisions and stuff
        self.space.simulate()

        if self.MOUSE_CONTROL:
            self.player.body.shape.center = Pos(pygame.mouse.get_pos()) // 4

        # Update light position, update from input etc for next frame
        # This should be before space.simulate, but I need to put it after the MOUSE_CONTROL
        # Otherwise the player is moved and is not on the mouse
        self.player.update()

    def render(self, surf):
        surf.fill(SKY_COLOR)

        # Platforms
        for pos in self.map:
            img = self.map.get_chached_image_at(pos, 1)
            r = self.map.pos_to_rect(pos)
            surf.blit(img, r)

        # Player
        self.player.render(surf)

        if self.DEBUG:
            # POLY is just a huge and awful hack to ket the last visible polygon generated
            # don't look at it...
            poly = POLY[0]
            tl = self.player.light_pos
            poly = [(p[0] + tl[0], p[1] + tl[1]) for p in poly]
            pygame.draw.lines(surf, (0, 0, 0), True, poly)

            # segments that block the light
            for a, b in self.map.light_blockers():
                color = random_cached_color(a, b)
                pygame.draw.line(surf, color, a, b)

    def do_shadow(self):
        # It is not really the main part of the shadow, the interesting stuff is in light.py and vfx.py

        if self.ENABLE_SHADOW:
            self.update_light_mask()
            # Basically, the surf_mask is a RGB surface where each value represent the amount
            # of red green and blue light that reached a point
            # Therefore we multiply it with the real color because that's how light works
            # I thought it was a minimum for a while, but it isn't
            self.back_screen.blit(self.light_mask.surf_mask, (0, 0), None,
                                  pygame.BLEND_RGB_MULT)

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
            self.light_mask.update_mask()
        # Every 6 frames we cycle through the variants, so the edge of the lights appear wiggling (?) like a fire
        if self.frame % 6 == 0:
            for l in self.light_mask.lights:
                l.next_variant()


if __name__ == '__main__':
    App().run()
