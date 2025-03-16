import re

# 正则式：提取 BV 号
def handle_bv_input(bv_input):
    bv_pattern = r"(BV[0-9A-Za-z]{10})"
    match = re.search(bv_pattern, bv_input)
    if match:
        return match.group(1)
    else:
        raise ValueError("无效的 BV 号或视频链接")

# 转换秒数为hh:mm:ss格式
def seconds_to_hms(seconds):
    try:
        seconds = float(seconds)
    except ValueError:
        raise ValueError("输入的秒数无效，请传入有效的数字。")
    
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}:{m:02}:{s:02}"
