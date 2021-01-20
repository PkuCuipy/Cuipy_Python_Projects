
# 宏定义
BG_COLOR = (200, 200, 200)
CURSOR_COLOR = (200, 0, 100)
PLAYER_COLOR_DEFAULT = (0, 255, 200)
BULLET_COLOR = (0, 0, 0)
WIN_SIZE = (WIN_WIDTH, WIN_HEIGHT) = (1200, 600)
WIN_CENTER = (WIN_WIDTH // 2, WIN_HEIGHT // 2)
PLAYER_MAX_SPEED_PER_SEC = 200          # 玩家最大速度
PLAYER_ACCELERATION_PER_SEC = 1000      # 加速时的加速度(Ratio/second)
PLAYER_REDUCTION_PER_SEC = 0.03         # 减速时的加速度(Ratio/second)
BULLET_SPEED_PER_SEC = 400              # 子弹速度
BULLET_MAX_AMOUNT_PER_PLAYER = 300     # 每个玩家的子弹数上限
DIVISION_ANGLE = 0.1                    # 子弹分裂角度
BULLET_LIFETIME_SEC = 100                 # 子弹初始存活时间
FADE_OUT_THRESHOLD_SEC = 0.8            # 子弹淡出时间限
PLAYER_HEALTH_DEFAULT = 10
PLAYER_HITBOX_DEFAULT = 10
BULLET_INFO_AMOUNT_SEND_EACH = 16       # 每次传输多少个子弹的数据
SERVER_IP_PORT = ("192.168.1.100", 6000)

# 网络传输
VAR_X           = 0
VAR_Y           = 1
VAR_VX          = 2
VAR_VY          = 3
VAR_LIFETIME    = 4
VAR_BULLETS     = 5
VAR_HEALTH      = 6
