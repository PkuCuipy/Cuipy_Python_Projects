import wave
import math
import numpy as np
from PIL import Image


def write_sine(data, framerate, start_sec, sustain_sec, frequency, amplitude):
    """
    :param data: 数据写入目标位置(类型应为short的ndarray)
    :param framerate: 采样率
    :param start_sec: 正弦波开始时间
    :param sustain_sec: 正弦波持续时间
    :param frequency: 正弦波频率 (hz)
    :param amplitude: 正弦波振幅 (0~1的float)
    :return: None
    """
    # 计算起始位置在data的索引
    start_frame = int(start_sec * framerate)
    end_frame = int((start_sec + sustain_sec) * framerate)
    # 写入正弦波
    phi = math.tau * frequency / framerate
    f = lambda x: 32768 * amplitude * math.sin(phi * x)
    for i in range(start_frame, end_frame + 1):
        data[i] += f(i)
    return


def write_pixel(data, which, x, y, pixel_width = 0.1, intensity = 0.001):
    """
    功能: 绘制单个像素点
    像素绘制在10kHz到20kHz频段, 分辨率为100*100, 即:
    (x, y): (0, 0) -> (99, 99) 的方形区域
     0 ➡ y
    x⬇  99
    :param data: 数据写入目标位置(类型应为short的ndarray)
    :param which: 第几个字 (默认为方形字, which从0开始数)
    :param x: x坐标 {0,1,2,...,99}
    :param y: y坐标 {0,1,2,...,99}
    :param pixel_width: 像素时间跨度(second) (0,1]
    :param intensity: 像素颜色深浅系数(amplitude) (0,1]
    :return: None
    """
    if intensity == 0:
        return
    start_sec = (which * pixel_width * 100) + (y * pixel_width)
    frequency = 20000 - 100 * x
    write_sine(data, 44100, start_sec, pixel_width, frequency, intensity)
    

def write_image(data, image, which):
    """
    功能: 传入image的路径
    :param data: 数据写入目标位置(类型应为short的ndarray)
    :param image: 图片(路径): 格式必须为100*100的png图像
    :param which: 图片表示第几个字
    :return: None
    """
    # 先把图像转成灰度图, 得到一个100*100的二维数组, 元素value: 0~255
    matrix = np.array(Image.open(image).convert('L'))
    for i in range(100):
        for j in range(100):
            write_pixel(data, which, i, j, intensity = (1 - matrix[i][j] / 255) / 100)
            print(i, j, 'DONE', sep='\t')
    return



# 基础设置
FRAMERATE = 44100 # 音频采样率(不支持更改)
TIME = 40 # 生成的音频时长
IMAGE_PATH = "example.png" # 绘入音频频谱的图像

# 处理数据
wave_data = np.array([0 for _ in range(FRAMERATE * TIME)]).astype(np.short) # 创建TIME长度的全0数组
write_image(wave_data, IMAGE_PATH, 0) # 绘制IMAGE_PATH对应的图案

# 写入WAV文档
f = wave.open(IMAGE_PATH + ".wav", "wb")
f.setnchannels(1) # 配置声道数(本程序只支持输出单声道)
f.setsampwidth(2) # 配置量化位数(数字2对应16bit)
f.setframerate(FRAMERATE) # 配置取样频率(本程序只支持44100Hz)
f.writeframes(wave_data.tostring()) # 将wav_data转换为二进制数据写入文件
f.close()


