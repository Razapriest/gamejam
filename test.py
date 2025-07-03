import pygame
import random
import sys
import copy
import time

pygame.init()

info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Butterfly Defect")
font = pygame.font.SysFont(None, 32)

ROWS, COLS = 9, 9
LOGIC_MATRIX = [[0 for x in range(COLS)] for y in range(ROWS)]
LOGIC_MATRIX[4][4] = 1
CELL_SIZE = min(SCREEN_WIDTH // (COLS + 3), SCREEN_HEIGHT // (ROWS + 3))
GRID_WIDTH, GRID_HEIGHT = CELL_SIZE * COLS, CELL_SIZE * ROWS
GRID_START_X = (SCREEN_WIDTH - GRID_WIDTH) // 2
GRID_START_Y = (SCREEN_HEIGHT - int(GRID_HEIGHT * 1.25)) // 2

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRID_COLOR = (200, 200, 200)
BUTTON_COLOR = (100, 100, 250)
RED = (255, 0, 0)

def load_sprite(filename):
    img = pygame.image.load(filename).convert_alpha()
    return pygame.transform.scale(img, (CELL_SIZE, CELL_SIZE))

sprites = {
    1: load_sprite("treasure.png"),
    2: load_sprite("turret_1.png"),
    3: load_sprite("turret_2.png"),
    4: load_sprite("turret_3.png"),
    5: load_sprite("turret_4.png"),
    6: [load_sprite("enemy.png"), load_sprite("turret_1.png")],
    7: load_sprite("projectile_1.png"),
    8: load_sprite("projectile_2.png"),
    9: load_sprite("projectile_3.png"),
    10: load_sprite("dead_zone.png"),
}

turret_button_images = {
    1: pygame.image.load("button_1.png").convert_alpha(),
    2: pygame.image.load("button_2.png").convert_alpha(),
    3: pygame.image.load("button_3.png").convert_alpha(),
    4: pygame.image.load("button_4.png").convert_alpha(),
}

# helper function for the minions test
def load_img(path):
    img = pygame.image.load(path).convert()
    img = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    return img

minions = [load_img("minions_test/frame_0" + str(num) + "_delay-0.04s.gif") for num in range(10)]

wave_button_image = pygame.image.load("button_start.png").convert_alpha()
rewind_button_image = pygame.image.load("button_rewind.png").convert_alpha()
background_img = pygame.image.load("background_layout.png").convert()
background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
background_img2 = pygame.image.load("minion.gif").convert()
background_img2 = pygame.transform.scale(background_img2, (SCREEN_WIDTH, SCREEN_HEIGHT))

# left button settings
BUTTON_CENTER_X = GRID_START_X - CELL_SIZE * 3
BUTTON_CENTER_Y = GRID_START_Y + GRID_HEIGHT // 2
BUTTON_RADIUS = CELL_SIZE * 0.75

button_positions = {
    2: (BUTTON_CENTER_X, BUTTON_CENTER_Y - CELL_SIZE * 1.5),  # Top
    3: (BUTTON_CENTER_X + CELL_SIZE * 1.5, BUTTON_CENTER_Y),  # Right
    4: (BUTTON_CENTER_X, BUTTON_CENTER_Y + CELL_SIZE * 1.5),  # Bottom
    5: (BUTTON_CENTER_X - CELL_SIZE * 1.5, BUTTON_CENTER_Y),  # Left
}

#right button settings
WAVE_BUTTON_X = GRID_START_X + GRID_WIDTH + CELL_SIZE * 2
WAVE_BUTTON_Y = GRID_START_Y + GRID_HEIGHT // 2.5
WAVE_BUTTON_RADIUS = CELL_SIZE * 0.75

REWIND_BUTTON_X = GRID_START_X + GRID_WIDTH + CELL_SIZE * 4
REWIND_BUTTON_Y = GRID_START_Y + GRID_HEIGHT // 5
REWIND_BUTTON_RADIUS = CELL_SIZE * 0.75

player_hp = 10
currency = 1000
# Used for the rewind mechanic
saved_states = []

popup = {
    "active": False,
    "text": "",
    "start_time": 0,
    "duration": 1  # seconds
}

def show_popup(text):
    popup["text"] = text
    popup["start_time"] = time.time()
    popup["active"] = True

def draw_popup():
    if not popup["active"]:
        return

    elapsed = time.time() - popup["start_time"]
    if elapsed > popup["duration"]:
        popup["active"] = False
        return

    #rectangle
    rect_width, rect_height = 300, 100
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
    padding = 6
    text_surf = font.render(text, True, (255, 255, 255))
    text_rect = text_surf.get_rect()

    # position below cursor
    tooltip_x = mouse_pos[0] - text_rect.width // 2
    tooltip_y = mouse_pos[1] - text_rect.height // 2 + 30

    bg_rect = pygame.Rect(tooltip_x - padding, tooltip_y - padding,
                          text_rect.width + 2 * padding, text_rect.height + 2 * padding)

    s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
    s.fill((0, 0, 0, 180))
    screen.blit(s, (bg_rect.x, bg_rect.y))

    screen.blit(text_surf, (tooltip_x, tooltip_y))
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

def trigger_anomaly(hp_ref):
    anomaly_type = 0
    if anomaly_type == 0:
        random_x = random.randint(1, COLS - 2)
        random_y = random.randint(1, ROWS - 2)
        while 3 <= random_x <= 5 and 3 <= random_y <= 5:
            random_x = random.randint(1, COLS - 2)
            random_y = random.randint(1, ROWS - 2)
        LOGIC_MATRIX[random_y][random_x] =  10
    if anomaly_type == 1:
        hp_ref[0] -= 1


# Helper class that handles all animated object
# Parameters: object that gets the sprites changed
            # animation_frames is the vector that is used for animation loops
            # time_to_complete_loop : how fast the loop should go, in seconds
            # loop_back : whether to change loop direction upon finishing a loop
            # coords_can_change : if True, then coords will be evaluated upon advancing the frame
class Animated:
    # Static members: starting clock
    starting_clock = 0
    has_overwritten_clock = False
    # time_to_complete_loop = (float)(1.0) # 1 second for an entire animation loop
    
    def __init__(self, coords, animation_frames, time_to_complete_loop = ((float)(1.0)), loop_back = False, coords_can_change = False):
        self.coords = coords
        self.animation_frames = animation_frames
        self.animation_frame_direction = 1
        self.animation_frame = 0
        self.time_to_complete_loop = time_to_complete_loop
        self.loop_back = loop_back
        self.coords_can_change = coords_can_change
        self.time_to_change_frame = self.time_to_complete_loop / ((float)(len(self.animation_frames)))
        self.last_updated = pygame.time.get_ticks()
        # When the first animated object is created, get the time
        if not(Animated.has_overwritten_clock):
            Animated.has_overwritten_clock = True
            Animated.starting_clock = pygame.time.get_ticks()

    # Function that gets to the next frame, if the time to switch to the next frame has come
    def advance_frame(self):
        # use the global screen variable
        global screen
        # if the frame hasn't been updated in a while
        if(pygame.time.get_ticks() - self.last_updated > self.time_to_change_frame * 1000):
            self.last_updated = pygame.time.get_ticks()
            # Switch to the next frame
            self.animation_frame += self.animation_frame_direction
            # If the next frame is out of bounds, reset the loop
            if(self.animation_frame == -1 or self.animation_frame == len(self.animation_frames)):
                self.animation_frame_direction *= -1
                if not(self.loop_back):
                    self.animation_frame_direction = 1
                    self.animation_frame = -1
                self.animation_frame += self.animation_frame_direction
        if not(self.coords_can_change):
            screen.blit(self.animation_frames[self.animation_frame], self.coords)
        else:
            if(self.coords[0][0] >= 0):
                screen.blit(self.animation_frames[self.animation_frame], self.coords[0])

objects_to_animate = []
def animation_loop():
    for object in objects_to_animate:
        object.advance_frame()

objects_to_animate = [Animated((0, 0), [background_img], time_to_complete_loop = 0.5)]

sprites_coords = {}

for value in sprites:
    sprites_coords[value] = [(-1, -1)]
    if value != 6:
        objects_to_animate.append(Animated(sprites_coords[value], [sprites[value]], coords_can_change = True))
    else:
        objects_to_animate.append(Animated(sprites_coords[value], sprites[value], coords_can_change = True, time_to_complete_loop = 0.3))


def draw_grid():
    
    # screen.blit(background_img, (0, 0))

    # draw grid (continuously)
    for row in range(ROWS):
        for col in range(COLS):
            x = GRID_START_X + col * CELL_SIZE
            y = GRID_START_Y + row * CELL_SIZE

            value = LOGIC_MATRIX[row][col]
            if value in sprites:
                sprites_coords[value][0] = (x, y)

    animation_loop()

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

    below_grid_y = GRID_START_Y + GRID_HEIGHT + 20  # y under the grid
    wave_num_text = font.render(f"Wave: {wave_number}", True, BLACK)
    hp_text = font.render(f"HP: {player_hp}", True, RED)

    wave_text_rect = wave_num_text.get_rect(center=(SCREEN_WIDTH // 2, below_grid_y + 20)) # wave text
    hp_text_rect = hp_text.get_rect(center=(SCREEN_WIDTH // 2, below_grid_y + 50)) # hp text

    screen.blit(wave_num_text, wave_text_rect)
    screen.blit(hp_text, hp_text_rect)

    # draw grid (continuously - need to do again because of overwriting by animation_loop)
    for row in range(ROWS):
        for col in range(COLS):
            x = GRID_START_X + col * CELL_SIZE
            y = GRID_START_Y + row * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

            value = LOGIC_MATRIX[row][col]
            if value in sprites:
                sprites_coords[value][0] = (x, y)
                # print(value, sprites_coords[value])
                # screen.blit(sprites[value], (x, y))
            elif value != 0:
                text = font.render(str(value), True, BLACK)
                screen.blit(text, text.get_rect(center=rect.center))
    
    # animation_loop()

def rewind():
    global LOGIC_MATRIX, enemies, turrets, player_hp, wave_number
    if len(saved_states) >= 2:
        saved_state = saved_states[-2]  # second to last save
        LOGIC_MATRIX = [row[:] for row in saved_state["logic_matrix"]]
        turrets = saved_state["turrets"][:]
        player_hp = saved_state["hp"]
        currency = saved_state["currency"]
        wave_number = saved_state["wave_number"]
        hp_ref = [player_hp]
        trigger_anomaly(hp_ref)
        player_hp = hp_ref[0]
        show_popup("Rewinded time!")
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

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()

            # turret button checking
            for number, (x, y) in button_positions.items():
                dist = pygame.math.Vector2(mouse_pos).distance_to((x, y))
                if dist <= BUTTON_RADIUS:
                    selected_number = number
                    break
                else:
                    # wave button
                    dist_wave = pygame.math.Vector2(mouse_pos).distance_to((WAVE_BUTTON_X, WAVE_BUTTON_Y))
                    dist_rewind = pygame.math.Vector2(mouse_pos).distance_to((REWIND_BUTTON_X, REWIND_BUTTON_Y))

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
                            save_game_state()
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

                # grid clicking
                for row in range(ROWS):
                    for col in range(COLS):
                        cell_x = GRID_START_X + col * CELL_SIZE
                        cell_y = GRID_START_Y + row * CELL_SIZE
                        cell_rect = pygame.Rect(cell_x, cell_y, CELL_SIZE, CELL_SIZE)
                        if cell_rect.collidepoint(mouse_pos):
                            if not wave_active and LOGIC_MATRIX[row][col] == 0 and selected_number:
                                LOGIC_MATRIX[row][col] = selected_number
                                if selected_number in (2, 3, 4, 5):
                                    turrets.append(Turret(col, row, selected_number))
                                selected_number = None

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
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
                show_popup("Wave cleared!")
                save_game_state()

    mouse_pos = pygame.mouse.get_pos()
    tooltip_text = None  # default no tooltip

    # tooltip hover for turrets !!! needs expanding
    for number, (x, y) in button_positions.items():
        dist = pygame.math.Vector2(mouse_pos).distance_to((x, y))
        if dist <= BUTTON_RADIUS:
            tooltip_text = f"Place turret type {number}"
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
            tooltip_text = "Rewind to previous state"

    screen.fill((255, 255, 255))
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
    pygame.display.update()
    clock.tick(60)
