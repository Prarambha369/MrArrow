"""MrArrow - an archery game made with Pygame.

Controls
    LEFT / RIGHT  (or A / D)   move the archer
    UP / DOWN     (or W / S)   aim the bow
    hold SPACE                 draw the bow (more power the longer you hold)
    release SPACE              shoot
    P                          pause
    M                          mute / unmute
    ESC                        quit
"""

import array
import math
import os
import random

import pygame

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 800, 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 40, 40)
GREEN = (60, 200, 90)
YELLOW = (250, 210, 60)
BLUE = (60, 120, 230)
BROWN = (140, 90, 40)
GREY = (120, 120, 120)
SKY_TOP = (25, 30, 60)
SKY_BOTTOM = (70, 90, 150)
GRASS = (40, 110, 50)

# Player
PLAYER_SIZE = 50
PLAYER_SPEED = 5
GROUND_Y = HEIGHT - 40

# Arrow physics
GRAVITY = 0.25          # pixels per frame^2, pulls arrows down
MIN_POWER = 6           # arrow speed when you tap SPACE
MAX_POWER = 20          # arrow speed when the bow is fully drawn
CHARGE_RATE = 0.4       # how quickly the bow draws
ARROW_LENGTH = 30
AIM_SPEED = 2           # degrees per frame
MIN_ANGLE, MAX_ANGLE = 20, 160   # 90 = straight up

# Scoring: (fraction of target radius, points)
RINGS = [(0.2, 10), (0.4, 8), (0.6, 6), (0.8, 4), (1.0, 2)]
RING_COLORS = [YELLOW, RED, BLUE, BLACK, WHITE]

HIGHSCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.txt")


# ---------------------------------------------------------------------------
# Levels: each level has a target size, target speed, score goal and arrows
# ---------------------------------------------------------------------------
LEVELS = [
    {"radius": 45, "speed": 0.0, "goal": 20, "arrows": 8},
    {"radius": 40, "speed": 1.5, "goal": 30, "arrows": 10},
    {"radius": 35, "speed": 2.5, "goal": 40, "arrows": 10},
    {"radius": 30, "speed": 3.5, "goal": 45, "arrows": 10},
    {"radius": 25, "speed": 4.5, "goal": 50, "arrows": 10},
]


def level_settings(level):
    """Settings for a level number (1-based). After the last level it keeps getting harder."""
    if level <= len(LEVELS):
        return dict(LEVELS[level - 1])
    extra = level - len(LEVELS)
    last = LEVELS[-1]
    return {
        "radius": max(15, last["radius"] - 2 * extra),
        "speed": last["speed"] + 0.5 * extra,
        "goal": last["goal"] + 5 * extra,
        "arrows": last["arrows"],
    }


# ---------------------------------------------------------------------------
# Sound effects - made in code so the game needs no sound files
# ---------------------------------------------------------------------------
class Sounds:
    def __init__(self):
        self.enabled = False
        self.muted = False
        self.effects = {}
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1)
        except pygame.error:
            return  # no audio device - play silently
        self.enabled = True
        self.effects = {
            "shoot": self._tone(700, 300, 0.12),
            "hit": self._tone(500, 900, 0.15),
            "bullseye": self._tone(800, 1600, 0.3),
            "miss": self._tone(250, 150, 0.2),
            "level": self._tone(400, 1200, 0.5),
            "gameover": self._tone(400, 100, 0.7),
        }

    def _tone(self, start_freq, end_freq, seconds, volume=0.3):
        """A short beep that slides from start_freq to end_freq."""
        rate, fmt, channels = pygame.mixer.get_init()
        count = int(rate * seconds)
        samples = array.array("h")
        phase = 0.0
        for i in range(count):
            t = i / count
            freq = start_freq + (end_freq - start_freq) * t
            phase += 2 * math.pi * freq / rate
            fade = 1 - t  # fade out so it doesn't click
            value = int(32767 * volume * fade * math.sin(phase))
            for _ in range(channels):
                samples.append(value)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play(self, name):
        if self.enabled and not self.muted and name in self.effects:
            self.effects[name].play()

    def play_music(self):
        """Gentle background tune looped forever."""
        if not self.enabled:
            return
        notes = [262, 330, 392, 330, 294, 349, 440, 349]
        rate, fmt, channels = pygame.mixer.get_init()
        samples = array.array("h")
        for freq in notes:
            count = int(rate * 0.35)
            for i in range(count):
                fade = 1 - i / count
                value = int(32767 * 0.05 * fade * math.sin(2 * math.pi * freq * i / rate))
                for _ in range(channels):
                    samples.append(value)
        self.music = pygame.mixer.Sound(buffer=samples.tobytes())
        self.music_channel = self.music.play(loops=-1)

    def toggle_mute(self):
        self.muted = not self.muted
        if not self.enabled:
            return
        if self.muted:
            pygame.mixer.pause()
        else:
            pygame.mixer.unpause()


# ---------------------------------------------------------------------------
# Game objects
# ---------------------------------------------------------------------------
class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.angle = 90  # degrees, 90 = straight up
        self.power = MIN_POWER
        self.charging = False

    def move(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += PLAYER_SPEED
        self.x = max(PLAYER_SIZE // 2, min(WIDTH - PLAYER_SIZE // 2, self.x))

        # UP turns the bow left, DOWN turns it right (like turning a dial)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.angle += AIM_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.angle -= AIM_SPEED
        self.angle = max(MIN_ANGLE, min(MAX_ANGLE, self.angle))

        if self.charging:
            self.power = min(MAX_POWER, self.power + CHARGE_RATE)

    def bow_position(self):
        return self.x, GROUND_Y - PLAYER_SIZE

    def shoot(self):
        """Release the bow and return a new Arrow."""
        x, y = self.bow_position()
        rad = math.radians(self.angle)
        arrow = Arrow(x, y, math.cos(rad) * self.power, -math.sin(rad) * self.power)
        self.power = MIN_POWER
        self.charging = False
        return arrow

    def draw(self, surface):
        x, y = self.bow_position()
        # body
        body = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        body.midbottom = (self.x, GROUND_Y)
        pygame.draw.rect(surface, GREEN, body, border_radius=8)
        pygame.draw.circle(surface, WHITE, (self.x - 10, body.top + 18), 5)
        pygame.draw.circle(surface, WHITE, (self.x + 10, body.top + 18), 5)
        # bow
        rad = math.radians(self.angle)
        bow_rect = pygame.Rect(0, 0, 50, 50)
        bow_rect.center = (x, y)
        pygame.draw.arc(surface, BROWN, bow_rect, rad - 1.2, rad + 1.2, 4)
        # aim guide - longer when the bow is drawn harder
        guide = 40 + self.power * 4
        end = (x + math.cos(rad) * guide, y - math.sin(rad) * guide)
        for i in range(1, 6):
            px = x + (end[0] - x) * i / 5
            py = y + (end[1] - y) * i / 5
            pygame.draw.circle(surface, WHITE, (int(px), int(py)), 2)


class Arrow:
    def __init__(self, x, y, vx, vy):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy

    def update(self):
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy

    def tip(self):
        speed = math.hypot(self.vx, self.vy) or 1
        return (self.x + self.vx / speed * ARROW_LENGTH / 2,
                self.y + self.vy / speed * ARROW_LENGTH / 2)

    def off_screen(self):
        return self.x < -50 or self.x > WIDTH + 50 or self.y > HEIGHT + 50

    def draw(self, surface):
        speed = math.hypot(self.vx, self.vy) or 1
        dx, dy = self.vx / speed, self.vy / speed
        tail = (self.x - dx * ARROW_LENGTH / 2, self.y - dy * ARROW_LENGTH / 2)
        tip = self.tip()
        pygame.draw.line(surface, BROWN, tail, tip, 3)
        # arrow head
        left = (tip[0] - dx * 8 - dy * 5, tip[1] - dy * 8 + dx * 5)
        right = (tip[0] - dx * 8 + dy * 5, tip[1] - dy * 8 - dx * 5)
        pygame.draw.polygon(surface, GREY, [tip, left, right])
        # feathers
        pygame.draw.line(surface, RED, tail, (tail[0] - dy * 5, tail[1] + dx * 5), 2)
        pygame.draw.line(surface, RED, tail, (tail[0] + dy * 5, tail[1] - dx * 5), 2)


class Target:
    def __init__(self, radius, speed):
        self.radius = radius
        self.speed = speed
        self.direction = random.choice([-1, 1])
        self.place()

    def place(self):
        """Put the target at a random spot fully on the screen."""
        r = self.radius
        self.x = random.randint(r + 10, WIDTH - r - 10)
        self.y = random.randint(r + 60, HEIGHT // 2)

    def update(self):
        self.x += self.speed * self.direction
        if self.x - self.radius < 0 or self.x + self.radius > WIDTH:
            self.direction *= -1
            self.x = max(self.radius, min(WIDTH - self.radius, self.x))

    def score_for(self, point):
        """Points for hitting `point`, or 0 if it missed."""
        distance = math.hypot(point[0] - self.x, point[1] - self.y)
        for fraction, points in RINGS:
            if distance <= self.radius * fraction:
                return points
        return 0

    def draw(self, surface):
        for (fraction, _), color in reversed(list(zip(RINGS, RING_COLORS))):
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.radius * fraction))
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.radius, 1)


class FloatingText:
    """Text like '+10' that floats up and disappears."""

    def __init__(self, text, x, y, color):
        self.text, self.x, self.y, self.color = text, x, y, color
        self.life = 45

    def update(self):
        self.y -= 1
        self.life -= 1

    def draw(self, surface, font):
        img = font.render(self.text, True, self.color)
        surface.blit(img, img.get_rect(center=(self.x, self.y)))


# ---------------------------------------------------------------------------
# The game
# ---------------------------------------------------------------------------
def load_highscore():
    try:
        with open(HIGHSCORE_FILE) as f:
            return int(f.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def save_highscore(score):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(str(score))
    except OSError:
        pass


class Game:
    # screens
    TITLE, PLAYING, PAUSED, LEVEL_DONE, GAME_OVER = range(5)

    def __init__(self):
        self.window = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("MrArrow - Archery Game")
        self.clock = pygame.time.Clock()
        self.big_font = pygame.font.SysFont(None, 72)
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 26)
        self.background = self._make_background()
        self.sounds = Sounds()
        self.sounds.play_music()
        self.highscore = load_highscore()
        self.state = Game.TITLE
        self.running = True
        self.new_game()

    def _make_background(self):
        bg = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            t = y / HEIGHT
            color = [int(a + (b - a) * t) for a, b in zip(SKY_TOP, SKY_BOTTOM)]
            pygame.draw.line(bg, color, (0, y), (WIDTH, y))
        pygame.draw.rect(bg, GRASS, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        return bg

    # --- game flow -------------------------------------------------------
    def new_game(self):
        self.total_score = 0
        self.level = 1
        self.start_level()

    def start_level(self):
        settings = level_settings(self.level)
        self.goal = settings["goal"]
        self.arrows_left = settings["arrows"]
        self.level_score = 0
        self.player = Player()
        self.target = Target(settings["radius"], settings["speed"])
        self.arrows = []
        self.texts = []

    def finish_level_if_done(self):
        if self.level_score >= self.goal:
            self.state = Game.LEVEL_DONE
            self.sounds.play("level")
        elif self.arrows_left == 0 and not self.arrows:
            self.state = Game.GAME_OVER
            self.sounds.play("gameover")
            if self.total_score > self.highscore:
                self.highscore = self.total_score
                save_highscore(self.highscore)

    # --- input -----------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key == pygame.K_m:
                self.sounds.toggle_mute()
            elif self.state == Game.TITLE and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.state = Game.PLAYING
            elif self.state == Game.PLAYING and event.key == pygame.K_p:
                self.state = Game.PAUSED
            elif self.state == Game.PAUSED and event.key in (pygame.K_p, pygame.K_SPACE):
                self.state = Game.PLAYING
            elif self.state == Game.LEVEL_DONE and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.level += 1
                self.start_level()
                self.state = Game.PLAYING
            elif self.state == Game.GAME_OVER and event.key in (pygame.K_r, pygame.K_RETURN):
                self.new_game()
                self.state = Game.PLAYING
            elif self.state == Game.PLAYING and event.key == pygame.K_SPACE and self.arrows_left > 0:
                self.player.charging = True
        elif event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            # only one arrow per press of SPACE
            if self.state == Game.PLAYING and self.player.charging:
                self.arrows.append(self.player.shoot())
                self.arrows_left -= 1
                self.sounds.play("shoot")

    # --- update ----------------------------------------------------------
    def update(self):
        if self.state != Game.PLAYING:
            return
        self.player.move(pygame.key.get_pressed())
        self.target.update()

        for arrow in self.arrows[:]:  # loop over a copy so removing is safe
            arrow.update()
            points = self.target.score_for(arrow.tip())
            if points:
                self.arrows.remove(arrow)
                self.level_score += points
                self.total_score += points
                color = YELLOW if points == 10 else WHITE
                label = "BULLSEYE! +10" if points == 10 else f"+{points}"
                self.texts.append(FloatingText(label, self.target.x, self.target.y - self.target.radius, color))
                self.sounds.play("bullseye" if points == 10 else "hit")
                self.target.place()
            elif arrow.off_screen():
                self.arrows.remove(arrow)
                self.texts.append(FloatingText("miss", max(30, min(WIDTH - 30, arrow.x)), HEIGHT // 2, GREY))
                self.sounds.play("miss")

        for text in self.texts[:]:
            text.update()
            if text.life <= 0:
                self.texts.remove(text)

        self.finish_level_if_done()

    # --- drawing ---------------------------------------------------------
    def draw_text(self, text, font, color, center):
        img = font.render(text, True, color)
        self.window.blit(img, img.get_rect(center=center))

    def draw_hud(self):
        self.window.blit(self.font.render(f"Level {self.level}", True, WHITE), (15, 10))
        self.window.blit(self.font.render(f"Score {self.total_score}", True, WHITE), (15, 40))
        goal = self.small_font.render(f"Level goal: {self.level_score} / {self.goal}", True, YELLOW)
        self.window.blit(goal, goal.get_rect(midtop=(WIDTH // 2, 12)))
        best = self.small_font.render(f"Best {self.highscore}", True, WHITE)
        self.window.blit(best, best.get_rect(topright=(WIDTH - 15, 12)))

        # arrows left, drawn as little arrows
        for i in range(self.arrows_left):
            x = WIDTH - 20 - i * 12
            pygame.draw.line(self.window, BROWN, (x, 45), (x, 70), 3)
            pygame.draw.polygon(self.window, GREY, [(x, 40), (x - 4, 48), (x + 4, 48)])

        # power bar
        bar = pygame.Rect(15, HEIGHT - 28, 150, 14)
        pygame.draw.rect(self.window, BLACK, bar)
        fill = (self.player.power - MIN_POWER) / (MAX_POWER - MIN_POWER)
        pygame.draw.rect(self.window, YELLOW, (bar.x, bar.y, int(bar.width * fill), bar.height))
        pygame.draw.rect(self.window, WHITE, bar, 1)
        self.window.blit(self.small_font.render("power", True, WHITE), (bar.right + 8, bar.y - 2))

    def draw_overlay(self, title, lines):
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 160))
        self.window.blit(shade, (0, 0))
        self.draw_text(title, self.big_font, YELLOW, (WIDTH // 2, HEIGHT // 2 - 80))
        for i, line in enumerate(lines):
            self.draw_text(line, self.font, WHITE, (WIDTH // 2, HEIGHT // 2 - 10 + i * 36))

    def draw(self):
        self.window.blit(self.background, (0, 0))
        self.target.draw(self.window)
        for arrow in self.arrows:
            arrow.draw(self.window)
        self.player.draw(self.window)
        for text in self.texts:
            text.draw(self.window, self.font)
        self.draw_hud()

        if self.state == Game.TITLE:
            self.draw_overlay("MrArrow", [
                "LEFT/RIGHT move   UP/DOWN aim",
                "Hold SPACE to draw the bow, release to shoot",
                "Hit the middle for more points!",
                "",
                "Press SPACE to start",
            ])
        elif self.state == Game.PAUSED:
            self.draw_overlay("Paused", ["Press P to continue"])
        elif self.state == Game.LEVEL_DONE:
            self.draw_overlay(f"Level {self.level} complete!", [
                f"Score: {self.total_score}",
                "Press SPACE for the next level",
            ])
        elif self.state == Game.GAME_OVER:
            self.draw_overlay("Game Over", [
                f"You reached level {self.level}",
                f"Final score: {self.total_score}   Best: {self.highscore}",
                "Press R to play again or ESC to quit",
            ])
        pygame.display.flip()

    # --- main loop -------------------------------------------------------
    def run(self, max_frames=None):
        frames = 0
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.update()
            self.draw()
            self.clock.tick(FPS)
            frames += 1
            if max_frames is not None and frames >= max_frames:
                break


def main():
    pygame.init()
    try:
        Game().run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
