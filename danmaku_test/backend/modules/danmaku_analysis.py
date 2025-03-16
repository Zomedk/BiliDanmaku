from collections import Counter
import jieba
import os

# 停用词文件路径
STOPWORDS_PATH = r'D:\Lernen\danmaku_test\danmaku_test\backend\stopwords_cn.txt'

# 加载停用词
def load_stopwords(file_path):
    """
    从文件中加载停用词
    :param file_path: 停用词文件路径
    :return: 停用词集合
    """
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

def calculate_word_frequency(danmaku_data, logger=None):
    """
    计算弹幕内容的词频
    :param danmaku_data: 弹幕数据列表，每个元素包含 'content' 键
    :param logger: 日志记录器（可选），用于与 app.py 集成
    :return: 前10个高频词及其出现次数
    """
    if not danmaku_data or not isinstance(danmaku_data, (list, tuple)):
        if logger:
            logger.debug("Danmaku data is empty or invalid")
        return []

    # 设置 jieba 为精确模式，提升分词质量
    jieba.setLogLevel(0)  # 关闭 jieba 的日志输出，避免干扰
    words = []

    for item in danmaku_data:
        try:
            content = item.get('content', '')
            if not content:
                continue
            # 使用精确模式分词
            seg_list = jieba.cut(content, cut_all=False)
            # 过滤停用词和单字符
            filtered_words = [word for word in seg_list if word not in STOP_WORDS and len(word) > 1]
            words.extend(filtered_words)
        except (TypeError, AttributeError) as e:
            if logger:
                logger.warning(f"Skipping invalid item: {e}")
            else:
                print(f"Skipping invalid item: {e}")
            continue

    # 统计词频
    word_count = Counter(words)

    # 获取前10个高频词
    top_words = word_count.most_common(10)

    if logger:
        logger.debug(f"Top words calculated: {top_words}")
    
    return top_words