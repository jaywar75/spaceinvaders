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
    # Generate 1 to 3 planets that appear in the upper half of the screen
    planets = []
    num_planets = random.randint(1, 3)
    for i in range(num_planets):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT // 2)
        radius = random.randint(20, 60)
        color = random.choice(planet_colors)
        planets.append({'x': x, 'y': y, 'radius': radius, 'color': color})

# Call once to generate the initial background
generate_background()

def draw_background(surface):
    surface.fill(BLACK)
    # Draw stars
    for star in stars:
        # star is (x, y, color)
        surface.set_at((star[0], star[1]), star[2])
    # Draw planets (a simple dot-matrix style could be emulated by drawing a circle)
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

# Load sprites for the player, normal enemy, king, and queen
player_sprite = load_sprite("assets/images/player.png", PLAYER_WIDTH, PLAYER_HEIGHT)
enemy_sprite  = load_sprite("assets/images/enemy.png", ENEMY_WIDTH, ENEMY_HEIGHT)
king_sprite   = load_sprite("assets/images/king.png", ENEMY_WIDTH, ENEMY_HEIGHT)
queen_sprite  = load_sprite("assets/images/queen.png", ENEMY_WIDTH, ENEMY_HEIGHT)

def load_sound(filename):
    if os.path.exists(filename):
        try:
            return pygame.mixer.Sound(filename)
        except Exception as e:
            print(f"Error loading sound {filename}: {e}")
    return None

shoot_sound         = load_sound("shoot.wav")
explosion_sound     = load_sound("explosion.wav")
level_complete_sound = load_sound("level_complete.wav")
game_over_sound     = load_sound("game_over.wav")

# --- Enemy Creation ---
def create_enemies():
    global enemies
    enemies.clear()
    # Increase rows and columns slightly with level
    rows = 3 + level // 2
    cols = 8 + level // 2
    for row in range(rows):
        for col in range(cols):
            # Base positions with a slight random offset for variety
            enemy_x = 50 + col * (ENEMY_WIDTH + 20) + random.randint(-5, 5)
            enemy_y = 50 + row * (ENEMY_HEIGHT + 20) + random.randint(-5, 5)
            enemy_rect = pygame.Rect(enemy_x, enemy_y, ENEMY_WIDTH, ENEMY_HEIGHT)
            enemy = {
                'x': enemy_x,
                'y': enemy_y,
                'rect': enemy_rect,
                'type': 'normal',            # Default enemy type
                'score_value': level * 10     # Normal enemy score value
            }
            enemies.append(enemy)
    # If there are at least two enemies, assign one as 'king' and one as 'queen'
    if len(enemies) >= 2:
        special_indices = random.sample(range(len(enemies)), 2)
        # King enemy (custom score value)
        enemies[special_indices[0]]['type'] = 'king'
        enemies[special_indices[0]]['score_value'] = 555
        # Queen enemy (custom score value)
        enemies[special_indices[1]]['type'] = 'queen'
        enemies[special_indices[1]]['score_value'] = 888

create_enemies()

# --- Level and Game Reset Functions ---
def next_level():
    global player_x, player_y, bullets, enemy_speed, enemy_direction, game_state, level
    player_x = player_start_x
    player_y = player_start_y
    bullets.clear()
    create_enemies()
    level += 1
    enemy_speed += 0.5  # Increase enemy speed for added difficulty
    enemy_direction = 1
    game_state = "playing"
    generate_background()  # Generate a new background for the level
    if level_complete_sound:
        level_complete_sound.play()

def reset_game():
    global player_x, player_y, bullets, enemies, enemy_speed, enemy_direction, game_state, level, score, high_score
    # Update high score if current score is greater
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
    generate_background()  # Regenerate background on reset

# Set initial player position
player_x = player_start_x
player_y = player_start_y

clock = pygame.time.Clock()
running = True

while running:
    try:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if game_state == "playing":
                if event.type == pygame.KEYDOWN:
                    # Fire a bullet (limit to 3 on screen)
                    if event.key == pygame.K_SPACE and len(bullets) < 3:
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

        # --- Game State: Playing ---
        if game_state == "playing":
            keys = pygame.key.get_pressed()
            # Lateral movement
            if keys[pygame.K_LEFT] and player_x > 0:
                player_x -= player_speed
            if keys[pygame.K_RIGHT] and player_x < WIDTH - PLAYER_WIDTH:
                player_x += player_speed
            # Vertical movement: Up (faster) and Down (normal)
            if keys[pygame.K_UP] and player_y > 0:
                player_y -= PLAYER_UP_SPEED
            if keys[pygame.K_DOWN] and player_y < HEIGHT - PLAYER_HEIGHT:
                player_y += player_speed

            # Update bullets
            for bullet in bullets[:]:
                bullet.y -= bullet_speed
                if bullet.y < 0:
                    bullets.remove(bullet)

            # Update enemies
            move_down = False
            for enemy in enemies[:]:
                enemy['x'] += enemy_speed * enemy_direction
                enemy['rect'].x = enemy['x']
                # Reverse direction if any enemy hits a boundary
                if enemy['x'] <= 0 or enemy['x'] >= WIDTH - ENEMY_WIDTH:
                    move_down = True

                # Check collision with bullets
                for bullet in bullets[:]:
                    if enemy['rect'].colliderect(bullet):
                        if enemy in enemies:
                            enemies.remove(enemy)
                        if bullet in bullets:
                            bullets.remove(bullet)
                        score += enemy['score_value']  # Award points based on enemy type
                        if explosion_sound:
                            explosion_sound.play()
                        break

                # Check collision with player
                player_rect = pygame.Rect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
                if enemy['rect'].colliderect(player_rect):
                    game_state = "game_over"
                    if game_over_sound:
                        game_over_sound.play()

                # End game if an enemy reaches the bottom
                if enemy['y'] > HEIGHT - ENEMY_HEIGHT:
                    game_state = "game_over"
                    if game_over_sound:
                        game_over_sound.play()

            # Reverse enemy direction and move them down if needed
            if move_down:
                enemy_direction *= -1
                for enemy in enemies:
                    enemy['y'] += 40
                    enemy['rect'].y = enemy['y']

            # Level complete if all enemies are eliminated
            if not enemies:
                game_state = "level_complete"

        # --- Drawing ---
        draw_background(window)
        if game_state == "playing":
            # Draw the player (sprite if available)
            if player_sprite:
                window.blit(player_sprite, (player_x, player_y))
            else:
                pygame.draw.rect(window, WHITE, (player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT))
            # Draw bullets
            for bullet in bullets:
                pygame.draw.rect(window, WHITE, bullet)
            # Draw enemies with their specific sprites based on type
            for enemy in enemies:
                if enemy['type'] == 'king' and king_sprite:
                    window.blit(king_sprite, enemy['rect'])
                elif enemy['type'] == 'queen' and queen_sprite:
                    window.blit(queen_sprite, enemy['rect'])
                elif enemy_sprite:
                    window.blit(enemy_sprite, enemy['rect'])
                else:
                    pygame.draw.rect(window, RED, enemy['rect'])
            # Draw scoreboard (Score and High Score)
            score_text = scoreboard_font.render("Score: " + str(score), True, WHITE)
            window.blit(score_text, (10, 10))
            high_score_text = scoreboard_font.render("High Score: " + str(high_score), True, WHITE)
            window.blit(high_score_text, (10, 50))
            # Draw level number (top-right)
            level_text = scoreboard_font.render("Level: " + str(level), True, WHITE)
            level_rect = level_text.get_rect(topright=(WIDTH - 10, 10))
            window.blit(level_text, level_rect)
        elif game_state == "level_complete":
            complete_text = message_font.render("Level Complete, Well Done User!", True, WHITE)
            prompt_text = scoreboard_font.render("Advance to next level?  y/n", True, WHITE)
            complete_rect = complete_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
            prompt_rect = prompt_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            window.blit(complete_text, complete_rect)
            window.blit(prompt_text, prompt_rect)
        elif game_state == "game_over":
            # Update high score on game over
            high_score = max(high_score, score)
            over_text = message_font.render("Game Over! Final Score: " + str(score), True, WHITE)
            prompt_text = scoreboard_font.render("Play again?  y/n", True, WHITE)
            over_rect = over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
            prompt_rect = prompt_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            window.blit(over_text, over_rect)
            window.blit(prompt_text, prompt_rect)
            # Also display the High Score on the game over screen
            high_score_text = scoreboard_font.render("High Score: " + str(high_score), True, WHITE)
            high_score_rect = high_score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70))
            window.blit(high_score_text, high_score_rect)

        pygame.display.update()
        clock.tick(60)
    except Exception as e:
        print(f"Error in game loop: {e}")
        running = False

pygame.quit()