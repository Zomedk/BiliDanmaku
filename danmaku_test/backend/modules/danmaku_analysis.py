from collections import Counter
import re
import jieba  # 引入中文分词库

# 简单的停用词列表（可根据需求扩展）
STOP_WORDS = {'的', '了', '是', '我', '你', '在', '啊', '吧', '嗯'}

def calculate_word_frequency(danmaku_data):
    """
    计算弹幕内容的词频
    :param danmaku_data: 弹幕数据列表，每个元素包含 'content' 键
    :return: 前10个高频词及其出现次数
    """
    if not danmaku_data or not isinstance(danmaku_data, (list, tuple)):
        return []  # 如果数据为空或格式错误，返回空列表
    
    words = []
    
    for item in danmaku_data:
        try:
            content = item.get('content', '')  # 使用 get 避免 KeyError
            if not content:
                continue
            # 使用 jieba 进行中文分词
            seg_list = jieba.cut(content)
            # 过滤停用词和单字符
            words.extend([word for word in seg_list if word not in STOP_WORDS and len(word) > 1])
        except (TypeError, AttributeError) as e:
            print(f"Skipping invalid item: {e}")
            continue
    
    # 统计词频
    word_count = Counter(words)
    
    # 获取前10个高频词
    top_words = word_count.most_common(10)
    
    return top_words