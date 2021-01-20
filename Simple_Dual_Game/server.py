import socket
import struct
from macro import *

# 用于从客户端接收
recv_fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    # IPv4, UDP
recv_fd.bind(SERVER_IP_PORT)
print(f"Server running on {SERVER_IP_PORT}")

# 用于向客户端发送
send_fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    # IPv4, UDP

# 两个玩家用于接收的IP_port
player_IP_port = [None, None]
player_IP_port[0] = None
player_IP_port[1] = None

# 等待两个玩家
while True:
    data, IP_port = recv_fd.recvfrom(1024)
    data_list = data.decode().split("|")
    if data_list[0] == "PLAYER0":
        player_IP_port[0] = (data_list[1], int(data_list[2]))
        print("player 0 is ready...")
    if data_list[0] == "PLAYER1":
        player_IP_port[1] = (data_list[1], int(data_list[2]))
        print("player 1 is ready...")
    if player_IP_port[0] and player_IP_port[1]:
        break

# 打印两个玩家的 (IP:port)
print(player_IP_port)

# 告诉两个玩家自己准备好了
send_fd.sendto(b"GAME|START", player_IP_port[0])
send_fd.sendto(b"GAME|START", player_IP_port[1])


# 从某个Player接收数据, 并立刻向另一个Player转发相应的数据
while True:
    recv_data_b, IP_port = recv_fd.recvfrom(1024)
    who = struct.unpack("i", recv_data_b[0:4])[0]
    send_target = not who   # 来自player_0的信息, 要发送给player_1. 反之亦然.

    # 去掉头部, 原封不动地转发数据
    send_data_b = recv_data_b[4:]
    send_fd.sendto(send_data_b, player_IP_port[send_target])
