import paddlehub as hub
import matplotlib.pyplot as plt
import base64
import jieba
import io
from collections import defaultdict
from modules.logger import app_logger

# 初始化模型（首次运行会自动下载）
try:
    senta = hub.Module(name="senta_bilstm")
except Exception as e:
    app_logger.error(f"情感分析模型加载失败: {str(e)}")

def analyze_sentiment(danmaku_list):
    """执行情感分析并生成可视化图表"""
    try:
        # 提取弹幕文本
        texts = [d.get('content', '') for d in danmaku_list if d.get('content')]
        if not texts:
            raise ValueError("没有有效的弹幕文本数据")

        # 执行情感分析
        results = senta.sentiment_classify(texts=texts)

        # 统计情感分布
        sentiment_counts = defaultdict(int)
        positive_words = []
        negative_words = []
        
        for result in results:
            label = "positive" if result['positive_probs'] > 0.6 else "negative" if result['negative_probs'] > 0.6 else "neutral"
            sentiment_counts[label] += 1
            
            # 收集高频情感词
            if label != "neutral":
                words = jieba.lcut(result['text'])
                if label == "positive":
                    positive_words.extend(words)
                else:
                    negative_words.extend(words)

        # 生成饼图
        plt.figure(figsize=(10, 6))
        labels = list(sentiment_counts.keys())
        sizes = list(sentiment_counts.values())
        
        plt.subplot(1, 2, 1)
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        plt.title('情感分布比例')

        # 生成柱状图
        plt.subplot(1, 2, 2)
        plt.bar(labels, sizes)
        plt.title('情感分布数量')
        plt.ylabel('数量')

        # 转换为Base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()

        return {
            "counts": dict(sentiment_counts),
            "chart": f"data:image/png;base64,{img_base64}",
            "positive_words": calculate_word_frequency(positive_words),
            "negative_words": calculate_word_frequency(negative_words)
        }

    except Exception as e:
        app_logger.error(f"情感分析失败: {str(e)}")
        raise

def calculate_word_frequency(words, top_n=10):
    """统计词语频率"""
    freq = defaultdict(int)
    for word in words:
        if len(word) > 1:  # 过滤单字
            freq[word] += 1
    return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top_n]