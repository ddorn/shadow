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


# Useless
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


# Useless
def np_blit(dest, surf, pos):
    """Blit an surf on dest like pygame.blit."""
    x1, x2, y1, y2, a1, a2, b1, b2 = np_blit_rect(dest, surf, pos)
    dest[x1:x2, y1:y2] = surf[a1:a2, b1:b2]
