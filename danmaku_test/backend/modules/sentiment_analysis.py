import matplotlib
from io import BytesIO
matplotlib.use('Agg')  # 使用 Agg 后端，这样避免了 Tkinter 主循环的问题，适合无 GUI 环境（比如服务器）

import matplotlib.pyplot as plt
import base64
import jieba  # jieba 用来做中文分词
import io
import csv
from collections import defaultdict  # defaultdict 用来方便统计词频
from matplotlib.font_manager import FontProperties  # 用来设置中文字体
from snownlp import SnowNLP  # SnowNLP 是中文情感分析库
from modules.logger import app_logger  # 自定义日志，方便调试和记录错误

# 加载停用词表的函数
def load_stopwords(file_path='stopwords_cn.txt'):
    try:
        # 打开停用词文件，读取每行
        with open(file_path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())  # 去掉空行，并存入 set
    except FileNotFoundError:
        app_logger.warning(f"Stopwords file {file_path} not found, using empty set")  # 文件没找到，输出警告
        return set()  # 如果找不到文件，就返回空集合

stopwords = load_stopwords()  # 调用函数加载停用词

# 加载情感词典的函数
def load_sentiment_lexicon(file_path='hownetvsa.csv'):
    lexicon = {}
    try:
        # 打开情感词典文件
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:  # 确保每行至少有两个元素：词和分数
                    word = row[0]  # 词
                    score = float(row[1])  # 情感分数
                    lexicon[word] = score  # 将词和分数存入字典
    except FileNotFoundError:
        app_logger.warning(f"Sentiment lexicon file {file_path} not found, using empty dict")  # 文件没找到，输出警告
        return {}  # 如果文件没找到，返回空字典
    return lexicon  # 返回字典

sentiment_lexicon = load_sentiment_lexicon()  # 调用函数加载情感词典

# 计算词频，并且过滤掉非情感词的函数
def calculate_word_frequency(words, sentiment_lexicon, stopwords, sentiment_type, top_n=10, threshold=0.5):
    """统计词语频率，过滤停用词、单字和非情感词"""
    freq = defaultdict(int)  # 使用 defaultdict 来统计词频，默认值为 0
    for word in words:
        if len(word) > 1 and word not in stopwords and word in sentiment_lexicon:  # 过滤掉单字和停用词
            score = sentiment_lexicon[word]  # 获取词的情感分数
            # 根据情感类型（正向/负向）过滤词汇
            if (sentiment_type == 'positive' and score > threshold) or (sentiment_type == 'negative' and score < -threshold):
                freq[word] += 1  # 词频 +1
    return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top_n]  # 按照频率降序排列，返回前 top_n 个词

def analyze_sentiment(danmaku_list):
    """执行情感分析并生成可视化图表"""
    try:
        # 验证输入：确保传入的是列表或元组类型
        if not isinstance(danmaku_list, (list, tuple)):
            raise ValueError("弹幕数据格式错误")  # 如果不是列表或元组，抛出异常
        
        # 提取弹幕文本：从弹幕数据中提取出 'content' 字段
        texts = [str(d.get('content', '')) for d in danmaku_list if d.get('content')]
        if not texts:
            raise ValueError("没有有效的弹幕文本数据")  # 如果没有弹幕文本，抛出异常
        
        app_logger.debug(f"Processing {len(texts)} danmaku texts for sentiment analysis")  # 打印正在处理的弹幕数量

        # 执行情感分析：用 SnowNLP 分析情感，按分数分类
        sentiment_counts = defaultdict(int)  # 存储各类情感的计数
        positive_words = []  # 正向情感词
        negative_words = []  # 负向情感词
        
        for text in texts:
            s = SnowNLP(text)  # 用 SnowNLP 分析每条弹幕的情感
            score = s.sentiments  # 获取情感分数（0-1之间）
            if score > 0.6:  # 情感倾向于正向
                label = "positive"
                positive_words.extend(jieba.lcut(text, cut_all=False))  # 分词，并将正向词添加到 positive_words
            elif score < 0.4:  # 情感倾向于负向
                label = "negative"
                negative_words.extend(jieba.lcut(text, cut_all=False))  # 分词，并将负向词添加到 negative_words
            else:
                label = "neutral"  # 中性情感
            sentiment_counts[label] += 1  # 每种情感类型的计数 +1

        # 验证情感分析结果是否为空
        if not sentiment_counts:
            raise ValueError("情感分析结果为空")

        # 计算百分比
        total = sum(sentiment_counts.values())  # 总数
        percentages = {
            "positive": (sentiment_counts.get('positive', 0) / total * 100) if total > 0 else 0,
            "negative": (sentiment_counts.get('negative', 0) / total * 100) if total > 0 else 0,
            "neutral": (sentiment_counts.get('neutral', 0) / total * 100) if total > 0 else 0
        }

        # 设置中文字体
        font_path = r'C:\Users\zzzwww\AppData\Local\Microsoft\Windows\Fonts\NotoSansSC-Regular.otf'  # Noto Sans SC
        # font_path = r'C:\Windows\Fonts\simhei.ttf'  # 备选：SimHei
        font = FontProperties(fname=font_path, size=12)

        # 生成图表：情感分布的饼图和柱状图
        plt.figure(figsize=(8, 4), dpi=150)  # 调整画布大小
        plt.gcf().set_facecolor('#e0f7fa')  # 浅蓝色背景

        # 定义蓝色渐变调色板
        colors = ['#0077b6', '#48cae4', '#b2ebf2']  # 积极、消极、中性

        # 数据准备
        labels = ['积极', '消极', '中性']
        sizes = [sentiment_counts.get('positive', 0), sentiment_counts.get('negative', 0), sentiment_counts.get('neutral', 0)]
        explode = (0.1, 0, 0)  # 增强爆炸效果

        # 画饼图
        plt.subplot(1, 2, 1)
        ax1 = plt.gca()
        ax1.set_facecolor('#e0f7fa')
        wedges, texts, autotexts = plt.pie(
            sizes,
            explode=explode,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={'edgecolor': '#ffffff', 'linewidth': 2, 'antialiased': True},
            textprops={'fontproperties': font, 'fontsize': 12, 'color': '#023e8a'}
        )
        for text in texts:
            text.set_fontproperties(font)
            text.set_color('#023e8a')
        for autotext in autotexts:
            autotext.set_fontproperties(font)
            autotext.set_color('#ffffff')
            autotext.set_weight('bold')
        plt.title('情感分布比例', fontproperties=font, size=16, color='#023e8a', pad=15)

        # 画柱状图
        plt.subplot(1, 2, 2)
        ax2 = plt.gca()
        ax2.set_facecolor('#e0f7fa')
        bars = plt.bar(labels, sizes, color=colors, edgecolor='#ffffff', linewidth=1.5, alpha=0.9)
        plt.title('情感分布数量', fontproperties=font, size=16, color='#023e8a', pad=15)
        plt.ylabel('数量', fontproperties=font, size=12, color='#023e8a')
        plt.xticks(fontproperties=font, color='#023e8a')
        plt.yticks(color='#023e8a')

        # 在柱状图上显示数量
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2, height, int(height),
                ha='center', va='bottom', fontproperties=font, size=10, color='#ffffff',
                bbox=dict(facecolor='#023e8a', edgecolor='none', alpha=0.7, boxstyle='round,pad=0.3')
            )

        # 设置网格
        plt.grid(True, linestyle='--', color='#b2ebf2', alpha=0.4, axis='y')

        # 调整布局
        plt.tight_layout(pad=2)

        # 保存为 Base64
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor=plt.gcf().get_facecolor())
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()

        # 计算高频词
        positive_freq = calculate_word_frequency(positive_words, sentiment_lexicon, stopwords, 'positive')
        negative_freq = calculate_word_frequency(negative_words, sentiment_lexicon, stopwords, 'negative')

        app_logger.debug(f"Sentiment analysis completed: {dict(sentiment_counts)}")  # 打印分析结果

        return {
            "counts": dict(sentiment_counts),  # 返回情感分类的数量
            "percentages": percentages,  # 返回情感分类的百分比
            "chart": f"data:image/png;base64,{img_base64}",  # 返回 Base64 编码的图表图片
            "positive_words": positive_freq,  # 返回正向情感高频词
            "negative_words": negative_freq   # 返回负向情感高频词
        }

    except Exception as e:
        app_logger.error(f"情感分析失败: {str(e)}")  # 如果出错，记录错误日志
        raise  # 抛出异常，方便外部捕获和处理
