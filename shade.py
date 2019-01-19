#!/usr/bin/env python3

from math import floor

import pygame
from graphalama.text import SimpleText
from visibility import VisibiltyCalculator

from apple import Map
from maths import segments, Pos
from physics import Space, AABB
from player import Player
from vfx import np_limit_visibility, get_light_mask

pygame.init()

BLOCK_SIZE = 16
GAME_SIZE = (480, 270)
SCREEN_SIZE = (1920, 1080)
LIGHT_COLOR = (248 // 2, 235 // 2, 68 // 2, 255)
LIGHT_COLOR = (255, 170, 100)
SHADOW_COLOR = (20, 70, 80)
SHADOW_COLOR = (0, 0, 0)
SIGHT = 160
SPEED = 10


class App:
    FPS = 60
    ENABLE_SHADOW = True
    BLIT_MODE = 0
    MOUSE_CONTROL = False

    def __init__(self):
        self.display = pygame.display.set_mode(SCREEN_SIZE)  # type: pygame.Surface
        self.back_screen = pygame.Surface(GAME_SIZE, pygame.SRCALPHA)
        self.clock = pygame.time.Clock()
        self.map = Map.load('assets/levels/0', )
        self.walls = self.map.collision_rects()
        self.shadow_caster = VisibiltyCalculator(self.create_shadow_walls(GAME_SIZE))
        self.sight = SIGHT
        self.frame = 0
        self.stop = False
        self.player = Player()
        self.space = self.create_space()
        self.light_mask = None
        self.light_mask_view_point = self.player.light_pos
        self.fps_text = SimpleText("Coucou", (20, 20), color=(255, 180, 180))

    def run(self):
        while not self.stop:
            self.frame += 1

            self.event_loop()
            self.update()

            self.render(self.back_screen)
            self.do_shadow()
            self.fps_text.render(self.display)

            pygame.display.update()

            self.clock.tick(self.FPS)
            print("FPS:", round(self.clock.get_fps()), end='\r')
            self.fps_text.text = f"FPS: {round(self.clock.get_fps())}"

    def event_loop(self):
        for e in pygame.event.get():
            # quit
            if e.type == pygame.QUIT:
                self.stop = True
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.stop = True
                elif e.key == pygame.K_t:
                    self.ENABLE_SHADOW = not self.ENABLE_SHADOW
                elif e.key == pygame.K_p:
                    pygame.image.save(self.display, "shadows.png")
                elif e.key == pygame.K_b:
                    self.BLIT_MODE += 1
                    self.BLIT_MODE %= 8
                elif e.key == pygame.K_m:
                    self.MOUSE_CONTROL = not self.MOUSE_CONTROL
            self.player.event_loop(e)

    def update(self):
        self.space.simulate()
        self.player.update()

        if self.MOUSE_CONTROL:
            self.player.body.shape.topleft = Pos(pygame.mouse.get_pos()) // 6

    def render(self, surf):
        surf.fill(LIGHT_COLOR)
        # platforms
        for pos in self.map:
            img = self.map.get_chached_image_at(pos, 1)
            r = self.map.pos_to_rect(pos)
            surf.blit(img, r)

        # for a, b in self.map.shadow_blockers():
        #     pygame.draw.line(surf, (255, 0, 0), a, b)

        self.player.render(surf)

    def do_shadow(self):
        s = pygame.Surface(GAME_SIZE)
        s.fill(SHADOW_COLOR)

        if self.ENABLE_SHADOW:
            self.update_light_mask()
            rect = np_limit_visibility(self.back_screen, self.light_mask_view_point, self.light_mask)
            s.blit(self.back_screen, (0, 0))
        else:
            s.blit(self.back_screen, (0, 0))

        pygame.transform.scale(s, SCREEN_SIZE, self.display)

    def create_shadow_walls(self, screensize):
        shadow_block = self.map.shadow_blockers()
        bound = pygame.Rect((0, 0), screensize)
        shadow_block.extend(segments((bound.topleft, bound.topright,
                                      bound.bottomright, bound.bottomleft)))
        return shadow_block

    def create_space(self):

        space = Space((0, 0.2))

        for rect in self.walls:
            p = AABB(rect.topleft, rect.size)
            space.add(p)

        space.add(self.player.body)
        self.player.body.space = space

        return space

    def update_light_mask(self):
        if self.light_mask is None or self.frame % 2 == 0:
            visible_poly = self.shadow_caster.visible_polygon(self.player.light_pos)
            self.light_mask = get_light_mask(visible_poly, self.player.light_pos, self.sight, self.frame // 6 % 10)
            self.light_mask_view_point = self.player.light_pos


if __name__ == '__main__':
    App().run()
