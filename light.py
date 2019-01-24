from colorsys import hsv_to_rgb
from functools import lru_cache
from time import time

import numpy as np
import scipy.ndimage
import pygame
import visibility
from scipy.stats import truncnorm

from maths import expand_poly, clip_poly_to_rect

GAUSSIAN = 42
QUADRATIC = 2


class Light:
    """The basic class representing a light."""

    def __init__(self, center, color=(255, 255, 255), range=120, piercing=0, variants=1, light_shape=QUADRATIC):
        """
        A Light emitter.

        :param center: position of the light on the screen
        :param color: color of the light
        :param range: number of pixel lit in each direction
        :param piercing: number of pixels that the light can go through walls
        :param variants: number of base light mask
        """

        self.variant = 0
        self.light_shape = light_shape
        self.color = color
        self.range = range
        self.piercing = piercing
        self.variants = variants
        # This will always be an array with 0s where the light from this light can't reach
        # up to 255 when it can
        self.alpha = None  # type: np.ndarray
        self.center = center

    def next_variant(self):
        """On next mask update, the variant will change."""
        self.variant = (self.variant + 1) % self.variants

    def update_mask(self, visible_poly):
        """
        Compute the array of alpha according to the visible polygon.

        :param visible_poly: The list of points defining the polygon of what the light can see.
            It must be centered on `light.center`.
        """

        if self.piercing:
            visible_poly = expand_poly(visible_poly, self.center, self.piercing)

        self.alpha = self.visible_mask(visible_poly)

    @staticmethod
    @lru_cache()
    def compute_gauss_light_mask(radius, variant=0):
        """
        Generate a random mask of the area a light lights (without any wall)

        :param int radius: How far the light lights
        :param variant: Anything hashable, different variant will generate slightly different masks.
        """

        mask = np.zeros((2 * radius, 2 * radius), dtype=np.uint8)

        # We genereate lots of random numbers with a truncated normal distribution
        # each of them is pixel with light
        # TODO: use a quadratic distribution (if that exist) because light intensity
        #  is proportional to the inverse of the distance squared
        #  (in 2d)
        xs = truncnorm.rvs(a=-4, b=4, loc=radius, scale=radius / 4, size=7 * radius ** 2).astype(np.int)
        ys = truncnorm.rvs(a=-4, b=4, loc=radius, scale=radius / 4, size=7 * radius ** 2).astype(np.int)

        mask[xs, ys] = 255

        # We blur everything so light pixels are not alone
        mask = scipy.ndimage.filters.gaussian_filter(mask, radius / 10)

        return mask

    @staticmethod
    @lru_cache()
    def compute_quad_light_mask(radius, variant=0):

        s = pygame.Surface((2 * radius, 2 * radius))
        # for r in range(radius - 4, 1, -1):
        #     intensity = 255 * (1 - (r/radius)**2)
        # intensity = 255 * (1 - r / radius)
        # pygame.draw.circle(s, (intensity, 0, 0), (radius, radius), r)
        pygame.draw.circle(s, (255, 0, 0), (radius, radius), radius // 2)

        mask = pygame.surfarray.pixels_red(s)

        # We blur everything so light pixels are not alone
        mask = scipy.ndimage.filters.gaussian_filter(mask, radius / 4)

        return mask

    @property
    def light_mask(self):
        if self.light_shape == GAUSSIAN:
            return self.compute_gauss_light_mask(self.range, self.variant)
        if self.light_shape == QUADRATIC:
            return self.compute_quad_light_mask(self.range, self.variant)
        raise ValueError(f"Unkonwn light shape {self.light_shape}")

    def visible_mask(self, visible_poly):
        """
        Get a 2D array of intensity of the light at every point, between 0 and 255 (to use as the alpha chanel).

        :param visible_poly: visible polygon, centered on the light's center
        :return: a mask (np.array) with the intensity of light at each point
        """

        # we move the polygon so that the light center is at (range, range) so the top left of the polygon
        # is at (0, 0), and we can blit it easily
        visible_poly = [(p[0] - self.topleft[0], p[1] - self.topleft[1]) for p in visible_poly]

        # we clip the visible polygon to work with smaller surfaces
        # otherwise pygame draws it wrong (suppress all point outside the surf)
        size = (2 * self.range, 2 * self.range)
        visible_poly = clip_poly_to_rect(visible_poly, pygame.Rect((0, 0), size))

        # points inside the visible polygon
        # we use pygame to draw the polygon as it's the fastest thing i've found
        # 8 bit 'cos why use more ?
        poly_surf = pygame.Surface(size, depth=8)
        # we paint what we can see in white, and what we can't is black, with a boolean value of 0
        if visible_poly:  # Can be empty if nothing is visible
            pygame.draw.polygon(poly_surf, (255, 255, 255), visible_poly)
        # TODO: i think we can optimise by replacing the ~visible and the .as_bool by just > 0
        visible = pygame.surfarray.pixels2d(poly_surf).astype(np.bool)

        # We get the intensity of light that should reach each point if there was no wall
        light_mask = self.light_mask.copy()  # those are cached, so we need to make a copy before modifying it

        # we remove the visible from the mask
        light_mask[~visible] = 0

        # and we blur it for a bleeding / bloom effect
        # Gaussian blur is better looking but too complex to use often on big surfaces

        # I think it is better to just blur the whole global mask, but if not, just uncomment hose two lines
        # blur = max(self.range // 8, 2)
        # light_mask = scipy.ndimage.gaussian_filter(light_mask, blur)
        return light_mask

    def get_surf_mask(self):
        """
        Return a pygame RGB surface with the colors indicating how much red,
        green and blue light reach each pixel.
        """

        # GOAL: encode the alpha array into a RGB colored surface
        s = pygame.Surface(self.alpha.shape, pygame.SRCALPHA)
        # We create a surface of the light's color with the correct per-pixel alpha
        s.fill(self.color)
        pix = pygame.surfarray.pixels_alpha(s)
        pix[:] = self.alpha
        # unlocks the surface
        del pix

        # And then encode the alpha into the color
        # ie. (255, 200, 20) and an alpha of 128 -> (128, 100, 10)
        # since the final mask is the maximum possible color for each pixel
        s2 = pygame.Surface(self.alpha.shape)
        s2.blit(s, (0, 0))
        return s2

    @property
    def topleft(self):
        """Position to blit the mask"""
        return self.center[0] - self.range, self.center[1] - self.range

    @property
    def size(self):
        return 2 * self.range, 2 * self.range


class RainbowLight(Light):
    def __init__(self, center, hue_start: "Between 0 and 1" = 0, loop_time=5, range=120, piercing=0, variants=1,
                 light_shape=QUADRATIC):
        self.start = time()
        self.loop_time = loop_time
        self.hue_start = hue_start
        super().__init__(center, self.color, range, piercing, variants, light_shape)

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

    def __init__(self, lights, size, shadow_caster, minimum_light=(0, 0, 0), blur=10):
        """
        Light combiner and renderer.

        Create an object to blend multiple lights together and apply them on a Surface.

        :param lights: A list of `Light` to manage
        :param size: The total of the surface where the lights have effect. This is usually the screensize.
        :param shadow_caster: A ShadowCaster object, containing the description of all the walls where
            the light is blocked.
        :param minimum_light: ambient light, useful to have wall that are not pure black
        """

        self.lights = lights
        self.size = size
        self.minimum_light = minimum_light
        self.blur = blur
        self.surf_mask = pygame.Surface(size)
        self.shadow_caster = shadow_caster  # type: visibility.VisibiltyCalculator

    def update_mask(self):
        """
        Update the global mask according to each light's center and color.

        This merges (add) all the lights into `surf_mask`.
        """

        # update each lights
        for light in self.lights:
            visible_poly = self.shadow_caster.visible_polygon(light.center)
            light.update_mask(visible_poly)

        # reset the mask
        self.surf_mask.fill(self.minimum_light)

        # add them all
        for light in self.lights:
            # light is additive
            self.surf_mask.blit(light.get_surf_mask(), light.topleft, None, pygame.BLEND_RGB_ADD)

        if self.blur:
            pix = pygame.surfarray.pixels3d(self.surf_mask)
            for axis in range(3):
                pix[:,:,axis] = scipy.ndimage.uniform_filter(pix[:,:,axis], self.blur)

    def apply_light_on(self, surf, offset=(0, 0)):
        """
        Apply the colored lights on a surface.

        Update_mask must be called before this so the most up to date lights are rendered.
        Note that you can call update_mask only every second or third frame to reduce CPU usage
        without too noticeable effects.

        :param surf: a RGB surface with your graphics already rendered that you want to light
        :param offset: Topleft of where the lights are blit.
        """

        # Basically, the surf_mask is a RGB surface where each value represent the amount
        # of red green and blue light that reached a point
        # Therefore we multiply it with the real color because that's how light works
        # I thought it was a minimum for a while, but it isn't
        surf.blit(self.surf_mask, offset, None, pygame.BLEND_RGB_MULT)
