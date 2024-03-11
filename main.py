import pygame as pg
import pytmx
import json
import random

pg.init()

pg.mixer.init()

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
RESOLUTIONS = ((250, 250), (400, 300), (500, 350), (600, 400), (750, 480), (900, 600), (1100, 600), (1300, 700), (1500, 800))

MENU_NAV_XPAD = 90
MENU_NAV_YPAD = 130

BUTTON_WIDTH = 80
BUTTON_HEIGHT = 80

ICON_SIZE = 80
PADDING = 10

FPS = 80
TILE_SIZE = 2.5

font = pg.font.Font(None, 40)


def load_image(file, width, height):
    image = pg.image.load(file).convert_alpha()
    image = pg.transform.scale(image, (width, height))
    return image


def text_render(text, color = 'black'):
    return font.render(str(text), True, color)


def get_gravity(fps=30):
    fps = fps * 0.2
    return (30 / (fps / 2)) / fps


class Player(pg.sprite.Sprite):
    def __init__(self, map_width, map_height):
        super(Player, self).__init__()

        self.load_animation()

        self.current_animation = self.idle_animation_right
        self.image = self.current_animation[0]
        self.current_image = 0

        self.money = 0

        self.hp = 10

        self.fireballs_count = 0
        self.fireballs = pg.sprite.Group()

        self.rect = self.image.get_rect()
        self.spawn = (200, 3000)
        self.rect.center = self.spawn  # Начальное положение персонажа

        # Начальная скорость и гравитация
        self.velocity_x = 0
        self.velocity_y = 0
        self.gravity = get_gravity(FPS)
        self.friction = 1.2

        self.is_jumping = False
        self.jump_height = 32

        self.map_width = map_width
        self.map_height = map_height

        self.interval = 100
        self.timer = pg.time.get_ticks()

        self._fly_mode = False

        self.damage_timer = pg.time.get_ticks()
        self.damage_interval = 2000

    def load_animation(self):
        tile_size, tile_scale = 32, TILE_SIZE / 2

        self.idle_animation_right = []

        spritesheet = pg.image.load('Tiled Projects/tiles/Legacy Adventure Pack - RUINS/Assets/Idle_(32 x 32).png')

        tile_numbers = 5
        for i in range(tile_numbers):
            x = i * tile_size
            y = 0
            rect = pg.Rect(x, y, tile_size, tile_size)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_size * tile_scale, tile_size * tile_scale))
            self.idle_animation_right.append(image)

        self.idle_animation_left = [pg.transform.flip(image, True, False) for image in self.idle_animation_right]

        self.running_animation_right = []

        spritesheet = pg.image.load('Tiled Projects/tiles/Legacy Adventure Pack - RUINS/Assets/Running_(32 x 32).png')

        tile_numbers = 6
        for i in range(tile_numbers):
            x = i * tile_size
            y = 0
            rect = pg.Rect(x, y, tile_size, tile_size)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_size * tile_scale, tile_size * tile_scale))
            self.running_animation_right.append(image)

        self.running_animation_left = [pg.transform.flip(image, True, False) for image in self.running_animation_right]

        image = pg.image.load('Tiled Projects/tiles/Legacy Adventure Pack - RUINS/Assets/Jumping_(32 x 32).png')
        self.jumping_right = pg.transform.scale(image, (tile_size * tile_scale, tile_size * tile_scale))
        self.jumping_left = pg.transform.flip(self.jumping_right, True, False)

    def get_damage(self, damage):
        if pg.time.get_ticks() - self.damage_timer > self.damage_interval:
            self.hp -= damage
            self.velocity_y = -7
            self.velocity_x  = -10
            self.damage_timer = pg.time.get_ticks()

    def attack(self, sprites):
        if self.fireballs_count > 0 :
            fireball = Fireball(self.rect, True if self.current_animation == self.running_animation_right or self.current_animation == self.idle_animation_right or self.current_animation == self.jumping_right else False)
            self.fireballs.add(fireball)
            sprites.add(fireball)
            self.fireballs_count -= 1

    def update(self, platforms, coins, checkpoints):
        keys = pg.key.get_pressed()
        if keys[pg.K_d]:
            if self.current_animation != self.running_animation_right:
                self.current_animation = self.running_animation_right
                self.current_image = 0
                self.timer -= self.interval
            self.velocity_x = 4
        elif keys[pg.K_a]:
            if self.current_animation != self.running_animation_left:
                self.current_animation = self.running_animation_left
                self.current_image = 0
                self.timer -= self.interval
            self.velocity_x = -4
        else:
            if self.current_animation == self.running_animation_right:
                self.current_animation = self.idle_animation_right
                self.current_image = 0
            elif self.current_animation == self.running_animation_left:
                self.current_animation = self.idle_animation_left
                self.current_image = 0
            self.velocity_x = self.velocity_x / self.friction
            if self.velocity_x ** 2 < 1:
                self.velocity_x = 0

        new_x = self.rect.x + self.velocity_x
        if 0 <= new_x and self.map_width - self.rect.width >= new_x:
            self.rect.x = new_x

        self.velocity_y += self.gravity
        self.rect.y += self.velocity_y

        for platform in platforms:
            if platform.rect.collidepoint(self.rect.midbottom):
                self.velocity_y = 0
                self.rect.bottom = platform.rect.top
                if keys[pg.K_w] or keys[pg.K_SPACE]:
                    if self.current_animation == self.running_animation_right or self.current_animation == self.idle_animation_right:
                        self.image = self.jumping_right
                        self.timer = pg.time.get_ticks() + self.interval * 6
                    else:
                        self.image = self.jumping_left
                        self.timer = pg.time.get_ticks() + self.interval * 6

                    self.velocity_y = -self.jump_height * self.gravity

            if platform.rect.collidepoint(self.rect.midtop):
                self.velocity_y = 0
                self.rect.top = platform.rect.bottom

            if platform.rect.collidepoint(self.rect.midright):
                self.velocity_x = 0
                self.rect.right = platform.rect.left
            if platform.rect.collidepoint(self.rect.midleft):
                self.velocity_x = 0
                self.rect.left = platform.rect.right

        for sprite in checkpoints:
            if sprite.rect.collidepoint(self.rect.center):
                self.spawn = sprite.rect.center

        for sprite in coins:
            if self.rect.collidepoint(sprite.rect.center):
                self.money += random.randint(5, 15)
                self.fireballs_count += 1
                sprite.kill()

        if self.rect.y > self.map_height + 500:
            self.hp -= 2
            self.rect.center = self.spawn

        if keys[pg.K_d] and keys[pg.K_LEFT] and keys[pg.K_SPACE]:
            self._fly_mode = True
        if keys[pg.K_d] and keys[pg.K_RIGHT] and keys[pg.K_SPACE]:
            self._fly_mode = False
        if keys[pg.K_SPACE] and self._fly_mode:
            self.velocity_y = -self.jump_height * self.gravity
        if keys[pg.K_z] and keys[pg.K_f] and keys[pg.K_b]:
            self.money += 1000
        if keys[pg.K_z] and keys[pg.K_c] and keys[pg.K_v]:
            self.fireballs_count += 1

        if pg.time.get_ticks() - self.timer > self.interval:
            self.current_image += 1
            if self.current_image >= len(self.current_animation):
                self.current_image = 0
            self.image = self.current_animation[self.current_image]
            self.timer = pg.time.get_ticks()


class Fireball(pg.sprite.Sprite):
    def __init__(self, player_rect, direction):
        pg.sprite.Sprite.__init__(self)

        self.direction = direction
        self.speed = 10 if self.direction else -10

        self.image = pg.image.load('resourses/images/fireball/fireball.png').convert_alpha()
        self.image = pg.transform.scale(self.image, (30, 30))

        self.timer = pg.time.get_ticks()
        self.interval = 700

        self.rect = self.image.get_rect()
        if self.direction:
            self.rect.center = player_rect.midright
        else:
            self.rect.center = player_rect.midleft

    def update(self):
        self.rect.x += self.speed
        if self.timer + self.interval < pg.time.get_ticks():
            self.kill()


class Bomb(pg.sprite.Sprite):
    def __init__(self, spawn):
        pg.sprite.Sprite.__init__(self)

        self.load_animation()

        self.current_animation = self.running_animation_right
        self.image = self.current_animation[0]
        self.current_image = 0

        self.rect = self.image.get_rect()
        self.spawn = spawn
        self.rect.topleft = self.spawn  # Начальное положение
        self.direction = True

        # Начальная скорость и гравитация
        self.velocity_x = 0
        self.velocity_y = 0
        self.gravity = get_gravity(FPS)

        self.interval = 150
        self.timer = pg.time.get_ticks()

    def load_animation(self):
        tile_size = 32
        tile_scale = TILE_SIZE / 2

        self.running_animation_left = []

        spritesheet = pg.image.load('resourses/images/bomb/Running_(32 x 32).png')

        tile_numbers = 3
        for i in range(tile_numbers):
            x = i * tile_size
            y = 0
            rect = pg.Rect(x, y, tile_size, tile_size)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_size * tile_scale, tile_size * tile_scale))
            self.running_animation_left.append(image)

        self.running_animation_right = [pg.transform.flip(image, True, False) for image in self.running_animation_left]

        self.boom_animation = []

        spritesheet = pg.image.load('resourses/images/bomb/2dBOOM.png')

        tile_numbers = 5
        for i in range(tile_numbers):
            x = i * 96
            y = 0
            rect = pg.Rect(x, y, 96, 96)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_size * tile_scale, tile_size * tile_scale))
            self.boom_animation.append(image)

    def update(self, platforms, area):
        if not self.current_animation == self.boom_animation:
            if self.direction:
                self.current_animation = self.running_animation_right
                self.velocity_x = -3
            else:
                self.current_animation = self.running_animation_left
                self.velocity_x = 3

            new_x = self.rect.x + self.velocity_x
            self.rect.x = new_x

            self.velocity_y += self.gravity
            self.rect.y += self.velocity_y

            for platform in platforms:
                if platform.rect.collidepoint(self.rect.midright):
                    self.rect.right = platform.rect.left
                    self.rect.x += -10
                    self.direction = True
                if platform.rect.collidepoint(self.rect.midleft):
                    self.rect.left = platform.rect.right
                    self.rect.x += 10
                    self.direction = False

                if platform.rect.collidepoint(self.rect.midbottom):
                    self.velocity_y = 0
                    self.rect.bottom = platform.rect.top

            for block in area:
                if block.rect.collidepoint(self.rect.midbottom):
                    self.direction = not self.direction

            if self.rect.y > 10000:
                self.kill()

        if pg.time.get_ticks() - self.timer > self.interval:
            self.current_image += 1
            if self.current_image >= len(self.current_animation):
                if self.current_animation == self.boom_animation:
                    self.kill()
                self.current_image = 0
            self.image = self.current_animation[self.current_image]
            self.timer = pg.time.get_ticks()


class Worm(pg.sprite.Sprite):
    def __init__(self, spawn):
        pg.sprite.Sprite.__init__(self)

        self.load_animation()

        self.current_animation = self.running_animation_right
        self.image = self.current_animation[0]
        self.current_image = 0

        self.rect = self.image.get_rect()
        self.spawn = spawn
        self.rect.topleft = self.spawn  # Начальное положение
        self.direction = True

        # Начальная скорость и гравитация
        self.velocity_x = 0
        self.velocity_y = 0
        self.gravity = get_gravity(FPS)

        self.interval = 100
        self.timer = pg.time.get_ticks()

    def load_animation(self):
        tile_size = 32
        tile_scale = TILE_SIZE / 2

        self.running_animation_right = []

        spritesheet = pg.image.load('resourses/images/worm/Movement_(32 x 32).png')

        tile_numbers = 3
        for i in range(tile_numbers):
            x = i * tile_size
            y = 0
            rect = pg.Rect(x, y, tile_size, tile_size)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_size * tile_scale, tile_size * tile_scale))
            self.running_animation_right.append(image)

        self.running_animation_left = [pg.transform.flip(image, True, False) for image in self.running_animation_right]

    def update(self, platforms, area):
        if self.direction:
            self.current_animation = self.running_animation_right
            self.velocity_x = -3
        else:
            self.current_animation = self.running_animation_left
            self.velocity_x = 3

        new_x = self.rect.x + self.velocity_x
        self.rect.x = new_x

        self.velocity_y += self.gravity
        self.rect.y += self.velocity_y

        for platform in platforms:
            if platform.rect.collidepoint(self.rect.midright):
                self.rect.right = platform.rect.left
                self.rect.x += -10
                self.direction = True
            if platform.rect.collidepoint(self.rect.midleft):
                self.rect.left = platform.rect.right
                self.rect.x += 10
                self.direction = False

            if platform.rect.collidepoint(self.rect.midbottom):
                self.velocity_y = 0
                self.rect.bottom = platform.rect.top

        for block in area:
            if block.rect.collidepoint(self.rect.midbottom):
                self.direction = not self.direction

        if self.rect.y > 10000:
            self.kill()

        if pg.time.get_ticks() - self.timer > self.interval:
            self.current_image += 1
            if self.current_image >= len(self.current_animation):
                self.current_image = 0
            self.image = self.current_animation[self.current_image]
            self.timer = pg.time.get_ticks()


class Black_Hole(pg.sprite.Sprite):
    def __init__(self, spawn):
        pg.sprite.Sprite.__init__(self)

        self.load_animation()

        self.current_animation = self.spawn_animation
        self.image = self.current_animation[0]
        self.current_image = 0

        self.rect = self.image.get_rect()
        self.spawn = spawn
        self.rect.topleft = self.spawn  # Начальное положение

        # Начальная скорость
        self.velocity_x = 0

        self.interval = 150
        self.timer = pg.time.get_ticks()

    def load_animation(self):
        tile_size = 32
        tile_scale = TILE_SIZE / 2

        self.spawn_animation = []

        tile_numbers = 6
        for i in range(tile_numbers):
            self.spawn_animation.append(load_image(f'resourses/images/black hole/spawn {i + 1}.png', tile_size * tile_scale, tile_size * tile_scale))

    def update(self):
        if self.current_image >= len(self.current_animation):
            self.velocity_x = -15

        new_x = self.rect.x + self.velocity_x
        self.rect.x = new_x

        if self.rect.x < -100:
            self.kill()

        if pg.time.get_ticks() - self.timer > self.interval:
            self.current_image += 1
            if not self.current_image >= len(self.current_animation):
                self.image = self.current_animation[self.current_image]
                self.timer = pg.time.get_ticks()


class Platform(pg.sprite.Sprite):
    def __init__(self, image, coords, width, height, animated=False, tile_numbers=0, tile_size=1):
        pg.sprite.Sprite.__init__(self)
        self.animated = animated
        if self.animated:
            self.load_animation(image, tile_numbers, width, height, tile_size)
            self.image = self.animation[0]
            self.current_image = 0
            self.timer = pg.time.get_ticks()
            self.interval = 300
        else:
            self.image = pg.transform.scale(image, (width * TILE_SIZE, height * TILE_SIZE))
        self.mask = pg.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.topleft = coords

    def load_animation(self, image, tile_numbers, tile_width, tile_height, tile_size):
        self.animation = []

        spritesheet = image

        tile_numbers = tile_numbers
        for i in range(tile_numbers):
            x = i * tile_width
            y = 0
            rect = pg.Rect(x, y, tile_width, tile_height)
            image = spritesheet.subsurface(rect)
            image = pg.transform.scale(image, (tile_width * tile_size, tile_height * tile_size))
            self.animation.append(image)

    def update(self):
        if self.animated:
            if pg.time.get_ticks() - self.timer > self.interval:
                self.current_image += 1
                if self.current_image >= len(self.animation):
                    self.current_image = 0
                self.image = self.animation[self.current_image]
                self.timer = pg.time.get_ticks()


class AreaBlock(pg.sprite.Sprite):
    def __init__(self, coords):
        pg.sprite.Sprite.__init__(self)
        self.rect = pg.Rect(0, 0, 40, 40)
        self.rect.topleft = coords


class Button:
    def __init__(self, x, y, width=BUTTON_WIDTH, height=BUTTON_HEIGHT, func=None, image = 'resourses/images/menu/menu_button.png'):
        self.image = load_image(image, width, height)
        self.rect = self.image.get_rect()
        self.rect.topleft = x, y

        self.is_pressed = False

        self.func = func

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self):
        ...

    def is_clicked(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_pressed = True
                self.func()
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.is_pressed = False


class Menu:
    def __init__(self, game):
        self.game = game
        self.menu_page = load_image('resourses/images/menu/menu.png', 400, 400)

        self.mode = 'main'
        self.quit = False

        self.right_button_image = pg.image.load('resourses/images/menu/right_button.png').convert_alpha()
        self.right_button_image = pg.transform.scale(self.right_button_image, (50, 50))
        self.left_button_image = pg.transform.flip(self.right_button_image, True, False)

        buy_jump_button = Button(SCREEN_WIDTH // 2 - BUTTON_WIDTH, SCREEN_HEIGHT // 2 + 100 - BUTTON_HEIGHT,  height=int(BUTTON_HEIGHT*2), width=int(BUTTON_WIDTH*2), func=self.buy_jump, image='resourses/images/menu/jump_bust_button.png')
        buy_health_button = Button(SCREEN_WIDTH // 2 - BUTTON_WIDTH, SCREEN_HEIGHT // 2 - 100 - BUTTON_HEIGHT,  height=int(BUTTON_HEIGHT*2), width=int(BUTTON_WIDTH*2), func=self.buy_health, image='resourses/images/menu/heart.png')

        self.shop_buttons = [buy_jump_button, buy_health_button]

        settings_button = Button(SCREEN_WIDTH // 2 - BUTTON_WIDTH, SCREEN_HEIGHT // 2 + 100 - BUTTON_HEIGHT,  height=int(BUTTON_HEIGHT*2), width=int(BUTTON_WIDTH*2), func=self.settings_on, image='resourses/images/menu/settings_button.png')
        shop_button = Button(SCREEN_WIDTH // 2 - BUTTON_WIDTH, SCREEN_HEIGHT // 2 - 100 - BUTTON_HEIGHT,  height=int(BUTTON_HEIGHT*2), width=int(BUTTON_WIDTH*2), func=self.shop_on, image='resourses/images/menu/shop_button.png')

        self.main_buttons = [settings_button, shop_button]

        view_mode_button = Button(SCREEN_WIDTH // 2 - BUTTON_WIDTH, SCREEN_HEIGHT // 2 - 100 - BUTTON_HEIGHT,  height=int(BUTTON_HEIGHT*2), width=int(BUTTON_WIDTH*2), func=self.view_mode, image='resourses/images/menu/view_mode_button.png')
        left_resolution_button = Button(SCREEN_WIDTH // 2 - BUTTON_WIDTH * 2, SCREEN_HEIGHT // 2 - 50 + BUTTON_HEIGHT,  height=int(BUTTON_HEIGHT), width=int(BUTTON_WIDTH), func=self.previous_resolution, image='resourses/images/menu/right_button.png')
        right_resolutin_button = Button(SCREEN_WIDTH // 2 + BUTTON_WIDTH, SCREEN_HEIGHT // 2 - 50 + BUTTON_HEIGHT,  height=int(BUTTON_HEIGHT), width=int(BUTTON_WIDTH), func=self.next_resolution, image='resourses/images/menu/right_button.png')
        left_resolution_button.image = pg.transform.flip(left_resolution_button.image, True, False)

        self.settings_buttons = [view_mode_button, left_resolution_button, right_resolutin_button]

    def buy_jump(self):
        if self.game.player.money >= 100:
            self.game.player.jump_height += 5
            self.game.player.money -= 100

    def buy_health(self):
        if self.game.player.money >= 50:
            self.game.player.hp += 1
            self.game.player.money -= 50

    def settings_on(self):
        self.mode = 'settings'

    def shop_on(self):
        self.mode = 'shop'

    def view_mode(self):
        self.game.view_mode = not self.game.view_mode

    def previous_resolution(self):
        self.quit = True
        self.game.resolution -= 1
        if self.game.resolution < 0:
            self.game.resolution = len(RESOLUTIONS) - 1

    def next_resolution(self):
        self.quit = True
        self.game.resolution += 1
        if self.game.resolution > len(RESOLUTIONS) - 1:
            self.game.resolution = 0

    def update(self):
        for button in self.buttons:
            button.update()

    def is_clicked(self, event):
        if self.mode == 'main':
            for button in self.main_buttons:
                button.is_clicked(event)
        elif self.mode == 'shop':
            for button in self.shop_buttons:
                button.is_clicked(event)
        elif self.mode == 'settings':
            for button in self.settings_buttons:
                button.is_clicked(event)

    def draw(self, screen):
        screen.blit(self.menu_page, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 200))

        if self.mode == 'main':
            for button in self.main_buttons:
                button.draw(screen)
        if self.mode == 'shop':
            for button in self.shop_buttons:
                button.draw(screen)
        if self.mode == 'settings':
            for button in self.settings_buttons:
                button.draw(screen)
            text = text_render(f'{RESOLUTIONS[self.game.resolution][0]}X{RESOLUTIONS[self.game.resolution][1]}', 'brown')
            text_rect = text.get_rect()
            text_rect.center = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10 + BUTTON_HEIGHT
            screen.blit(text_render(f'{RESOLUTIONS[self.game.resolution][0]}X{RESOLUTIONS[self.game.resolution][1]}', 'brown'), text_rect)


class Game:
    def __init__(self):
        global SCREEN_WIDTH, SCREEN_HEIGHT
        with open('save.json', encoding='utf-8') as f:
            data = json.load(f)
            self.data = data

        self.resolution = self.data['settings']['resolution']
        SCREEN_WIDTH = RESOLUTIONS[self.resolution][0]
        SCREEN_HEIGHT = RESOLUTIONS[self.resolution][1]

        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.bg = load_image('Tiled Projects/tiles/Legacy Adventure Pack - RUINS/Assets/Background_1.png', SCREEN_WIDTH, SCREEN_HEIGHT)
        self.heart = pg.image.load('resourses/images/heart/heart.png').convert_alpha()
        self.heart = pg.transform.scale(self.heart, (30, 30))

        self.menu = Menu(self)

        self.view_mode = self.data['settings']['view_mode']

        button_x = SCREEN_WIDTH - BUTTON_WIDTH - PADDING
        self.buttons = [Button(button_x, PADDING + 30, func=self.menu_on)]

        self.setup()

    def setup(self):
        self.mode = 'game'
        pg.display.set_caption("Платформер")
        self.clock = pg.time.Clock()
        self.is_running = False

        self.tmx_map = pytmx.load_pygame('Tiled Projects/level.tmx')

        self.camera_x = 0
        self.camera_y = 0

        self.all_sprites = pg.sprite.Group()
        self.platforms = pg.sprite.Group()
        self.checkpoints = pg.sprite.Group()
        self.portals = pg.sprite.Group()
        self.spikes = pg.sprite.Group()
        self.coins = pg.sprite.Group()
        self.bombs = pg.sprite.Group()
        self.worms = pg.sprite.Group()
        self.black_holes = pg.sprite.Group()
        self.black_holes_timer = pg.time.get_ticks()
        self.black_holes_interval = 3000
        self.area_blocks = pg.sprite.Group()

        self.map_width = self.tmx_map.width * self.tmx_map.tilewidth * TILE_SIZE
        self.map_height = self.tmx_map.height * self.tmx_map.tileheight * TILE_SIZE

        self.player = Player(self.map_width, self.map_height)
        self.all_sprites.add(self.player)
        self.player.money = 0

        for x, y, gid in self.tmx_map.get_layer_by_name('level'):
            tile = self.tmx_map.get_tile_image_by_gid(gid)
            if tile:
                platform = Platform(tile, (x * self.tmx_map.tilewidth * TILE_SIZE, y * self.tmx_map.tileheight * TILE_SIZE), self.tmx_map.tilewidth, self.tmx_map.tileheight)
                self.platforms.add(platform)
                self.all_sprites.add(platform)

        try:
            for x, y, gid in self.tmx_map.get_layer_by_name('portals'):
                tile = self.tmx_map.get_tile_image_by_gid(gid)
                if tile:
                    platform = Platform(pg.image.load('resourses/images/portal/Green Portal Sprite Sheet.png'), (x * self.tmx_map.tilewidth * TILE_SIZE - 32, y * self.tmx_map.tileheight * TILE_SIZE - 64), 64, 64, True, 8, 2.5)
                    self.portals.add(platform)
                    self.all_sprites.add(platform)
        except:
            print('Portals not found')

        try:
            for x, y, gid in self.tmx_map.get_layer_by_name('enemys area'):
                tile = self.tmx_map.get_tile_image_by_gid(gid)
                if tile:
                    area = AreaBlock((x * self.tmx_map.tilewidth * TILE_SIZE, y * self.tmx_map.tileheight * TILE_SIZE))
                    self.area_blocks.add(area)
        except:
            print('Area not found')

        try:
            for x, y, gid in self.tmx_map.get_layer_by_name('bombs'):
                tile = self.tmx_map.get_tile_image_by_gid(gid)
                if tile:
                    enemy = Bomb((x * self.tmx_map.tilewidth * TILE_SIZE, y * self.tmx_map.tileheight * TILE_SIZE))
                    self.bombs.add(enemy)
                    self.all_sprites.add(enemy)
        except:
            print('Bombs not found')

        try:
            for x, y, gid in self.tmx_map.get_layer_by_name('worms'):
                tile = self.tmx_map.get_tile_image_by_gid(gid)
                if tile:
                    enemy = Worm((x * self.tmx_map.tilewidth * TILE_SIZE, y * self.tmx_map.tileheight * TILE_SIZE))
                    self.worms.add(enemy)
                    self.all_sprites.add(enemy)
        except:
            print('Worms not found')

        self.black_holes_spawns = []
        try:
            for x, y, gid in self.tmx_map.get_layer_by_name('black holes'):
                tile = self.tmx_map.get_tile_image_by_gid(gid)
                if tile:
                    enemy = Black_Hole((x * self.tmx_map.tilewidth * TILE_SIZE, y * self.tmx_map.tileheight * TILE_SIZE))
                    self.black_holes_spawns.append((x * self.tmx_map.tilewidth * TILE_SIZE, y * self.tmx_map.tileheight * TILE_SIZE))
                    self.black_holes.add(enemy)
                    self.all_sprites.add(enemy)
        except:
            print('Black holes not found')

        try:
            for x, y, gid in self.tmx_map.get_layer_by_name('ghosts'):
                tile = self.tmx_map.get_tile_image_by_gid(gid)
                if tile:
                    platform = Platform(tile, (x * self.tmx_map.tilewidth * TILE_SIZE, y * self.tmx_map.tileheight * TILE_SIZE), self.tmx_map.tilewidth, self.tmx_map.tileheight)
                    self.all_sprites.add(platform)
        except:
            print('Ghosts not found')

        try:
            for x, y, gid in self.tmx_map.get_layer_by_name('spikes'):
                tile = self.tmx_map.get_tile_image_by_gid(gid)
                if tile:
                    platform = Platform(tile, (x * self.tmx_map.tilewidth * TILE_SIZE, y * self.tmx_map.tileheight * TILE_SIZE), self.tmx_map.tilewidth, self.tmx_map.tileheight)
                    self.spikes.add(platform)
                    self.all_sprites.add(platform)
        except:
            print('Spikes not found')

        try:
            for x, y, gid in self.tmx_map.get_layer_by_name('checkpoints'):
                tile = self.tmx_map.get_tile_image_by_gid(gid)
                if tile:
                    platform = Platform(pg.image.load('resourses/images/flag/Flag.png'), (x * self.tmx_map.tilewidth * TILE_SIZE, y * self.tmx_map.tileheight * TILE_SIZE - self.tmx_map.tileheight // 2), 48, 48, True, 4)
                    self.checkpoints.add(platform)
                    self.all_sprites.add(platform)
        except:
            print('Checkpoints not found')

        try:
            for x, y, gid in self.tmx_map.get_layer_by_name('coins'):
                tile = self.tmx_map.get_tile_image_by_gid(gid)
                if tile:
                    platform = Platform(pg.image.load('resourses/images/coins/Coin.png'), (x * self.tmx_map.tilewidth * TILE_SIZE + self.tmx_map.tilewidth - 10, y * self.tmx_map.tileheight * TILE_SIZE + self.tmx_map.tileheight - 10), 10, 10, True, 4, 2.5)
                    self.coins.add(platform)
                    self.all_sprites.add(platform)
        except:
            print('Coins not found')

        self.run()

    def menu_on(self):
        self.mode = 'menu'
        self.menu.mode = 'main'

    def save(self):
        self.data['settings']['resolution'] = self.resolution
        self.data['settings']['view_mode'] = self.view_mode
        with open('save.json', 'w', encoding='utf-8') as outdata:
            json.dump(self.data, outdata, ensure_ascii=False)

    def run(self):
        self.is_running = True
        while self.is_running:
            self.event()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pg.quit()
        quit()

    def event(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.save()
                self.is_running = False
            if self.mode == 'game over':
                if event.type == pg.KEYDOWN:
                    self.setup()
            if self.mode == 'game':
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_e:
                        self.player.attack(self.all_sprites)
                    if event.key == pg.K_p:
                        self.setup()
                for button in self.buttons:
                    button.is_clicked(event)
            elif self.mode == 'menu':
                self.menu.is_clicked(event)
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        if self.menu.quit:
                            self.save()
                            self.is_running = False
                        self.mode = 'game'

    def update(self):
        if self.player.hp <= 0:
            self.mode = 'game over'
            return

        if self.mode == 'winner':
            return

        if self.mode == 'game':
            self.bombs.update(self.platforms, self.area_blocks)
            self.coins.update()
            self.checkpoints.update()
            self.portals.update()
            self.worms.update(self.platforms, self.area_blocks)
            self.black_holes.update()
            if self.black_holes_timer + self.black_holes_interval <= pg.time.get_ticks():
                self.black_holes_timer = pg.time.get_ticks()
                for spawn in self.black_holes_spawns:
                    enemy = Black_Hole(spawn)
                    self.black_holes.add(enemy)
                    self.all_sprites.add(enemy)

            self.player.update(self.platforms, self.coins, self.checkpoints)
            self.player.fireballs.update()
            pg.sprite.groupcollide(self.player.fireballs, self.platforms, True, False)
            pg.sprite.groupcollide(self.player.fireballs, self.worms, True, True)
            pg.sprite.groupcollide(self.player.fireballs, self.bombs, True, True)

            hits = pg.sprite.spritecollide(self.player, self.bombs, False)
            for hit in hits:
                hit.current_animation = hit.boom_animation
                self.player.get_damage(3)

            hits = pg.sprite.spritecollide(self.player, self.worms, False)
            for hit in hits:
                self.player.get_damage(1)

            hits = pg.sprite.spritecollide(self.player, self.spikes, False)
            for hit in hits:
                self.player.get_damage(2)
                self.player.rect.center = self.player.spawn

            hits = pg.sprite.spritecollide(self.player, self.black_holes, False)
            for hit in hits:
                self.player.get_damage(2)

            hits = pg.sprite.spritecollide(self.player, self.portals, False, pg.sprite.collide_mask)
            for hit in hits:
                self.mode = 'winner'

            if self.view_mode:
                self.camera_x = (self.player.rect.centerx - 100) // (SCREEN_WIDTH - 200) * (SCREEN_WIDTH - 200)
                self.camera_y = (self.player.rect.centery - 50) // (SCREEN_HEIGHT - 100) * (SCREEN_HEIGHT - 100)
            else:
                self.camera_x = self.player.rect.centerx - SCREEN_WIDTH // 2
                self.camera_y = self.player.rect.centery - SCREEN_HEIGHT // 2

            self.camera_x = max(0, min(self.camera_x, self.map_width - SCREEN_WIDTH))
            self.camera_y = max(0, min(self.camera_y, self.map_height - SCREEN_HEIGHT))

    def draw(self):
        self.screen.blit(self.bg, (0, 0))

        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, sprite.rect.move(-self.camera_x, -self.camera_y))

        for button in self.buttons:
            button.draw(self.screen)

        for i in range(self.player.hp):
            self.screen.blit(self.heart, (SCREEN_WIDTH + (i + 1) * -30, 0))

        self.screen.blit(text_render(self.player.money, 'yellow'), (0, 0))
        self.screen.blit(text_render(self.player.fireballs_count, 'red'), (0, 30))

        if self.mode == 'winner':
            self.screen.blit(text_render('WINNER', 'yellow'), (SCREEN_WIDTH//2-50, SCREEN_HEIGHT//2-10))
            self.screen.blit(text_render(f'you have {self.player.money} money', 'yellow'), (SCREEN_WIDTH//2-150, SCREEN_HEIGHT//2-50))

        if self.mode == 'game over':
            self.screen.blit(text_render('GAME OVER', 'red'), (SCREEN_WIDTH//2-100, SCREEN_HEIGHT//2-10))

        if self.mode == 'menu':
            self.menu.draw(self.screen)

        pg.display.flip()


if __name__ == "__main__":
    game = Game()
