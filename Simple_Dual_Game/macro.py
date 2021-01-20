import time
import pygame
import sys
import math
import threading
import socket
import struct
from macro import *


class Bullet:
    def __init__(self, belong_to_player, pos, v, lifetime):
        self.x, self.y = pos
        self.vx, self.vy = v   # 速度(像素/秒)
        self.belong_to_player = belong_to_player
        self.color = list(BULLET_COLOR)
        self.lifetime = lifetime
        self.last_frame_time = time.time()

    def active(self):
        return self.lifetime > 0

    def act(self):
        # 获得距离上一帧的时间. 因为帧率不一定永远60hz
        current_frame_time = time.time()
        delta_frame_time = current_frame_time - self.last_frame_time
        dt = delta_frame_time   # 简记

        # 自身寿命--
        self.lifetime -= dt

        # 根据自己的速度, 改变自己的位置
        self.x += self.vx * dt
        self.y += self.vy * dt

        # 如果自己的位置越界了, 子弹反弹, 寿命减半
        if self.x < 0:
            self.x = 0
            self.vx *= -1
            self.lifetime /= 2
        if self.x > WIN_WIDTH:
            self.x = WIN_WIDTH
            self.vx *= -1
            self.lifetime /= 2
        if self.y < 0:
            self.y = 0
            self.vy *= -1
            self.lifetime /= 2
        if self.y > WIN_HEIGHT:
            self.y = WIN_HEIGHT
            self.vy *= -1
            self.lifetime /= 2


        # 尝试攻击玩家
        global players
        if self.active():
            for p in players:
                if not p is self.belong_to_player:
                    self.try_hurt(p)

        # 修改自身颜色
        self.set_color()

        # 留着下一帧用
        self.last_frame_time = current_frame_time


    # 当自己的lifetime不足1s时, 颜色逐渐从纯黑变为和背景色相同
    def set_color(self):
        if self.lifetime >= FADE_OUT_THRESHOLD_SEC:
            self.color = [0, 0, 0]
        elif self.lifetime <= 0:
            self.color = list(BG_COLOR)
        else:
            c = BG_COLOR[0] * (FADE_OUT_THRESHOLD_SEC - self.lifetime)
            self.color = [c, c, c]

    def try_hurt(self, p):
        if p != self.belong_to_player:
            if math.dist((self.x, self.y), (p.x, p.y)) <= p.hitbox:
                p.damaged_by(self)      # 被攻击的玩家受伤
                self.lifetime = 0       # 自己**立即**失效(否则会重复判定)



class Player:
    def __init__(self, player_id, pos, v, hitbox, health):
        self.id = player_id
        self.x, self.y = pos
        self.vx, self.vy = v   # 速度(像素/秒)
        self.color = list(PLAYER_COLOR_DEFAULT)
        self.hitbox = hitbox
        self.health = health
        self.bullets = [Bullet(belong_to_player=self, pos=(0,0), v=(0,0), lifetime=0)
                                                                for _ in range(BULLET_MAX_AMOUNT_PER_PLAYER)]
        self.last_frame_time = time.time()

        # 为了提高性能, 每重新调用act(), 才强迫 dead_bullets_pos[] 更新
        self.inactive_bullets_pos = []   # 存放失活子弹在bullets[]中的下标
        self.recalc_bullets_inactive_pos = True


    def act(self, info):

        # 获得距离上一帧的时间. 因为帧率不一定稳定在60hz
        current_frame_time = time.time()
        delta_frame_time = current_frame_time - self.last_frame_time
        self.last_frame_time = current_frame_time  # 留着下一帧用
        dt = delta_frame_time  # 简记

        # 为了提高性能, 每重新调用act(), 才强迫 bullets_active[] 更新
        self.recalc_bullets_inactive_pos = True

        # [左键]: 自己发射一个子弹
        if info.get("LEFT_CLICK"):
            # 计算子弹发射的速度(矢量)
            vx = info["MOUSE_POS"][0] - self.x
            vy = info["MOUSE_POS"][1] - self.y
            length = math.sqrt(vx ** 2 + vy ** 2)
            while length == 0:
                vx, vy = 1, 1
                length = math.sqrt(vx ** 2 + vy ** 2)
            vx *= BULLET_SPEED_PER_SEC / length
            vy *= BULLET_SPEED_PER_SEC / length
            # 添加一个子弹
            self.activate_a_bullet(Bullet(self, (self.x, self.y), (vx, vy), BULLET_LIFETIME_SEC))

        # [右键]: 清除自己的所有子弹
        if info.get("RIGHT_CLICK"):
            for b in self.bullets:
                b.lifetime = min(b.lifetime, FADE_OUT_THRESHOLD_SEC)

        # [下滚轮]: 自己的子弹分裂
        if info.get("ROLL_DOWN"):
            for b in self.bullets:
                if b.active():
                    # 获取当前子弹的速度方向
                    alpha = math.atan(b.vy / b.vx)
                    point_to_left = (b.vx <= 0)   # 是否指向左侧. 因为tan本身不能区分这一点.
                    if point_to_left:   # 如果指向左侧, 应该给予一个 pi 的修正
                        alpha += math.pi
                    # 计算新子弹的速度(矢量)
                    alpha_new1 = alpha + DIVISION_ANGLE
                    alpha_new2 = alpha - DIVISION_ANGLE
                    v_new1 = BULLET_SPEED_PER_SEC * math.cos(alpha_new1), BULLET_SPEED_PER_SEC * math.sin(alpha_new1)
                    v_new2 = BULLET_SPEED_PER_SEC * math.cos(alpha_new2), BULLET_SPEED_PER_SEC * math.sin(alpha_new2)
                    # 创建新的子弹
                    self.activate_a_bullet(Bullet(b.belong_to_player, (b.x, b.y), v_new1, BULLET_LIFETIME_SEC))
                    self.activate_a_bullet(Bullet(b.belong_to_player, (b.x, b.y), v_new2, BULLET_LIFETIME_SEC))


        # 如果对应方向的键被按下, 执行对应方向的加速
        if info.get("W"): self.vy -= PLAYER_ACCELERATION_PER_SEC * dt
        if info.get("S"): self.vy += PLAYER_ACCELERATION_PER_SEC * dt
        if info.get("A"): self.vx -= PLAYER_ACCELERATION_PER_SEC * dt
        if info.get("D"): self.vx += PLAYER_ACCELERATION_PER_SEC * dt

        # 如果对应方向的键没有被按下, 执行对应方向的减速
        if not info.get("W") and not info.get("S"): self.vy *= (PLAYER_REDUCTION_PER_SEC ** dt)
        if not info.get("A") and not info.get("D"): self.vx *= (PLAYER_REDUCTION_PER_SEC ** dt)

        # 如果|速度|超过最大速度, 限制之
        current_speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        if current_speed > PLAYER_MAX_SPEED_PER_SEC:
            ratio = PLAYER_MAX_SPEED_PER_SEC / current_speed
            self.vx *= ratio
            self.vy *= ratio

        # 根据自己的速度, 改变自己的位置
        self.x += self.vx * dt
        self.y += self.vy * dt

        # 如果自己的位置越界了, 强行修正进来
        if self.x < 0: self.x = 0
        if self.x > WIN_WIDTH: self.x = WIN_WIDTH
        if self.y < 0: self.y = 0
        if self.y > WIN_HEIGHT: self.y = WIN_HEIGHT

        # 自己的子弹移动
        for i in self.bullets:
            i.act()

        # 设置自身颜色
        self.set_color();


    # 被子弹击中
    def damaged_by(self, bullet):
        self.health -= 1


    # 设置Player自身的颜色
    def set_color(self):
        health_ratio = max(0, min(1, self.health / PLAYER_HEALTH_DEFAULT))
        self.color[0] = int((1 - health_ratio) * 255)   # R
        self.color[1] = int(health_ratio * 255)         # G
        self.color[2] = 100                             # B


    # 统计
    def __get_inactive_bullets_list(self):
        if self.recalc_bullets_inactive_pos:   # 需要重新统计
            self.inactive_bullets_pos = []
            for index, b in enumerate(self.bullets):
                if not b.active():
                    self.inactive_bullets_pos.append(index)
            self.recalc_bullets_inactive_pos = False  # 避免再重复统计
        return self.inactive_bullets_pos


    # 通过把一个已经失效的子弹重置为b(bullet的缩写), 新添加一个子弹
    def activate_a_bullet(self, b):
        inactive_list = self.__get_inactive_bullets_list()
        if inactive_list:   # 如果尚有失效的可以让我们重新激活
            b.last_frame_time = time.time()
            self.bullets[inactive_list.pop()] = b


# Pygame 初始化
pygame.init()
screen = pygame.display.set_mode(WIN_SIZE)
main_running = True
server_game_start = False

# 限制帧率
clock = pygame.time.Clock()

# 鼠标
pygame.mouse.set_visible(False)     # 设置不可见
# pygame.event.set_grab(True)         # 设置鼠标不能移出程序窗口

# 多人游戏
MY_PLAYER_ID = int(input("请输入一个整数作为自己的ID(仅支持0或1):"))
my_receive_IP_port = ("192.168.1.100", 63128 + MY_PLAYER_ID)

# 添加自己和对方
me = Player(1028, WIN_CENTER, (0, 0), PLAYER_HITBOX_DEFAULT, PLAYER_HEALTH_DEFAULT)   # 自己角色
him = Player(1234, WIN_CENTER, (0, 0), PLAYER_HITBOX_DEFAULT, PLAYER_HEALTH_DEFAULT)  # 另一个玩家角色
players = list()
players.append(me)
players.append(him)




# 本地游戏主线程
def main():

    while True:

        #=========
        # 控制检测
        #=========

        # 发生的所有我们关心的信息
        me_info = dict()

        # 检测现在鼠标的位置
        mouse_pos = pygame.mouse.get_pos()
        me_info["MOUSE_POS"] = mouse_pos

        # 检测现在按下的键
        key_pressed = pygame.key.get_pressed()      # 获得一个序列，包含整个键盘是否被按下的bool值
        me_info["W"] = key_pressed[pygame.K_w]
        me_info["A"] = key_pressed[pygame.K_a]
        me_info["S"] = key_pressed[pygame.K_s]
        me_info["D"] = key_pressed[pygame.K_d]

        # 事件检测
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                global main_running
                main_running = False    # 通知所有线程结束
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:       # [左键]
                    me_info["LEFT_CLICK"] = True
                if event.button == 3:       # [右键]
                    me_info["RIGHT_CLICK"] = True
                if event.button == 5:       # [下滚轮]
                    me_info["ROLL_DOWN"] = True
                if event.button == 4:       # [上滚轮]
                    me_info["ROLL_UP"] = True

        #=========
        # 游戏进程
        #=========

        # 自己的行为
        me.act(me_info)

        # 对方的行为
        him_info = dict()
        him.act(him_info)


        #=========
        # 绘制相关
        #=========
        # 1. 背景填充
        screen.fill(BG_COLOR)

        # 2. 鼠标绘制
        pygame.draw.circle(screen, color=CURSOR_COLOR, center=mouse_pos, radius=2)

        for p in players:
            # 3. 玩家绘制
            pygame.draw.circle(screen, color=p.color, center=(int(p.x), int(p.y)), radius=p.hitbox)

            # 4. 子弹绘制
            if p is me:     # 自己的子弹, 实心的
                for b in p.bullets:
                    if b.active():
                        pygame.draw.circle(screen, color=b.color, center=(int(b.x), int(b.y)), radius=2)
            else:           # 别人的子弹, 空心的
                for b in p.bullets:
                    if b.active():
                        pygame.draw.circle(screen, color=b.color, center=(int(b.x), int(b.y)), radius=2, width = 1)

        # 5. 双缓冲, 以及限制帧率
        pygame.display.flip()
        clock.tick(60)




# 把自己的信息发给server
def send_thread():

    # 用于向服务器发送最初的Header, 表示自己准备好了
    send_fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    # IPv4, UDP
    send_fd.sendto(f"PLAYER{MY_PLAYER_ID}|{my_receive_IP_port[0]}|{my_receive_IP_port[1]}".encode(), SERVER_IP_PORT)

    # 等待服务器宣布两个玩家都准备好了
    global server_game_start
    while not server_game_start:
        time.sleep(0.01)

    print("I know the server is ready.")

    # 发送自己(me)的数据给服务器
    while main_running:
        time.sleep(0.02) # 防止流量过大导致的延迟过高

        # 发送基础信息
        send_fd.sendto(struct.pack("iif", MY_PLAYER_ID, VAR_X, me.x), SERVER_IP_PORT)           # x
        send_fd.sendto(struct.pack("iif", MY_PLAYER_ID, VAR_Y, me.y), SERVER_IP_PORT)           # y
        send_fd.sendto(struct.pack("iif", MY_PLAYER_ID, VAR_VX, me.vx), SERVER_IP_PORT)         # vx
        send_fd.sendto(struct.pack("iif", MY_PLAYER_ID, VAR_VY, me.vy), SERVER_IP_PORT)         # vy

        # 告知 him him的血量
        send_fd.sendto(struct.pack("iif", MY_PLAYER_ID, VAR_HEALTH, him.health), SERVER_IP_PORT) # health

        # 发送子弹信息(数据量巨大..)
        i = 0
        while i < BULLET_MAX_AMOUNT_PER_PLAYER:
            left_to_send = min(BULLET_MAX_AMOUNT_PER_PLAYER - i, BULLET_INFO_AMOUNT_SEND_EACH)
            send_data_b = struct.pack("iif", MY_PLAYER_ID, VAR_BULLETS, left_to_send)   # header
            for j in range(i, i + left_to_send):
                b = me.bullets[j]
                send_data_b += struct.pack("ifffff", j, b.x, b.y, b.vx, b.vy, b.lifetime)
            send_fd.sendto(send_data_b, SERVER_IP_PORT)
            i += left_to_send



# 从server接收对方的信息
def recv_thread():

    # 用于从服务器接收
    recv_fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    # IPv4, UDP
    recv_fd.bind(my_receive_IP_port)

    # 等待服务器宣布可以开始send_thread()
    recv_data_b, recv_IP_port = recv_fd.recvfrom(1024)
    if recv_data_b == b"GAME|START":
        global server_game_start
        server_game_start = True

    # 从服务器接收数据
    while main_running:
        recv_data_b, recv_IP_port = recv_fd.recvfrom(1024)      # 接收到的原始字节
        recv_type = struct.unpack("i", recv_data_b[0:4])[0]     # 类型
        recv_value = struct.unpack("f", recv_data_b[4:8])[0]    # 值
        if recv_type == VAR_X:          # 敌人的 x 坐标
            him.x = recv_value
        elif recv_type == VAR_Y:        # 敌人的 y 坐标
            him.y = recv_value
        elif recv_type == VAR_VX:       # 敌人的 vx 速度
            him.vx = recv_value
        elif recv_type == VAR_VY:       # 敌人的 vy 速度
            him.vy = recv_value
        elif recv_type == VAR_HEALTH:   # **自己的** health        # 注意这里和其他信息的本质区别!
            me.health = recv_value
        elif recv_type == VAR_BULLETS:  # 敌人的子弹信息
            amount = int(recv_value)    # recv_value 在这里对应于本条信息中的子弹数目
            for i in range(amount):
                info = struct.unpack("ifffff", recv_data_b[8+i*24 : 32+i*24])
                him.bullets[info[0]].x, him.bullets[info[0]].y, him.bullets[info[0]].vx, \
                him.bullets[info[0]].vy, him.bullets[info[0]].lifetime = info[1:]
                him.bullets[info[0]].last_frame_time = time.time()


# 开启网络线程
t_send = threading.Thread(target=send_thread)
t_recv = threading.Thread(target=recv_thread)
t_send.start()
t_recv.start()


# 开启本地线程
main()


# 回收线程
t_send.join()
t_recv.join()

