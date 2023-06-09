from random import random
from time import time

import pygame

from entities import LightParticle
from light import Light
from maths import Pos, clamp
from physics import Body, AABB

MAX_PLAYER_SPEED = (3, 6)
JUMP_IMPULSE = -3
JUMP_DURATION = 30
WALLJUMP_DURATION = 40
JUMP_BRAKE_STRENGTH = 2
WALK_ACCELERATION = 0.2
WALLJUMP_IMPULSE = (3, -3.5)
HOVERING_GRAVITY_FACTOR = 0.5
# LIGHT_COLOR = (255, 130, 80)
LIGHT_COLOR = (100, ) * 3
LIGHT_PIERCING = 5
SIGHT = 69
LIGHT_EMIT_DELAY = 10
LIGHT_LIFE_TIME = 10


class Player:
    building_fire: LightParticle

    def __init__(self):

        # image and shape
        img = pygame.image.load("assets/wizzard.png").convert_alpha()
        # img.set_colorkey((255, 0, 255))
        self._img = img
        self._img_flipped = pygame.transform.flip(img, True, False)
        self.sprite_offset = (1, 0)
        shape = AABB((42, 8), (16, 26))

        self.direction = [False, False]
        self.looking_left = True
        self.jumping = False
        self.hovering = False
        self.wall_jump = 0
        self.jump_frames = 0
        self.firing = False
        self.fire_time = 0
        self.building_fire = None
        self.raffale = False

        self.body = Body(shape, max_velocity=MAX_PLAYER_SPEED, moving=True)

        self.light = Light(self.light_pos, LIGHT_COLOR, SIGHT, LIGHT_PIERCING, variants=10)
        self.lights = []
        self.last_light_emit_time = 0

    @property
    def img(self):
        if self.looking_left:
            return self._img
        else:
            return self._img_flipped

    @property
    def light_pos(self):
        r = self.get_rect()
        if self.looking_left:
            return r.topleft + Pos(1, 7)
        else:
            return r.topright + Pos(-3, 7)

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
            elif e.key == pygame.K_w:
                self.firing = True
                self.fire_time = time()
                self.building_fire = LightParticle(self.light_pos, range=15)
            elif e.key == pygame.K_d:
                self.raffale = True
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
            elif e.key == pygame.K_w:
                self.fire()
                self.firing = False
                self.fire_time = None
            elif e.key == pygame.K_d:
                self.raffale = False
                self.raffle_fire()

    def update(self):
        self.light.center = self.light_pos

        if self.direction[0] == self.direction[1]:
            self.body.velocity.x = 0
        elif self.direction[0]:
            self.body.acceleration.x -= WALK_ACCELERATION
            self.looking_left = True
        elif self.direction[1]:
            self.looking_left = False
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

        # Lights
        if self.raffale:
            if self.building_fire is None:
                self.building_fire = LightParticle(self.light_pos, range=15)
            elif self.building_fire.range > 40:
                self.raffle_fire()
                self.building_fire = LightParticle(self.light_pos, range=15)
            else:
                self.building_fire.range += 4
            self.building_fire.center = self.light_pos

        elif self.building_fire:
            self.building_fire.range = round(min(time() - self.fire_time, 1) * 50) + 10
            self.building_fire.center = self.light_pos

        for l in self.lights[:]:
            l.update()
            if l.range < 3:
                self.lights.remove(l)
                self.body.space.moving_bodies.remove(l)



        if False:
            if time() - self.last_light_emit_time > LIGHT_EMIT_DELAY:
                self.last_light_emit_time = time()
                velocity = self.body.velocity + (random() - 1/2, random() - 1/2)
                light = LightParticle(self.light_pos, velocity, life_time=LIGHT_LIFE_TIME)
                self.lights.append(light)
                self.body.space.add(light)
            for l in self.lights[:]:
                l.update()
                if l.range < 2:
                    self.lights.remove(l)
                    l.space.moving_bodies.remove(l)
                else:
                    # add a spring between the light and the player
                    spring_origin = self.light_pos + Pos(20, 0) * (2*self.looking_left - 1)  # 20 px behind player
                    r = l.center - spring_origin
                    v = l.velocity

                    # -kr - bv  #physicsclass
                    l.acceleration += -0.01 * r - 0.05 * v
    def get_rect(self):
        return self.body.shape.pygame_rect

    def render(self, display: pygame.Surface):
        display.blit(self.img, self.body.shape.topleft - self.sprite_offset)
        # display.set_at(approx(self.light_pos), rainbow)

    def get_rotated(self, angle: int) -> pygame.Surface:
        return pygame.transform.rotate(self.img, angle)

    def get_all_lights(self):
        ret = [self.light, *self.lights]
        if self.building_fire:
            ret.append(self.building_fire)
        return ret

    def fire(self):
        if not self.building_fire:
            return

        if not self.building_fire.velocity:
            vx = self.body.velocity.x - 10*(self.looking_left * 2 - 1)
            self.building_fire.velocity = Pos(vx, random() / 5 - 0.1)
        if not self.building_fire.life_time:
            self.building_fire.life_time = self.building_fire.range / 30
        self.lights.append(self.building_fire)
        self.body.space.add(self.building_fire)
        self.building_fire = None

    def raffle_fire(self):
        if not self.building_fire:
            return
        vx = -6 * (2 * self.looking_left - 1), 3*random() - 2
        self.building_fire.velocity = self.body.velocity + vx
        self.building_fire.life_time = 0.4
        self.fire()

