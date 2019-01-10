from functools import lru_cache

import numpy as np
import pygame
import scipy
import scipy.ndimage
from scipy.stats import truncnorm


@lru_cache()
def np_light_mask(radius, variant=0):
    mask = np.zeros((2 * radius, 2 * radius), dtype=np.uint8)
    """Generate a random mask of the area a light lights"""

    xs = truncnorm.rvs(a=-4, b=4, loc=radius, scale=radius / 4, size=3 * radius ** 2).astype(np.int)
    ys = truncnorm.rvs(a=-4, b=4, loc=radius, scale=radius / 4, size=3 * radius ** 2).astype(np.int)

    mask[xs, ys] = 255

    mask = scipy.ndimage.filters.gaussian_filter(mask, 7)

    return mask


def np_blit_rect(dest, surf, pos):
    w, h = dest.shape
    sw, sh = surf.shape

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


def np_limit_visibility(surf: pygame.Surface, visible_poly, view_point, sight_range=100, variant=0):
    """
    Get a 2D array of intensity of the light at every point, between 0 and 255 (to use as the alpha chanel.

    surf: surface with the graphics to limit visibility. must be pygame.SRCALPHA
    viewpoint: position of the light
    sight_range: intensity of the light (max range where we can see
    variant: light is randomly generated and cached, change variant to generate an other one
    :return: a rect of the area where there is light
    """

    # alpha chanel of the texture
    alpha = pygame.surfarray.pixels_alpha(surf)

    # points inside the visible polygon
    # we use pygame to draw the polygon as it's the fastest thing i've found
    # 8 bit 'cos why use more ?
    poly_surf = pygame.Surface(alpha.shape, depth=8)
    poly_surf.fill((255, 255, 255))
    # later we'll want to remove what we can see, so what we do see is 0, the rest is true
    pygame.draw.polygon(poly_surf, (0, 0, 0), visible_poly)
    invisible = pygame.surfarray.array2d(poly_surf).astype(np.bool)

    # intensity of light that should reach a given point
    light_mask = np_light_mask(sight_range, variant).copy()

    topleft = (view_point[0] - sight_range,
               view_point[1] - sight_range)
    # we remove the invisible from the mask
    x1, x2, y1, y2, a1, a2, b1, b2 = np_blit_rect(light_mask, invisible, (-topleft[0], -topleft[1]))
    # this ugly line is just light_mask[where its invisible] = 0
    # but taking account of the border
    light_mask[x1:x2, y1:y2][invisible[a1:a2, b1:b2]] = 0
    # and we blur the light so the edges appear, and it's not sharp (bleeding effect)
    light_mask = scipy.ndimage.uniform_filter(light_mask, 20)

    # zero it
    alpha[:] = 0
    # add the light
    np_blit(alpha, light_mask, topleft)

    return pygame.Rect(topleft, (2*sight_range, 2*sight_range))
