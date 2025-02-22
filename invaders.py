import pygame
import random
import os
import math

# Initialize Pygame and the mixer for sound
try:
    pygame.init()
    pygame.mixer.init()
except Exception as e:
    print(f"Error initializing Pygame or mixer: {e}")
    exit()

# Set up the game window (resolution updated)
WIDTH, HEIGHT = 1147, 745
try:
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Space Monsters")
except Exception as e:
    print(f"Error setting up display: {e}")
    exit()

# Set up fonts for the scoreboard and messages
try:
    scoreboard_font = pygame.font.Font(None, 36)  # For score, level, and high score display
    message_font = pygame.font.Font(None, 48)       # For main messages
except Exception as e:
    print(f"Error loading font: {e}")
    exit()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)

# Player properties
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 40
player_start_x = WIDTH // 2 - PLAYER_WIDTH // 2
player_start_y = HEIGHT - 60
player_speed = 5
PLAYER_UP_SPEED = player_speed * 2  # Upward movement is faster

# Bullet properties
BULLET_WIDTH = 5
BULLET_HEIGHT = 15
bullet_speed = 7
bullets = []

# Enemy properties
ENEMY_WIDTH = 40
ENEMY_HEIGHT = 40
base_enemy_speed = 2       # Base enemy speed
enemy_speed = base_enemy_speed  # Will increase with each level
enemy_direction = 1        # 1 for right, -1 for left
enemies = []

# Boss movement area (restrict boss to an 800x600 rectangle)
BOSS_AREA_WIDTH = 800
BOSS_AREA_HEIGHT = 600

# Game state variables: "playing", "level_complete", "game_over"
game_state = "playing"
score = 0
level = 1
high_score = 0  # Retained across games

# --- Background Generation ---
NUM_STARS = 100
stars = []
planets = []

# Lists of possible colors
star_colors = [(255, 255, 255), (255, 255, 150), (200, 200, 255), (255, 200, 200)]
planet_colors = [(100, 100, 255), (255, 100, 100), (100, 255, 100), (200, 100, 255), (255, 150, 50)]

def generate_background():
    global stars, planets
    stars = []
    for i in range(NUM_STARS):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        color = random.choice(star_colors)
        stars.append((x, y, color))
    planets = []
    num_planets = random.randint(1, 3)
    for i in range(num_planets):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT // 2)
        radius = random.randint(20, 60)
        color = random.choice(planet_colors)
        planets.append({'x': x, 'y': y, 'radius': radius, 'color': color})

# Generate initial background
generate_background()

def draw_background(surface):
    surface.fill(BLACK)
    for star in stars:
        surface.set_at((star[0], star[1]), star[2])
    for planet in planets:
        pygame.draw.circle(surface, planet['color'], (planet['x'], planet['y']), planet['radius'])

# --- Helper Functions for Sprites & Sound ---
def load_sprite(filename, width, height):
    if os.path.exists(filename):
        try:
            sprite = pygame.image.load(filename)
            return pygame.transform.scale(sprite, (width, height))
        except Exception as e:
            print(f"Error loading sprite {filename}: {e}")
    return None

# Load sprites
player_sprite = load_sprite("assets/images/player.png", PLAYER_WIDTH, PLAYER_HEIGHT)
enemy_sprite  = load_sprite("assets/images/enemy.png", ENEMY_WIDTH, ENEMY_HEIGHT)
king_sprite   = load_sprite("assets/images/king.png", ENEMY_WIDTH, ENEMY_HEIGHT)
queen_sprite  = load_sprite("assets/images/queen.png", ENEMY_WIDTH, ENEMY_HEIGHT)
boss_sprite   = load_sprite("assets/images/boss.png", ENEMY_WIDTH * 3, ENEMY_HEIGHT * 3)

def load_sound(filename):
    if os.path.exists(filename):
        try:
            return pygame.mixer.Sound(filename)
        except Exception as e:
            print(f"Error loading sound {filename}: {e}")
    return None

# Load sounds from assets/sounds
shoot_sound          = load_sound("assets/sounds/laser.wav")
explosion_sound      = load_sound("assets/sounds/explosion.flac")
level_complete_sound = load_sound("assets/sounds/level_complete.wav")
game_over_sound      = load_sound("assets/sounds/game_over.wav")

# --- Background Music Update Function ---
def update_background_music():
    pygame.mixer.music.stop()  # Ensure any currently playing music is stopped
    print(f"update_background_music: level = {level}")
    if level % 3 == 0:
        print("Loading pixel_boss.wav")
        pygame.mixer.music.load("assets/sounds/pixel_boss.wav")
    else:
        print("Loading game_music.wav")
        pygame.mixer.music.load("assets/sounds/game_music.wav")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)

# Call update_background_music() at initialization
update_background_music()

# --- Enemy Creation ---
def create_enemies():
    global enemies
    enemies.clear()
    # Boss level: create pixel bosses.
    if level % 3 == 0:
        num_bosses = level // 3  # Level 3: 1 boss; level 6: 2 bosses; etc.
        scale = 1 + 0.5 * (level // 3)  # Moderate scaling: level 3 -> 1.5x, level 6 -> 2.0x, etc.
        boss_width = int(ENEMY_WIDTH * 3 * scale)
        boss_height = int(ENEMY_HEIGHT * 3 * scale)
        spacing = 20  # Horizontal spacing between bosses
        total_width = num_bosses * boss_width + (num_bosses - 1) * spacing
        start_x = (BOSS_AREA_WIDTH - total_width) // 2
        for i in range(num_bosses):
            boss_x = start_x + i * (boss_width + spacing)
            boss_y = 50  # Fixed vertical offset within boss area
            enemy_rect = pygame.Rect(boss_x, boss_y, boss_width, boss_height)
            boss_hits = random.randint(11, 33)
            boss = {
                'x': float(boss_x),
                'y': float(boss_y),
                'rect': enemy_rect,
                'type': 'boss',
                'score_value': 1000000,  # 1,000,000 points per boss
                'health': int(boss_hits * scale),
                'max_health': int(boss_hits * scale),
                'state': 'moving',     # "moving" or "paused"
                'state_timer': 0.0,
                'velocity': (0.0, 0.0),  # To be set below
                'regen_timer': 0.0     # For health regeneration
            }
            speed = random.uniform(50, 150)
            angle = random.uniform(0, 2 * math.pi)
            boss['velocity'] = (speed * math.cos(angle), speed * math.sin(angle))
            enemies.append(boss)
    else:
        rows = 3 + level // 2
        cols = 8 + level // 2
        for row in range(rows):
            for col in range(cols):
                enemy_x = 50 + col * (ENEMY_WIDTH + 20) + random.randint(-5, 5)
                enemy_y = 50 + row * (ENEMY_HEIGHT + 20) + random.randint(-5, 5)
                enemy_rect = pygame.Rect(enemy_x, enemy_y, ENEMY_WIDTH, ENEMY_HEIGHT)
                enemy = {
                    'x': enemy_x,
                    'y': enemy_y,
                    'rect': enemy_rect,
                    'type': 'normal',
                    'score_value': level * 10 + 10000
                }
                enemies.append(enemy)
        if len(enemies) >= 2:
            special_indices = random.sample(range(len(enemies)), 2)
            enemies[special_indices[0]]['type'] = 'king'
            enemies[special_indices[0]]['score_value'] = 555 + 10000
            enemies[special_indices[1]]['type'] = 'queen'
            enemies[special_indices[1]]['score_value'] = 888 + 10000

create_enemies()

# --- Level and Game Reset Functions ---
def next_level():
    global player_x, player_y, bullets, enemy_speed, enemy_direction, game_state, level
    player_x = player_start_x
    player_y = player_start_y
    bullets.clear()
    create_enemies()
    level += 1
    enemy_speed += 0.5  # Increase enemy speed for added difficulty (for normal enemies)
    enemy_direction = 1
    game_state = "playing"
    generate_background()
    update_background_music()
    if level_complete_sound:
        level_complete_sound.play()

def reset_game():
    global player_x, player_y, bullets, enemies, enemy_speed, enemy_direction, game_state, level, score, high_score
    high_score = max(high_score, score)
    player_x = player_start_x
    player_y = player_start_y
    bullets.clear()
    enemies.clear()
    level = 1
    score = 0
    enemy_speed = base_enemy_speed
    enemy_direction = 1
    create_enemies()
    game_state = "playing"
    generate_background()
    update_background_music()

player_x = player_start_x
player_y = player_start_y

# --- Main Game Loop ---
clock = pygame.time.Clock()
running = True

while running:
    try:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if game_state == "playing":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and len(bullets) < 11:
                        bullet_rect = pygame.Rect(
                            player_x + PLAYER_WIDTH // 2 - BULLET_WIDTH // 2,
                            player_y - BULLET_HEIGHT,
                            BULLET_WIDTH,
                            BULLET_HEIGHT
                        )
                        bullets.append(bullet_rect)
                        if shoot_sound:
                            shoot_sound.play()
            elif game_state in ["level_complete", "game_over"]:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        if game_state == "level_complete":
                            next_level()
                        elif game_state == "game_over":
                            reset_game()
                    elif event.key == pygame.K_n:
                        running = False

        if game_state == "playing":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and player_x > 0:
                player_x -= player_speed
            if keys[pygame.K_RIGHT] and player_x < WIDTH - PLAYER_WIDTH:
                player_x += player_speed
            if keys[pygame.K_UP] and player_y > 0:
                player_y -= PLAYER_UP_SPEED
            if keys[pygame.K_DOWN] and player_y < HEIGHT - PLAYER_HEIGHT:
                player_y += player_speed

            for bullet in bullets[:]:
                bullet.y -= bullet_speed
                if bullet.y < 0:
                    bullets.remove(bullet)

            move_down = False
            for enemy in enemies[:]:
                if enemy['type'] == 'boss':
                    enemy['state_timer'] += dt
                    enemy['regen_timer'] += dt
                    if enemy['regen_timer'] >= 4.0:
                        enemy['health'] = min(enemy['health'] + int(0.05 * enemy['max_health']), enemy['max_health'])
                        enemy['regen_timer'] = 0.0
                    if enemy['state'] == 'moving':
                        vx, vy = enemy['velocity']
                        enemy['x'] += vx * dt
                        enemy['y'] += vy * dt
                        boss_width = enemy['rect'].width
                        boss_height = enemy['rect'].height
                        enemy['x'] = max(0, min(enemy['x'], BOSS_AREA_WIDTH - boss_width))
                        enemy['y'] = max(0, min(enemy['y'], BOSS_AREA_HEIGHT - boss_height))
                        enemy['rect'].x = int(enemy['x'])
                        enemy['rect'].y = int(enemy['y'])
                        if enemy['state_timer'] >= 3.89:
                            enemy['state'] = 'paused'
                            enemy['state_timer'] = 0.0
                    elif enemy['state'] == 'paused':
                        if enemy['state_timer'] >= 2.23:
                            speed = random.uniform(50, 150)
                            angle = random.uniform(0, 2 * math.pi)
                            enemy['velocity'] = (speed * math.cos(angle), speed * math.sin(angle))
                            enemy['state'] = 'moving'
                            enemy['state_timer'] = 0.0

                    for bullet in bullets[:]:
                        if enemy['rect'].colliderect(bullet):
                            enemy['health'] -= 1
                            if explosion_sound:
                                explosion_sound.play()
                            if bullet in bullets:
                                bullets.remove(bullet)
                            if enemy['health'] <= 0:
                                score += enemy['score_value']
                                enemies.remove(enemy)
                            break
                else:
                    enemy['x'] += enemy_speed * enemy_direction
                    enemy['rect'].x = enemy['x']
                    if enemy['x'] <= 0 or enemy['x'] >= WIDTH - ENEMY_WIDTH:
                        move_down = True
                    for bullet in bullets[:]:
                        if enemy['rect'].colliderect(bullet):
                            if enemy in enemies:
                                enemies.remove(enemy)
                            if bullet in bullets:
                                bullets.remove(bullet)
                            score += enemy['score_value']
                            if explosion_sound:
                                explosion_sound.play()
                            break

                player_rect = pygame.Rect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
                if enemy['rect'].colliderect(player_rect):
                    game_state = "game_over"
                    if game_over_sound:
                        game_over_sound.play()
                if enemy['type'] != 'boss' and enemy['y'] > HEIGHT - ENEMY_HEIGHT:
                    game_state = "game_over"
                    if game_over_sound:
                        game_over_sound.play()

            if move_down:
                enemy_direction *= -1
                for enemy in enemies:
                    if enemy['type'] != 'boss':
                        enemy['y'] += 40
                        enemy['rect'].y = enemy['y']

            if not enemies:
                game_state = "level_complete"

        draw_background(window)
        if game_state == "playing":
            if player_sprite:
                window.blit(player_sprite, (player_x, player_y))
            else:
                pygame.draw.rect(window, WHITE, (player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT))
            for bullet in bullets:
                pygame.draw.rect(window, WHITE, bullet)
            for enemy in enemies:
                if enemy['type'] == 'boss':
                    if boss_sprite:
                        window.blit(boss_sprite, enemy['rect'])
                    else:
                        pygame.draw.rect(window, RED, enemy['rect'])
                    # Draw a vertical health bar fixed to 90% of boss height
                    bar_width = 10
                    health_bar_height = int(0.9 * enemy['rect'].height)
                    health_bar_y = enemy['rect'].y + (enemy['rect'].height - health_bar_height) // 2
                    filled_height = int(health_bar_height * (enemy['health'] / enemy['max_health']))
                    bar_x = enemy['rect'].right + 5
                    bar_y = health_bar_y + (health_bar_height - filled_height)
                    pygame.draw.rect(window, RED, (bar_x, health_bar_y, bar_width, health_bar_height))
                    pygame.draw.rect(window, (0, 255, 0), (bar_x, bar_y, bar_width, filled_height))
                elif enemy['type'] == 'king' and king_sprite:
                    window.blit(king_sprite, enemy['rect'])
                elif enemy['type'] == 'queen' and queen_sprite:
                    window.blit(queen_sprite, enemy['rect'])
                elif enemy_sprite:
                    window.blit(enemy_sprite, enemy['rect'])
                else:
                    pygame.draw.rect(window, RED, enemy['rect'])
            score_text = scoreboard_font.render("Score: " + f"{score:,}", True, WHITE)
            window.blit(score_text, (10, 10))
            high_score_text = scoreboard_font.render("High Score: " + f"{high_score:,}", True, WHITE)
            window.blit(high_score_text, (10, 50))
            level_text = scoreboard_font.render("Level: " + str(level), True, WHITE)
            level_rect = level_text.get_rect(topright=(WIDTH - 10, 10))
            window.blit(level_text, level_rect)
        elif game_state == "level_complete":
            complete_text = message_font.render("Level Complete, Well Done!", True, WHITE)
            prompt_text = scoreboard_font.render("Advance to next level?  y/n", True, WHITE)
            complete_rect = complete_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
            prompt_rect = prompt_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            window.blit(complete_text, complete_rect)
            window.blit(prompt_text, prompt_rect)
        elif game_state == "game_over":
            high_score = max(high_score, score)
            over_text = message_font.render("Game Over! Final Score: " + f"{score:,}", True, WHITE)
            prompt_text = scoreboard_font.render("Play again?  y/n", True, WHITE)
            over_rect = over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
            prompt_rect = prompt_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            window.blit(over_text, over_rect)
            window.blit(prompt_text, prompt_rect)
            high_score_text = scoreboard_font.render("High Score: " + f"{high_score:,}", True, WHITE)
            high_score_rect = high_score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70))
            window.blit(high_score_text, high_score_rect)

        pygame.display.update()
    except Exception as e:
        print(f"Error in game loop: {e}")
        running = False

pygame.quit()