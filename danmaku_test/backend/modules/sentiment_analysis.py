import paddlehub as hub
import matplotlib.pyplot as plt
import base64
import jieba
import io
from collections import defaultdict
from matplotlib.font_manager import FontProperties
import numpy as np
from modules.logger import app_logger

# 加载停用词表
def load_stopwords(file_path='stopwords.txt'):
    """加载停用词表"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        app_logger.warning(f"Stopwords file {file_path} not found, using empty set")
        return set()

stopwords = load_stopwords()

# 初始化情感分析模型
senta = None
try:
    senta = hub.Module(name="senta_bilstm")
    app_logger.info("情感分析模型加载成功")
except Exception as e:
    app_logger.error(f"情感分析模型加载失败: {str(e)}")
    raise RuntimeError("无法加载情感分析模型，请检查网络或环境配置")

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
        if not senta:
            raise RuntimeError("情感分析模型未加载")
        results = senta.sentiment_classify(texts=texts)

        # 统计情感分布
        sentiment_counts = defaultdict(int)
        positive_words = []
        negative_words = []
        
        for result in results:
            positive_prob = result['positive_probs']
            negative_prob = result['negative_probs']
            # 动态分类：选择概率最高的类别
            if positive_prob > negative_prob and positive_prob >= 0.5:
                label = "positive"
            elif negative_prob > positive_prob and negative_prob >= 0.5:
                label = "negative"
            else:
                label = "neutral"
            sentiment_counts[label] += 1
            
            # 收集高频情感词
            if label != "neutral":
                words = jieba.lcut(result['text'], cut_all=False)
                if label == "positive":
                    positive_words.extend(words)
                else:
                    negative_words.extend(words)

        # 验证情感分布
        if not sentiment_counts:
            raise ValueError("情感分析结果为空")

        # 设置中文字体
        font_path = r'C:\Windows\Fonts\simhei.ttf'  # 使用 SimHei 字体
        font = FontProperties(fname=font_path, size=12)

        # 生成图表
        plt.figure(figsize=(12, 5))
        labels = ['积极', '消极', '中性']  # 更简洁的标签
        sizes = [sentiment_counts.get('positive', 0), sentiment_counts.get('negative', 0), sentiment_counts.get('neutral', 0)]
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # 蓝色、橙色、绿色
        explode = (0.05, 0, 0)  # 突出积极部分

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
        positive_freq = calculate_word_frequency(positive_words)
        negative_freq = calculate_word_frequency(negative_words)

        app_logger.debug(f"Sentiment analysis completed: {dict(sentiment_counts)}")

        return {
            "counts": dict(sentiment_counts),
            "chart": f"data:image/png;base64,{img_base64}",
            "positive_words": positive_freq,
            "negative_words": negative_freq
        }

    except Exception as e:
        app_logger.error(f"情感分析失败: {str(e)}")
        raise

def calculate_word_frequency(words, top_n=10):
    """统计词语频率，过滤停用词和单字"""
    freq = defaultdict(int)
    for word in words:
        if len(word) > 1 and word not in stopwords:  # 过滤单字和停用词
            freq[word] += 1
    return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top_n]