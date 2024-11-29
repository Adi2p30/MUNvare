import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
BLOCK_SIZE = 40
FPS = 15

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
PINK = (255, 192, 203)  # Pink color
LIGHT_BLUE = (173, 216, 230)  # Light blue color

# Setup screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Escaping Gangalegends")


# Classes
class Player:
    def __init__(self, obstacles):
        while True:
            self.rect = pygame.Rect(0, random.randint(0, (SCREEN_HEIGHT // BLOCK_SIZE) - 1) * BLOCK_SIZE, BLOCK_SIZE,
                                    BLOCK_SIZE)
            if not any(self.rect.colliderect(obs) for obs in obstacles):
                break

    def move(self, dx, dy, obstacles):
        new_rect = self.rect.move(dx, dy)
        if new_rect.left < 0 or new_rect.right > SCREEN_WIDTH or new_rect.top < 0 or new_rect.bottom > SCREEN_HEIGHT:
            return
        for obs in obstacles:
            if new_rect.colliderect(obs):
                return
        self.rect = new_rect


class Guard:
    def __init__(self, start_x, start_y):
        self.rect = pygame.Rect(start_x, start_y, BLOCK_SIZE, BLOCK_SIZE)

    def follow_player(self, player, obstacles):
        # Determine direction towards player
        target_x = player.rect.x
        target_y = player.rect.y

        # Calculate direction
        dx = target_x - self.rect.x
        dy = target_y - self.rect.y

        step_x, step_y = 0, 0

        # Decide which direction to move
        if abs(dx) > abs(dy):
            step_x = BLOCK_SIZE if dx > 0 else -BLOCK_SIZE
        else:
            step_y = BLOCK_SIZE if dy > 0 else -BLOCK_SIZE

        # Move the guard, checking for collisions
        if not self.move_with_collision_check(step_x, step_y, obstacles):
            # Try moving perpendicular if collision occurs
            if step_x != 0:
                step_y = BLOCK_SIZE if dy > 0 else -BLOCK_SIZE
                step_x = 0
            else:
                step_x = BLOCK_SIZE if dx > 0 else -BLOCK_SIZE
                step_y = 0

            # Try moving again with the new step
            self.move_with_collision_check(step_x, step_y, obstacles)

    def move_with_collision_check(self, dx, dy, obstacles):
        new_rect = self.rect.move(dx, dy)
        if new_rect.left < 0 or new_rect.right > SCREEN_WIDTH or new_rect.top < 0 or new_rect.bottom > SCREEN_HEIGHT:
            return False
        for obs in obstacles:
            if new_rect.colliderect(obs):
                return False
        self.rect = new_rect
        return True


def generate_maze():
    obstacles = []
    for _ in range(10):  # Generate 10 random obstacles
        while True:
            x = random.randint(0, (SCREEN_WIDTH // BLOCK_SIZE) - 1) * BLOCK_SIZE
            y = random.randint(0, (SCREEN_HEIGHT // BLOCK_SIZE) - 1) * BLOCK_SIZE
            width = BLOCK_SIZE * random.randint(1, 3)
            height = BLOCK_SIZE * random.randint(1, 3)
            obs = pygame.Rect(x, y, width, height)
            if (obs.right <= SCREEN_WIDTH and obs.bottom <= SCREEN_HEIGHT and
                    not any(obs.colliderect(o) for o in obstacles) and
                    not (obs.colliderect(pygame.Rect(0, 0, BLOCK_SIZE, BLOCK_SIZE)) or
                         obs.colliderect(
                             pygame.Rect(SCREEN_WIDTH - BLOCK_SIZE, SCREEN_HEIGHT // 2, BLOCK_SIZE, BLOCK_SIZE)))):
                obstacles.append(obs)
                break
    return obstacles


def display_message(message, bg_color):
    font = pygame.font.SysFont(None, 48)
    lines = message.splitlines()
    screen.fill(bg_color)
    for i, line in enumerate(lines):
        text = font.render(line, True, BLACK)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + (i * 50) - (len(lines) * 25)))
        screen.blit(text, text_rect)
    pygame.display.flip()
    pygame.time.wait(3000)


def main():
    clock = pygame.time.Clock()
    obstacles = generate_maze()
    player = Player(obstacles)
    guard = Guard(SCREEN_WIDTH - BLOCK_SIZE, SCREEN_HEIGHT // 2)

    display_message(
        "Welcome to Escaping Gangalegends!\nTry to make it to the other side\nof the terrace without getting caught by the guard :D",
        WHITE)

    player_move_timer = 0
    guard_move_timer = 0
    player_move_time = 0.01 * 1000  # 0.01 seconds in milliseconds
    guard_move_time = 0.01 * 1000  # 0.01 seconds in milliseconds

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] and player_move_timer <= 0:
            player.move(0, -BLOCK_SIZE, obstacles)
            player_move_timer = player_move_time
        if keys[pygame.K_DOWN] and player_move_timer <= 0:
            player.move(0, BLOCK_SIZE, obstacles)
            player_move_timer = player_move_time
        if keys[pygame.K_LEFT] and player_move_timer <= 0:
            player.move(-BLOCK_SIZE, 0, obstacles)
            player_move_timer = player_move_time
        if keys[pygame.K_RIGHT] and player_move_timer <= 0:
            player.move(BLOCK_SIZE, 0, obstacles)
            player_move_timer = player_move_time

        # Decrease the timers
        if player_move_timer > 0:
            player_move_timer -= clock.get_time()

        # Move the guard if the timer allows
        if guard_move_timer <= 0:
            guard.follow_player(player, obstacles)
            guard_move_timer = guard_move_time
        else:
            guard_move_timer -= clock.get_time()

        # Check for collisions with guard
        if player.rect.colliderect(guard.rect):
            display_message("Aw man you got caught,\nbe careful they might call the police O_O", LIGHT_BLUE)
            obstacles = generate_maze()
            player = Player(obstacles)
            guard.rect.topleft = (SCREEN_WIDTH - BLOCK_SIZE, SCREEN_HEIGHT // 2)
            continue

        if player.rect.left >= SCREEN_WIDTH - BLOCK_SIZE:
            display_message("Well done, you made it,\nlooks like you weren't scared <3", PINK)
            obstacles = generate_maze()
            player = Player(obstacles)
            guard.rect.topleft = (SCREEN_WIDTH - BLOCK_SIZE, SCREEN_HEIGHT // 2)
            continue

        # Draw everything
        screen.fill(WHITE)
        pygame.draw.rect(screen, GREEN, player.rect)
        pygame.draw.rect(screen, RED, guard.rect)

        for obs in obstacles:
            pygame.draw.rect(screen, BLACK, obs)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
