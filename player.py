import pygame

from maths import Pos, approx
from physics import Body, AABB

MAX_SPEED = 80
MOVE_FORCE = 300
JUMP_IMPULSE = 50

class Player:
    def __init__(self):
        img = pygame.image.load("assets/fire2.png").convert()
        img.set_colorkey((255, 255, 255))
        self.img = pygame.transform.smoothscale(img, (8, 8))

        self.direction = [False, False]
        self.jumping = False
        self.jump_frames = 0

        shape = AABB((32, 8), self.img.get_size())
        self.body = Body(shape, (1, 2), moving=True)

    @property
    def light_pos(self):
        r = self.get_rect()
        return r.center  # + Pos(0, r.h/4)

    def event_loop(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                if self.body.grounded:
                    self.jumping = True
            elif e.key == pygame.K_LEFT:
                self.direction[0] = True
            elif e.key == pygame.K_RIGHT:
                self.direction[1] = True

        elif e.type == pygame.KEYUP:
            if e.key == pygame.K_SPACE:
                self.jumping = False
                self.jump_frames = 0
            elif e.key == pygame.K_LEFT:
                self.direction[0] = False
            elif e.key == pygame.K_RIGHT:
                self.direction[1] = False

    def update(self):

        if self.direction[0] == self.direction[1]:
            self.body.velocity.x = 0
        elif self.direction[0]:
            self.body.acceleration.x -= 0.4
        elif self.direction[1]:
            self.body.acceleration.x += 0.4

        if self.jumping:
            self.jump_frames += 1
            if self.jump_frames < 15:
                ay = self.body.space.gravity.y * 2
            else:
                ay = self.body.space.gravity.y / 2
            self.body.acceleration.y -= ay

    def get_rect(self):
        return self.body.shape.pygame_rect

    def render(self, display):
        display.blit(self.img, self.body.shape.topleft)

    def get_rotated(self, angle: int) -> pygame.Surface:
        return pygame.transform.rotate(self.img, angle)

