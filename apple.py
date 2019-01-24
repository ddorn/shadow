#!/usr/bin/env python3

import json
import os
from collections import defaultdict
from functools import lru_cache
from typing import Dict, List

import pygame
from graphalama.app import Screen, App
from graphalama.buttons import CarouselSwitch, Button

from physics import AABB


class Tile:
    solid: bool
    transparent: bool
    name: str
    file_path: str
    sprite_sheet: pygame.Surface
    neighbours_patterns: list
    tile_size: int

    def __init__(self, path, tile_size=0, solid=True, transparent=False):
        self.solid = solid
        self.transparent = transparent
        self.file_path = path
        self.tile_size = tile_size
        self.load(self.file_path)

    def load(self, path):
        print("Loading tile set", path)
        self.sprite_sheet = pygame.image.load(path).convert()
        self.sprite_sheet.set_colorkey((255, 0, 255))
        self.name = os.path.basename(path)
        self.neighbours_patterns = self.load_neighbourg_data(path + ".data")

    def load_neighbourg_data(self, path):
        return [
            ["? ? ==?=?", "? ?======", "? ?== ?=?", "? ? = ?=?", "===?==?= ", "=====? =?"],
            ["?=? ==?=?", "=========", "?=?== ?=?", "?=? = ?=?", "?= ?=====", " =?==?==="],
            ["?=? ==? ?", "?=?===? ?", "?=?== ? ?", "?=? = ? ?", "? ? ==?= ", "? ?==  =?"],
            ["? ? ==? ?", "? ?===? ?", "? ?== ? ?", "? ? = ? ?", "?=  ==? ?", " =?== ? ?"]
        ]

    def get_tile_from_sheet(self, pos):
        pos = pos[0] * self.tile_size, pos[1] * self.tile_size
        size = self.tile_size, self.tile_size
        return  self.sprite_sheet.subsurface((pos, size))

    def get_image(self, neighbours=()):
        tile_name = neighbours[0][0]
        pos = (1, 1)
        for Y, line in enumerate(self.neighbours_patterns):
            for X, pattern in enumerate(line):
                match = True
                for x in range(3):
                    for y in range(3):
                        c = pattern[3 * y + x]
                        if c == '=':
                            if neighbours[x - 1][y - 1] != tile_name:
                                match = False
                        elif c == ' ':
                            if neighbours[x - 1][y - 1] == tile_name:
                                match = False
                        elif c == '?':
                            # any tile will do
                            pass

                if match:
                    pos = X, Y

        img = self.get_tile_from_sheet(pos)
        return pygame.transform.scale(img, (self.tile_size, self.tile_size))


class TileMap:
    tiles: Dict[tuple, int]
    tile_objects: List[Tile]
    tile_size: int

    def __init__(self, tile_objects=None, tiles=None, tile_size=16):
        self.tile_size = tile_size
        self.tiles = tiles if tiles is not None else {}
        self.tile_objects = tile_objects if tile_objects is not None else []

    def world_pos_to_map(self, world_pos):
        return (world_pos[0] // self.tile_size, world_pos[1] // self.tile_size)

    def map_to_world_pos(self, map_pos):
        return (map_pos[0] * self.tile_size, map_pos[1] * self.tile_size)

    def tile_at_map_pos(self, map_pos):
        if map_pos in self.tiles:
            tile_id = self.tiles[map_pos]
            return self.tile_objects[tile_id]

        return None

    def tile_at_world_pos(self, world_pos):
        world_pos = self.world_pos_to_map(world_pos)
        return self.tile_at_map_pos(world_pos)

    def save(self, file='assets/levels/0'):
        tile_paths = [tile.file_path for tile in self.tile_objects]

        tile_map = {}
        for pos, tile_id in self.tiles.items():
            tile_map[f'{pos[0]} {pos[1]}'] = tile_id

        to_save = dict(tile_paths=tile_paths,
                       tile_map=tile_map,
                       tile_size=self.tile_size)
        s = json.dumps(to_save)
        with open(file, 'w') as f:
            f.write(s)

    @classmethod
    def load(cls, file='assets/levels/0'):
        with open(file, 'r') as f:
            d = json.loads(f.read())

        tile_ids = d.pop('tile_map')
        tile_paths = d.pop('tile_paths')
        tile_size = d.pop('tile_size')

        tiles = [Tile(path, tile_size) for path in tile_paths]

        map_ = {}
        for pos_string, tile in tile_ids.items():
            x, y = map(int, pos_string.split())
            map_[(x, y)] = tile

        map_ = cls(tiles, map_, tile_size)

        return map_

    def get_neighbours_name(self, map_pos):
        """Get a table with the neighbors. topleft will be table[-1][-1] and center right will be table[1][0]."""
        neigh = [[None] * 3 for _ in range(3)]

        for x in range(-1, 2):
            for y in range(-1, 2):
                neighbor = map_pos[0] + x, map_pos[1] + y
                tile = self.tile_at_map_pos(neighbor)
                if tile is not None:
                    tile = tile.name
                neigh[x][y] = tile

        return tuple(tuple(line) for line in neigh)

    @lru_cache(maxsize=None)
    def get_image_at(self, map_pos, scale):
        tile = self.tile_at_map_pos(map_pos)
        image = tile.get_image(self.get_neighbours_name(map_pos))
        return pygame.transform.scale(image, (scale * self.tile_size, scale * self.tile_size))

    def collision_rects(self):
        # we sort them by Y then X
        positions = [(pos[1], pos[0]) for pos in self.tiles]
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

    def light_blockers(self):
        segments = set()
        for pos in self.tiles:
            tile = self.tile_at_map_pos(pos)
            if tile.transparent:
                continue
            x, y = pos
            segs = [
                ((x, y), (x + 1, y)),
                ((x, y + 1), (x + 1, y + 1)),
                ((x, y), (x, y + 1)),
                ((x + 1, y), (x + 1, y + 1)),
            ]

            for seg in segs:
                if seg in segments:
                    # If it's already there, it's an edge between to blocks -> not visible
                    segments.remove(seg)
                else:
                    segments.add(seg)

        # At this point we have a set of unique edges that are between transparent and visible blocks
        # we want to combine edges that are aligned to have less of them

        # we class them by start position
        start_dict = defaultdict(list)
        for s in sorted(segments):
            start_dict[s[0]].append(s)

        def same_orientation(s1, s2):
            # check collinearity
            (ax, ay), (bx, by) = s1
            (cx, cy), (dx, dy) = s2
            ab = bx - ax, by - ay
            cd = dx - cx, dy - cy
            return ab[0] * cd[1] - ab[1] * cd[0] == 0

        final = []
        # reverse to avoid poping from left
        segments = sorted(segments, reverse=True)
        s = segments.pop()
        # we merge all segments that have the same end but only when there's only only two that share to avoid crosses
        while segments:
            # only one that share end
            if len(start_dict[s[1]]) == 1:
                other = start_dict[s[1]][0]
                if same_orientation(s, other):
                    s = s[0], other[1]
                    segments.remove(other)
                else:
                    final.append(s)
                    s = segments.pop()
            else:
                final.append(s)
                s = segments.pop()
        final.append(s)

        # scale everything right
        p = self.tile_size
        final = [((s[0][0] * p, s[0][1] * p), (s[1][0] * p, s[1][1] * p)) for s in final]

        return final

    def add_new_tile_type(self, path, *args, **kwargs):
        tile = Tile(path, *args, **kwargs)
        tile.tile_size = self.tile_size
        self.tile_objects.append(tile)

    def add_tile(self, pos, tile_id):
        self.get_image_at.cache_clear()
        self.tiles[pos] = tile_id

    def remove_tile(self, pos):
        self.get_image_at.cache_clear()
        self.tiles.pop(pos, None)

    def render(self, surf, scale=1, offset=(0, 0)):
        for pos, tile_id in self.tiles.items():
            tile = self.tile_objects[tile_id]
            if tile.transparent:
                continue
            img = self.get_image_at(pos, scale)
            topleft = self.map_to_world_pos(pos)
            topleft = topleft[0] + offset[0], topleft[1] + offset[1]
            surf.blit(img, topleft)


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
        try:
            self.map = TileMap.load()
        except:
            print("Cannot load map")
            self.map = TileMap()
            self.map.add_new_tile_type("assets/dirt_sheet.png")
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
        self._tile_index = value % len(self.map.tile_objects)

    @property
    def current_tile(self):
        return self.map.tile_objects[self.tile_index]

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
                self.map.add_tile(pos, self.tile_index)
            elif self.tool == self.ERASER:
                self.map.remove_tile(pos)

    def render(self, display):
        self.draw_background(display)

        # draw tiles
        for pos in self.map.tiles:
            image = self.map.get_image_at(pos, self.scale)
            display.blit(image, self.pos_to_screen(pos))

        self.widgets.render(display)

    def pos_to_screen(self, pos):
        tot_scale = self.tile_size * self.scale
        return pos[0] * tot_scale, pos[1] * tot_scale

    def screen_to_pos(self, screen):
        tot_scale = self.tile_size * self.scale
        return screen[0] // tot_scale, screen[1] // tot_scale

    def reset(self):
        self.map.tiles.clear()

    def save(self):
        self.map.save()

EDIT = 1

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
    pygame.init()
    Apple().run()
    pygame.quit()


if __name__ == '__main__':
    main()
