import pygame

from maths import Pos
from physics import Body

MAX_SPEED = 80
MOVE_FORCE = 300
JUMP_IMPULSE = 50

class Player:
    def __init__(self):
        img = pygame.image.load("assets/fire2.png").convert()
        img.set_colorkey((255, 255, 255))
        self.img = pygame.transform.smoothscale(img, (8, 8))

        self.direction = Pos(0, 0)

        self.body = Body((32, 8), self.img.get_size(), (1, 2), moving=True)

    @property
    def light_pos(self):
        r = self.get_rect()
        return r.center  # + Pos(0, r.h/4)

    def event_loop(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                ...
            elif e.key == pygame.K_LEFT:
                self.direction[0] = True
            elif e.key == pygame.K_RIGHT:
                self.direction[1] = True
            elif e.key == pygame.K_r:
                self.body.position = (32, 24)

        if e.type == pygame.KEYUP:
            if e.key == pygame.K_LEFT:
                self.direction[0] = False
            elif e.key == pygame.K_RIGHT:
                self.direction[1] = False

    def update(self):

        if self.direction[0] == self.direction[1]:
            pass
        elif self.direction[0]:
            self.body.acceleration.x -= 0.5
        elif self.direction[1]:
            self.body.acceleration.x += 0.5

    def get_rect(self):
        return self.body

    def render(self, display):
        r = self.get_rect()
        display.blit(self.img, self.body.topleft)

    def get_rotated(self, angle: int) -> pygame.Surface:
        return pygame.transform.rotate(self.img, angle)

