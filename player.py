import pygame

from maths import Pos, approx, clamp
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
        self.hovering = False
        self.jump_frames = 0

        shape = AABB((32, 8), self.img.get_size())
        self.body = Body(shape, (2, 3), moving=True)

    @property
    def light_pos(self):
        r = self.get_rect()
        return r.center  # + Pos(0, r.h/4)

    def event_loop(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                self.hovering = True
                if self.body.grounded:
                    self.jumping = True
                    self.body.velocity.y -= 2
            elif e.key == pygame.K_LEFT:
                self.direction[0] = True
            elif e.key == pygame.K_RIGHT:
                self.direction[1] = True

        elif e.type == pygame.KEYUP:
            if e.key == pygame.K_SPACE:
                self.jumping = False
                self.hovering = False
                self.jump_frames = 0
            elif e.key == pygame.K_LEFT:
                self.direction[0] = False
            elif e.key == pygame.K_RIGHT:
                self.direction[1] = False

    def update(self):

        if self.direction[0] == self.direction[1]:
            self.body.velocity.x = 0
        elif self.direction[0]:
            self.body.acceleration.x -= 0.1
        elif self.direction[1]:
            self.body.acceleration.x += 0.1

        ay = 0
        if self.jumping:
            # we almost cancel gravity for the first frames and then less and less
            ay = self.body.space.gravity.y * clamp(1 - self.jump_frames / 20, 0, 1)
            self.jump_frames += 1
        elif self.hovering:
            # if we go down when hovering, we reduce the gravity
            if self.body.velocity.y > 0:
                ay += self.body.space.gravity.y * 0.5

        # after a jump we want to quickly start going down for more control
        # hovering but going up is not wanted
        if not self.jumping and self.body.velocity.y < 0:
            self.body.velocity.y /= 2

        self.body.acceleration.y -= ay

    def get_rect(self):
        return self.body.shape.pygame_rect

    def render(self, display):
        display.blit(self.img, self.body.shape.topleft)

    def get_rotated(self, angle: int) -> pygame.Surface:
        return pygame.transform.rotate(self.img, angle)

