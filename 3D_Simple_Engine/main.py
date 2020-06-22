import pygame
from pygame.locals import *
import sys
import math
import random


def get_camera(position, target, fov_h=0.4 * math.pi, fov_v=0.4 * math.pi):
    """
    :param position: Camera_position_in_R^3
    :param target: View_vec
    :param fov_h: 水平视野大小(Field of View Horizontal)
    :param fov_v: 垂直视野大小(Field of View Vertical)
    :return: Function: camera
    感性而言，就是依据"架设位置"、"镜头朝向"、"视角度"，架设一个Camera，它能给出R^3中的物体在Camera的光屏上的成像(位置)信息
    """
    pos_x, pos_y, pos_z = position
    target_a, target_b, target_c = target

    def camera(relative_object_position, dist=1):
        """
        :param relative_object_position: (物体在以pos_x,pos_y,pos_z为原点的R^3平移坐标系中的坐标)
        :param dist: 光屏到传感器距离
        :return: 正常情况返回一个(-1,1)×(-1,1)的坐标(u,v), 表示其在光屏的相对位置
        """
        # 简记名称
        rel_obj_x, rel_obj_y, rel_obj_z = relative_object_position
        (x, y, z) = (rel_obj_x - pos_x, rel_obj_y - pos_y, rel_obj_z - pos_z)
        (a, b, c) = (target_a, target_b, target_c)
        # 计算obj在CameraSpace的坐标 x_, y_, z_
        z_ = a * x + b * y + c * z
        if z_ <= 0:  # obj在摄像机后方, 超出视野
            return None
        sr = math.sqrt(a ** 2 + b ** 2)  # 预存平方根, 减少重复计算
        x_ = (x * b - a * y) / sr
        y_ = (-a * c * x - b * c * y) / sr + z * sr
        # 计算obj在光屏上的像在光屏上的相对坐标(∈(0,1)×(0,1))
        view_max_H = math.tan(fov_h / 2) * dist
        view_max_V = math.tan(fov_v / 2) * dist
        u_ = x_ / z_ * dist / view_max_H
        v_ = y_ / z_ * dist / view_max_V
        depth = z_  # 暂时不考虑

        # # 超出视野则返回None
        # if abs(u_) > 1 or abs(v_) > 1:
        #     # print(round(u_), round(v_), "（超出视野）")
        #     return None

        # 超出视野"过多",则返回None
        if abs(u_) > 10 or abs(v_) > 10:
            # print(round(u_), round(v_), "（超出视野）")
            return None


        return u_, v_

    return camera


class Point:
    def __init__(self, position, color, movable=False, speed_vec=None):
        self.pos = position
        self.color = color
        self.movable = movable
        self.speed_vec = speed_vec

    def calc_dist(self, pos):
        return math.sqrt((self.pos[0] - pos[0]) ** 2 + (self.pos[1] - pos[1]) ** 2 + (self.pos[2] - pos[2]) ** 2)


class Triangle:
    def __init__(self, pos_A, pos_B, pos_C, line_color, surface_color):
        """
        :param pos_A: [A_x, A_y, A_z]
        :param pos_B: [B_x, B_y, B_z]
        :param pos_C: [C_x, C_y, C_z]
        :param line_color: AB/BC/CA 线段颜色 (r,g,b) 或 None
        :param surface_color: ∆ABC 填充色 (r,g,b) 或 None
        [注]: 采用 x-y-z空间坐标系 即高中数学中定义的右手笛卡尔系
        """
        self.pos_A = pos_A
        self.pos_B = pos_B
        self.pos_C = pos_C
        self.line_color = line_color
        self.surface_color = surface_color


# 颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
# 位置
pos_x, pos_y, pos_z = -1, -1, 0
# 垂直升降速度
speed_z = 0.05
# 前进速度
speed_move = 0.05
# 视线方向
phi, theta = math.pi / 2, math.pi / 4
# 视线旋转速度
speed_phi = 0.05 * 8 / 9
speed_theta = 0.05 * 8 / 9
mouse_speed_phi = 0.002
mouse_speed_theta = 0.002
# 视角大小
FOV_H = 0.4 * math.pi
FOV_V = 0.4 * math.pi

# 窗口信息
WIN_SIZE = 1000, 700
CAPTION = "3D_Simple_Demo"

items = []
items.append(Triangle([1,0,0], [0,1,0], [0,0,1], BLACK, RED)) # 边框为黑色，填充红色的R^3中三角形
# 三角形如果有一部分在视野后方的解决方案还没有思路 先考虑最简单的Point的情况吧...

# 生成一个点阵正方体
X, Y, Z = 11, 11, 1
for i in range(X):
    for j in range(Y):
        for k in range(Z):
            items.append(Point([i / 10, j / 10, k / 10], [i * 255 // X, j * 255 // Y, k * 255 // Z]))
# 生成地面
for i in range(0, 10):
    for j in range(0, 10):
        items.append(Point([i, j, 0], [255, 255, 255]))


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
pygame.event.set_grab(False)
pygame.mouse.set_visible(False)
pygame.mouse.set_pos(WIN_SIZE[0] / 2, WIN_SIZE[1] / 2)
CENTER_POS = (WIN_SIZE[0] / 2, WIN_SIZE[1] / 2)

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_EQUALS:
                print()
                print(f"当前位置: x={round(pos_x, 3)}, y={round(pos_y, 3)}, z={round(pos_z, 3)}")
                print(f"视角方向: φ={round(phi / math.pi, 3)}π, θ={round(theta / math.pi, 3)}π")

    # 根据鼠标相对移动 更改视线方向
    current_mouse_pos = pygame.mouse.get_pos()  # 当前鼠标位置
    mouse_move_delta = current_mouse_pos[0] - CENTER_POS[0], current_mouse_pos[1] - CENTER_POS[1];  # 与上一帧的相对位移
    # 计算水平转动量
    theta = (theta - mouse_speed_theta * mouse_move_delta[0]) % math.tau
    # 计算垂直转动量
    if mouse_move_delta[1] > 0:
        phi = min(phi + mouse_speed_phi * mouse_move_delta[1], 0.999999 * math.pi)
    else:
        phi = max(phi + mouse_speed_phi * mouse_move_delta[1], 0.000001 * math.pi)
    # 鼠标位置reset
    pygame.mouse.set_pos(WIN_SIZE[0] / 2, WIN_SIZE[1] / 2)

    # 持续性键盘事件
    key_pressed = pygame.key.get_pressed()
    if key_pressed[K_SPACE]:  # 上升
        pos_z += speed_z
    if key_pressed[K_LSHIFT]:  # 下降
        pos_z -= speed_z
    if key_pressed[K_UP]:  # 视角向上
        phi = max(phi - speed_phi, 0.000001 * math.pi)
    if key_pressed[K_DOWN]:  # 视角向下
        phi = min(phi + speed_phi, 0.999999 * math.pi)
    if key_pressed[K_LEFT]:  # 视角向左
        theta = (theta + speed_theta) % math.tau
    if key_pressed[K_RIGHT]:  # 视角向右
        theta = (theta - speed_theta) % math.tau
    if key_pressed[K_w]:  # 沿视角方向平行于地面(x-y平面)前进
        pos_x += math.cos(theta) * speed_move
        pos_y += math.sin(theta) * speed_move
    if key_pressed[K_s]:  # 沿视角方向平行于地面(x-y平面)后退
        pos_x -= math.cos(theta) * speed_move
        pos_y -= math.sin(theta) * speed_move
    if key_pressed[K_d]:  # 右平移
        a = math.cos(theta)
        b = math.sin(theta)
        sr = math.sqrt(a * a + b * b)
        pos_x += speed_move * b / sr
        pos_y += -speed_move * a / sr
    if key_pressed[K_a]:  # 左平移
        a = math.cos(theta)
        b = math.sin(theta)
        sr = math.sqrt(a * a + b * b)
        pos_x -= speed_move * b / sr
        pos_y -= -speed_move * a / sr
    if key_pressed[K_LCTRL]: # 加速
        speed_move = 0.07
        # FOV_H = 0.45 * math.pi # 这里和下面的拉近视野有逻辑冲突，待解决
    if not key_pressed[K_LCTRL] and not key_pressed[K_w]: # 恢复正常速度
        speed_move = 0.05
        # FOV_H = 0.4 * math.pi
    if key_pressed[K_c]: # 拉近视野
        FOV_H = 0.1 * math.pi
        FOV_V = 0.1 * math.pi
    else: # 恢复正常视野
        FOV_H = 0.4 * math.pi
        FOV_V = 0.4 * math.pi

    # 背景填充色
    screen.fill(BLACK)

    # 建立Camera
    target_a = math.sin(phi) * math.cos(theta)
    target_b = math.sin(phi) * math.sin(theta)
    target_c = math.cos(phi)
    cam = get_camera([pos_x, pos_y, pos_z], [target_a, target_b, target_c], fov_h=FOV_H, fov_v=FOV_V)

    # 遍历空间中的物体, 计算其在光屏的坐标, 按比例放大后绘制,
    for item in items:
        if type(item) == Triangle:
            # 先计算三个顶点的位置
            A_pos = adapt(cam(item.pos_A))
            B_pos = adapt(cam(item.pos_B))
            C_pos = adapt(cam(item.pos_C))
            # 顶点全部合法才绘制
            if A_pos and B_pos and C_pos:
                # 绘制边框
                if item.line_color:
                    pygame.draw.aaline(screen, item.line_color, A_pos, B_pos, blend=1)
                    pygame.draw.aaline(screen, item.line_color, B_pos, C_pos, blend=1)
                    pygame.draw.aaline(screen, item.line_color, C_pos, A_pos, blend=1)
                # 填充内部
                if item.surface_color:
                    pygame.draw.polygon(screen, item.surface_color, [A_pos, B_pos, C_pos])

        elif type(item) == Point:
            # 如果太远了就不绘制了
            if item.calc_dist([pos_x, pos_y, pos_z]) > 200:
                continue
            # 先计算点的位置
            pos = adapt(cam(item.pos))
            # 在视野内则绘制
            if pos:
                pygame.draw.circle(screen, item.color, pos, 3)

    pygame.display.flip()

    # 限制帧率
    clock.tick(60)
