import time
import math
import pygame
import random
import ctypes
import os.path
import sqlite3
from pygame.locals import *
import sys, pygame, pygame.mixer
from workWithDB import WorkWithDB

# получение хар-тик. экрана пользователя
user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
WIDTH, HEIGHT = screensize[0], screensize[1]

pygame.init()

# установка шрифта для игры
font_path = "data\\Mistral.ttf"
font_size = 30
font = pygame.font.Font(font_path, font_size)

# необходимые базовые настройки
pygame.display.set_caption("Paw-paw")
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# загрузка изображений
hero1 = pygame.image.load("data\\images\\cat1.png").convert_alpha()
hero2 = pygame.image.load("data\\images\\cat2.png").convert_alpha()

# загрузка звуков
shot = pygame.mixer.Sound("data\\music\\shot.wav")
shot.set_volume(0.3)
reload_gun = pygame.mixer.Sound("data\\music\\reload.wav")
reload_gun.set_volume(0.3)
out_bullets = pygame.mixer.Sound("data\\music\\out_pistol.wav")
out_bullets.set_volume(0.3)
pygame.mixer.music.load("data\\music\\bg_music.wav")
pygame.mixer.music.set_volume(0.1)
pygame.mixer.music.play(loops=-1)

# создание переменных с задним фоном
d = {}
for x in range(1, 5):
    d["bg{0}".format(x)] = pygame.transform.scale(
        pygame.image.load(f"data\\images\\paw_bg{x}.png").convert_alpha(),
        (WIDTH, HEIGHT),
    )
hero_x, hero_y = WIDTH // 2, HEIGHT // 2


# стартовый экран
def start_screen():
    # загрузка заднего фона
    fon = pygame.transform.scale(
        pygame.image.load("data\\images\\start_img.png").convert_alpha(),
        (WIDTH, HEIGHT),
    )
    screen.blit(fon, (0, 0))

    # создание rect'a кнопки
    button = pygame.Rect(WIDTH // 1.413, HEIGHT // 1.93, 312, 325)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                rect = pygame.Rect(event.pos, (1, 1))
                # нахождение пересечния нажатия курсора и кнопки
                if rect.colliderect(button):
                    return  # начинаем игру
        pygame.display.flip()
        clock.tick(1)


# класс главного героя
class HeroCat:
    # счёт, открытые тиры, разброс , магазин пистолета, ценность попадания
    score = 0
    shoot_ranges = 1
    spread = [-1, 3]
    magazine = 7
    price = 1

    def __init__(self, score, shoot_ranges, spread, magazine, price):
        HeroCat.shoot_ranges = shoot_ranges
        HeroCat.score = score
        HeroCat.spread = [int(str(spread)[:-1]), int(str(spread)[-1])]
        HeroCat.magazine = magazine
        HeroCat.price = price


# вызов стартового экрана
start_screen()

# проверка наличия БД с прогрессом
# и вызов класса ГГ c обычной/загруженной информацией
if not os.path.isfile("data\\progress.db"):
    WorkWithDB.create_database()
    WorkWithDB.add_elem("player", [0, 0, -13, 7, 1])
    HeroCat(0, 0, -13, 7, 1)
else:
    info = [x for x in WorkWithDB.load_info("player")][0]
    HeroCat(info[0], info[1], info[2], info[3], info[4])


def upgrade_menu():
    # загрузка меню
    fon = pygame.transform.scale(
        pygame.image.load("data\\images\\menu.png").convert_alpha(),
        (WIDTH, HEIGHT),
    )
    screen.blit(fon, (0, 0))

    # создание rect'a кнопки
    button1 = pygame.Rect(175, 220, 220, 200)
    button2 = pygame.Rect(750, 220, 220, 200)
    button3 = pygame.Rect(175, 540, 220, 200)
    button4 = pygame.Rect(750, 540, 220, 200)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                rect = pygame.Rect(event.pos, (1, 1))
                if rect.colliderect(button1):
                    a = HeroCat.price // 10
                    if HeroCat.score - (150 * a) >= 0:
                        HeroCat.score -= 150 * a
                        HeroCat.price += 10
                elif rect.colliderect(button2):
                    a = (HeroCat.magazine - 7) // 2
                    if HeroCat.score - (50 * a) >= 0:
                        HeroCat.score -= 50 * a
                        HeroCat.magazine += 2
                elif rect.colliderect(button3):
                    if HeroCat.score - 500 >= 0:
                        HeroCat.score -= 500
                        HeroCat.spread = [0, 0]
                elif rect.colliderect(button4):
                    # if HeroCat.score - 1000 >= 0:
                    HeroCat.shoot_ranges += 1
                    return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

        pygame.display.flip()
        clock.tick(1)


# класс мишени
class Target(pygame.sprite.Sprite):
    # движущаяся или статичная, номер дорожки
    def __init__(self, shoot_range, moving=False):
        super().__init__(group)
        self.moving = moving
        self.image = pygame.transform.scale(
            pygame.image.load("data\\images\\target.png").convert_alpha(),
            (50, 30),
        )
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(x=150, bottom=50)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, move_from, move_to):
        super().__init__(group)
        self.image = pygame.image.load("data\\images\\bullet.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (5, 21))
        # self.image = pygame.transform.rotate(self.image, angle)
        self.rect = self.image.get_rect(center=move_from)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        if not pygame.sprite.collide_mask(self, target):
            self.rect.y -= 10
        else:
            HeroCat.score += HeroCat.price
            self.rect.y -= 100

        # if random.randrange(-2, 1) >= 0:
        #     self.rect.x += random.randrange(HeroCat.spread[0], HeroCat.spread[1])
        # if (
        #     self.move_to[0] - 10 < self.rect.x < self.move_to[0] + 10
        #     and self.move_to[1] + 10 > self.rect.y > self.move_to[1] - 10
        # ):
        #     if self.rect.y >= self.move_to[1] + 10:
        #         self.rect.y -= 10
        #     if self.rect.x <= self.move_to[0]:
        #         self.rect.x += 10
        # else:
        #     if angle <= 0:
        #         self.rect.x += 10
        #     else:
        #         self.rect.x -= 10
        #     self.rect.y -= 10


running = True

remaining_bullets = HeroCat.magazine

group = pygame.sprite.Group()
target = Target(1)
green_zone = pygame.Rect(0, HEIGHT - 300, 500, 300)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break
        elif event.type == MOUSEBUTTONDOWN:
            # стрельба при наличии патронов
            if remaining_bullets > 0:
                # angle = (hero_x + 20 - event.pos[0]) / (hero_y - event.pos[1])
                # angle = math.degrees(math.atan(angle))
                # if -50 <= angle <= 50:
                shot.play()
                Bullet((hero_x + 20, hero_y), event.pos)
                remaining_bullets -= 1
            else:
                out_bullets.play()
        elif event.type == pygame.KEYDOWN:
            # перезарядка
            if event.key == pygame.K_r:
                if remaining_bullets == 0:
                    reload_gun.play()
                    remaining_bullets = HeroCat.magazine
            # выход из игры на esc
            if event.key == pygame.K_ESCAPE:
                running = False
                break
            # выключение/включение музыки
            if event.key == pygame.K_m:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.pause()
                else:
                    pygame.mixer.music.unpause()
            if event.key == pygame.K_q:
                if (pygame.Rect(hero_x, hero_y, 1, 1)).colliderect(green_zone):
                    upgrade_menu()

    key_pressed_is = pygame.key.get_pressed()

    # передвижение персонажа
    if key_pressed_is[K_a]:
        if hero_x - 5 >= 0:
            hero_x -= 5
    if key_pressed_is[K_d]:
        if hero_x + 5 <= WIDTH - 50:
            hero_x += 5
    if key_pressed_is[K_w]:
        if hero_y - 5 >= HEIGHT // 2 - 33:
            hero_y -= 5
    if key_pressed_is[K_s]:
        if hero_y + 5 <= HEIGHT - 93:
            hero_y += 5

    mx, my = pygame.mouse.get_pos()

    # отрисовка фона, игрока, пулей
    screen.fill(pygame.Color(0, 0, 0))
    screen.blit(d[f"bg{HeroCat.shoot_ranges + 1}"], (0, 0))
    screen.blit(hero1, (hero_x, hero_y))

    # отображение счёта игрока
    string_rendered = font.render(f"СЧЁТ: {HeroCat.score}", 1, pygame.Color("green"))
    intro_rect = string_rendered.get_rect()
    intro_rect.top = 5
    intro_rect.x = 5
    screen.blit(string_rendered, intro_rect)
    # отображение патронов
    if remaining_bullets != 0:
        string_rendered = font.render(
            f"{remaining_bullets} / {HeroCat.magazine}", 1, pygame.Color("green")
        )
        intro_rect = string_rendered.get_rect()
        intro_rect.top = HEIGHT - 40
        intro_rect.x = WIDTH - 80
    else:
        string_rendered = font.render(f"Нажмите R", 1, pygame.Color("red"))
        intro_rect = string_rendered.get_rect()
        intro_rect.top = HEIGHT - 40
        intro_rect.x = WIDTH - 130
    screen.blit(string_rendered, intro_rect)

    group.draw(screen)
    group.update()
    pygame.display.update()

    pygame.display.flip()
    clock.tick(60)

# обновление информации в БД
HeroCat.spread = int("".join(list(map(str, HeroCat.spread))))
info = [
    HeroCat.score,
    HeroCat.shoot_ranges,
    HeroCat.spread,
    HeroCat.magazine,
    HeroCat.price,
]
WorkWithDB.overwrite("player", info)


# made by aksenianets, capyzs
