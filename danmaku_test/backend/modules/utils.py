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

# 新增辅助函数：将时间字符串转换为秒数
def parse_time_to_seconds(time_str):
    """
    将 'HH:MM:SS' 或 'MM:SS' 格式的时间字符串转换为秒数
    :param time_str: 时间字符串，如 '00:12:28'
    :return: 秒数（浮点数）
    """
    try:
        parts = time_str.split(':')  # 按冒号分割
        if len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:  # MM:SS
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        else:
            return float(time_str)  # 如果已经是数字，直接转换
    except (ValueError, TypeError):
        return 0  # 如果转换失败，返回 0