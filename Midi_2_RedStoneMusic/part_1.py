import pretty_midi
from classes import Note, Bar, Block
from tools import round
from consts import *
from part_2_and_part_3 import *

"""
日志:
1. 由于RSM的特殊性, 最小音乐单元为 BPM=150 下的 16分音符
2. 由于RSM的特殊性, 只考虑midi中的start事件.
"""


#================================#
#====== PART-1 读取MIDI文件 ======#
#================================#

# 读取文件为PrettyMIDI格式
midi_file_name = "combine.mid"
midi_data = pretty_midi.PrettyMIDI(midi_file_name)


# 一对一对地(L 和 R)遍历.midi文件的所有channel
for instrument_idx in range(0, int(len(midi_data.instruments) / 2)):

    # 存储当前乐器 [左/右声道] 的所有 [小节(Bar类的类实例)] 的 [列表(list)] 组成的字典(用字典只是为了LR共用代码)
    bars = dict()
    bars['L'] = [Bar(i, 'L') for i in range(BAR_AMOUNT)]
    bars['R'] = [Bar(i, 'R') for i in range(BAR_AMOUNT)]

    # 确保文件命名符合规范
    assert midi_data.instruments[2 * instrument_idx].name[-1] == 'L'
    assert midi_data.instruments[2 * instrument_idx + 1].name[-1] == 'R'
    assert midi_data.instruments[2 * instrument_idx].name[0:-1] == midi_data.instruments[2 * instrument_idx + 1].name[0:-1]

    # 一次读取两个乐器, 虽然s在midi中是两个乐器, 但其实是一个音色的两个声道
    instruments = dict()
    instruments['L'] = midi_data.instruments[2 * instrument_idx]
    instruments['R'] = midi_data.instruments[2 * instrument_idx + 1]
    instrument_name = instruments['L'].name[:-1]   # 乐器名(去掉L/R后缀了)

    for LorR in ['L', 'R']:
        for note in instruments[LorR].notes:
            total_which = round(note.start / SEMIQUAVER_SEC)    # 在整个时间线的位置
            bar_ = total_which // 16                            # 在哪个小节
            which_ = total_which % 16                           # 在这个小节的第几个十六分音符
            qpos_ = which_ // 4                                 # 在这个小节的第几个四分音符(quarter)
            spos_ = which_ % 4                                  # 在这个四分音符的第几个十六分音符(semiquaver)
            pitch_ = note.pitch                                 # 音符的标准绝对音高
            # 当前载入的乐器是否为鼓组(drums)
            is_drums_ = True if instrument_name == "drums" else False
            drum_name_ = DRUM_NAME_BY_PITCH[note.pitch] if is_drums_ else None
            # bars_L 的第 bar_ 小节, 的第 qpos_ 拍, 新增一个音符
            bars[LorR][bar_][qpos_].append(Note(bar_, which_, qpos_, spos_, pitch_, instrument_name, is_drums_, drum_name_))

    # 将LR的midi数据传递给Part2和Part3进行后续操作
    part2_and_part3(instrument_idx, instrument_name, X, Y + instrument_idx * 4, Z, bars['L'], bars['R'], FUNCTION_FOLDER)




