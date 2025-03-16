# 导入需要的库
from collections import Counter  # 用于统计词频
import jieba  # 中文分词工具
import os  # 处理文件路径
from wordcloud import WordCloud, ImageColorGenerator  # 生成词云图和动态颜色
from io import BytesIO  # 处理内存中的图片数据
import base64  # 将图片转为 Base64 编码
from PIL import Image  # 处理图片
from modules.utils import parse_time_to_seconds
import numpy as np
import matplotlib.pyplot as plt  # 新增：绘制折线图
from matplotlib.font_manager import FontProperties  # 新增：支持中文


# 定义文件路径常量
STOPWORDS_PATH = r'D:\Lernen\danmaku_test\danmaku_test\backend\stopwords_cn.txt'  # 停用词文件路径（过滤无意义的词）
FONT_PATH = r'C:\Windows\Fonts\simhei.ttf'  # 字体文件路径（支持中文显示）
MASK_PATH = r'D:\Lernen\danmaku_test\backend\assets\circle_mask.png'  # 蒙版图片路径（定义词云形状）

# 函数：加载停用词
def load_stopwords(file_path):
    """
    从文件中读取停用词（如“的”、“了”），这些词不会出现在词云中
    :param file_path: 停用词文件的路径
    :return: 一个集合，包含所有停用词
    """
    stopwords = set()  # 创建一个空集合存储停用词
    if os.path.exists(file_path):  # 检查文件是否存在
        with open(file_path, 'r', encoding='utf-8') as f:  # 打开文件，指定编码为 UTF-8
            for line in f:  # 逐行读取
                word = line.strip()  # 去掉每行的首尾空白
                if word:  # 如果不是空行
                    stopwords.add(word)  # 添加到集合中
    else:
        print(f"Warning: Stopwords file not found at {file_path}")  # 如果文件不存在，打印警告
    return stopwords

# 初始化停用词（只加载一次，避免重复操作）
STOP_WORDS = load_stopwords(STOPWORDS_PATH)

# 函数：计算词频
def calculate_word_frequency(danmaku_data, logger=None, top_n=10):
    """
    从弹幕数据中提取高频词
    :param danmaku_data: 弹幕数据列表，每个元素包含 'content' 键
    :param logger: 日志工具，用于记录调试信息（可选）
    :param top_n: 返回前多少个高频词，默认是 10
    :return: 一个列表，包含 [词, 出现次数] 的对
    """
    # 检查输入数据是否有效
    if not danmaku_data or not isinstance(danmaku_data, (list, tuple)):
        if logger:  # 如果有日志工具
            logger.debug("Danmaku data is empty or invalid")  # 记录调试信息
        return []  # 返回空列表

    jieba.setLogLevel(0)  # 关闭 jieba 的日志输出，避免干扰
    words = []  # 存储所有分词结果

    # 遍历每条弹幕
    for item in danmaku_data:
        try:
            content = item.get('content', '')  # 获取弹幕内容，默认为空字符串
            if not content:  # 如果内容为空，跳过
                continue
            seg_list = jieba.cut(content, cut_all=False)  # 对内容进行分词（精确模式）
            # 过滤掉停用词和单字符词
            filtered_words = [word for word in seg_list if word not in STOP_WORDS and len(word) > 1]
            words.extend(filtered_words)  # 将分词结果添加到总列表
        except (TypeError, AttributeError) as e:  # 捕获可能的错误（如数据格式不对）
            if logger:
                logger.warning(f"Skipping invalid item: {e}")  # 记录警告信息
            continue

    # 统计词频
    word_count = Counter(words)  # 使用 Counter 计算每个词出现的次数
    top_words = word_count.most_common(top_n)  # 获取前 top_n 个高频词

    if logger:
        logger.debug(f"Top {top_n} words calculated: {top_words}")  # 记录结果
    
    return top_words  # 返回词频列表

# 函数：生成词云图
def generate_word_cloud(danmaku_data, logger=None):
    """
    根据弹幕数据生成美观的词云图，并返回 Base64 编码的图片
    :param danmaku_data: 弹幕数据列表
    :param logger: 日志工具（可选）
    :return: Base64 编码的图片字符串，可直接用于 <img> 标签
    """
    # 检查输入数据是否有效
    if not danmaku_data or not isinstance(danmaku_data, (list, tuple)):
        if logger:
            logger.debug("Danmaku data is empty or invalid for word cloud")
        raise ValueError("未获取到弹幕数据")  # 抛出错误，告诉调用者数据有问题

    # 计算词频，获取前 200 个高频词
    top_words = calculate_word_frequency(danmaku_data, logger=logger, top_n=200)
    word_freq = {word: freq for word, freq in top_words}  # 转为字典，方便词云使用

    # 加载蒙版图片（定义词云形状）
    if os.path.exists(MASK_PATH):  # 检查蒙版文件是否存在
        mask = np.array(Image.open(MASK_PATH).convert('L'))  # 打开图片并转为灰度数组
    else:
        mask = None  # 如果没有蒙版，使用默认矩形
        if logger:
            logger.warning(f"Mask file not found at {MASK_PATH}, using default rectangle")

    # 创建词云对象并设置参数
    wc = WordCloud(
        font_path=FONT_PATH,  # 指定中文字体文件
        width=800,  # 图片宽度（像素）
        height=600,  # 图片高度（像素）
        mask=mask,  # 使用蒙版形状（如圆形）
        background_color=None,  # 透明背景
        mode='RGBA',  # 支持透明度（需要 PNG 格式）
        max_words=150,  # 最多显示 150 个词
        min_font_size=12,  # 最小字体大小
        max_font_size=120,  # 最大字体大小
        prefer_horizontal=0.7,  # 70% 的词水平排列，增加多样性
        colormap='plasma',  # 使用渐变色系（炫酷效果）
        contour_width=2,  # 词云边缘轮廓宽度
        contour_color='white',  # 轮廓颜色为白色
        random_state=42  # 固定随机种子，确保每次生成一致
    ).generate_from_frequencies(word_freq)  # 根据词频生成词云

    # （可选）根据蒙版图片生成动态颜色
    if mask is not None:
        image_colors = ImageColorGenerator(np.array(wc.to_image()))  # 从词云图片提取颜色
        wc.recolor(color_func=image_colors)  # 重新着色

    # 将词云图转为 Base64 编码
    img = wc.to_image()  # 生成 PIL 图片对象
    img_io = BytesIO()  # 创建内存缓冲区
    img.save(img_io, format='PNG')  # 保存为 PNG 格式（支持透明）
    img_io.seek(0)  # 将指针移到开头
    img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')  # 转为 Base64 字符串

    if logger:
        logger.debug("Word cloud image generated successfully")  # 记录成功信息
    
    return f'data:image/png;base64,{img_base64}'  # 返回图片数据


# 生成弹幕随时间分布折线图
def generate_danmaku_timeline(danmaku_data, logger=None):
    """
    根据弹幕时间生成折线图，并标注关键时刻
    :param danmaku_data: 弹幕数据列表，包含 'time' 键（可能是字符串或浮点数）
    :param logger: 日志工具（可选）
    :return: Base64 编码的折线图图片
    """
    if not danmaku_data or not isinstance(danmaku_data, (list, tuple)):
        if logger:
            logger.debug("Danmaku data is empty or invalid for timeline")
        raise ValueError("未获取到弹幕数据")

    # 提取弹幕时间并转换为秒数
    times = []
    for item in danmaku_data:
        time_value = item.get('time', 0)
        if isinstance(time_value, str):  # 如果是字符串格式
            time_in_seconds = parse_time_to_seconds(time_value)
        else:  # 如果已经是数字
            time_in_seconds = float(time_value or 0)
        times.append(time_in_seconds)

    if not times:
        raise ValueError("弹幕数据中没有有效的时间信息")

    # 将时间按分钟分组
    max_time = max(times)  # 视频总时长（秒）
    bins = int(max_time // 60) + 1  # 按分钟划分，总分钟数
    hist, bin_edges = np.histogram(times, bins=bins, range=(0, max_time))  # 统计每分钟弹幕数

    # 生成时间轴（分钟）
    minutes = [i for i in range(bins)]

    # 找到弹幕峰值（关键时刻）
    peak_indices = np.where(hist >= np.percentile(hist, 95))[0]  # 取前 5% 的峰值
    peaks = [(minutes[i], hist[i]) for i in peak_indices]  # (分钟, 弹幕数)

    # 设置中文字体
    font = FontProperties(fname=FONT_PATH, size=12)

    # 创建折线图
    plt.figure(figsize=(10, 6))
    plt.plot(minutes, hist, color='#1f77b4', linewidth=2, label='弹幕数量')
    plt.fill_between(minutes, hist, color='#1f77b4', alpha=0.2)

    # 标注关键时刻
    for peak_min, peak_count in peaks:
        plt.scatter(peak_min, peak_count, color='red', s=50, zorder=5)
        plt.text(peak_min, peak_count + 5, f'关键时刻\n{int(peak_min)}分', 
                 ha='center', va='bottom', fontproperties=font, color='red')

    # 设置图表样式
    plt.title('弹幕随时间分布', fontproperties=font, size=16)
    plt.xlabel('时间 (分钟)', fontproperties=font)
    plt.ylabel('弹幕数量', fontproperties=font)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(prop=font)

    # 保存图片到内存
    img_io = BytesIO()
    plt.savefig(img_io, format='PNG', bbox_inches='tight', dpi=100)
    img_io.seek(0)
    img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
    plt.close()

    if logger:
        logger.debug("Danmaku timeline image generated successfully")
    
    return f'data:image/png;base64,{img_base64}'