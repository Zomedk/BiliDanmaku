from collections import Counter
import jieba
import os
from collections import Counter
import jieba
import os
from wordcloud import WordCloud
from io import BytesIO
import base64
from PIL import Image


# 停用词文件路径
STOPWORDS_PATH = r'D:\Lernen\danmaku_test\danmaku_test\backend\stopwords_cn.txt'
# 字体路径
FONT_PATH = 'C:/Windows/Fonts/simhei.ttf' 


# 加载停用词
def load_stopwords(file_path):

    stopwords = set()
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word:
                    stopwords.add(word)
    else:
        print(f"Warning: Stopwords file not found at {file_path}")
    return stopwords

# 初始化停用词（全局变量，避免重复加载）
STOP_WORDS = load_stopwords(STOPWORDS_PATH)

def calculate_word_frequency(danmaku_data, logger=None, top_n=10):
    if not danmaku_data or not isinstance(danmaku_data, (list, tuple)):
        if logger:
            logger.debug("Danmaku data is empty or invalid")
        return []

    jieba.setLogLevel(0)
    words = []

    for item in danmaku_data:
        try:
            content = item.get('content', '')
            if not content:
                continue
            seg_list = jieba.cut(content, cut_all=False)
            filtered_words = [word for word in seg_list if word not in STOP_WORDS and len(word) > 1]
            words.extend(filtered_words)
        except (TypeError, AttributeError) as e:
            if logger:
                logger.warning(f"Skipping invalid item: {e}")
            continue

    word_count = Counter(words)
    top_words = word_count.most_common(top_n)
    
    if logger:
        logger.debug(f"Top {top_n} words calculated: {top_words}")
    
    return top_words

def generate_word_cloud(danmaku_data, logger=None):
    """
    生成词云图并返回 Base64 编码的图片
    :param danmaku_data: 弹幕数据列表
    :param logger: 日志记录器（可选）
    :return: Base64 编码的图片字符串
    """
    if not danmaku_data or not isinstance(danmaku_data, (list, tuple)):
        if logger:
            logger.debug("Danmaku data is empty or invalid for word cloud")
        raise ValueError("未获取到弹幕数据")

    # 计算词频（增加词数到 200）
    top_words = calculate_word_frequency(danmaku_data, logger=logger, top_n=200)
    word_freq = {word: freq for word, freq in top_words}

    # 生成词云图
    wc = WordCloud(
        font_path=FONT_PATH,
        width=800,  # 增加分辨率
        height=600,
        background_color='white',  # 改为白色背景
        max_words=150,  # 显示更多词
        colormap='Set2',  # 使用更鲜艳的颜色方案
        min_font_size=10,  # 最小字体
        max_font_size=100,  # 最大字体
        prefer_horizontal=0.8,  # 80% 水平排列
        contour_width=1,  # 添加轮廓
        contour_color='gray',  # 轮廓颜色
        random_state=42  # 固定随机种子，确保每次生成一致
    ).generate_from_frequencies(word_freq)

    # 将图片转为 Base64
    img = wc.to_image()
    img_io = BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

    if logger:
        logger.debug("Word cloud image generated successfully")
    
    return f'data:image/png;base64,{img_base64}'