from functools import lru_cache

import numpy as np
import pygame

from maths import expand_poly
from vfx import np_light_mask, get_light_mask, np_blit_rect


class Light:
    def __init__(self, pos, color=(255, 255, 255), range=120, variants=10):
        self.variant = 0
        self.color = color
        self.range = range
        self.variants = variants
        self.alpha = np_light_mask(self.range, self.variants)
        self.pos = pos

    @property
    def topleft(self):
        return self.pos[0] - self.range, self.pos[1] - self.range

    def next_variant(self):
        """On next mask update, the variant will change."""
        self.variant =  (self.variant + 1) % self.variants

    def update_mask(self, visible_poly, view_point):
        self.alpha = get_light_mask(visible_poly, view_point, self.range, self.variant)

    def get_surf_mask(self):
        s = pygame.Surface(self.alpha.shape, pygame.SRCALPHA)
        # We create a surface of the light's color with the correct alpha
        s.fill(self.color)
        pix = pygame.surfarray.pixels_alpha(s)
        pix[:] = self.alpha
        del pix

        # And then encode the alpha into the color
        # ie. (255, 200, 20) and an alpha of 128 -> (128, 100, 10)
        # since the final mask is the maximum possible color for each pixel
        s2 = pygame.Surface(self.alpha.shape)
        s2.blit(s, (0, 0))
        return s2


class GlobalLightMask:
    def __init__(self, lights, size, shadow_caster):
        self.lights = lights
        self.size = size
        self.surf_mask = pygame.Surface(size)
        self.shadow_caster = shadow_caster

    def update_mask(self):
        # update all lights
        for light in self.lights:
            visible_poly = self.shadow_caster.visible_polygon(light.pos)
            visible_poly = expand_poly(visible_poly, light.pos, 3)
            light.update_mask(visible_poly, light.pos)

        # reset the mask
        self.surf_mask.fill((0, 0, 0))

        # add them all
        for light in self.lights:
            # light is additive
            self.surf_mask.blit(light.get_surf_mask(), light.topleft, None, pygame.BLEND_RGB_ADD)
