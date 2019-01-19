import pygame

from maths import Pos, approx, clamp
from physics import Body, AABB

MAX_PLAYER_SPEED = (3, 6)
JUMP_IMPULSE = -3
JUMP_DURATION = 30
WALLJUMP_DURATION = 40
JUMP_BRAKE_STRENGTH = 2
WALK_ACCELERATION = 0.2
WALLJUMP_IMPULSE = (3, -3.5)
HOVERING_GRAVITY_FACTOR = 0.5


class Player:
    def __init__(self):
        img = pygame.image.load("assets/fire2.png").convert()
        img.set_colorkey((255, 255, 255))
        self.img = pygame.transform.smoothscale(img, (8, 8))

        self.direction = [False, False]
        self.jumping = False
        self.hovering = False
        self.wall_jump = 0
        self.jump_frames = 0

        shape = AABB((42, 8), self.img.get_size())
        self.body = Body(shape, MAX_PLAYER_SPEED, moving=True)

    @property
    def light_pos(self):
        r = self.get_rect()
        return r.center  # + Pos(0, r.h/4)

    def event_loop(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                self.hovering = True
                if self.body.collide_down:
                    self.jumping = True
                    self.body.velocity.y += JUMP_IMPULSE
                elif self.body.collide_left:
                    self.jumping = False
                    self.wall_jump = 1
                    self.body.velocity = Pos(WALLJUMP_IMPULSE)
                elif self.body.collide_right:
                    self.jumping = False
                    self.wall_jump = -1
                    self.body.velocity = Pos(-WALLJUMP_IMPULSE[0], WALLJUMP_IMPULSE[1])
            elif e.key == pygame.K_LEFT:
                self.direction[0] = True
            elif e.key == pygame.K_RIGHT:
                self.direction[1] = True

        elif e.type == pygame.KEYUP:
            if e.key == pygame.K_SPACE:
                self.jumping = False
                self.hovering = False
                self.wall_jump = 0
                self.jump_frames = 0
            elif e.key == pygame.K_LEFT:
                self.direction[0] = False
            elif e.key == pygame.K_RIGHT:
                self.direction[1] = False

    def update(self):

        if self.direction[0] == self.direction[1]:
            self.body.velocity.x = 0
        elif self.direction[0]:
            self.body.acceleration.x -= WALK_ACCELERATION
        elif self.direction[1]:
            self.body.acceleration.x += WALK_ACCELERATION

        ay = 0
        if self.jumping:
            # we almost cancel gravity for the first frames and then less and less
            ay = self.body.space.gravity.y * clamp(1 - self.jump_frames / JUMP_DURATION, 0, 1)
            self.jump_frames += 1
        elif self.wall_jump:
            ay = self.body.space.gravity.y * clamp(1 - self.jump_frames / WALLJUMP_DURATION, 0, 1)
            # self.body.acceleration.x += self.wall_jump * ay
            self.jump_frames += 1
        elif self.hovering:
            # if we go down when hovering, we reduce the gravity
            if self.body.velocity.y > 0:
                ay += self.body.space.gravity.y * HOVERING_GRAVITY_FACTOR

        # after a jump we want to quickly start going down for more control
        # hovering but going up is not wanted
        if not self.jumping and not self.wall_jump and self.body.velocity.y < 0:
            self.body.velocity.y /= JUMP_BRAKE_STRENGTH

        self.body.acceleration.y -= ay

    def get_rect(self):
        return self.body.shape.pygame_rect

    def render(self, display):
        display.blit(self.img, self.body.shape.topleft)

    def get_rotated(self, angle: int) -> pygame.Surface:
        return pygame.transform.rotate(self.img, angle)

