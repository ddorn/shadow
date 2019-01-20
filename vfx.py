"""
Function working on numpy arrays of alpha values.
"""

from functools import lru_cache

import numpy as np
import pygame
import scipy.ndimage
from scipy.stats import truncnorm

from maths import clip_poly_to_rect, Pos

BLUR = 5
POLY = [None, None]


@lru_cache()
def np_light_mask(radius, variant=0):
    """
    Generate a random mask of the area a light lights (without any wall

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


def np_blit_rect(dest, surf, pos):
    """Return the 8 coordinates to blit np array on each other, like pygame.blit, with bound checking."""
    w = dest.shape[0]
    h = dest.shape[1]

    sw = surf.shape[0]
    sh = surf.shape[1]

    # blit start position (on dest)
    x, y = map(int, pos)
    # blit end pos (on dest)
    bex, bey = x + sw, y + sh

    # if the beginning of the surf is outside dest (more on the top/left)
    # we take only what's inside
    sx = sy = 0
    if x < 0:
        sx = -x
        x = 0
    if y < 0:
        sy = -y
        y = 0

    # and we cut also what's on the other side
    if w < bex:
        bex = w
    if h < bey:
        bey = h

    # and finally update the end position of surf that will be blit
    ex = sx + (bex - x)
    ey = sy + (bey - y)

    return x, bex, y, bey, sx, ex, sy, ey


def np_blit(dest, surf, pos):
    """Blit an surf on dest like pygame.blit."""
    x1, x2, y1, y2, a1, a2, b1, b2 = np_blit_rect(dest, surf, pos)
    dest[x1:x2, y1:y2] = surf[a1:a2, b1:b2]


def np_get_alpha_visibility(visible_poly, sight_range, variant=0):
    """
    Get a 2D array of intensity of the light at every point, between 0 and 255 (to use as the alpha chanel).

    :param visible_poly: visible polygon, centered on (0, 0), the view_point
    :param sight_range: max distance that the light should go
    :param variant: light patterns are cached, so use the variant to control the one you want
    :return: a mask (np.array) with the intensity of light t each point
    """

    # we clip the visible polygon to work with smaller surfaces
    # otherwise pygame draws it wrong (suppress all point outside the surf)
    topleft = (-sight_range,
               -sight_range)
    size = (2 * sight_range, 2 * sight_range)
    visible_poly = clip_poly_to_rect(visible_poly, pygame.Rect(topleft, size))
    # express the poly relatively to the topleft so we can draw it ON the surface
    visible_poly = [(p[0] - topleft[0], p[1] - topleft[1]) for p in visible_poly]
    POLY[0] = visible_poly

    # points inside the visible polygon
    # we use pygame to draw the polygon as it's the fastest thing i've found
    # 8 bit 'cos why use more ?
    poly_surf = pygame.Surface(size, depth=8)
    # later we'll want to remove what we can see, so what we do see is 0, the rest is true
    if visible_poly:  # Can be empty if nothing is visible
        pygame.draw.polygon(poly_surf, (255, 255, 255), visible_poly)
    # TODO: i think we can optimise by replacing the ~visible and the .as_bool by just > 0
    visible = pygame.surfarray.pixels2d(poly_surf).astype(np.bool)

    # intensity of light that should reach a given point
    light_mask = np_light_mask(sight_range, variant).copy()

    # we remove the visible from the mask
    light_mask[~visible] = 0

    # and we blur it for a bleeding / bloom effect
    # Gaussian blur is better looking but too complex to use often on big surfaces

    light_mask = scipy.ndimage.uniform_filter(light_mask, sight_range / 10)
    return light_mask


def get_light_mask(visible_poly, view_point, sight_range=100, variant=0):
    """Return the computed light mask."""

    # np_get_alpha_visibility needs a list of point centered on (0, 0)
    visible_poly = [tuple((Pos(p) - view_point)) for p in visible_poly]
    light_mask = np_get_alpha_visibility(visible_poly, sight_range, variant)

    return light_mask
