from functools import lru_cache

import pygame
from pygame import Vector2 as Pos

MAX_SPEED = 10

class Player:
    def __init__(self):
        img = pygame.image.load("assets/fire.png").convert_alpha()
        self.img = pygame.transform.smoothscale(img, (55, 110))

        self.angle = 0

        self.pos = Pos(0, 0)
        self.speed = Pos(0, 0)
        self.acceleration = Pos(0, 0)

    def update(self):
        self.angle += 12
        self.angle %= 360

        # we use pressed to better handle LEFT + RIGHT
        pressed = pygame.key.get_pressed()
        ax = ay = 0
        if pressed[pygame.K_LEFT]:
            ax -= 1
        if pressed[pygame.K_RIGHT]:
            ax += 1
        if pressed[pygame.K_UP]:
            ay -= 1
        if pressed[pygame.K_DOWN]:
            ay += 1
        self.acceleration = Pos(ax, ay)

        self.speed += self.acceleration
        # clamp the speed to MAX_SPEED
        if self.speed.length() > MAX_SPEED:
            self.speed *= MAX_SPEED / self.speed.length()

        # Brake
        if self.acceleration.x == 0:
            self.speed = Pos(self.speed.x / 2, self.speed.y)
        if self.acceleration.y == 0:
            self.speed = Pos(self.speed.x, self.speed.y / 2)

        self.pos += self.speed

    def get_rect(self):
        rect = self.img.get_rect()
        rect.center = self.pos - (0, rect.h / 4)
        return rect

    def render(self, display):
        display.blit(self.img, self.get_rect())

    @lru_cache()
    def rotated(self, angle):
        rect = self.img.get_rect()
        # but the image is bigger, aka it doesn't cut corners
        rot = pygame.transform.rotate(self.img, angle)
        rrot = rot.get_rect()
        # rrot.center = rect.center
        rect.center = rrot.center
        well = pygame.Surface(rect.size, pygame.SRCALPHA)
        well.blit(rot, (-rect.x, -rect.y))
        return well
