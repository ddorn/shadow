#!/usr/bin/env python3

"""
Another Perfect Lite Level Editor.

Perfect ? Not yet... for now it works and that's more than enough.
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Dict
from collections import defaultdict

import pygame
from graphalama.app import App, Screen
from graphalama.buttons import CarouselSwitch, Button

from physics import AABB

pygame.init()

EDIT = 1


def print_pos_2d(pos):
    xs, ys = zip(*pos)
    minx = min(xs)
    miny = min(ys)
    maxx = max(xs)
    maxy = max(ys)

    l = [[" "] * (maxx - minx + 1) for _ in range(maxy - miny + 1)]
    for x, y in pos:
        l[y - miny][x - minx] = '\u2588'

    for line in l:
        print(*line, sep='')


@dataclass
class Point:
    x: int
    left: bool
    belong_to_current_rect: bool = False

    def __hash__(self):
        return hash(self.x)

    def __eq__(self, other):
        return isinstance(other, Point) and self.x == other.x

    def __lt__(self, other):
        return self.x < other.x

    def __repr__(self):
        return f"{self.x}{'[' if self.left else ']'}"


class Tile:
    def __init__(self, path, size):
        self.path = path
        self.sheet = pygame.image.load(path).convert()  # type: pygame.Surface
        self.sheet.set_colorkey((255, 0, 255))
        self.size = size

    @lru_cache()
    def get_at(self, x, y):
        return self.sheet.subsurface((self.size * x, self.size * y, self.size, self.size))

    @lru_cache()
    def get_image(self, neighbors, scale=2):
        map = [
            ["? ? ==?=?", "? ?======", "? ?== ?=?", "? ? = ?=?", "===?==?= ", "=====? =?"],
            ["?=? ==?=?", "=========", "?=?== ?=?", "?=? = ?=?", "?= ?=====", " =?==?==="],
            ["?=? ==? ?", "?=?===? ?", "?=?== ? ?", "?=? = ? ?", "? ? ==?= ", "? ?==  =?"],
            ["? ? ==? ?", "? ?===? ?", "? ?== ? ?", "? ? = ? ?", "?=  ==? ?", " =?== ? ?"]
        ]
        tile_id = neighbors[0][0]
        pos = (1, 1)
        for Y, line in enumerate(map):
            for X, patern in enumerate(line):
                match = True
                for x in range(3):
                    for y in range(3):
                        c = patern[3 * y + x]
                        if c == '=':
                            if neighbors[x - 1][y - 1] != tile_id:
                                match = False
                        elif c == ' ':
                            if neighbors[x - 1][y - 1] == tile_id:
                                match = False
                        elif c == '?':
                            # any tile will do
                            pass

                if match:
                    pos = X, Y

        img = self.get_at(*pos)
        return pygame.transform.scale(img, (self.size * scale, self.size * scale))


class Map(dict):

    def __init__(self, tiles=(), **kwargs):
        self.tiles = tiles  # type: List[Tile]
        self.image_cache = dict()

        super().__init__(**kwargs)

    def save(self, file='assets/levels/0'):
        to_save = {}
        for pos, tile in self.items():
            to_save[f'{pos[0]} {pos[1]}'] = tile

        to_save['tiles'] = [(t.path, t.size) for t in self.tiles]

        s = json.dumps(to_save, indent=4)
        with open(file, 'w') as f:
            f.write(s)

    @classmethod
    def load(cls, file='assets/levels/0'):
        with open(file, 'r') as f:
            d = json.loads(f.read())

        tiles = d.pop('tiles')
        tiles = [Tile(*t) for t in tiles]

        map_ = cls(tiles)
        for pos_string, tile in d.items():
            x, y = map(int, pos_string.split())
            map_[(x, y)] = tile

        return map_

    def get_chached_image_at(self, pos, scale=4):
        if (pos, scale) in self.image_cache:
            return self.image_cache[pos, scale]

        img = self.get_image_at(pos, scale)
        self.image_cache[pos, scale] = img
        return img

    def get_image_at(self, pos, scale=4):
        tile_index = self[pos]
        tile = self.tiles[tile_index]
        image = tile.get_image(self.get_neighbors(pos), scale)
        return image

    def get_neighbors(self, pos):
        """Get a table with the neighbors. topleft will be table[-1][-1] and center right will be table[1][0]."""
        neigh = [[None] * 3 for _ in range(3)]

        for x in range(-1, 2):
            for y in range(-1, 2):
                neighbor = pos[0] + x, pos[1] + y
                tile = self.get(neighbor, None)
                neigh[x][y] = tile

        return tuple(tuple(line) for line in neigh)

    def collision_rects(self):
        # we sort them by Y then X
        positions = [(pos[1], pos[0]) for pos in self.keys()]
        positions.sort()

        # assuming a constant tile size
        tile_size = self.tile_size

        # so we can have line rects easily
        line_rects = []
        first = positions[0]
        last = positions[0]
        for pos in positions[1:]:
            if pos[0] == last[0] and pos[1] == last[1] + 1:
                # just after on the same line : we expand the block
                last = pos
            else:
                # end of last block
                size = last[1] - first[1] + 1
                x = first[1] * tile_size
                y = first[0] * tile_size
                w = size * tile_size
                h = tile_size
                line_rects.append(AABB(x, y, w, h))

                # we start a new block
                first = pos
                last = pos

        # we add the last block too
        size = last[1] - first[1] + 1
        x = first[1] * tile_size
        y = first[0] * tile_size
        w = size * tile_size
        h = tile_size
        line_rects.append(AABB(x, y, w, h))

        # todo: merge lines with the same width
        return line_rects

    @property
    def tile_size(self):
        # assuming that all tiles have the same size
        if self.tiles:
            return self.tiles[0].size
        return 0

    def pos_to_rect(self, pos):
        s = self.tile_size
        x = pos[0] * s
        y = pos[1] * s
        r = pygame.Rect(x, y, s, s)
        return r

    def unoptimized_shadow_blockers(self):
        s = self.tile_size
        blocks = list(self.keys())
        edges = set()
        for x, y in blocks:
            x = s * x
            y = s * y
            edges.add(((x, y), (x + 1, y)))
            edges.add(((x, y + 1), (x + 1, y + 1)))
            edges.add(((x, y), (x, y + 1)))
            edges.add(((x + 1, y), (x + 1, y + 1)))

        return list(edges)

    def _shadow_blocker_helper(self, r, other_line, y):
        segments = set()
        left = Point(r.left, True, True)
        right = Point(r.right, False, True)
        points = {left, right}
        for a in other_line:
            points.add(Point(a.left, True))
            points.add(Point(a.right, False))

        # We care only about points between the borders of the rect
        points = sorted(points)
        begin = points.index(left)
        end = points.index(right)
        points = points[begin:end + 1]

        # the non visible segments are the one that start with left[ and end with right]
        # so we add all the other to se wall segments
        for (a, b) in zip(points[:-1], points[1:]):
            if a.belong_to_current_rect and b.belong_to_current_rect:
                # there is nothing in between (this case is a [ ] but we still want the segment)
                segments.add(((a.x, y), (b.x, y)))
            elif a.left and not b.left:
                pass
            else:
                segments.add(((a.x, y), (b.x, y)))

        return segments

    def light_blockers(self):
        # collision_rects return a rectangle for each part of the line
        rectlines = self.collision_rects()

        segments = set()

        # For the vertical part, it's easy, ase there is no overlapping
        for r in rectlines:
            r = r.pygame_rect
            segments.add((r.topleft, r.bottomleft))
            segments.add((r.topright, r.bottomright))


        # but sometimes rectangles are like this :
        #  ____    _
        # |____|__|_|
        #    |____|
        #
        # so we need to remove the common parts

        # class the rects by line
        lines = defaultdict(list)  # type: Dict[int, pygame.Rect]
        for line in rectlines:
            lines[line.y].append(line)
        ys = sorted(lines.keys())
        for y in ys:
            line_before = lines[y - self.tile_size]
            line_after = lines[y + self.tile_size]

            for r in lines[y]:
                segments.update(self._shadow_blocker_helper(r, line_before, y))
                segments.update(self._shadow_blocker_helper(r, line_after, y + self.tile_size))

        return list(segments)

    def get_shadow_blockers(self):

        directions = ((1, 0), (0, 1), (-1, 0), (0, -1))
        height_directions = directions + ((1, 1), (1, -1), (-1, -1), (-1, 1))

        # STEP 0: Separate tiles in connex block, with a floodfill
        # But we keep only block that touch the air
        def touches_air(pos):
            for dx, dy in height_directions:
                new_pos = pos[0] + dx, pos[1] + dy
                if self.get(new_pos) is None:
                    return True
            return False

        tiles = set(self.keys())
        blocks = []
        while tiles:
            heads = [tiles.pop()]
            block = []
            while heads:
                head = heads.pop()
                if touches_air(head):
                    block.append(head)

                # on each side
                for dx, dy in directions:
                    new_head = head[0] + dx, head[1] + dy
                    if new_head in tiles:
                        tiles.remove(new_head)
                        heads.append(new_head)
            blocks.append(block)
            print_pos_2d(block)

        # STEP 1: We follow the edge in clockwise order

        def find_next(current, direction, points):
            """Find the segment following this one, turning in clockwise order"""

            # Directions are >v<^, we check first the one before
            # then the same direction then the next one
            # so we go in CW order
            directions_to_check = (direction - 1,
                                   direction,
                                   direction + 1)
            # normalisation
            directions_to_check = (d % 4 for d in directions_to_check)

            for d in directions_to_check:
                dx, dy = directions[d]
                next_pos = current[0] + dx, current[1] + dy
                if next_pos in points:
                    return next_pos, d

            return None, None

        paths = []
        for block in blocks:
            # 0 = right
            # 1 = down
            # 2 = left
            # 3 = up
            direction = 0
            block = sorted(block)
            path = []
            start = block[0]
            current = start

            while current is not None:
                path.append(current)
                current, direction = find_next(current, direction, block)

                # This is the stop condition
                if current == start:
                    current = None
            paths.append(path)

        return paths


class EditScreen(Screen):
    BRUSH = 1
    ERASER = 2

    def __init__(self, app):

        # widgets
        self.tool_carousel = CarouselSwitch(["Brush", "Eraser"], self.tool_change, (20, 20))
        reset = Button("Reset", self.reset, bg_color=(240, 100, 60))
        save = Button("Save", self.save)
        widgets = (self.tool_carousel, reset, save)
        super().__init__(app, widgets, (20, 40, 90))

        # map
        self.tile_size = 16
        tiles = [Tile("assets/dirt_sheet.png", self.tile_size)]
        self.map = Map.load()
        self._tile_index = 0

        # editor settings
        self.scale = 4
        self.drawing = False
        self.tool = self.BRUSH

    @property
    def tile_index(self):
        return self._tile_index

    @tile_index.setter
    def tile_index(self, value):
        self._tile_index = value % len(self.map.tiles)

    @property
    def current_tile(self):
        return self.map.tiles[self.tile_index]

    def tool_change(self, tool_name: str):
        self.tool = getattr(self, tool_name.upper(), self.BRUSH)

    def update(self, event):
        if super(EditScreen, self).update(event):
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            self.drawing = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.drawing = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.reset()
            elif event.key == pygame.K_s:
                self.save()
            elif event.key == pygame.K_b:
                self.tool_carousel.option_index = self.tool_carousel.options.index("Brush")
            elif event.key == pygame.K_e:
                self.tool_carousel.option_index = self.tool_carousel.options.index("Eraser")

    def internal_logic(self):

        if self.drawing:
            pos = pygame.mouse.get_pos()
            pos = self.screen_to_pos(pos)

            if self.tool == self.BRUSH:
                self.map[pos] = self.tile_index
            elif self.tool == self.ERASER:
                self.map.pop(pos, None)

    def render(self, display):
        self.draw_background(display)

        # draw tiles
        for pos, tile_i in self.map.items():
            # tile = self.tiles[tile_i]
            image = self.map.get_image_at(pos, self.scale)
            # image = tile.get_image(self.get_neighbors(pos), self.scale)
            display.blit(image, self.pos_to_screen(pos))

        self.widgets.render(display)

    def pos_to_screen(self, pos):
        tot_scale = self.tile_size * self.scale
        return pos[0] * tot_scale, pos[1] * tot_scale

    def screen_to_pos(self, screen):
        tot_scale = self.tile_size * self.scale
        return screen[0] // tot_scale, screen[1] // tot_scale

    def reset(self):
        self.map.clear()

    def save(self):
        self.map.save()


class Apple(App):
    SCREEN_SIZE = (1600, 1008)
    FPS = 30

    def __init__(self):
        screens = {
            EDIT: EditScreen
        }
        initial_screen = EDIT
        super().__init__(screens, initial_screen)
        self.display = pygame.display.set_mode(self.SCREEN_SIZE, pygame.RESIZABLE)


def main():
    Apple().run()
    pygame.quit()


if __name__ == '__main__':
    main()
    m = Map.load()
    for s in m.get_shadow_blockers():
        print(len(s), "\t:  ", s)
    # print(m.get_shadow_blockers())
