from colorsys import hsv_to_rgb
from time import time

import numpy as np
import pygame
import visibility

from maths import expand_poly
from vfx import get_light_mask

MIN_SHADOW = 50


class Light:
    """The basic class representing a light."""

    def __init__(self, center, color=(255, 255, 255), range=120, piercing=0, variants=1):
        """
        A Light emitter.

        :param center: position of the light on the screen
        :param color: color of the light
        :param range: number of pixel lit in each direction
        :param piercing: number of pixels that the light can go through walls
        :param variants: number of base light mask
        """

        self.variant = 0
        self.color = color
        self.range = range
        self.piercing = piercing
        self.variants = variants
        # This will always be an array with 0s where the light from this light can't reach
        # up to 255 when it can
        self.alpha = None  # type: np.ndarray
        self.center = center

    @property
    def topleft(self):
        """Position to blit the mask"""
        return self.center[0] - self.range, self.center[1] - self.range

    def next_variant(self):
        """On next mask update, the variant will change."""
        self.variant = (self.variant + 1) % self.variants

    def update_mask(self, visible_poly, view_point):
        self.alpha = get_light_mask(visible_poly, view_point, self.range, self.variant)

    def get_surf_mask(self):
        """
        Return a pygame RGB surface with the colors indicating how much red,
        green and blue light arrive to each pixel.
        """

        # GOAL: encode the alpha array into the colored surface
        s = pygame.Surface(self.alpha.shape, pygame.SRCALPHA)
        # We create a surface of the light's color with the per-pixel alpha
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

    @property
    def size(self):
        return 2 * self.range, 2 * self.range


class RainbowLight(Light):
    def __init__(self, center, hue_start: "Between 0 and 1" = 0, loop_time=5, range=120, piercing=0, variants=1):
        self.start = time()
        self.loop_time = loop_time
        self.hue_start = hue_start
        super().__init__(center, self.color, range, piercing, variants)

    @property
    def color(self):
        hue = (self.hue_start + time() - self.start) % self.loop_time
        hue /= self.loop_time
        hsv = hsv_to_rgb(hue, 1, 1)
        return [round(255 * c) for c in hsv]

    @color.setter
    def color(self, value):
        # we don't set the color of a rainbow
        pass


class GlobalLightMask:
    """Base class that take care of merging all the lights together."""

    def __init__(self, lights, size, shadow_caster):
        self.lights = lights
        self.size = size
        self.surf_mask = pygame.Surface(size)
        self.shadow_caster = shadow_caster  # type: visibility.VisibiltyCalculator

    def update_mask(self):
        # update all lights
        for light in self.lights:
            visible_poly = self.shadow_caster.visible_polygon(light.center)
            if light.piercing:
                visible_poly = expand_poly(visible_poly, light.center, light.piercing)
            light.update_mask(visible_poly, light.center)

        # reset the mask
        self.surf_mask.fill((MIN_SHADOW, MIN_SHADOW, MIN_SHADOW))

        # add them all
        for light in self.lights:
            # light is additive
            self.surf_mask.blit(light.get_surf_mask(), light.topleft, None, pygame.BLEND_RGB_ADD)
