import pygame


# noinspection PyArgumentList
def Pos(*args):
    return pygame.Vector2(*args)

def clamp(x, mini, maxi):
    if maxi < mini:
        return x
    if x < mini:
        return mini
    if maxi < x:
        return maxi
    return x

def approx(p):
    if isinstance(p, (int, float)):
        return round(p)
    return list(map(approx, p))

def cross(a, b, c, d):
    v1 = b[0] - a[0], b[1] - a[1]
    v2 = d[0] - c[0], d[1] - c[1]
    return round(v1[0]*v2[1] - v1[1]*v2[0], 6)


def segments(l):
    return zip(l, l[1:] + (l[0],))


def intersection(p, q, a, b, full_line=False):
    """
    Find the intersection between the half line [PQ) and the segment [AB].
    If there is no intersection, return None instead
    :full_line: if true, check the intersection with (PQ) instead
    """
    # if full_line:
    #     print(p, q, a, b)

    # \vec{PQ}
    dx, dy = q[0] - p[0], q[1] - p[1]
    # \vec{AB}
    vx, vy = b[0] - a[0], b[1] - a[1]

    # shortcuts
    x, y = p
    ax, ay = a

    # check if they are parallel (cross product)
    cross = dx*vy - dy*vx
    if cross == 0:
        return None

    t2 = (y*dx - x*dy + dy*ax - dx*ay) / cross
    if dx != 0:
        t1 = (ax + vx*t2 - x) / dx
    else:
        t1 = (ay + vy*t2 - y) / dy


    if (full_line or t1 >= 0) and (0 <= t2 <= 1):
        # check wether the paraeters are in the good range
        return (x + t1*dx, y + t1*dy)
    else:
        # Non collision
        return None

def dist2(a, b):
    """Return the sqared dist between a and b."""
    return (a[0] - b[0])**2 + (a[1] - b[1])**2

def find_block_point(source_pos, dir_pos, segment):
    """Finds the point where the light is blocked. This assumes the light with be blocked. (aka you put borders)."""

    inf = float('inf')
    def key(p):
        if p is None:
            return inf
        # all points are on the same line, so manathan distance is enough
        return abs(p[0] - source_pos[0]) + abs(p[1] - source_pos[1])

    intersections = (intersection(source_pos, dir_pos, *s) for s in segment)
    return min(intersections, key=key)

def cast_shadow(walls, pos):
    """Calculate the visible polygon from pos where the sight is blocked by the walls."""

    # find interesting directions to cast shadow
    seg = [s for p in walls for s in segments(p)]

    dirs = []
    for poly in walls:
        for point in poly:
            p = pygame.Vector2(point)
            dirs.extend(( p.rotate(0.0001), p.rotate(-0.0001)))

    inters = list(filter(lambda x: x is not None, (find_block_point(pos, dir, seg) for dir in dirs)))
    inters.sort(key=lambda p: (pygame.Vector2(p) - pos).as_polar()[1])
    return inters


def clip_poly_to_rect(poly, rect: pygame.Rect):
    """
    Clip the polygon inside the rectangle.
    Coordinates of points are converted to integer, because floating point arithmetic sucks.
    """
    # print(poly)
    clip = segments((rect.topleft, rect.bottomleft, rect.bottomright, rect.topright))
    new_poly = poly
    for edge in approx(clip):
        # print(edge)
        new_poly, poly = [], new_poly[:]
        s = approx(poly[-1])
        for e in approx(poly):

            i = 0
            # e inside clipping edge
            if cross(edge[0], edge[1], edge[0], e) <= 0:
                # s outside
                if cross(edge[0], edge[1], edge[0], s) > 0:
                    i = intersection(*edge, s, e, True)
                    # print(1, i)
                    new_poly.append(i)
                new_poly.append(e)
            elif cross(edge[0], edge[1], edge[0], s) <= 0:
                # s inside
                i = intersection(*edge, s, e, True)
                # print(2, i)
                new_poly.append(i)

            if i is None:
                print("edge:", edge)
                print("e", e, "s", s)
                print("poly", approx(poly))
                print("cross1", cross(edge[0], edge[1], edge[0], s))
                print("cross2", cross(edge[0], edge[1], edge[0], s))
            s = e

    return new_poly
