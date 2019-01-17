"""
Another Perfect Lite Level Editor
"""
from functools import lru_cache

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


class EditScreen(Screen):
    BRUSH = 1
    ERASER = 2

    def __init__(self, app):

        tool = CarouselSwitch(["Brush", "Eraser"], self.tool_change, (20, 20))
        reset = Button("Reset", self.reset, bg_color=(240, 60, 60))
        save = Button("Save", self.save)
        widgets = (tool, reset, save)
        super().__init__(app, widgets, (20, 40, 90))
        self.map = {}
        self.tile_size = 16
        self.tiles = [Tile("assets/dirt_sheet.png", self.tile_size)]
        self.tile_index = 0
        self.scale = 4
        self.drawing = False
        self.tool = self.BRUSH

    @property
    def current_tile(self):
        return self.tiles[self.tile_index % len(self.tiles)]

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
            tile = self.tiles[tile_i]
            image = tile.get_image(self.get_neighbors(pos), self.scale)
            display.blit(image, self.pos_to_screen(pos))

        self.widgets.render(display)

    def pos_to_screen(self, pos):
        tot_scale = self.tile_size * self.scale
        return pos[0] * tot_scale, pos[1] * tot_scale

    def screen_to_pos(self, screen):
        tot_scale = self.tile_size * self.scale
        return screen[0] // tot_scale, screen[1] // tot_scale

    def get_neighbors(self, pos):
        """Get a table with the neighbors. topleft will be table[-1][-1] and center right will be table[1][0]."""
        neigh = [[None] * 3 for _ in range(3)]

        for x in range(-1, 2):
            for y in range(-1, 2):
                neighbor = pos[0] + x, pos[1] + y
                tile = self.map.get(neighbor, None)
                neigh[x][y] = tile

        return tuple(tuple(line) for line in neigh)

    def reset(self):
        self.map = {}

    def save(self):
        pass


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