"""
Flappy Bird — Python / Pygame
================================
Run:
    pip install pygame
    python flappy_bird.py

Controls:
    SPACE / UP ARROW / LEFT CLICK — flap
    ESC                           — quit
"""

import pygame
import sys
import random

# ── Pygame setup ──────────────────────────────────────────────
pygame.init()

# ── Window / display ──────────────────────────────────────────
WINDOW_WIDTH  = 400
WINDOW_HEIGHT = 500
FPS           = 60

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Flappy Bird")
clock = pygame.time.Clock()

# ── Colors (R, G, B) ──────────────────────────────────────────
SKY_TOP      = (180, 220, 255)
SKY_BOTTOM   = (220, 240, 255)
GRASS_GREEN  = (100, 190, 90)
GROUND_TAN   = (195, 165, 105)
PIPE_MAIN    = (70, 185, 90)
PIPE_DARK    = (45, 158, 70)
PIPE_CAP     = (60, 175, 80)
BIRD_BODY    = (245, 200, 65)
BIRD_WING    = (230, 165, 0)
BIRD_EYE     = (255, 255, 255)
BIRD_PUPIL   = (30, 30, 30)
BIRD_BEAK    = (240, 125, 45)
WHITE        = (255, 255, 255)
BLACK        = (0,   0,   0)
OVERLAY      = (0,   0,   0,  100)   # semi-transparent (used with Surface)

# ── Physics & gameplay constants ──────────────────────────────
GRAVITY        = 0.45   # downward acceleration per frame (pixels/frame²)
JUMP_FORCE     = -9.0   # vertical velocity applied on flap (negative = up)
PIPE_WIDTH     = 55     # width of each pipe in pixels
PIPE_GAP       = 148    # vertical gap between top and bottom pipe
PIPE_SPEED     = 2.5    # horizontal pixels pipes move per frame
PIPE_INTERVAL  = 90     # frames between spawning a new pipe pair
GROUND_HEIGHT  = 50     # height of the ground strip at the bottom

# ── Fonts ─────────────────────────────────────────────────────
font_large  = pygame.font.SysFont("segoeui", 36, bold=False)
font_medium = pygame.font.SysFont("segoeui", 22, bold=False)
font_small  = pygame.font.SysFont("segoeui", 14, bold=False)


# ══════════════════════════════════════════════════════════════
#  Bird class
# ══════════════════════════════════════════════════════════════
class Bird:
    """Represents the player-controlled bird."""

    RADIUS = 14   # collision circle radius

    def __init__(self):
        self.x  = 90                          # fixed horizontal position
        self.y  = float(WINDOW_HEIGHT // 2)   # vertical position (float for smooth movement)
        self.vy = 0.0                         # vertical velocity

    # ── Physics update ────────────────────────────────────────
    def update(self):
        """Apply gravity and move the bird each frame."""
        self.vy += GRAVITY
        self.y  += self.vy

    # ── Jump ──────────────────────────────────────────────────
    def flap(self):
        """Give the bird an upward impulse."""
        self.vy = JUMP_FORCE

    # ── Collision helpers ─────────────────────────────────────
    @property
    def hit_radius(self):
        """Slightly smaller radius for a forgiving hitbox."""
        return self.RADIUS - 3

    def is_out_of_bounds(self):
        """Returns True if the bird hits the ground or flies above the screen."""
        top_bound    = self.hit_radius
        bottom_bound = WINDOW_HEIGHT - GROUND_HEIGHT - self.hit_radius
        return self.y - self.hit_radius < 0 or self.y + self.hit_radius > bottom_bound + GROUND_HEIGHT - 8

    # ── Drawing ───────────────────────────────────────────────
    def draw(self, surface):
        """Draw the bird: wing, body, eye, pupil, beak."""
        cx, cy = int(self.x), int(self.y)
        r = self.RADIUS

        # Clamp rotation angle based on vertical velocity
        angle_deg = max(-25, min(self.vy * 4, 60))

        # Build a small surface to rotate the bird sprite
        sprite_size = (r * 4, r * 4)
        sprite = pygame.Surface(sprite_size, pygame.SRCALPHA)
        origin = (r * 2, r * 2)   # center of the sprite surface

        # Wing (ellipse behind body)
        wing_rect = pygame.Rect(origin[0] - r, origin[1], r * 1.2, r * 0.7)
        pygame.draw.ellipse(sprite, BIRD_WING, wing_rect)

        # Body (circle)
        pygame.draw.circle(sprite, BIRD_BODY, origin, r)

        # White of eye
        eye_pos = (origin[0] + 6, origin[1] - 4)
        pygame.draw.circle(sprite, BIRD_EYE, eye_pos, 5)

        # Pupil
        pupil_pos = (origin[0] + 7, origin[1] - 4)
        pygame.draw.circle(sprite, BIRD_PUPIL, pupil_pos, 2)

        # Beak (triangle)
        beak = [
            (origin[0] + 10, origin[1] - 1),
            (origin[0] + 18, origin[1] + 1),
            (origin[0] + 10, origin[1] + 4),
        ]
        pygame.draw.polygon(sprite, BIRD_BEAK, beak)

        # Rotate the sprite and blit it centered on the bird position
        rotated = pygame.transform.rotate(sprite, -angle_deg)
        rect    = rotated.get_rect(center=(cx, cy))
        surface.blit(rotated, rect)


# ══════════════════════════════════════════════════════════════
#  Pipe class
# ══════════════════════════════════════════════════════════════
class Pipe:
    """A single pipe pair (top + bottom) that scrolls left."""

    CAP_HEIGHT = 20    # extra cap height at the mouth of the pipe
    CAP_EXTRA  = 10    # how much wider the cap is compared to the pipe body

    def __init__(self):
        # Random opening position: gap center kept away from edges
        min_top = 60
        max_top = WINDOW_HEIGHT - GROUND_HEIGHT - PIPE_GAP - 60
        self.top_height = random.randint(min_top, max_top)  # height of the top pipe
        self.x          = float(WINDOW_WIDTH)               # starts off-screen right
        self.scored     = False                             # True once the bird passes it

    @property
    def gap_top(self):
        """Y coordinate where the gap starts (bottom of top pipe)."""
        return self.top_height

    @property
    def gap_bottom(self):
        """Y coordinate where the gap ends (top of bottom pipe)."""
        return self.top_height + PIPE_GAP

    # ── Movement ──────────────────────────────────────────────
    def update(self):
        """Move the pipe left by PIPE_SPEED each frame."""
        self.x -= PIPE_SPEED

    def is_off_screen(self):
        """True once the pipe has scrolled completely past the left edge."""
        return self.x + PIPE_WIDTH < 0

    # ── Collision ─────────────────────────────────────────────
    def collides_with(self, bird: Bird):
        """
        Check if the bird's hit circle overlaps with either pipe rectangle.
        Uses a simple circle-vs-rectangle test.
        """
        bx, by = bird.x, bird.y
        hr = bird.hit_radius
        px = self.x

        # Horizontal overlap?
        if bx + hr <= px + 4 or bx - hr >= px + PIPE_WIDTH - 4:
            return False   # bird is clearly to the left or right

        # Vertical overlap with top or bottom pipe?
        hits_top    = by - hr < self.gap_top
        hits_bottom = by + hr > self.gap_bottom
        return hits_top or hits_bottom

    # ── Drawing ───────────────────────────────────────────────
    def draw(self, surface):
        """Draw top pipe + bottom pipe, each with a cap."""
        px   = int(self.x)
        ch   = self.CAP_HEIGHT
        cw   = PIPE_WIDTH + self.CAP_EXTRA
        cx   = px - self.CAP_EXTRA // 2   # cap starts a few px to the left

        # ─ Top pipe body ─
        body_rect = pygame.Rect(px, 0, PIPE_WIDTH, self.gap_top - ch)
        pygame.draw.rect(surface, PIPE_MAIN, body_rect)
        # Right shadow strip
        shadow = pygame.Rect(px + PIPE_WIDTH - 6, 0, 6, self.gap_top - ch)
        pygame.draw.rect(surface, PIPE_DARK, shadow)
        # Top pipe cap
        cap_rect = pygame.Rect(cx, self.gap_top - ch, cw, ch)
        pygame.draw.rect(surface, PIPE_CAP, cap_rect, border_radius=4)

        # ─ Bottom pipe body ─
        bot_start = self.gap_bottom + ch
        bot_height = WINDOW_HEIGHT - GROUND_HEIGHT - bot_start
        body_bot = pygame.Rect(px, bot_start, PIPE_WIDTH, bot_height)
        pygame.draw.rect(surface, PIPE_MAIN, body_bot)
        shadow_bot = pygame.Rect(px + PIPE_WIDTH - 6, bot_start, 6, bot_height)
        pygame.draw.rect(surface, PIPE_DARK, shadow_bot)
        # Bottom pipe cap
        cap_bot = pygame.Rect(cx, self.gap_bottom, cw, ch)
        pygame.draw.rect(surface, PIPE_CAP, cap_bot, border_radius=4)


# ══════════════════════════════════════════════════════════════
#  Drawing helpers
# ══════════════════════════════════════════════════════════════

def draw_background(surface):
    """Draw a vertical gradient sky and the ground."""
    # Gradient sky: draw horizontal strips transitioning from top to bottom color
    for y in range(WINDOW_HEIGHT - GROUND_HEIGHT):
        ratio  = y / (WINDOW_HEIGHT - GROUND_HEIGHT)
        r = int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * ratio)
        g = int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * ratio)
        b = int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (WINDOW_WIDTH, y))

    # Grass strip
    pygame.draw.rect(surface, GRASS_GREEN,
                     (0, WINDOW_HEIGHT - GROUND_HEIGHT, WINDOW_WIDTH, 8))
    # Dirt / ground
    pygame.draw.rect(surface, GROUND_TAN,
                     (0, WINDOW_HEIGHT - GROUND_HEIGHT + 8,
                      WINDOW_WIDTH, GROUND_HEIGHT - 8))


def draw_overlay(surface, text_lines):
    """
    Draw a semi-transparent dark overlay with centered text lines.
    text_lines: list of (text, font, color) tuples.
    """
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 100))
    surface.blit(overlay, (0, 0))

    total_height = sum(font.size(text)[1] + 10 for text, font, _ in text_lines)
    y = WINDOW_HEIGHT // 2 - total_height // 2

    for text, font, color in text_lines:
        rendered = font.render(text, True, color)
        rect     = rendered.get_rect(centerx=WINDOW_WIDTH // 2, top=y)
        surface.blit(rendered, rect)
        y += rendered.get_height() + 10


def draw_hud(surface, score):
    """Draw the current score at the top center of the screen."""
    text = font_large.render(str(score), True, WHITE)
    rect = text.get_rect(centerx=WINDOW_WIDTH // 2, top=14)
    surface.blit(text, rect)


# ══════════════════════════════════════════════════════════════
#  Game states
# ══════════════════════════════════════════════════════════════
STATE_IDLE    = "idle"      # waiting for the player to start
STATE_PLAYING = "playing"   # game in progress
STATE_DEAD    = "dead"      # collision happened, showing game-over screen


# ══════════════════════════════════════════════════════════════
#  Main game loop
# ══════════════════════════════════════════════════════════════
def main():
    bird        = Bird()
    pipes       = []
    score       = 0
    best        = 0
    state       = STATE_IDLE
    frame_count = 0   # counts frames to time pipe spawning

    while True:

        # ── Event handling ────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    if state == STATE_DEAD:
                        # Reset everything for a new game
                        bird        = Bird()
                        pipes       = []
                        score       = 0
                        frame_count = 0
                        state       = STATE_IDLE
                    elif state == STATE_IDLE:
                        state = STATE_PLAYING
                        bird.flap()
                    else:
                        bird.flap()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == STATE_DEAD:
                    bird        = Bird()
                    pipes       = []
                    score       = 0
                    frame_count = 0
                    state       = STATE_IDLE
                elif state == STATE_IDLE:
                    state = STATE_PLAYING
                    bird.flap()
                else:
                    bird.flap()

        # ── Game logic (only when playing) ───────────────────
        if state == STATE_PLAYING:

            # Update bird physics
            bird.update()
            frame_count += 1

            # Spawn a new pipe pair every PIPE_INTERVAL frames
            if frame_count % PIPE_INTERVAL == 0:
                pipes.append(Pipe())

            # Update pipes, check scoring, remove off-screen pipes
            for pipe in pipes:
                pipe.update()
                # Award a point when the bird clears the pipe
                if not pipe.scored and pipe.x + PIPE_WIDTH < bird.x:
                    pipe.scored = True
                    score += 1
                    if score > best:
                        best = score

            pipes = [p for p in pipes if not p.is_off_screen()]

            # Check collision with bounds or any pipe
            if bird.is_out_of_bounds() or any(p.collides_with(bird) for p in pipes):
                state = STATE_DEAD

        # ── Rendering ─────────────────────────────────────────
        draw_background(screen)

        for pipe in pipes:
            pipe.draw(screen)

        bird.draw(screen)

        if state == STATE_PLAYING:
            draw_hud(screen, score)

        if state == STATE_IDLE:
            draw_overlay(screen, [
                ("Flappy Bird",            font_large,  WHITE),
                ("Space / Click to start", font_medium, (210, 210, 210)),
            ])

        if state == STATE_DEAD:
            draw_overlay(screen, [
                ("Game Over",              font_large,  WHITE),
                (f"Score: {score}",        font_medium, (210, 210, 210)),
                (f"Best:  {best}",         font_medium, (210, 210, 210)),
                ("Click to retry",         font_small,  (170, 170, 170)),
            ])

        pygame.display.flip()
        clock.tick(FPS)   # cap at 60 frames per second


# ── Entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    main()
