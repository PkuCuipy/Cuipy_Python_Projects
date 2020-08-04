
# 四舍五入到最近的"十分位", 并在舍入超出阈值时发出警告
# 用于处理float的精度问题,
# 或者用于 对速度不匹配的.midi进行近似
def round(x):
    as_return = int(10 * x + 0.5) / 10
    if abs(x-as_return) > 0.04:
        print(f"Warning: 产生了一个节奏显著错位的音符(误差={x-as_return}s)")
    return int(x+0.5)

