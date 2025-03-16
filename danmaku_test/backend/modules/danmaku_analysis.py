from collections import Counter
import re

# 词频统计函数
def calculate_word_frequency(danmaku_data):
    words = []
    
    for item in danmaku_data:
        # 提取弹幕内容并进行分词（这里你可以使用更复杂的分词器）
        content = item['content']
        words += re.findall(r'\w+', content)  # 使用正则提取单词（你可以根据需求调整正则）
    
    # 统计词频
    word_count = Counter(words)
    
    # 获取前几名高频词
    top_words = word_count.most_common(10)  # 这里取前10个高频词，调整数量可以修改数字
    
    return top_words