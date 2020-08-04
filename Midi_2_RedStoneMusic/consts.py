
#================================#
#======  PART-0 超参数定义  ======#
#================================#



# ====== 可调整部分 ======
# function文件夹
FUNCTION_FOLDER = "/Users/cuipy/Library/Application Support/minecraft/saves/RSM_20200804/datapacks/rsm/data/rsm/functions/"

# 设置"建造原点"坐标, 默认为(0,64,0)
X = 0
Y = 64
Z = 0

# 设置midi的小节数量上限
BAR_AMOUNT = 99





# ====== 除非有bug, 否则不应更改的部分 ======

# 移调相关: 把针对不同乐器的 midi_pitch 映射到[0-24]
# 注意: 请自己确保midi音符符合该乐器的音域要求!
PITCH_DELTA = {
    "bass":-42,
    "didgeridoo": -42,
    "guitar": -54,
    "pling": -66,
    "bit": -66,
    "banjo": -66,
    "harp": -66,
    "iron_xylophone": -66,
    "cow_bell": -78,
    "flute": -78,
    "xylophone": -90,
    "chime": -90,
    "bell": -90,
    "bassdrum": -35,
    "snare": -36,
    "hat": -37
}

# 音色对应的底部方块
BASE_BLOCK = {
    "bass": "oak_planks",
    "didgeridoo": "pumpkin",
    "guitar": "white_wool",
    "pling": "glowstone",
    "bit": "emerald_block",
    "banjo": "hey_block",
    "harp": "dirt",
    "iron_xylophone": "iron_block",
    "cow_bell": "soul_sand",
    "flute": "clay",
    "xylophone": "bone_block",
    "chime": "packed_ice",
    "bell": "gold_block",
    "bassdrum": "stone",
    "snare": "sand",
    "hat": "glass"
}

# 通过音高区分鼓件
DRUM_NAME_BY_PITCH = {
    36: "bassdrum",
    37: "snare",
    38: "hat"
}


# 一些用到的方块宏定义
FRAME_BLOCK = "yellow_concrete"     # 框架方块1
DEBUG_BLOCK = "red_concrete"        # 框架方块2
NOTE_BLOCK = "note_block"           # 音符盒
PRE_BLOCK = "redstone_lamp"         # 前置在音符盒前, 传递中继器信号的方块
REPEATER = "repeater"               # 中继器
REDSTONE_WIRE = "redstone_wire"     # 红石线
REDSTONE_LAMP = "redstone_lamp"     # 红石灯




# minecraft原生支持的 BPM / 单位长度
# 其余的速度都有可能导致四舍五入, 造成节奏错乱!
# 具体而言, 由于 redstone_tick 固定为0.1s, 速度信息是不可修改的.
# 而此红石工程的最小音乐单位因此固定为0.1s.
# 其实这个工程还有扩充的可能:
# - 首先, 很多乐器是可以共享充能方块的, 借此增加容纳的音符数
# (事实上只要这个乐器的BASE_BLOCK是非透明方块就行)
# 但目前好像没有必要这么做...也主要是程序实现起来可能会麻烦一点
# - 其次, 可以相隔1tick(0.05s)激活两套RSM设备, 使得最小单位变为0.05s (1 game_tick)
MIDI_BPM = 150
SEMIQUAVER_SEC = 0.1

