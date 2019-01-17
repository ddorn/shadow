#!/usr/bin/env python3

"""
Another Perfect Lite Level Editor
"""
import json
from functools import lru_cache
from typing import List

import pygame
from graphalama.app import App, Screen
from graphalama.buttons import CarouselSwitch, Button
from graphalama.maths import Pos

pygame.init()

EDIT = 1

class Tile:
    def __init__(self, path, size):
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
                        c = patern[3*y + x]
                        if c == '=':
                            if neighbors[x - 1][y -1] != tile_id:
                                match = False
                        elif c == ' ':
                            if neighbors[x - 1][y -1] == tile_id:
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

        super().__init__(**kwargs)

    def save(self, file='assets/levels/0'):
        to_save = {}
        for pos, tile in self.items():
            to_save[f'{pos[0]}, {pos[1]}'] = tile
        s = json.dumps(to_save, indent=4)
        with open(file, 'w') as f:
            f.write(s)

    @classmethod
    def load(cls, file='assets/levels/0'):
        with open(file, 'r') as f:
            d = json.loads(f.read())

        map_ = cls()
        for pos_string, tile in d.items():
            x, y = map(int, pos_string.split())
            map_[(x, y)] = tile

        return map_

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
        self.map = Map(tiles)
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


if __name__ == '__main__':
    main()
    pygame.quit()
