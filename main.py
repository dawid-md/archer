import pygame
import sys
import math
import random

FPS = 60
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720

GRAVITY = 0.6
JUMP_FORCE = -14.0
PLAYER_SPEED = 5
PLAYER_WIDTH = 24
PLAYER_HEIGHT = 60
GROUND_HEIGHT = 28
PUNCH_DURATION = 14
KICK_DURATION = 20

SHOOT_COOLDOWN = 20
SHOOT_ANIM_DURATION = 10
BOW_HALF_SPAN = 12
BOW_CURVE = 8
ARROW_SPEED = 16.0
ARROW_LENGTH = 20
ARROW_GRAVITY = 0.14

HEAD_RADIUS = 9
TORSO_LEN = 18
ARM_LEN = 16
LEG_LEN = 22

SKY_COLOR = (6, 6, 18)
MOON_COLOR = (235, 228, 195)
MTN_FAR = (11, 11, 26)
MTN_NEAR = (17, 17, 36)
GROUND_TOP = (52, 140, 60)
GROUND_MID = (38, 110, 44)
GROUND_BOT = (22, 72, 28)
SKIN = (210, 170, 130)
CLOTH = (65, 85, 155)
HAIR = (50, 32, 14)
EYE = (28, 18, 10)
BOW_COLOR = (96, 62, 30)
STRING_COLOR = (215, 210, 195)
ARROW_SHAFT_COLOR = (200, 195, 180)
ARROW_HEAD_COLOR = (150, 150, 160)
ARROW_FLETCH_COLOR = (175, 45, 45)

BIRD_COUNT = 6
BIRD_MIN_SPEED = 1.2
BIRD_MAX_SPEED = 2.6
BIRD_SIZE = 6
BIRD_COLOR = (30, 30, 35)
BIRD_MIN_Y_FRAC = 0.08
BIRD_MAX_Y_FRAC = 0.35
BIRD_FALL_GRAVITY = 0.5


def draw_segment(surface, color, start, length, angle, width=3):
    """Draw a limb from start; angle is radians from downward vertical (+= rightward)."""
    ex = start[0] + math.sin(angle) * length
    ey = start[1] + math.cos(angle) * length
    end = (int(ex), int(ey))
    pygame.draw.line(surface, color, (int(start[0]), int(start[1])), end, width)
    return end


class Background:
    def __init__(self, screen_w: int, screen_h: int) -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.stars = self._gen_stars(90)
        self.far_pts = self._gen_mountain(seed=7, x_step=(50, 110), y_range=(0.42, 0.62))
        self.near_pts = self._gen_mountain(seed=13, x_step=(70, 150), y_range=(0.58, 0.76))

    def _gen_stars(self, count):
        rng = random.Random(99)
        stars = []
        for _ in range(count):
            x = rng.randint(0, self.screen_w)
            y = rng.randint(0, int(self.screen_h * 0.72))
            size = rng.choices([1, 2], weights=[4, 1])[0]
            base = rng.randint(140, 255)
            phase = rng.uniform(0, math.tau)
            speed = rng.uniform(0.01, 0.05)
            stars.append((x, y, size, base, phase, speed))
        return stars

    def _gen_mountain(self, seed, x_step, y_range):
        rng = random.Random(seed)
        pts = [(0, self.screen_h)]
        x = 0
        lo = int(self.screen_h * y_range[0])
        hi = int(self.screen_h * y_range[1])
        while x < self.screen_w:
            x += rng.randint(*x_step)
            pts.append((min(x, self.screen_w), rng.randint(lo, hi)))
        pts.append((self.screen_w, self.screen_h))
        return pts

    def render(self, surface: pygame.Surface, t: float) -> None:
        surface.fill(SKY_COLOR)

        # Crescent moon (top-right area, proportional to screen)
        moon_x = int(self.screen_w * 0.85)
        pygame.draw.circle(surface, MOON_COLOR, (moon_x, 75), 38)
        pygame.draw.circle(surface, SKY_COLOR, (moon_x + 20, 62), 32)

        # Twinkling stars
        for x, y, size, base, phase, speed in self.stars:
            b = int(base * (0.65 + 0.35 * math.sin(t * speed + phase)))
            color = (b, b, int(b * 0.88))
            if size == 1:
                surface.set_at((x, y), color)
            else:
                pygame.draw.circle(surface, color, (x, y), size)

        # Two-layer mountain silhouettes
        pygame.draw.polygon(surface, MTN_FAR, self.far_pts)
        pygame.draw.polygon(surface, MTN_NEAR, self.near_pts)

        # Green ground
        gy = self.screen_h - GROUND_HEIGHT
        pygame.draw.rect(surface, GROUND_BOT, (0, gy, self.screen_w, GROUND_HEIGHT))
        pygame.draw.rect(surface, GROUND_MID, (0, gy, self.screen_w, GROUND_HEIGHT - 6))
        pygame.draw.rect(surface, GROUND_TOP, (0, gy, self.screen_w, 6))


class Arrow:
    def __init__(self, x: float, y: float, angle_deg: float) -> None:
        self.x = x
        self.y = y
        rad = math.radians(angle_deg)
        self.dir_x = math.cos(rad)
        self.dir_y = -math.sin(rad)
        self.vel_x = self.dir_x * ARROW_SPEED
        self.vel_y = self.dir_y * ARROW_SPEED
        self.active = True

    def update(self, screen_w: int, screen_h: int) -> None:
        self.vel_y += ARROW_GRAVITY
        self.x += self.vel_x
        self.y += self.vel_y

        speed = math.hypot(self.vel_x, self.vel_y)
        if speed > 0:
            self.dir_x = self.vel_x / speed
            self.dir_y = self.vel_y / speed

        margin = 60
        if not (-margin <= self.x <= screen_w + margin and -margin <= self.y <= screen_h + margin):
            self.active = False

    def render(self, surface: pygame.Surface) -> None:
        dx, dy = self.dir_x, self.dir_y
        tip = (self.x, self.y)
        tail = (self.x - dx * ARROW_LENGTH, self.y - dy * ARROW_LENGTH)
        pygame.draw.line(surface, ARROW_SHAFT_COLOR, tail, tip, 2)

        perp = (-dy, dx)
        head_left = (tip[0] - dx * 6 + perp[0] * 4, tip[1] - dy * 6 + perp[1] * 4)
        head_right = (tip[0] - dx * 6 - perp[0] * 4, tip[1] - dy * 6 - perp[1] * 4)
        pygame.draw.polygon(surface, ARROW_HEAD_COLOR, [tip, head_left, head_right])

        fletch_a = (tail[0] + perp[0] * 3, tail[1] + perp[1] * 3)
        fletch_b = (tail[0] - perp[0] * 3, tail[1] - perp[1] * 3)
        pygame.draw.line(surface, ARROW_FLETCH_COLOR, tail, fletch_a, 2)
        pygame.draw.line(surface, ARROW_FLETCH_COLOR, tail, fletch_b, 2)


class Bird:
    def __init__(self, screen_w: int, screen_h: int) -> None:
        self.respawn(screen_w, screen_h)

    def respawn(self, screen_w: int, screen_h: int) -> None:
        self.x = random.uniform(0, screen_w)
        self.y = random.uniform(screen_h * BIRD_MIN_Y_FRAC, screen_h * BIRD_MAX_Y_FRAC)
        self.vel_x = random.uniform(BIRD_MIN_SPEED, BIRD_MAX_SPEED) * random.choice([-1, 1])
        self.vel_y = 0.0
        self.wing_phase = random.uniform(0, math.tau)
        self.alive = True

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - BIRD_SIZE), int(self.y - BIRD_SIZE),
                            BIRD_SIZE * 2, BIRD_SIZE * 2)

    def hit(self) -> None:
        if self.alive:
            self.alive = False
            self.vel_y = -2.0

    def update(self, screen_w: int, screen_h: int) -> None:
        self.wing_phase += 0.25
        if self.alive:
            self.x += self.vel_x
            if self.x < -20:
                self.x = screen_w + 20
            elif self.x > screen_w + 20:
                self.x = -20
        else:
            self.vel_y += BIRD_FALL_GRAVITY
            self.x += self.vel_x * 0.3
            self.y += self.vel_y
            if self.y > screen_h + 30:
                self.respawn(screen_w, screen_h)

    def render(self, surface: pygame.Surface) -> None:
        cx, cy = int(self.x), int(self.y)
        flap = int(math.sin(self.wing_phase) * BIRD_SIZE) if self.alive else -BIRD_SIZE
        pygame.draw.line(surface, BIRD_COLOR, (cx - BIRD_SIZE * 2, cy - flap), (cx, cy), 2)
        pygame.draw.line(surface, BIRD_COLOR, (cx + BIRD_SIZE * 2, cy - flap), (cx, cy), 2)
        pygame.draw.circle(surface, BIRD_COLOR, (cx, cy), 2)


class Player:
    def __init__(self, x: int, y: int) -> None:
        self.rect = pygame.Rect(x, y, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.vel_x = 0
        self.vel_y = 0.0
        self.on_ground = False
        self.facing_right = True
        self.walk_cycle = 0.0
        self.attack: str | None = None
        self.attack_timer = 0
        self.aim_angle_deg = 0.0
        self.shoot_cooldown = 0
        self.bow_timer = 0

    def process_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = PLAYER_SPEED
            self.facing_right = True
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = JUMP_FORCE
            self.on_ground = False

    def shoulder_pos(self) -> tuple[float, float]:
        cx = self.rect.centerx
        top = self.rect.top
        return (cx, top + HEAD_RADIUS * 2 + 2)

    def update_aim(self, mouse_pos: tuple[int, int]) -> None:
        shoulder = self.shoulder_pos()
        dx = mouse_pos[0] - shoulder[0]
        dy = mouse_pos[1] - shoulder[1]
        if dx == 0 and dy == 0:
            return
        self.aim_angle_deg = math.degrees(math.atan2(-dy, dx))
        self.facing_right = dx >= 0

    def hand_pos(self) -> tuple[float, float]:
        shoulder = self.shoulder_pos()
        rad = math.radians(self.aim_angle_deg)
        fwd = (math.cos(rad), -math.sin(rad))
        return (shoulder[0] + fwd[0] * ARM_LEN, shoulder[1] + fwd[1] * ARM_LEN)

    def try_shoot(self) -> "Arrow | None":
        if self.shoot_cooldown > 0 or self.attack is not None:
            return None
        self.shoot_cooldown = SHOOT_COOLDOWN
        self.bow_timer = SHOOT_ANIM_DURATION
        hand = self.hand_pos()
        return Arrow(hand[0], hand[1], self.aim_angle_deg)

    def update(self, screen_w: int, screen_h: int) -> None:
        self.vel_y += GRAVITY
        if self.vel_x != 0:
            self.walk_cycle += 0.18
        self.rect.x += self.vel_x
        self.rect.y += int(self.vel_y)
        self.rect.x = max(0, min(screen_w - self.rect.width, self.rect.x))
        floor = screen_h - GROUND_HEIGHT
        if self.rect.bottom >= floor:
            self.rect.bottom = floor
            self.vel_y = 0.0
            self.on_ground = True

        if self.attack_timer > 0:
            self.attack_timer -= 1
            if self.attack_timer == 0:
                self.attack = None

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.bow_timer > 0:
            self.bow_timer -= 1

    def try_attack(self, kind: str) -> None:
        if self.attack is None:
            self.attack = kind
            self.attack_timer = PUNCH_DURATION if kind == 'punch' else KICK_DURATION

    def render(self, surface: pygame.Surface) -> None:
        cx = self.rect.centerx
        top = self.rect.top
        f = 1 if self.facing_right else -1

        head_pos = (cx, top + HEAD_RADIUS)
        shoulder = (cx, top + HEAD_RADIUS * 2 + 2)
        hip = (cx, shoulder[1] + TORSO_LEN)

        if self.on_ground and self.vel_x != 0:
            s = math.sin(self.walk_cycle) * 0.45
        elif not self.on_ground:
            s = 0.22
        else:
            s = 0.0

        if self.attack is not None:
            duration = PUNCH_DURATION if self.attack == 'punch' else KICK_DURATION
            progress = 1.0 - self.attack_timer / duration
            swing = math.sin(progress * math.pi)
            if self.attack == 'punch':
                back_leg, front_leg = -f * s, f * s
                back_arm = -f * 0.35
                front_arm = f * swing * 1.5
            else:  # kick
                back_leg, front_leg = -f * 0.2, f * swing * 1.25
                back_arm = -f * s * 0.6
                front_arm = f * s * 0.6
        else:
            back_leg, front_leg = -f * s, f * s
            back_arm = -f * s * 0.6
            front_arm = math.radians(self.aim_angle_deg) + math.pi / 2

        draw_segment(surface, CLOTH, hip, LEG_LEN, back_leg, 5)
        draw_segment(surface, CLOTH, hip, LEG_LEN, front_leg, 5)
        pygame.draw.line(surface, CLOTH,
                         (int(shoulder[0]), int(shoulder[1])),
                         (int(hip[0]), int(hip[1])), 5)
        draw_segment(surface, SKIN, shoulder, ARM_LEN, back_arm, 3)
        hand_pos = draw_segment(surface, SKIN, shoulder, ARM_LEN, front_arm, 3)
        if self.attack is None:
            self._draw_bow(surface, hand_pos)
        pygame.draw.circle(surface, SKIN, head_pos, HEAD_RADIUS)
        hair_rect = pygame.Rect(cx - HEAD_RADIUS, top, HEAD_RADIUS * 2, HEAD_RADIUS + 2)
        pygame.draw.ellipse(surface, HAIR, hair_rect)
        pygame.draw.circle(surface, EYE, (cx + f * 5, head_pos[1] + 2), 2)

    def _draw_bow(self, surface: pygame.Surface, hand_pos: tuple[int, int]) -> None:
        rad = math.radians(self.aim_angle_deg)
        fwd = (math.cos(rad), -math.sin(rad))
        perp = (-fwd[1], fwd[0])
        pull = self.bow_timer / SHOOT_ANIM_DURATION if self.bow_timer > 0 else 0.15

        tip1 = (hand_pos[0] + perp[0] * BOW_HALF_SPAN - fwd[0] * BOW_CURVE * 0.3,
                hand_pos[1] + perp[1] * BOW_HALF_SPAN - fwd[1] * BOW_CURVE * 0.3)
        tip2 = (hand_pos[0] - perp[0] * BOW_HALF_SPAN - fwd[0] * BOW_CURVE * 0.3,
                hand_pos[1] - perp[1] * BOW_HALF_SPAN - fwd[1] * BOW_CURVE * 0.3)
        mid = (hand_pos[0] - fwd[0] * BOW_CURVE, hand_pos[1] - fwd[1] * BOW_CURVE)

        pts = []
        for i in range(9):
            t = i / 8
            x = (1 - t) ** 2 * tip1[0] + 2 * (1 - t) * t * mid[0] + t ** 2 * tip2[0]
            y = (1 - t) ** 2 * tip1[1] + 2 * (1 - t) * t * mid[1] + t ** 2 * tip2[1]
            pts.append((x, y))
        pygame.draw.lines(surface, BOW_COLOR, False, pts, 2)

        nock = (hand_pos[0] - fwd[0] * (2 + pull * 14), hand_pos[1] - fwd[1] * (2 + pull * 14))
        pygame.draw.line(surface, STRING_COLOR, tip1, nock, 1)
        pygame.draw.line(surface, STRING_COLOR, tip2, nock, 1)

        arrow_tip = (hand_pos[0] + fwd[0] * 10, hand_pos[1] + fwd[1] * 10)
        pygame.draw.line(surface, ARROW_SHAFT_COLOR, nock, arrow_tip, 2)


def main() -> None:
    pygame.init()

    screen_w, screen_h = DEFAULT_WIDTH, DEFAULT_HEIGHT
    screen = pygame.display.set_mode((screen_w, screen_h), pygame.RESIZABLE)
    pygame.display.set_caption("Fighter")
    clock = pygame.time.Clock()
    fullscreen = False

    bg = Background(screen_w, screen_h)
    player = Player(screen_w // 2 - PLAYER_WIDTH // 2, screen_h - GROUND_HEIGHT - PLAYER_HEIGHT)
    arrows: list[Arrow] = []
    birds = [Bird(screen_w, screen_h) for _ in range(BIRD_COUNT)]
    t = 0.0

    while True:
        # --- Input ---
        shoot_requested = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                shoot_requested = True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                if event.key in (pygame.K_z, pygame.K_j):
                    player.try_attack('punch')
                if event.key in (pygame.K_x, pygame.K_k):
                    player.try_attack('kick')

                alt_enter = event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT)
                if event.key == pygame.K_F11 or alt_enter:
                    fullscreen = not fullscreen
                    flags = pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE
                    size = (0, 0) if fullscreen else (DEFAULT_WIDTH, DEFAULT_HEIGHT)
                    screen = pygame.display.set_mode(size, flags)
                    screen_w, screen_h = screen.get_size()
                    bg = Background(screen_w, screen_h)
                    player.rect.bottom = min(player.rect.bottom, screen_h - GROUND_HEIGHT)

            if event.type == pygame.VIDEORESIZE and not fullscreen:
                screen_w, screen_h = event.w, event.h
                screen = pygame.display.set_mode((screen_w, screen_h), pygame.RESIZABLE)
                bg = Background(screen_w, screen_h)

        keys = pygame.key.get_pressed()
        player.process_input(keys)
        player.update_aim(pygame.mouse.get_pos())
        if shoot_requested:
            arrow = player.try_shoot()
            if arrow is not None:
                arrows.append(arrow)

        # --- Update ---
        player.update(screen_w, screen_h)
        for arrow in arrows:
            arrow.update(screen_w, screen_h)
        for bird in birds:
            bird.update(screen_w, screen_h)

        for arrow in arrows:
            if not arrow.active:
                continue
            for bird in birds:
                if bird.alive and bird.rect().collidepoint(arrow.x, arrow.y):
                    bird.hit()
                    arrow.active = False
                    break

        arrows = [arrow for arrow in arrows if arrow.active]
        t += 1.0

        # --- Render ---
        bg.render(screen, t)
        for bird in birds:
            bird.render(screen)
        player.render(screen)
        for arrow in arrows:
            arrow.render(screen)
        pygame.display.flip()

        clock.tick(FPS)


if __name__ == "__main__":
    main()
