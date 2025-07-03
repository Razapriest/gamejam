import pygame
from pygame import mixer
import random
import sys
import copy
import time

pygame.init()
mixer.init()
mixer.music.load("8bit.mp3")
pygame.mixer.music.set_volume(0.15)
pygame.mixer.music.play(-1,0.0)

info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Protect Zeeble")
font = pygame.font.Font("Grand9K Pixel.ttf", 24)

player_hp = 10
currency = 500
reward = 250

ROWS, COLS = 9, 9
LOGIC_MATRIX = [[0 for x in range(COLS)] for y in range(ROWS)]
LOGIC_MATRIX[4][4] = 1
CELL_SIZE = min(SCREEN_WIDTH // (COLS + 3), SCREEN_HEIGHT // (ROWS + 3))
GRID_WIDTH, GRID_HEIGHT = CELL_SIZE * COLS, CELL_SIZE * ROWS
GRID_START_X = (SCREEN_WIDTH - GRID_WIDTH) // 2
GRID_START_Y = (SCREEN_HEIGHT - int(GRID_HEIGHT * 1.25)) // 2

WHITE = (255, 255, 255)

def load_sprite(filename):
    img = pygame.image.load(filename).convert_alpha()
    return pygame.transform.scale(img, (CELL_SIZE, CELL_SIZE))

sprites = {
    1: load_sprite("cat.png"),
    2: load_sprite("turret_orange.png"),
    3: load_sprite("turret_blue.png"),
    4: load_sprite("turret_green.png"),
    5: load_sprite("turret_purple.png"),
    6: load_sprite("enemy.png"),
    7: load_sprite("bullet_orange.png"),
    8: load_sprite("bullet_blue.png"),
    9: load_sprite("bullet_green.png"),
    10: load_sprite("dead_zone_final.png"),
}

BUTTON_SIZE = (120, 120)
BUTTON_SIZE_SMALL = (80, 80)
turret_button_images = {
    1: pygame.transform.scale(pygame.image.load("button_fire.png").convert_alpha(), BUTTON_SIZE),
    2: pygame.transform.scale(pygame.image.load("button_shock.png").convert_alpha(), BUTTON_SIZE),
    3: pygame.transform.scale(pygame.image.load("button_gas.png").convert_alpha(), BUTTON_SIZE),
    4: pygame.transform.scale(pygame.image.load("button_wall.png").convert_alpha(), BUTTON_SIZE),
}

wave_button_image = pygame.transform.scale(pygame.image.load("start_wave.png").convert_alpha(), BUTTON_SIZE)
rewind_button_image = pygame.transform.scale(pygame.image.load("rewind_button.png").convert_alpha(), BUTTON_SIZE)
quit_button_image = pygame.transform.scale(pygame.image.load("quit_button_final.png").convert_alpha(), BUTTON_SIZE_SMALL)
background_img = pygame.image.load("background_layout.png").convert()
background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

# left button settings
BUTTON_CENTER_X = GRID_START_X - CELL_SIZE * 3
BUTTON_CENTER_Y = GRID_START_Y + GRID_HEIGHT * 0.3
BUTTON_RADIUS = CELL_SIZE * 0.75

button_positions = {
    2: (BUTTON_CENTER_X, BUTTON_CENTER_Y - CELL_SIZE * 1.5 - 10),  # Top
    3: (BUTTON_CENTER_X + CELL_SIZE * 1.5, BUTTON_CENTER_Y - 10),  # Right
    4: (BUTTON_CENTER_X, BUTTON_CENTER_Y + CELL_SIZE * 1.5 - 10),  # Bottom
    5: (BUTTON_CENTER_X - CELL_SIZE * 1.5, BUTTON_CENTER_Y - 10),  # Left
}

#right button settings
WAVE_BUTTON_X = GRID_START_X + GRID_WIDTH + CELL_SIZE * 2 - 5
WAVE_BUTTON_Y = GRID_START_Y + GRID_HEIGHT // 2.8
WAVE_BUTTON_RADIUS = CELL_SIZE * 0.75

REWIND_BUTTON_X = GRID_START_X + GRID_WIDTH + CELL_SIZE * 4 - 10
REWIND_BUTTON_Y = GRID_START_Y + GRID_HEIGHT // 5 + 5
REWIND_BUTTON_RADIUS = CELL_SIZE * 0.75

QUIT_BUTTON_X = GRID_START_X + GRID_WIDTH - CELL_SIZE
QUIT_BUTTON_Y = GRID_START_Y + GRID_HEIGHT + CELL_SIZE * 1.4
QUIT_BUTTON_RADIUS = CELL_SIZE * 0.75

# Used for the rewind mechanic
saved_states = []

popup = {
    "active": False,
    "text": "",
    "start_time": 0,
    "duration": 1  # seconds
}

def play_sound(sound_file):
    sound = pygame.mixer.Sound(sound_file)
    sound.set_volume(0.2)
    sound.play()

def show_popup(text, timer):
    popup["text"] = text
    popup["start_time"] = time.time()
    popup["active"] = True
    popup["duration"] = timer

def draw_popup():
    if not popup["active"]:
        return

    elapsed = time.time() - popup["start_time"]
    if elapsed > popup["duration"]:
        popup["active"] = False
        return

    #rectangle
    rect_width, rect_height = len(popup["text"]) * 16 + 50, 100
    rect_x = (screen.get_width() - rect_width) // 2
    rect_y = (screen.get_height() - rect_height) // 2

    s = pygame.Surface((rect_width, rect_height), pygame.SRCALPHA)
    s.fill((0, 0, 0, 180))  # semi transparent (180)
    screen.blit(s, (rect_x, rect_y))

    #popup text
    text_surf = font.render(popup["text"], True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=(rect_x + rect_width//2, rect_y + rect_height//2))
    screen.blit(text_surf, text_rect)


def draw_tooltip(screen, text, mouse_pos):
    padding = 10
    lines = text.split("\n")
    line_surfs = [font.render(line, True, (255, 255, 255)) for line in lines]
    line_heights = [surf.get_height() for surf in line_surfs]
    max_width = max(surf.get_width() for surf in line_surfs)
    total_height = sum(line_heights)

    # position below cursor
    tooltip_x = mouse_pos[0] - max_width // 2
    tooltip_y = mouse_pos[1] + 30

    bg_rect = pygame.Rect(tooltip_x - padding, tooltip_y - padding,
                          max_width + 2 * padding, total_height + 2 * padding)

    s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
    s.fill((0, 0, 0, 180))
    screen.blit(s, (bg_rect.x, bg_rect.y))

    current_y = tooltip_y
    for surf in line_surfs:
        screen.blit(surf, (tooltip_x, current_y))
        current_y += surf.get_height()
# Saves a state, used for recall
def save_game_state():
    state = {
        'logic_matrix': copy.deepcopy(LOGIC_MATRIX),
        'turrets': copy.deepcopy(turrets),
        'hp': player_hp,
        'currency': currency,
        'wave_number': wave_number,
    }
    saved_states.append(state) #save everything

class Enemy:
    def __init__(self):
        self.type = 6
        self.x, self.y, self.quadrant = self.random_spawn()
        self.has_moved = False
        self.at_center = False

    def random_spawn(self):
        direction = random.randint(1, 4)
        number = random.randint(0, 8)

        if direction == 1:
            x, y = 0, number
        elif direction == 2:
            x, y = number, 8
        elif direction == 3:
            x, y = 8, number
        else:
            x, y = number, 0

        if x <= 3 and y <= 4:
            quadrant = 1
        elif x <= 4 and y >= 5:
            quadrant = 2
        elif x >= 5 and y >= 4:
            quadrant = 3
        else:
            quadrant = 4

        return x, y, quadrant

    def move_toward_center(self, logic_matrix, enemies, turrets, hp_ref):

        xdif = 4 - self.x
        ydif = 4 - self.y

        # Determine direction based on quadrant
        if self.quadrant == 1:
            xdir, ydir = 1, 1
        elif self.quadrant == 2:
            xdir, ydir = 1, -1
        elif self.quadrant == 3:
            xdir, ydir = -1, -1
        else:
            xdir, ydir = -1, 1

        # move logic
        if abs(xdif) >= abs(ydif):
            new_x, new_y = self.x + xdir, self.y
        else:
            new_x, new_y = self.x, self.y + ydir

        if not (0 <= new_x < 9 and 0 <= new_y < 9):
            return

        # enemy reaches middle
        if (new_x, new_y) == (4, 4):
            logic_matrix[self.y][self.x] = 0
            if self in enemies:
                enemies.remove(self)
            play_sound("damage_taken.mp3")
            hp_ref[0] -= 1
            return

        target = logic_matrix[new_y][new_x]

        # destroy turret
        if (new_x, new_y) != (4, 4) and target in [2, 3, 4, 5]:
            logic_matrix[self.y][self.x] = 0
            if target in [2, 3, 4, 5]:
                for turret in turrets[:]:
                    if turret.x == new_x and turret.y == new_y:
                        turrets.remove(turret)
                        break
                logic_matrix[new_y][new_x] = 0
            if self in enemies:
                enemies.remove(self)
                play_sound("enemy_death.mp3")
            return

        # normal move, swap places with dead zones
        if target == 0:
            logic_matrix[self.y][self.x] = 0
            logic_matrix[new_y][new_x] = self.type
            self.x, self.y = new_x, new_y
        if target == 10:
            logic_matrix[self.y][self.x] = 10
            logic_matrix[new_y][new_x] = self.type
            self.x, self.y = new_x, new_y

class Turret:
    def __init__(self, x, y, turret_type):
        self.x = x
        self.y = y
        self.type = turret_type

last_fired_tiles = []

def fire_turrets(matrix, tick):
    fired = []

    for turret in turrets:
        x, y, t_type = turret.x, turret.y, turret.type

        orthogonal = [(-1, 0), (1, 0), (0, -1), (0, 1)] # plus sign
        diagonal = [(-1, -1), (-1, 1), (1, -1), (1, 1)] # x sign
        all_dirs = orthogonal + diagonal # aoe

        if t_type == 2 and tick % 3 == 0: #aoe turret fires on %3 ticks
            play_sound("shoot_orange.mp3")
            for dx, dy in all_dirs:
                tx, ty = x + dx, y + dy
                if 0 <= tx < COLS and 0 <= ty < ROWS and matrix[ty][tx] == 0:
                    matrix[ty][tx] = 7
                    fired.append((tx, ty))
                for enemy in enemies:
                    if enemy.x == tx and enemy.y == ty:
                        LOGIC_MATRIX[enemy.y][enemy.x] = 0
                        enemies.remove(enemy)
                        matrix[ty][tx] = 7
                        fired.append((tx, ty))

        elif t_type == 3 and tick % 2 == 0: # x sign turret fires on %2 ticks
            play_sound("shoot_blue.mp3")
            for dx, dy in diagonal:
                tx, ty = x + dx, y + dy
                if 0 <= tx < COLS and 0 <= ty < ROWS and matrix[ty][tx] == 0:
                    matrix[ty][tx] = 8
                    fired.append((tx, ty))
                for enemy in enemies:
                    if enemy.x == tx and enemy.y == ty:
                        LOGIC_MATRIX[enemy.y][enemy.x] = 0
                        enemies.remove(enemy)
                        matrix[ty][tx] = 8
                        fired.append((tx, ty))

        elif t_type == 4 and tick % 2 == 1: # + sign turret fires on %2==1 ticks
            play_sound("shoot_green.mp3")
            for dx, dy in orthogonal:
                tx, ty = x + dx, y + dy
                if 0 <= tx < COLS and 0 <= ty < ROWS and matrix[ty][tx] == 0:
                    matrix[ty][tx] = 9
                    fired.append((tx, ty))
                for enemy in enemies:
                    if enemy.x == tx and enemy.y == ty:
                        LOGIC_MATRIX[enemy.y][enemy.x] = 0
                        enemies.remove(enemy)
                        matrix[ty][tx] = 9
                        fired.append((tx, ty))

    return fired

def trigger_anomaly():
    show_popup("Rewinded time!", 1.5)
    play_sound("rewind_sound.mp3")
    random_x = random.randint(1, COLS - 2)
    random_y = random.randint(1, ROWS - 2)
    while 3 <= random_x <= 5 and 3 <= random_y <= 5:
        random_x = random.randint(1, COLS - 2)
        random_y = random.randint(1, ROWS - 2)
    LOGIC_MATRIX[random_y][random_x] =  10


def draw_grid():
    screen.blit(background_img, (0, 0))

    # turret buttons:
    for number, (x, y) in button_positions.items():
        img = turret_button_images[number - 1]
        rect = img.get_rect(center=(x, y))
        screen.blit(img, rect)

    # right buttons:
    wave_rect = wave_button_image.get_rect(center=(WAVE_BUTTON_X, WAVE_BUTTON_Y))
    screen.blit(wave_button_image, wave_rect)

    rewind_rect = rewind_button_image.get_rect(center=(REWIND_BUTTON_X, REWIND_BUTTON_Y))
    screen.blit(rewind_button_image, rewind_rect)

    quit_rect = quit_button_image.get_rect(center=(QUIT_BUTTON_X, QUIT_BUTTON_Y))
    screen.blit(quit_button_image, quit_rect)

    below_grid_y = GRID_START_Y + GRID_HEIGHT + 25  # y under the grid

    wave_num_text = font.render(f"Wave: {wave_number}", True, WHITE)
    hp_text = font.render(f"HP: {player_hp}", True, WHITE)
    currency_text = font.render(f"Currency: {currency}", True, WHITE)

    wave_text_rect = wave_num_text.get_rect(center=(SCREEN_WIDTH // 2, below_grid_y + 50)) # wave text
    hp_text_rect = hp_text.get_rect(center=(SCREEN_WIDTH // 2, below_grid_y + 80)) # hp text
    currency_text_rect = currency_text.get_rect(center=(SCREEN_WIDTH // 2, below_grid_y + 110))

    screen.blit(wave_num_text, wave_text_rect)
    screen.blit(hp_text, hp_text_rect)
    screen.blit(currency_text, currency_text_rect)

    # draw grid (continuously)
    for row in range(ROWS):
        for col in range(COLS):
            x = GRID_START_X + col * CELL_SIZE
            y = GRID_START_Y + row * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

            value = LOGIC_MATRIX[row][col]
            if value in sprites:
                screen.blit(sprites[value], (x, y))

def rewind():
    global LOGIC_MATRIX, enemies, turrets, player_hp, wave_number, currency
    if len(saved_states) >= 2:
        saved_state = saved_states[-2]  # second to last save
        LOGIC_MATRIX = [row[:] for row in saved_state["logic_matrix"]]
        turrets = saved_state["turrets"][:]
        player_hp = saved_state["hp"]
        currency = saved_state["currency"]
        wave_number = saved_state["wave_number"]
        hp_ref = [player_hp]
        trigger_anomaly()
        player_hp = hp_ref[0]
        save_game_state()
    else:
        print("Not enough save states to rewind to second to last.")

clock = pygame.time.Clock()
last_spawn = pygame.time.get_ticks()
last_move = pygame.time.get_ticks()
spawn_interval = 2000
move_interval = 1000
enemies = []
turrets = []

selected_number = None

global_tick = 0
temp_fired_tiles = []

# wave settings
wave_active = False
wave_queue = []
wave_spawned_count = 0
wave_total_enemies = 5
wave_spawn_interval = 2000
last_wave_spawn = 0
wave_enemies_per_spawn = 1
wave_number = 0
wave_queue_index = 0
NUM_WAVES = 5
preloaded_waves = []  # List of lists, one list per wave
prev_pos = None
# Generates all the waves at the beginning of the game
for wave_num in range(1, NUM_WAVES + 1):
    wave_enemies = []
    prev_pos = None
    num_enemies = 2 + 3 * wave_num
    while len(wave_enemies) < num_enemies:
        new_enemy = Enemy()
        new_pos = (new_enemy.x, new_enemy.y)
        if new_pos != prev_pos:
            wave_enemies.append(new_enemy)
            prev_pos = new_pos
    preloaded_waves.append(wave_enemies)

rewind_used = False
save_game_state()


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            play_sound("button_click.mp3")
            mouse_pos = pygame.mouse.get_pos()

            # turret button checking
            for number, (x, y) in button_positions.items():
                dist = pygame.math.Vector2(mouse_pos).distance_to((x, y))
                if dist <= BUTTON_RADIUS:
                    selected_number = number
                    if selected_number == 2:
                        currency_needed = 200
                    elif selected_number == 3:
                        currency_needed = 100
                    elif selected_number == 4:
                        currency_needed = 100
                    else:
                        currency_needed = 50
                    break
                else:
                    # wave button
                    dist_wave = pygame.math.Vector2(mouse_pos).distance_to((WAVE_BUTTON_X, WAVE_BUTTON_Y))
                    dist_rewind = pygame.math.Vector2(mouse_pos).distance_to((REWIND_BUTTON_X, REWIND_BUTTON_Y))
                    dist_quit = pygame.math.Vector2(mouse_pos).distance_to((QUIT_BUTTON_X, QUIT_BUTTON_Y))

                    if dist_rewind <= REWIND_BUTTON_RADIUS:
                        if not wave_active and not rewind_used:
                            # rewind
                            for row in range(ROWS):
                                for col in range(COLS):
                                    if LOGIC_MATRIX[row][col] == 7 or LOGIC_MATRIX[row][col] == 8 or LOGIC_MATRIX[row][col] == 9:
                                        LOGIC_MATRIX[row][col] = 0
                            rewind()
                            rewind_used = True

                    if dist_wave <= WAVE_BUTTON_RADIUS:
                        if not wave_active and wave_number < NUM_WAVES:
                            for row in range(ROWS):
                                for col in range(COLS):
                                    if LOGIC_MATRIX[row][col] in (7, 8, 9):
                                        LOGIC_MATRIX[row][col] = 0

                            wave_active = True
                            wave_spawned_count = 0
                            last_wave_spawn = pygame.time.get_ticks()

                            rewind_used = False
                            wave_queue = [copy.deepcopy(e) for e in preloaded_waves[wave_number]]
                            wave_total_enemies = len(wave_queue)
                            wave_number += 1  # increase after accessing
                        continue

                    if dist_quit <= QUIT_BUTTON_RADIUS:
                        pygame.quit()
                        sys.exit()

                # grid clicking
                for row in range(ROWS):
                    for col in range(COLS):
                        cell_x = GRID_START_X + col * CELL_SIZE
                        cell_y = GRID_START_Y + row * CELL_SIZE
                        cell_rect = pygame.Rect(cell_x, cell_y, CELL_SIZE, CELL_SIZE)
                        if cell_rect.collidepoint(mouse_pos):
                            if not wave_active and LOGIC_MATRIX[row][col] == 0 and selected_number  and currency >= currency_needed:
                                LOGIC_MATRIX[row][col] = selected_number
                                if selected_number in (2, 3, 4, 5):
                                    turrets.append(Turret(col, row, selected_number))
                                    currency = currency - currency_needed
                                else:
                                    selected_number = None
                                selected_number = None

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
        play_sound("button_click.mp3")
        selected_number = None

    current_time = pygame.time.get_ticks()

    if current_time - last_move >= move_interval: # 1 "move tick" = 1 second
        last_move = current_time
        global_tick += 1

        # enemies die when on the same tile as a "bullet"
        for x, y in last_fired_tiles:
            for enemy in enemies[:]:
                if enemy.x == x and enemy.y == y:
                    LOGIC_MATRIX[enemy.y][enemy.x] = 0
                    enemies.remove(enemy)

            # "bullets" get removed (with short delay)
            if LOGIC_MATRIX[y][x] in (7, 8, 9):
                LOGIC_MATRIX[y][x] = 0
        last_fired_tiles.clear()

        # enemy move
        hp_ref = [player_hp]
        for enemy in enemies[:]:
            enemy.move_toward_center(LOGIC_MATRIX, enemies, turrets, hp_ref)
        player_hp = hp_ref[0]

        if player_hp <= 0:
            print("Game Over!")  # console output
            pygame.quit()
            sys.exit()
        # v ^ at the same time, roughly
        # turret shot
        last_fired_tiles = fire_turrets(LOGIC_MATRIX, global_tick)

    # wave logic
    if wave_active:
        if current_time - last_wave_spawn >= wave_spawn_interval and wave_queue:
            for _ in range(wave_enemies_per_spawn):
                if wave_queue:
                    new_enemy = wave_queue.pop(0)
                    if LOGIC_MATRIX[new_enemy.y][new_enemy.x] == 0:
                        LOGIC_MATRIX[new_enemy.y][new_enemy.x] = new_enemy.type
                        enemies.append(new_enemy)
                    wave_spawned_count += 1
            last_wave_spawn = current_time

        if wave_spawned_count >= wave_total_enemies and not enemies:
            if player_hp > 0:
                wave_active = False
                currency += reward
                save_game_state()
                if wave_number == 5:
                    show_popup(f"Game Finished! Score = {player_hp*currency/100}", 10)
                else:
                    show_popup("Wave cleared!", 1.5)

    mouse_pos = pygame.mouse.get_pos()
    tooltip_text = None  # default no tooltip

    # tooltip hover for turrets !!! needs expanding
    for number, (x, y) in button_positions.items():
        dist = pygame.math.Vector2(mouse_pos).distance_to((x, y))
        if dist <= BUTTON_RADIUS:
            if number == 2:
                tooltip_text = "Fire turret.\nShoots around it.\nCost = 200"
            if number == 3:
                tooltip_text = "Electric turret.\nShoots diagonally.\nCost = 100"
            if number == 4:
                tooltip_text = "Poison turret.\nShoots orthogonally.\nCost = 100"
            if number == 5:
                tooltip_text = "Wall.\nCost = 50"
            break

    # tooltip hover start wave
    if tooltip_text is None:
        dist_wave = pygame.math.Vector2(mouse_pos).distance_to((WAVE_BUTTON_X, WAVE_BUTTON_Y))
        if dist_wave <= WAVE_BUTTON_RADIUS:
            tooltip_text = "Start next wave"

    # tooltip hover rewind
    if tooltip_text is None:
        dist_rewind = pygame.math.Vector2(mouse_pos).distance_to((REWIND_BUTTON_X, REWIND_BUTTON_Y))
        if dist_rewind <= REWIND_BUTTON_RADIUS:
            tooltip_text = "Rewind time...?"

    # tooltip hover quit
    if tooltip_text is None:
        dist_quit = pygame.math.Vector2(mouse_pos).distance_to((QUIT_BUTTON_X, QUIT_BUTTON_Y))
        if dist_quit <= QUIT_BUTTON_RADIUS:
            tooltip_text = "Quit...? :("

    draw_grid()
    if selected_number:
        turret_img = sprites[selected_number]
        if turret_img:
            img_rect = turret_img.get_rect()
            # grab turret sprite to place
            img_rect.center = mouse_pos
            screen.blit(turret_img, img_rect)
    draw_popup()
    if tooltip_text:
        draw_tooltip(screen, tooltip_text, mouse_pos)
    pygame.display.flip()
    clock.tick(60)
