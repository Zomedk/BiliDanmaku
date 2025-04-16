from collections import Counter
import jieba
import os
from wordcloud import WordCloud, ImageColorGenerator
from io import BytesIO
import base64
from PIL import Image
from modules.utils import hms_to_seconds
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from scipy.interpolate import make_interp_spline
from scipy.signal import find_peaks
from modules.logger import app_logger

STOPWORDS_PATH = r'D:\Lernen\danmaku_test\danmaku_test\backend\stopwords_cn.txt'
FONT_PATH = r'C:\Windows\Fonts\simhei.ttf'
MASK_PATH = r'D:\Lernen\danmaku_test\backend\assets\circle_mask.png'

def load_stopwords(file_path):
    stopwords = set()
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word:
                    stopwords.add(word)
    else:
        app_logger.warning(f"Stopwords file not found at {file_path}")
    return stopwords

STOP_WORDS = load_stopwords(STOPWORDS_PATH)

def calculate_word_frequency(danmaku_data, logger=None, top_n=10):
    if not danmaku_data or not isinstance(danmaku_data, list):
        if logger:
            logger.debug("Danmaku data is empty or invalid")
        return []

    jieba.setLogLevel(0)
    words = []
    for item in danmaku_data:
        try:
            if not isinstance(item, dict):
                logger.error(f"Invalid danmaku item: type={type(item)}, value={item}")
                continue
            content = item.get('content', '')
            if not content:
                continue
            seg_list = jieba.cut(content, cut_all=False)
            filtered_words = [word for word in seg_list if word not in STOP_WORDS and len(word) > 1]
            words.extend(filtered_words)
        except Exception as e:
            if logger:
                logger.warning(f"Skipping invalid item: {e}")
            continue

    word_count = Counter(words)
    top_words = word_count.most_common(top_n)
    if logger:
        logger.debug(f"Top {top_n} words calculated: {top_words}")
    return top_words

def generate_word_cloud(danmaku_data, logger=None):
    if not danmaku_data or not isinstance(danmaku_data, list):
        if logger:
            logger.debug("Danmaku data is empty or invalid for word cloud")
        raise ValueError("未获取到弹幕数据")

    top_words = calculate_word_frequency(danmaku_data, logger=logger, top_n=200)
    word_freq = {word: freq for word, freq in top_words}

    mask = np.array(Image.open(MASK_PATH).convert('L')) if os.path.exists(MASK_PATH) else None
    wc = WordCloud(
        font_path=FONT_PATH,
        width=800,
        height=600,
        mask=mask,
        background_color=None,
        mode='RGBA',
        max_words=150,
        min_font_size=12,
        max_font_size=120,
        prefer_horizontal=0.7,
        colormap='plasma',
        contour_width=2,
        contour_color='white',
        random_state=42
    ).generate_from_frequencies(word_freq)

    if mask is not None:
        image_colors = ImageColorGenerator(np.array(wc.to_image()))
        wc.recolor(color_func=image_colors)

    img = wc.to_image()
    img_io = BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
    if logger:
        logger.debug("Word cloud image generated successfully")
    return f'data:image/png;base64,{img_base64}'

def generate_danmaku_timeline(danmaku_list, logger=None):
    try:
        FONT_PATH = r'C:\Windows\Fonts\simhei.ttf'
        EMOJI_FONT_PATH = r'C:\Windows\Fonts\seguiemj.ttf'

        if not isinstance(danmaku_list, list):
            raise ValueError(f"弹幕数据格式错误: 期望列表，实际为 {type(danmaku_list)}")

        timeline = {}
        for danmaku in danmaku_list:
            if not isinstance(danmaku, dict):
                logger.error(f"Invalid danmaku item: type={type(danmaku)}, value={danmaku}")
                continue
            time_str = danmaku.get('time', '00:00:00')
            minutes = int(time_str.split(":")[0]) * 60 + int(time_str.split(":")[1])
            timeline[minutes] = timeline.get(minutes, 0) + 1

        x = sorted(timeline.keys())
        y = [timeline[min_] for min_ in x]

        x_new = np.linspace(min(x), max(x), 500)
        spline = make_interp_spline(x, y, k=3)
        y_smooth = spline(x_new)

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.set_facecolor('#fef3f3')
        fig.patch.set_facecolor('#fef3f3')

        ax.fill_between(x_new, y_smooth, color='#fbc2eb', alpha=0.4)
        ax.plot(x_new, y_smooth, color='#f67070', linewidth=2.5)

        for spine in ax.spines.values():
            spine.set_edgecolor('#dddddd')
            spine.set_linewidth(1.5)

        font_prop = FontProperties(fname=FONT_PATH)
        emoji_font = FontProperties(fname=EMOJI_FONT_PATH)

        ax.set_title("弹幕随时间分布图", fontsize=18, fontproperties=font_prop, color='#444')
        ax.set_xlabel("时间（分钟）", fontsize=14, fontproperties=font_prop, color='#666')
        ax.set_ylabel("弹幕数量", fontsize=14, fontproperties=font_prop, color='#666')

        ax.tick_params(colors='#999', labelsize=10)
        ax.grid(alpha=0.3)

        peaks, _ = find_peaks(y_smooth, distance=30, prominence=2)
        peak_points = [(x_new[i], y_smooth[i]) for i in peaks]
        max_index = np.argmax(y_smooth)
        max_point = (x_new[max_index], y_smooth[max_index])
        if max_point not in peak_points:
            peak_points.append(max_point)

        top_peaks = sorted(peak_points, key=lambda p: p[1], reverse=True)[:3]
        for x_val, y_val in top_peaks:
            ax.scatter(x_val, y_val, color='gold', s=150, edgecolors='white', zorder=5)
            ax.text(x_val + 0.5, y_val + 5, '关键时刻', fontsize=13,
                    fontproperties=font_prop, color='crimson')

        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)

        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        if logger:
            logger.debug("Danmaku timeline chart generated successfully")
        return f"data:image/png;base64,{img_base64}"

    except Exception as e:
        if logger:
            logger.error(f"生成时间分布图失败: {str(e)}")
        raise

def generate_danmaku_time_proportion(danmaku_list, logger=None):
    try:
        if not danmaku_list or not isinstance(danmaku_list, list):
            app_logger.error("弹幕数据为空或格式错误")
            raise ValueError("弹幕数据为空或格式错误")

        app_logger.debug(f"Processing {len(danmaku_list)} danmaku entries for time proportion, sample: {danmaku_list[:5]}")
        
        # 提取小时
        hours = []
        for i, d in enumerate(danmaku_list):
            if not isinstance(d, dict):
                app_logger.error(f"Invalid danmaku item {i}: type={type(d)}, value={d}")
                raise ValueError(f"弹幕数据元素格式错误: 期望字典，实际为 {type(d)}")
            
            send_time = d.get('send_time', '1970-01-01 00:00:00')
            try:
                hour = int(send_time.split(' ')[1].split(':')[0]) % 24
                hours.append(hour)
            except (ValueError, IndexError) as e:
                app_logger.warning(f"Invalid send_time format in danmaku: {send_time}, error: {str(e)}, skipping")
                continue

        if not hours:
            app_logger.error("没有有效的弹幕发送时间数据")
            raise ValueError("没有有效的弹幕发送时间数据")

        # 统计每小时弹幕数量
        hour_counts = Counter(hours)
        labels = [f"{h}时" for h in range(24)]
        sizes = [hour_counts.get(h, 0) for h in range(24)]
        total = sum(sizes)
        if total == 0:
            app_logger.error("弹幕数量总和为 0")
            raise ValueError("弹幕数量总和为 0")

        # 合并小占比（<1%）为“其他”
        threshold = total * 0.01
        other_size = 0
        filtered_labels = []
        filtered_sizes = []
        for label, size in zip(labels, sizes):
            if size < threshold:
                other_size += size
            else:
                filtered_labels.append(label)
                filtered_sizes.append(size)
        if other_size > 0:
            filtered_labels.append("其他")
            filtered_sizes.append(other_size)

        # 创建画布
        fig, ax = plt.subplots(figsize=(6, 6), dpi=150)
        fig.patch.set_facecolor('#E8ECEF')
        ax.set_facecolor('none')

        # 高对比颜色
        colors = [
            '#FF6699', '#00A1D6', '#9966FF', '#FFCC33', '#66CC99',
            '#FF99CC', '#33B5E5', '#CC99FF', '#FFD700', '#99FF99',
            '#FF6666', '#3399FF', '#CC66CC', '#FFAA33', '#66CCCC',
            '#FF99AA', '#66B3FF', '#AA66CC', '#FFCC66', '#99CCCC',
            '#FF3366', '#0066CC', '#9933CC', '#CCCCCC'  # 最后为“其他”
        ]

        # 绘制甜甜圈图
        wedges, texts, autotexts = ax.pie(
            filtered_sizes,
            labels=filtered_labels,
            colors=colors[:len(filtered_sizes)],
            startangle=90,
            counterclock=False,
            wedgeprops={'width': 0.4, 'edgecolor': 'white', 'linewidth': 2.5, 'antialiased': True},
            textprops={'fontproperties': FontProperties(fname=r'C:\Windows\Fonts\simhei.ttf'), 'fontsize': 12, 'color': '#1A1A1A'},
            autopct=lambda p: f'{p:.1f}%' if p > 2 else '',
            pctdistance=0.82,
        )

        # 美化标签
        for text in texts:
            text.set_fontproperties(FontProperties(fname=r'C:\Windows\Fonts\simhei.ttf'))
            text.set_fontsize(12)
        for autotext in autotexts:
            autotext.set_fontproperties(FontProperties(fname=r'C:\Windows\Fonts\simhei.ttf'))
            autotext.set_fontsize(10)
            autotext.set_color('white')
            autotext.set_weight('bold')

        # 中心圆
        centre_circle = plt.Circle((0, 0), 0.6, fc='white')
        ax.add_artist(centre_circle)

        # 标题
        plt.title("弹幕发送时间分布", fontsize=18, fontproperties=FontProperties(fname=r'C:\Windows\Fonts\simhei.ttf'), color='#1A1A1A', pad=25)

        # 居中调整
        plt.subplots_adjust(left=0.15, right=0.85, top=0.85, bottom=0.15)

        # 保存
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)

        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        app_logger.debug("Danmaku time proportion donut chart generated successfully")
        return f"data:image/png;base64,{img_base64}"

    except Exception as e:
        app_logger.error(f"生成弹幕时间占比图失败: {str(e)}")
        raise