from functools import lru_cache

import numpy as np
import pygame
import scipy
import scipy.ndimage
from scipy.stats import truncnorm

from maths import clip_poly_to_rect, Pos

BLUR = 5
POLY = [None]


@lru_cache()
def np_light_mask(radius, variant=0):
    mask = np.zeros((2 * radius, 2 * radius), dtype=np.uint8)
    """Generate a random mask of the area a light lights"""

    xs = truncnorm.rvs(a=-4, b=4, loc=radius, scale=radius / 4, size=7 * radius ** 2).astype(np.int)
    ys = truncnorm.rvs(a=-4, b=4, loc=radius, scale=radius / 4, size=7 * radius ** 2).astype(np.int)

    mask[xs, ys] = 255

    mask = scipy.ndimage.filters.gaussian_filter(mask, radius / 10)

    return mask


def np_blit_rect(dest, surf, pos):
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
    x1, x2, y1, y2, a1, a2, b1, b2 = np_blit_rect(dest, surf, pos)
    dest[x1:x2, y1:y2] = surf[a1:a2, b1:b2]

def np_blit_center(dest, surf, center):
    pos = center[0] - surf.shape[0] // 2, center[1] - surf.shape[1] // 2
    np_blit(dest, surf, pos)



def np_get_alpha_visibility(visible_poly, sight_range, variant=0):
    """
    Get a 2D array of intensity of the light at every point, between 0 and 255 (to use as the alpha chanel.

    :param visible_poly: visible polygon, centered (0, 0), the view_point
    :param sight_range: max distance that the light should go
    :param variant: light paterns are cached, so use the variant to control the one you want
    :return: a mask (np.array) with the intensity of light t each point
    """

    # we clip the visible polygon to work with smaller surfaces
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
    if visible_poly:
        pygame.draw.polygon(poly_surf, (255, 255, 255), visible_poly)
    # TODO: i think we can optimise by replacing the ~invisible and the .as_bool by just > 0
    invisible = pygame.surfarray.pixels2d(poly_surf).astype(np.bool)

    # intensity of light that should reach a given point
    light_mask = np_light_mask(sight_range, variant).copy()

    # we remove the invisible from the mask
    light_mask[~invisible] = 0

    # and we blur it for a bleeding / bloom effect
    # big_blur = scipy.ndimage.gaussian_filter(light_mask, BLUR)
    # small_blur = scipy.ndimage.gaussian_filter(light_mask, 3)
    # light_mask = np.maximum(small_blur, big_blur)

    big_blur = small_blur = light_mask

    # big_blur = scipy.ndimage.uniform_filter(light_mask, sight_range / 10)
    # small_blur = scipy.ndimage.gaussian_filter(light_mask, 4)
    # light_mask = np.maximum(small_blur, big_blur)
    big_blur = scipy.ndimage.uniform_filter(light_mask, sight_range / 10)
    #
    return big_blur
    # return small_blur
    return light_mask


def get_light_mask(visible_poly, view_point, sight_range=100, variant=0):
    # we make a downscaled version and we'll scale it up
    visible_poly = tuple(tuple((Pos(p) - view_point)) for p in visible_poly)
    light_mask = np_get_alpha_visibility(visible_poly, sight_range, variant)

    return light_mask

def np_limit_visibility(surf: pygame.Surface, view_point, light_mask: np.ndarray, light_color=(255, 255, 255)):
    """

    surf: surface with the graphics to limit visibility. must be pygame.SRCALPHA
    viewpoint: position of the light
    sight_range: intensity of the light (max range where we can see
    variant: light is randomly generated and cached, change variant to generate an other one
    :return: a rect of the area where there is light
    """

    # assuming square mask
    sight_range = light_mask.shape[0] // 2
    topleft = (view_point[0] - sight_range,
               view_point[1] - sight_range)

    # alpha chanel of the texture
    alpha = pygame.surfarray.pixels_alpha(surf)

    # zero it
    alpha[:] = 0
    # add the light
    np_blit(alpha, light_mask, topleft)

    return pygame.Rect(topleft, (2 * sight_range, 2 * sight_range))
