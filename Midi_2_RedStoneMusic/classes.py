
class Note:
    def __init__(self, bar, which, qpos, spos, pitch, channel, is_drums, drum_name):
        # 设置bar和which是为了直观表示某个音符的"时间轴位置"
        # 设置qpos和spos是为了方便后面计算"world位置"...
        self.bar = bar      # 第几个"小节"                           从0开始
        self.which = which  # 该小节的第几个"16分音符"                从0到3
        self.qpos = qpos    # 该小节的第几个"4分音符(quarter)"        从0到3
        self.spos = spos    # 该4分音符的第几个"16分音符(semiquaver)"  从0到3
        self.pitch = pitch  # 音符的音高                  mc支持的音高范围是很窄的
        self.channel = channel   # 该音符对应乐器
        self.is_drums = is_drums
        self.drum_name = drum_name
    def __repr__(self):
        return f"Note({self.channel}-{self.bar}-{self.qpos}-{self.spos}: {self.pitch})"


class Beat: # (1Beat = 1四分音符)
    def __init__(self, which):
        self.which = which
        self.notes = []
        self.note_count = 0

    def __getitem__(self, idx):
        return self.notes[idx]

    def append(self, item):
        self.notes.append(item)
        self.note_count += 1



class Bar:
    def __init__(self, which, channel_name):
        self.which = which
        self.channel_name = channel_name
        self.beats = [Beat(i) for i in range(4)]
    def __repr__(self):
        return f"声道:{self.channel_name}; 小节编号:{self.which}"
    def __getitem__(self, idx):
        return self.beats[idx]



class Block:
    def __init__(self, x, y, z, block_type, **info):
        self.x, self.y, self.z = x, y, z
        self.block_type = block_type
        self.info = info
