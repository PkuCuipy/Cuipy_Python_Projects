import pygame
from pygame.locals import *
import sys
import math
import random

"""
测试结论：
pygame的多边形绘制似乎完全运用CPU资源
当temp的值增加到240时，帧率已经下降到24fps
"""

# 颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# 窗口信息
WIN_SIZE = 1000, 700
CAPTION = "3D_Simple_Demo"



# (0,1)×(0,1) -> (-WIN_SIZE[0], WIN_SIZE[0])×(-WIN_SIZE[1], WIN_SIZE[1])
def adapt(pos):
    if pos:
        x, y = pos
        return x * WIN_SIZE[0] / 2 + WIN_SIZE[0] / 2, y * (-WIN_SIZE[1] / 2) + WIN_SIZE[1] / 2
    return None


pygame.init()
screen = pygame.display.set_mode(WIN_SIZE)
pygame.display.set_caption(CAPTION)

clock = pygame.time.Clock()
pygame.mouse.set_visible(True)
pygame.mouse.set_pos(WIN_SIZE[0] / 2, WIN_SIZE[1] / 2)
CENTER_POS = (WIN_SIZE[0] / 2, WIN_SIZE[1] / 2)

bomb_font = pygame.font.Font("../622尝试/myfont.otf", 30)

temp = 0
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            sys.exit()

    # 背景填充色
    screen.fill(BLACK)

    # 绘制一个不断拉长的三角形（渲染面积持续增大）
    temp += 1
    pygame.draw.polygon(screen, RED, [adapt((0, temp)), adapt((0.5, 0.5)), adapt((0, 0.5))])

    # 限制帧率
    clock.tick(60)

    # 屏幕左上角打印帧率
    print(clock.get_fps())
    bomb_text = bomb_font.render(str(int(clock.get_fps()+0.5)), True, WHITE)
    screen.blit(bomb_text, (10, 10))

    pygame.display.flip()

