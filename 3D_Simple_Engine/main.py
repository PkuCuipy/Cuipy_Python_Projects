import pygame
from pygame.locals import *
import sys
import math
import random

"""
问题日志:
[6.22]
    1. 如果三角形的一部分在视野后方，如何处理？
    2. 如果三角形的一部分在视野前方，但超出视野过多，会很占用资源，可以计算与显示器边缘的交点，然后绘制新得到的多边形...
    3. 我们可以给三角形用右手定则定义"正方向向量". 对于组成一个正方体的12个三角形而言，我们只需要渲染正方向向量和视线方向点积<0的

更新日志:
[6.25]
    1. 使用f2i函数, 将float规范为int, 增加兼容性
    2. adapt函数更名为Cl2Sc 表示从Clip_Space([-1,1]x[-1,1])到Screen_Space空间 的坐标伸缩变换
    3. 增加render_queue 并激活camera的返回值'depth', 现在可以按深度顺序渲染了!
        
"""



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

        # 超出视野"过多(>10)",则返回None
        if abs(u_) > 10 or abs(v_) > 10:
            # print(round(u_), round(v_), "（超出视野）")
            return None

        return {'pos': (u_, v_), 'depth': depth}

    return camera



"""
基础空间图形类:
(坐标采用高中数学定义的右手系, z轴向上)
Point: 空间点
Line: 空间线段
Triangle: 空间三角形
"""
class Point:
    def __init__(self, pos, color):
        self.pos = pos
        self.color = color


class Line:
    def __init__(self, A_pos, B_pos, color, width = 1):
        self.A_pos = A_pos
        self.B_pos = B_pos
        self.color = color
        self.center_pos = [(A_pos[_] + B_pos[_]) / 2 for _ in range(3)] # 重心


class Triangle:
    def __init__(self, A_pos, B_pos, C_pos, color):
        self.A_pos = A_pos
        self.B_pos = B_pos
        self.C_pos = C_pos
        self.color = color
        self.center_pos = [(A_pos[_] + B_pos[_] + C_pos[_]) / 3 for _ in range(3)] # 重心


"""
用于渲染的2D的 ScreenSpace 的点、线段和三角形
采用PyGame的2D坐标系: x右 y下

"""
class SSPoint:
    def __init__(self, pos, color, depth):
        self.pos = pos
        self.color = color
        self.depth = depth

class SSLine:
    def __init__(self, A_pos, B_pos, color, depth, width=1):
        self.A_pos = A_pos
        self.B_pos = B_pos
        self.color = color
        self.width = width
        self.depth = depth


class SSTriangle:
    def __init__(self, A_pos, B_pos, C_pos, color, depth):
        self.A_pos = A_pos
        self.B_pos = B_pos
        self.C_pos = C_pos
        self.color = color
        self.depth = depth


class McStyleCube:
    # MineCraft风格的方块类，本质上是12个Triangle和12个Line的组合
    def __init__(self, position, surface_color, line_color=(255,255,255), size=1):
        """
        :param position: (x,y,z): 表示了一个[x,y,z]->[x+size,y+size,z+size]的正方体
        :param surface_color: color[r,g,b] of [xp,xn,yp,yn,zp,zn] (目前只支持六个面同色)
        :param line_color: 边框颜色,默认为白色
        :param size: 方块大小, 默认就是1, 最好不要改
        """
        self.pos = position
        self.size = size
        self.surface_color = surface_color
        self.line_color = line_color
        x, y, z = position
        posA = (x,y,z)
        posB = (x+size,y,z)
        posC = (x+size,y+size,z)
        posD = (x,y+size,z)
        posE = (x,y,z+size)
        posF = (x+size,y,z+size)
        posG = (x+size,y+size,z+size)
        posH = (x,y+size,z+size)
        self.triangles = [ # 这里三角形的三个顶点要满足第三个点和第一个点的连线是正方形的对角线！
            Triangle(posA, posE, posF, surface_color), Triangle(posA, posB, posF, surface_color),
            Triangle(posE, posA, posD, surface_color), Triangle(posE, posH, posD, surface_color),
            Triangle(posA, posB, posC, surface_color), Triangle(posA, posD, posC, surface_color),
            Triangle(posB, posC, posG, surface_color), Triangle(posB, posF, posG, surface_color),
            Triangle(posE, posF, posG, surface_color), Triangle(posE, posH, posG, surface_color),
            Triangle(posC, posD, posH, surface_color), Triangle(posC, posG, posH, surface_color),
        ]
        self.lines = [
            Line(posA, posB, line_color), Line(posB, posC, line_color), Line(posC, posD, line_color), Line(posD, posA, line_color),
            Line(posE, posF, line_color), Line(posF, posG, line_color), Line(posG, posH, line_color), Line(posH, posE, line_color),
            Line(posA, posE, line_color), Line(posB, posF, line_color), Line(posC, posG, line_color), Line(posD, posH, line_color),
        ]





# 颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = GREY = (128, 128, 128)
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




items = [] # 空间物体集合

# 生成一个点阵正方体
X, Y, Z = 11, 11, 11
for i in range(X):
    for j in range(Y):
        for k in range(Z):
            items.append(Point([i / 10, j / 10, k / 10], [i * 255 // X, j * 255 // Y, k * 255 // Z]))
# 生成地面
for i in range(0, 30):
    for j in range(0, 30):
        items.append(Point([i, j, 0], [255, 255, 255]))

# 生成mc风格方块
items.append(McStyleCube((10,10,0),WHITE))
items.append(McStyleCube((10,10,1),GREY))
items.append(McStyleCube((10,10,2),WHITE))
items.append(McStyleCube((11,10,0),RED))
items.append(McStyleCube((10,12,0),GREEN))
items.append(McStyleCube((10,12,1),BLUE))




# 将float四舍五入为int
def f2i(x: float) -> int:
    return int(x + 0.5)

# (0,1)×(0,1) -> (-WIN_SIZE[0], WIN_SIZE[0])×(-WIN_SIZE[1], WIN_SIZE[1])
def Cl2Sc(pos):
    if pos:
        x, y = pos
        return f2i(x * WIN_SIZE[0] / 2 + WIN_SIZE[0] / 2), f2i(y * (-WIN_SIZE[1] / 2) + WIN_SIZE[1] / 2)
    return None





pygame.init() # 初始化pygame
screen = pygame.display.set_mode(WIN_SIZE) # 设置窗口大小
pygame.display.set_caption(CAPTION) # 设置标题

clock = pygame.time.Clock() # 计时器
pygame.mouse.set_visible(False) # 鼠标不可见
pygame.mouse.set_pos(f2i(WIN_SIZE[0] / 2), f2i(WIN_SIZE[1] / 2)) # 鼠标初始位置
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
    pygame.mouse.set_pos(f2i(WIN_SIZE[0] / 2), f2i(WIN_SIZE[1] / 2))

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


    # 遍历空间中的物体, 将确保合法的、需要绘制的点、线段和三角形添加进渲染队列
    render_queue = [] # 渲染队列

    for item in items:
        if type(item) == Triangle:
            # 获取camera的返回值
            A_data, B_data, C_data = cam(item.A_pos), cam(item.B_pos), cam(item.C_pos)
            # 三个顶点的返回值全部合法, 则加入队列
            if A_data and B_data and C_data:
                render_queue.append(SSTriangle(A_pos, B_pos, C_pos, item.color, average_depth))
                # 计算三个顶点的SS坐标
                A_pos = Cl2Sc(A_data['pos'])
                B_pos = Cl2Sc(B_data['pos'])
                C_pos = Cl2Sc(C_data['pos'])
                # 计算三个顶点的深度信息, 取平均, 代表整个三角形的深度信息
                average_depth = (A_data['depth'] + B_data['depth'] + C_data['depth']) / 3


        elif type(item) == Point:
            # 获取camera的返回值
            A_data = cam(item.pos)
            if A_data: # 返回值有效
                # 计算点的位置
                pos = Cl2Sc(A_data['pos'])
                dep = A_data['depth']
                render_queue.append(SSPoint(pos, item.color, dep))

        elif type(item) == McStyleCube:
            for tri in item.triangles:
                # 获取camera的返回值
                A_data, B_data, C_data = cam(tri.A_pos), cam(tri.B_pos), cam(tri.C_pos)
                # 顶点全部合法, 加入渲染队列
                if A_data and B_data and C_data:
                    # 计算三个顶点的SS坐标
                    A_pos = Cl2Sc(A_data['pos'])
                    B_pos = Cl2Sc(B_data['pos'])
                    C_pos = Cl2Sc(C_data['pos'])
                    # 计算三个顶点的深度信息, 取平均, 代表整个三角形的深度信息
                    average_depth = (A_data['depth'] + B_data['depth'] + C_data['depth']) / 3
                    # 推入队列
                    render_queue.append(SSTriangle(A_pos, B_pos, C_pos, tri.color, average_depth))



    # 渲染队列的SS对象排序
    render_queue.sort(key=lambda x: x.depth, reverse=True)


    # 渲染队列中的SS对象
    for item in render_queue:
        if type(item) == SSPoint:
            pygame.draw.circle(screen, item.color, item.pos, 3)
        if type(item) == SSLine:
            pass
        if type(item) == SSTriangle:
            pygame.draw.polygon(screen, item.color, (item.A_pos, item.B_pos, item.C_pos))




    pygame.display.flip()

    # 限制帧率
    clock.tick(60)
