# -*- coding: utf-8 -*-
import math
import random
from pygame import Rect  # allowed exception

TITLE = "Sweet Escape"
WIDTH = 800
HEIGHT = 450
RESIZABLE = False

STATE_MENU = "menu"
STATE_PLAY = "play"
STATE_WIN = "win"
STATE_LOSE = "lose"
MUSIC_MENU = "menu"
MUSIC_GAME = "bgm"
MUSIC_WIN = "win"
BG_MENU = (255, 205, 230)
BG_GAME = (255, 255, 255)

CANDY_TARGET = 20
PADDING = 24

BTN_W, BTN_H = 220, 55
btn_start = Rect((WIDTH // 2 - BTN_W // 2, 170), (BTN_W, BTN_H))
btn_sound = Rect((WIDTH // 2 - BTN_W // 2, 240), (BTN_W, BTN_H))
btn_exit = Rect((WIDTH // 2 - BTN_W // 2, 310), (BTN_W, BTN_H))


def clamp(value, low, high):
    return max(low, min(high, value))
def safe_play_music(track_name):
    """Play background music if sound is enabled and file exists."""
    if not game.sound_on:
        return

    if game.music_now == track_name:
        return

    try:
        music.stop()
        music.play(track_name)
        music.set_volume(0.6)
        game.music_now = track_name
    except Exception:
        # Missing music should not crash the game
        game.music_now = None

def safe_stop_music():
    try:
        music.stop()
    except Exception:
        pass

def safe_sfx(name):
    if not game.sound_on:
        return
    try:
        getattr(sounds, name).play()
    except Exception:
        pass

def draw_button(rect, text):
    screen.draw.filled_rect(rect, (255, 245, 250))
    screen.draw.rect(rect, (255, 120, 170))
    screen.draw.text(text, center=rect.center, fontsize=34, color=(140, 60, 100))

class SpriteAnimator:

    def __init__(self, actor, idle_frames, move_frames, idle_fps=5, move_fps=10):
        self.actor = actor
        self.idle_frames = idle_frames
        self.move_frames = move_frames

        self.frames = self.idle_frames
        self.frame_index = 0

        self.idle_step = 1.0 / max(1, idle_fps)
        self.move_step = 1.0 / max(1, move_fps)

        self.timer = 0.0
        self.moving = False
        self._set_image(self.frames[0])

    def set_moving(self, moving):
        if moving == self.moving:
            return

        self.moving = moving
        self.frames = self.move_frames if moving else self.idle_frames
        self.frame_index = 0
        self.timer = 0.0
        self._set_image(self.frames[0])

    def update(self, dt):
        if len(self.frames) < 2:
            return
        self.timer += dt
        step = self.move_step if self.moving else self.idle_step
        if self.timer >= step:
            self.timer = 0.0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self._set_image(self.frames[self.frame_index])

    def _set_image(self, image_name):
        try:
            self.actor.image = image_name
        except Exception:
            pass
class Hero:
    def __init__(self, pos):
        self.actor = Actor("sweet_idle_0", pos=pos)

        self.anim = SpriteAnimator(
            self.actor,
            idle_frames=["sweet_idle_0", "sweet_idle_1", "sweet_idle_2"],
            move_frames=["sweet_run_0", "sweet_run_1", "sweet_run_2"],
            idle_fps=5,
            move_fps=12,
        )

        self.speed = 220
        self.step_timer = 0.0
        self.step_interval = 0.22

    def update(self, dt):
        vx = 0
        vy = 0

        if keyboard.left:
            vx = -self.speed
        elif keyboard.right:
            vx = self.speed

        if keyboard.up:
            vy = -self.speed
        elif keyboard.down:
            vy = self.speed

        moving = (vx != 0 or vy != 0)
        self.anim.set_moving(moving)
        self.actor.x = clamp(self.actor.x + vx * dt, PADDING, WIDTH - PADDING)
        self.actor.y = clamp(self.actor.y + vy * dt, PADDING, HEIGHT - PADDING)
        self.anim.update(dt)
        self._update_steps(dt, moving)

    def _update_steps(self, dt, moving):
        if not moving:
            self.step_timer = 0.0
            return

        self.step_timer -= dt
        if self.step_timer <= 0.0:
            safe_sfx("step")
            self.step_timer = self.step_interval

    def draw(self):
        self.actor.draw()
class Enemy:
    def __init__(self, pos, left_limit, right_limit, prefix, speed=140):
        self.actor = Actor(f"{prefix}_idle_0", pos=pos)
   
        run_frames = [f"{prefix}_run_0", f"{prefix}_run_1", f"{prefix}_run_2"]
        if prefix == "cake2":
            run_frames = [f"{prefix}_run_0", f"{prefix}_run_1"]

        self.anim = SpriteAnimator(
            self.actor,
            idle_frames=[f"{prefix}_idle_0", f"{prefix}_idle_1"],
            move_frames=run_frames,
            idle_fps=4,
            move_fps=10,
        )
        self.left_limit = left_limit
        self.right_limit = right_limit
        self.speed = speed
        self.direction = 1

    def update(self, dt):
        # Enemies patrol all the time
        self.anim.set_moving(True)

        self.actor.x += self.direction * self.speed * dt

        if self.actor.x <= self.left_limit:
            self.actor.x = self.left_limit
            self.direction = 1
        elif self.actor.x >= self.right_limit:
            self.actor.x = self.right_limit
            self.direction = -1

        self.anim.update(dt)

    def draw(self):
        self.actor.draw()

class Game:
    def __init__(self):
        self.state = STATE_MENU
        self.sound_on = True
        self.music_now = None

        self.hero = None
        self.enemies = []
        self.candies = []
        self.collected = 0
        self.goal = None

    def start_new_run(self):
        self.collected = 0
        self.goal = None

        self.hero = Hero((120, HEIGHT // 2))
        self.enemies = [
            Enemy((520, HEIGHT // 2), left_limit=420, right_limit=740, prefix="cake1"),
            Enemy((520, 140), left_limit=260, right_limit=720, prefix="cake2"),
        ]
        self.candies = []
        for _ in range(CANDY_TARGET):
            x = random.randint(80, WIDTH - 80)
            y = random.randint(80, HEIGHT - 80)
            self.candies.append(Actor("candy", pos=(x, y)))

    def set_state(self, new_state):
        self.state = new_state

        if self.state == STATE_MENU:
            safe_play_music(MUSIC_MENU)
        elif self.state == STATE_PLAY:
            safe_play_music(MUSIC_GAME)
        elif self.state == STATE_WIN:
            safe_play_music(MUSIC_WIN)
        elif self.state == STATE_LOSE:
            pass

game = Game()
game.set_state(STATE_MENU)
def draw():
    if game.state == STATE_MENU:
        screen.fill(BG_MENU)
        screen.draw.text(
            "SWEET ESCAPE",
            center=(WIDTH // 2, 90),
            fontsize=64,
            color="white",
            owidth=2,
            ocolor=(255, 120, 170),
        )
        draw_button(btn_start, "START")
        draw_button(btn_sound, f"SOUND: {'ON' if game.sound_on else 'OFF'}")
        draw_button(btn_exit, "EXIT")
        screen.draw.text(
            "Click buttons with mouse",
            center=(WIDTH // 2, 410),
            fontsize=24,
            color=(120, 60, 90),
        )
        return

    screen.fill(BG_GAME)

    for candy in game.candies:
        candy.draw()

    if game.goal:
        game.goal.draw()

    for enemy in game.enemies:
        enemy.draw()

    if game.hero:
        game.hero.draw()
    screen.draw.text(
        f"CANDY: {game.collected}/{CANDY_TARGET}",
        topleft=(12, 10),
        fontsize=30,
        color=(50, 50, 50),
    )

    if game.state == STATE_LOSE:
        screen.draw.text("GAME OVER", center=(WIDTH // 2, HEIGHT // 2),
                         fontsize=70, color="red")
        screen.draw.text("Press R to restart", center=(WIDTH // 2, HEIGHT // 2 + 60),
                         fontsize=36, color="black")

    if game.state == STATE_WIN:
        screen.draw.text("YOU WIN!", center=(WIDTH // 2, HEIGHT // 2),
                         fontsize=70, color="green")
        screen.draw.text("Press R to play again", center=(WIDTH // 2, HEIGHT // 2 + 60),
                         fontsize=36, color="black")

def on_mouse_down(pos):
    if game.state != STATE_MENU:
        return
    if btn_start.collidepoint(pos):
        game.start_new_run()
        game.set_state(STATE_PLAY)
        return
    if btn_sound.collidepoint(pos):
        game.sound_on = not game.sound_on
        if not game.sound_on:
            safe_stop_music()
            game.music_now = None
        else:
            # Replay current state's music
            game.set_state(game.state)
        return

    if btn_exit.collidepoint(pos):
        raise SystemExit
def update(dt):
    if game.state == STATE_MENU:
        return

    if game.state in (STATE_WIN, STATE_LOSE):
        if keyboard.r:
            game.start_new_run()
            game.set_state(STATE_PLAY)
        return

    game.hero.update(dt)

    for enemy in game.enemies:
        enemy.update(dt)

    # Lose condition: hit any enemy
    if any(enemy.actor.colliderect(game.hero.actor) for enemy in game.enemies):
        safe_sfx("hit")
        game.set_state(STATE_LOSE)
        return
  
    remaining = []
    picked_any = False
    for candy in game.candies:
        if candy.colliderect(game.hero.actor):
            game.collected += 1
            picked_any = True
        else:
            remaining.append(candy)
    game.candies = remaining

    if picked_any:
        safe_sfx("pickup")

    if game.collected >= CANDY_TARGET and game.goal is None:
        game.goal = Actor("goal", pos=(WIDTH - 70, 60))

    if game.goal and game.goal.colliderect(game.hero.actor):
        safe_sfx("win")
        game.set_state(STATE_WIN)
