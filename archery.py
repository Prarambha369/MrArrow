import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Set up the game window
WIDTH, HEIGHT = 800, 600
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Archery Game")

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Set up the player
player_size = 50
player_pos = [WIDTH // 2, HEIGHT - 50]
arrow_speed = 20
arrows = []

# Set up the target
target_size = 50
target_pos = [random.randint(0, WIDTH - target_size), random.randint(50, HEIGHT - target_size - 50)]

# Set the game speed
clock = pygame.time.Clock()

# Define the game over function
def game_over():
    pygame.quit()
    quit()

# Draw the player
def draw_player():
    pygame.draw.rect(window, GREEN, (player_pos[0], player_pos[1], player_size, player_size))

# Draw the target
def draw_target():
    pygame.draw.circle(window, RED, (target_pos[0], target_pos[1]), target_size // 2)

# Draw the arrows
def draw_arrows():
    for arrow in arrows:
        pygame.draw.rect(window, WHITE, (arrow[0], arrow[1], 5, 10))

# Update the arrows' positions
def update_arrows():
    for arrow in arrows:
        arrow[1] -= arrow_speed
    for arrow in arrows:
        if arrow[1] < 0:
            arrows.remove(arrow)

# Check for arrow-target collisions
def check_collisions():
    for arrow in arrows:
        distance = math.sqrt((arrow[0] - target_pos[0]) ** 2 + (arrow[1] - target_pos[1]) ** 2)
        if distance < target_size // 2:
            arrows.remove(arrow)
            return True
    return False

# Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_over()

    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT] and player_pos[0] > 0:
        player_pos[0] -= 5
    if keys[pygame.K_RIGHT] and player_pos[0] < WIDTH - player_size:
        player_pos[0] += 5
    if keys[pygame.K_SPACE]:
        arrow_pos = [player_pos[0] + player_size // 2, player_pos[1]]
        arrows.append(arrow_pos)

    window.fill(BLACK)
    draw_player()
    draw_target()
    draw_arrows()
    update_arrows()

    if check_collisions():
        target_pos = [random.randint(0, WIDTH - target_size), random.randint(50, HEIGHT - target_size - 50)]

    clock.tick(30)
    pygame.display.update()
