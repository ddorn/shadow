from functools import lru_cache

import numpy as np
import pygame
import scipy
import scipy.ndimage
from numpy.lib.stride_tricks import as_strided
from scipy.stats import truncnorm
import skimage.transform

from maths import clip_poly_to_rect, Pos

DOWNSCALE = 1
BLUR = 15 // DOWNSCALE


def tile_array(a, b0):
    """
    Up scale an array by a factor b0
    """
    # from https://stackoverflow.com/a/32848377/6160055
    b1 = b0
    r, c = a.shape                                    # number of rows/columns
    rs, cs = a.strides                                # row/column strides
    x = as_strided(a, (r, b0, c, b1), (rs, 0, cs, 0)) # view a as larger 4D array
    return x.reshape(r*b0, c*b1)                      # create new 2D array


@lru_cache()
def np_light_mask(radius, variant=0):
    mask = np.zeros((2 * radius, 2 * radius), dtype=np.uint8)
    """Generate a random mask of the area a light lights"""

    xs = truncnorm.rvs(a=-4, b=4, loc=radius, scale=radius / 4, size=7 * radius ** 2).astype(np.int)
    ys = truncnorm.rvs(a=-4, b=4, loc=radius, scale=radius / 4, size=7 * radius ** 2).astype(np.int)

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


def np_get_alpha_visibility(visible_poly, sight_range, variant=0):
    """
    Get a 2D array of intensity of the light at every point, between 0 and 255 (to use as the alpha chanel.

    :param visible_poly: visible polygon, centered (0, 0), the view_point
    :param view_point:
    :param sight_range:
    :param variant:
    :return:
    """

    # we clip the visible polygon to work with smaller surfaces
    topleft = (-sight_range,
               -sight_range)
    size = (2*sight_range, 2*sight_range)
    visible_poly = clip_poly_to_rect(visible_poly, pygame.Rect(topleft, size))
    # express the poly relatively to the topleft so we can draw it ON the surface
    visible_poly = [(p[0] - topleft[0], p[1] - topleft[1]) for p in visible_poly]


    # points inside the visible polygon
    # we use pygame to draw the polygon as it's the fastest thing i've found
    # 8 bit 'cos why use more ?
    poly_surf = pygame.Surface(size, depth=8)
    # poly_surf.fill((255, 255, 255))
    # later we'll want to remove what we can see, so what we do see is 0, the rest is true
    pygame.draw.polygon(poly_surf, (255, 255, 255), visible_poly)
    # TODO: i think we can optimise by replacing the ~invisible and the .as_bool by just > 0
    invisible = pygame.surfarray.pixels2d(poly_surf).astype(np.bool)

    # intensity of light that should reach a given point
    light_mask = np_light_mask(sight_range, variant).copy()

    # we remove the invisible from the mask
    light_mask[~invisible] = 0

    light_mask = scipy.ndimage.gaussian_filter(light_mask, 3)
    # light_mask = scipy.ndimage.uniform_filter(light_mask, BLUR)

    return light_mask

def np_limit_visibility(surf: pygame.Surface, visible_poly, view_point, sight_range=100, variant=0):
    """

    surf: surface with the graphics to limit visibility. must be pygame.SRCALPHA
    viewpoint: position of the light
    sight_range: intensity of the light (max range where we can see
    variant: light is randomly generated and cached, change variant to generate an other one
    :return: a rect of the area where there is light
    """

    topleft = (view_point[0] - sight_range,
               view_point[1] - sight_range)

    # alpha chanel of the texture
    alpha = pygame.surfarray.pixels_alpha(surf)

    # we make a downscaled version and we'll scale it up
    visible_poly = [(Pos(p) - view_point) / DOWNSCALE for p in visible_poly]
    light_mask = np_get_alpha_visibility(visible_poly, sight_range, variant)
    # kronecker = np.ones((down_sampling, down_sampling))
    # light_mask = np.kron(light_mask, kronecker)
    # light_mask = tile_array(light_mask, DOWNSCALE)
    # light_mask = scipy.ndimage.uniform_filter(light_mask, DOWNSCALE)
    # light_mask = skimage.transform.rescale(light_mask, DOWNSCALE, anti_aliasing=False, preserve_range=True)

    # and then we put the light at the right spot
    # x1, x2, y1, y2, a1, a2, b1, b2 = np_blit_rect(light_mask, invisible, (-topleft[0], -topleft[1]))
    #
    # this ugly line is just light_mask[where its invisible] = 0
    # but taking account of the border
    # light_mask[x1:x2, y1:y2][invisible[a1:a2, b1:b2]] = 0
    # and we blur the light so the edges appear, and it's not sharp (bleeding effect)
    # light_mask = scipy.ndimage.uniform_filter(light_mask, 20)
    # light_mask = scipy.ndimage.gaussian_filter(light_mask, 10)

    # zero it
    alpha[:] = 0
    # add the light
    np_blit(alpha, light_mask, topleft)

    return pygame.Rect(topleft, (2*sight_range, 2*sight_range))
