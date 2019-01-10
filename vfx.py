from math import sqrt

import numpy
import pygame
from functools import lru_cache

import scipy.ndimage


@lru_cache()
def light_mask(radius):
    """Return a surface, with a circle of decreasing intensity drawn in the alpha chanel"""
    mask = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    for intensity in range(1, 256, 1):
        r = int(radius * sqrt(1 - intensity / 255))
        pygame.draw.circle(mask, (255, 255, 255, intensity), (radius, radius), r)
    return mask


@lru_cache()
def np_light_mask(radius, variant=0):
    mask = numpy.zeros((2*radius, 2*radius), dtype=numpy.uint8)
    rand = numpy.array(radius + radius/4*numpy.random.randn(4*radius**2, 2), dtype=numpy.int)

    for (a, b) in rand:
        if 0 <= a < 2*radius and 0 <= b < 2*radius:
            mask[a, b] = 255

    mask = scipy.ndimage.filters.gaussian_filter(mask, 7)

    return mask


def limit_visibility(visible_surf, view_point, range=100, variant=0):
    mask = np_light_mask(range, variant)
    alpha = pygame.surfarray.pixels_alpha(visible_surf)
    w, h = alpha.shape

    blitx, blity = view_point[0] - range, view_point[1] - range
    blitendx, blitendy = view_point[0] + range, view_point[1] + range

    sx = sy = 0
    if blitx < 0:
        sx = -blitx
        blitx = 0
    if blity < 0:
        sy = -blity
        blity = 0

    if w < blitendx:
        blitendx = w
    if h < blitendy:
        blitendy = h

    ex = sx + (blitendx - blitx)
    ey = sy + (blitendy - blity)

    alpha[:] = 0
    alpha[blitx:blitendx, blity:blitendy] = mask[sx:ex, sy:ey]
