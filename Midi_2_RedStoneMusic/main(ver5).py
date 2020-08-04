import pretty_midi
from classes import Note, Bar, Block
from tools import round

"""
日志:
1. 目前只支持4拍子; 3拍子需要修改红石机器架构
2. 由于RSM的特殊性, 暂时不考虑midi中音符的时长, 只考虑音符的start事件.
3. 由于RSM架构设计, 目前只支持BMP=150.
4. 传入的channel名称必须第一个为"L", 第二个为"R"
5. ver2简化框架, 现在音符盒和它前后上下那些方块/红石元件是一起生成的啦!

"""



#================================#
#======  PART-0 超参数定义  ======#
#================================#


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

DRUM_NAME_BY_PITCH = {
    36: "bassdrum",
    37: "snare",
    38: "hat"
}

# DRUM_BASE_BLOCK = {
#     "bassdrum": "stone",
#     "snare": "sand",
#     "hat": "glass"
# }

# 方块宏定义
FRAME_BLOCK = "yellow_concrete"
DEBUG_BLOCK = "red_concrete"
NOTE_BLOCK = "note_block"
PRE_BLOCK = "redstone_lamp"
REPEATER = "repeater"
REDSTONE_WIRE = "redstone_wire"
REDSTONE_LAMP = "redstone_lamp"





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
SEMIQUAVER_SEC = 60 / 4 / MIDI_BPM


# 设置midi的小节数量上限
BAR_AMOUNT = 99

# function文件夹
FUNCTION_FOLDER = "/Users/cuipy/Library/Application Support/minecraft/saves/RSM_20200804/datapacks/rsm/data/rsm/functions/"



# 当前.midi文件中包含的所有乐器名称
MIDI_INSTRUMENTS = ["bass", 'drums', "harp", "pling", "bell"]
MIDI_FILES_NAMES = ["bass.mid", 'drums.mid', 'harp.mid', 'pling.mid', 'bell.mid']


# 以后可以把下面全都提取为函数, 这几个就是参数
#!!!!!!!!!!!!现在只能这里手动调index
current_instrument_index = 4
current_instrument_name = MIDI_INSTRUMENTS[current_instrument_index]
midi_file_name = MIDI_FILES_NAMES[current_instrument_index]


# 设置"建造原点"坐标, 默认为(0,64,0)
X = 0
Y = 64 + current_instrument_index * 4
Z = 0



#================================#
#====== PART-1 读取MIDI文件 ======#
#================================#

# 读取文件为PrettyMIDI格式
midi_data = pretty_midi.PrettyMIDI(midi_file_name)

# 存储左/右声道的所有小节的实例(Bar())
channel_L = [Bar(i, 'L') for i in range(BAR_AMOUNT)]
channel_R = [Bar(i, 'R') for i in range(BAR_AMOUNT)]

# 从midi_data中, 获取全部音符信息, 以Note实例的形式存储在notes中.
assert midi_data.instruments[0].name == 'L' and midi_data.instruments[1].name == 'R'

# 遍历两个channel
for channel in midi_data.instruments:
    # 遍历当前channel的所有音符, 加入到相应的 channel_L/R 中
    current_channel = channel_L if channel.name == 'L' else channel_R

    for note in channel.notes:
        total_which = round(note.start / SEMIQUAVER_SEC)    # 在整个时间线的位置
        bar_ = total_which // 16                            # 在哪个小节
        which_ = total_which % 16                           # 在这个小节的第几个十六分音符
        qpos_ = which_ // 4                                 # 在这个小节的第几个四分音符(quarter)
        spos_ = which_ % 4                                  # 在这个四分音符的第几个十六分音符(semiquaver)
        is_drums_ = True if current_instrument_name == "drums" else False
        drum_name_ = DRUM_NAME_BY_PITCH[note.pitch] if is_drums_ else None
        current_channel[bar_][qpos_].append(Note(bar_, which_, qpos_, spos_, note.pitch, channel.name, is_drums_, drum_name_))







#================================#
#====== PART-2 内存虚拟建造 ======#
#================================#

world = dict()

# [主轴框架]
for dx in range(0, BAR_AMOUNT * 5):     # 框架方块
    world[(X + dx, Y, Z)] = Block(X + dx, Y, Z, DEBUG_BLOCK)
for dx in range(0, BAR_AMOUNT):         # 4个中继器
    world[(X + 5 * dx + 1, Y + 1, Z)] = Block(X + 5 * dx + 1, Y + 1, Z, REPEATER, delay=4, facing="west")
    world[(X + 5 * dx + 2, Y + 1, Z)] = Block(X + 5 * dx + 2, Y + 1, Z, REPEATER, delay=4, facing="west")
    world[(X + 5 * dx + 3, Y + 1, Z)] = Block(X + 5 * dx + 3, Y + 1, Z, REPEATER, delay=4, facing="west")
    world[(X + 5 * dx + 4, Y + 1, Z)] = Block(X + 5 * dx + 4, Y + 1, Z, REPEATER, delay=4, facing="west")
for dx in range(0, BAR_AMOUNT):         # 1个红石灯
    world[(X + 5 * dx, Y + 1, Z)] = Block(X + 5 * dx, Y + 1, Z, REDSTONE_LAMP)
for dx in range(0, BAR_AMOUNT):         # 连接主轴和支线的红石线及其底座
    world[(X + dx * 5, Y + 0, Z + 1)] = Block(X + dx * 5, Y + 0, Z + 1, FRAME_BLOCK)
    world[(X + dx * 5, Y + 1, Z + 1)] = Block(X + dx * 5, Y + 1, Z + 1, REDSTONE_WIRE)
    world[(X + dx * 5, Y + 0, Z - 1)] = Block(X + dx * 5, Y + 0, Z - 1, FRAME_BLOCK)
    world[(X + dx * 5, Y + 1, Z - 1)] = Block(X + dx * 5, Y + 1, Z - 1, REDSTONE_WIRE)




# [侧框架和音符盒相关]
# 每一拍最多容纳音符数, 最大为14(受当前架构中红石线传递距离限制)
# 你需要自己确保每一拍不会有更多的音符, 因为多出来的会被直接舍弃
# 此外, 由于架构缺陷, 如果小节音符过多,
MAX_NOTES_PER_BEATS = 14

for i in range(BAR_AMOUNT):     # R
    dz = 1
    for beats_index in range(4):
        for note in channel_L[i].beats[beats_index].notes[0:min(MAX_NOTES_PER_BEATS, len(channel_L[i].beats[beats_index].notes))]:
            dz += 1

            # 决定音符盒的音高 以及底部音色方块类型
            if current_instrument_name == "drums":
                base_block = BASE_BLOCK[DRUM_NAME_BY_PITCH[note.pitch]]
                pitch_0_25 = note.pitch + PITCH_DELTA[DRUM_NAME_BY_PITCH[note.pitch]]
                assert pitch_0_25 in range(0, 25)
            else:
                base_block = BASE_BLOCK[current_instrument_name]
                pitch_0_25 = note.pitch + PITCH_DELTA[current_instrument_name]
                assert pitch_0_25 in range(0, 25)

            world[(X + i * 5 + 3, Y + 0, Z + dz)] = Block(X + i * 5 + 3, Y + 0, Z + dz, base_block)  # 底部音色方块
            if base_block == "sand": world[(X + i * 5 + 3, Y - 1, Z + dz)] = Block(X + i * 5 + 3, Y - 1, Z + dz, DEBUG_BLOCK)   # 防止sand下坠
            world[(X + i * 5 + 3, Y + 1, Z + dz)] = Block(X + i * 5 + 3, Y + 1, Z + dz, NOTE_BLOCK, pitch=pitch_0_25)  # 音符盒
            world[(X + i * 5 + 2, Y + 1, Z + dz)] = Block(X + i * 5 + 2, Y + 1, Z + dz, PRE_BLOCK)      # 充能方块
            world[(X + i * 5 + 1, Y + 0, Z + dz)] = Block(X + i * 5 + 1, Y + 0, Z + dz, FRAME_BLOCK)    # 精细中继器底座
            world[(X + i * 5 + 1, Y + 1, Z + dz)] = Block(X + i * 5 + 1, Y + 1, Z + dz, REPEATER, facing="west", delay=note.spos + 1)   # 精细中继器
            world[(X + i * 5 + 0, Y + 0, Z + dz)] = Block(X + i * 5 + 0, Y + 0, Z + dz, FRAME_BLOCK)    # 红石线底座
            world[(X + i * 5 + 0, Y + 1, Z + dz)] = Block(X + i * 5 + 0, Y + 1, Z + dz, REDSTONE_WIRE)  # 红石线
        dz += 1
        if beats_index != 3:
            world[(X + i * 5 + 0, Y + 0, Z + dz)] = Block(X + i * 5, Y + 0, Z + dz, FRAME_BLOCK)        # 节拍间中继器底座
            world[(X + i * 5 + 0, Y + 1, Z + dz)] = Block(X + i * 5, Y + 1, Z + dz, REPEATER, facing="north", delay=4)      # 节拍间中继器

for i in range(BAR_AMOUNT):     # L
    dz = -1
    for beats_index in range(4):
        for note in channel_R[i].beats[beats_index].notes[0:min(MAX_NOTES_PER_BEATS, len(channel_R[i].beats[beats_index].notes))]:
            dz -= 1

            # 决定音符盒的音高 以及底部音色方块类型
            if current_instrument_name == "drums":
                base_block = BASE_BLOCK[DRUM_NAME_BY_PITCH[note.pitch]]
                pitch_0_25 = note.pitch + PITCH_DELTA[DRUM_NAME_BY_PITCH[note.pitch]]
                assert pitch_0_25 in range(0, 25)
            else:
                base_block = BASE_BLOCK[current_instrument_name]
                pitch_0_25 = note.pitch + PITCH_DELTA[current_instrument_name]
                assert pitch_0_25 in range(0, 25)

            world[(X + i * 5 + 3, Y + 0, Z + dz)] = Block(X + i * 5 + 3, Y + 0, Z + dz, base_block)     # 底部音色方块
            if base_block == "sand": world[(X + i * 5 + 3, Y - 1, Z + dz)] = Block(X + i * 5 + 3, Y - 1, Z + dz, DEBUG_BLOCK)  # 防止sand下坠
            world[(X + i * 5 + 3, Y + 1, Z + dz)] = Block(X + i * 5 + 3, Y + 1, Z + dz, NOTE_BLOCK, pitch=pitch_0_25)  # 音符盒
            world[(X + i * 5 + 2, Y + 1, Z + dz)] = Block(X + i * 5 + 2, Y + 1, Z + dz, PRE_BLOCK)      # 充能方块
            world[(X + i * 5 + 1, Y + 0, Z + dz)] = Block(X + i * 5 + 1, Y + 0, Z + dz, FRAME_BLOCK)    # 精细中继器底座
            world[(X + i * 5 + 0, Y + 0, Z + dz)] = Block(X + i * 5 + 0, Y + 0, Z + dz, FRAME_BLOCK)    # 红石线底座
            world[(X + i * 5 + 0, Y + 1, Z + dz)] = Block(X + i * 5 + 0, Y + 1, Z + dz, REDSTONE_WIRE)  # 红石线
            world[(X + i * 5 + 1, Y + 1, Z + dz)] = Block(X + i * 5 + 1, Y + 1, Z + dz, REPEATER, facing="west", delay=note.spos + 1)   # 精细中继器
        dz -= 1
        if beats_index != 3:
            world[(X + i * 5 + 0, Y + 0, Z + dz)] = Block(X + i * 5, Y + 0, Z + dz, FRAME_BLOCK)        # 节拍间中继器底座
            world[(X + i * 5 + 0, Y + 1, Z + dz)] = Block(X + i * 5, Y + 1, Z + dz, REPEATER, facing="south", delay=4)      # 节拍间中继器





#=====================================#
#====== PART-3 生成Minecraft指令 ======#
#=====================================#

# 构造指令[build_ID.mcfunction]
with open(FUNCTION_FOLDER + f"build_{current_instrument_index}.mcfunction", "w") as f:

    # 为 world 中的 Block实例 生成 setblock 指令
    for pos, block in world.items():
        if block.block_type == NOTE_BLOCK:
            pitch_0_25 = block.info['pitch']
            print(f"setblock {pos[0]} {pos[1]} {pos[2]} note_block[note={pitch_0_25}]", file=f)
        elif block.block_type == REPEATER:
            print(f"setblock {pos[0]} {pos[1]} {pos[2]} repeater[facing={block.info['facing']}, delay={block.info['delay']}]", file=f)
        else:
            print(f"setblock {pos[0]} {pos[1]} {pos[2]} {block.block_type}",file=f)


# 析构指令[clear_ID.mcfunction]
with open(FUNCTION_FOLDER + f"clear_{current_instrument_index}.mcfunction", "w") as f:
    for pos in world.keys():
        print(f"setblock {pos[0]} {pos[1]} {pos[2]} air", file=f)





