import matplotlib
matplotlib.use('Agg')  # 使用 Agg 后端，避免 Tkinter 主循环问题

import matplotlib.pyplot as plt
import base64
import jieba
import io
import csv
from collections import defaultdict
from matplotlib.font_manager import FontProperties
from snownlp import SnowNLP
from modules.logger import app_logger

# 加载停用词表
def load_stopwords(file_path='stopwords_cn.txt'):
    """加载停用词表"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        app_logger.warning(f"Stopwords file {file_path} not found, using empty set")
        return set()

stopwords = load_stopwords()

# 加载情感词典
def load_sentiment_lexicon(file_path='hownetvsa.csv'):
    """加载情感词典，假设格式为 word,score"""
    lexicon = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:  # 确保至少有词和分数
                    word = row[0]
                    score = float(row[1])
                    lexicon[word] = score
    except FileNotFoundError:
        app_logger.warning(f"Sentiment lexicon file {file_path} not found, using empty dict")
        return {}
    return lexicon

sentiment_lexicon = load_sentiment_lexicon()

# 计算词频，过滤情感词
def calculate_word_frequency(words, sentiment_lexicon, stopwords, sentiment_type, top_n=10, threshold=0.5):
    """统计词语频率，过滤停用词、单字和非情感词"""
    freq = defaultdict(int)
    for word in words:
        if len(word) > 1 and word not in stopwords and word in sentiment_lexicon:
            score = sentiment_lexicon[word]
            if (sentiment_type == 'positive' and score > threshold) or (sentiment_type == 'negative' and score < -threshold):
                freq[word] += 1
    return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top_n]

def analyze_sentiment(danmaku_list):
    """执行情感分析并生成可视化图表"""
    try:
        # 验证输入
        if not isinstance(danmaku_list, (list, tuple)):
            raise ValueError("弹幕数据格式错误")
        
        # 提取弹幕文本
        texts = [str(d.get('content', '')) for d in danmaku_list if d.get('content')]
        if not texts:
            raise ValueError("没有有效的弹幕文本数据")
        
        app_logger.debug(f"Processing {len(texts)} danmaku texts for sentiment analysis")

        # 执行情感分析
        sentiment_counts = defaultdict(int)
        positive_words = []
        negative_words = []
        
        for text in texts:
            s = SnowNLP(text)
            score = s.sentiments
            if score > 0.6:
                label = "positive"
                positive_words.extend(jieba.lcut(text, cut_all=False))
            elif score < 0.4:
                label = "negative"
                negative_words.extend(jieba.lcut(text, cut_all=False))
            else:
                label = "neutral"
            sentiment_counts[label] += 1

        # 验证情感分布
        if not sentiment_counts:
            raise ValueError("情感分析结果为空")

        # 计算百分比
        total = sum(sentiment_counts.values())
        percentages = {
            "positive": (sentiment_counts.get('positive', 0) / total * 100) if total > 0 else 0,
            "negative": (sentiment_counts.get('negative', 0) / total * 100) if total > 0 else 0,
            "neutral": (sentiment_counts.get('neutral', 0) / total * 100) if total > 0 else 0
        }

        # 设置中文字体
        font_path = r'C:\Windows\Fonts\simhei.ttf'  # 使用 SimHei 字体
        font = FontProperties(fname=font_path, size=12)

        # 生成图表
        plt.figure(figsize=(12, 5))
        labels = ['积极', '消极', '中性']
        sizes = [sentiment_counts.get('positive', 0), sentiment_counts.get('negative', 0), sentiment_counts.get('neutral', 0)]
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
        explode = (0.05, 0, 0)

        # 饼图
        plt.subplot(1, 2, 1)
        plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, textprops={'fontproperties': font})
        plt.title('情感分布比例', fontproperties=font, size=14, pad=10)

        # 柱状图
        plt.subplot(1, 2, 2)
        bars = plt.bar(labels, sizes, color=colors)
        plt.title('情感分布数量', fontproperties=font, size=14, pad=10)
        plt.ylabel('数量', fontproperties=font, size=12)
        plt.xticks(fontproperties=font)

        # 在柱状图上显示数量
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, height, int(height), ha='center', va='bottom', fontproperties=font, size=10)

        # 设置背景和网格
        plt.gca().set_facecolor('#f8f9fa')
        plt.gcf().set_facecolor('white')
        plt.grid(True, linestyle='--', color='#d3d3d3', alpha=0.5, axis='y')
        plt.tight_layout()

        # 转换为 Base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()

        # 计算高频词
        positive_freq = calculate_word_frequency(positive_words, sentiment_lexicon, stopwords, 'positive')
        negative_freq = calculate_word_frequency(negative_words, sentiment_lexicon, stopwords, 'negative')

        app_logger.debug(f"Sentiment analysis completed: {dict(sentiment_counts)}")

        return {
            "counts": dict(sentiment_counts),
            "percentages": percentages,
            "chart": f"data:image/png;base64,{img_base64}",
            "positive_words": positive_freq,
            "negative_words": negative_freq
        }

    except Exception as e:
        app_logger.error(f"情感分析失败: {str(e)}")
        raise