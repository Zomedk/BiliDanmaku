from collections import Counter  # 引入计数器，方便统计词频
import jieba  # 引入结巴分词库，用于分词
import os  # 用于文件和路径操作
from wordcloud import WordCloud, ImageColorGenerator  # 引入生成词云和图像色彩生成器
from io import BytesIO  # 用于将图片转换成字节流
import base64  # 用于将图片转为 base64 格式
from PIL import Image  # 用于处理图片
from modules.utils import hms_to_seconds  # 引入工具函数，可能用于时间转换
import numpy as np  # 引入 numpy，用于数组操作
import matplotlib.pyplot as plt  # 引入 matplotlib，用于绘图
from matplotlib.font_manager import FontProperties  # 用于设置字体
from scipy.interpolate import make_interp_spline  # 用于平滑曲线
from scipy.signal import find_peaks  # 用于查找数据峰值
from modules.logger import app_logger  # 引入日志模块，方便调试和记录错误
from collections import Counter
import logging
from matplotlib import font_manager
from openai import OpenAI
import json
import requests
from dotenv import load_dotenv
load_dotenv()
# 停用词文件路径
STOPWORDS_PATH = r'D:\Lernen\danmaku_test\danmaku_test\backend\stopwords_cn.txt'
# 字体文件路径
FONT_PATH = r'C:\Windows\Fonts\simhei.ttf'
# 蒙版图片路径
MASK_PATH = r'D:\Lernen\danmaku_test\backend\assets\circle_mask.png'

# 加载停用词
def load_stopwords(file_path):
    stopwords = set()  # 使用集合存储停用词，去重
    if os.path.exists(file_path):  # 如果停用词文件存在
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:  # 遍历文件每一行
                word = line.strip()  # 去除两端空格
                if word:  # 如果不是空行
                    stopwords.add(word)  # 将停用词添加到集合中
    else:
        app_logger.warning(f"Stopwords file not found at {file_path}")  # 如果文件找不到，记录警告
    return stopwords  # 返回停用词集合

# 加载停用词
STOP_WORDS = load_stopwords(STOPWORDS_PATH)

# 计算词频
def calculate_word_frequency(danmaku_data, logger=None, top_n=10):
    if not danmaku_data or not isinstance(danmaku_data, list):  # 如果弹幕数据为空或格式不正确
        if logger:
            logger.debug("Danmaku data is empty or invalid")  # 打印调试日志
        return []

    jieba.setLogLevel(0)  # 设置结巴分词的日志等级，避免打印日志
    words = []  # 存储所有分词后的词汇
    for item in danmaku_data:  # 遍历每一条弹幕数据
        try:
            if not isinstance(item, dict):  # 如果弹幕数据项不是字典格式
                logger.error(f"Invalid danmaku item: type={type(item)}, value={item}")
                continue
            content = item.get('content', '')  # 获取弹幕内容
            if not content:  # 如果弹幕内容为空，跳过
                continue
            seg_list = jieba.cut(content, cut_all=False)  # 进行分词，cut_all=False为精确模式
            # 过滤掉停用词和单个字符的词
            filtered_words = [word for word in seg_list if word not in STOP_WORDS and len(word) > 1]
            words.extend(filtered_words)  # 将过滤后的词添加到词汇列表中
        except Exception as e:
            if logger:
                logger.warning(f"Skipping invalid item: {e}")
            continue

    word_count = Counter(words)  # 统计词频
    top_words = word_count.most_common(top_n)  # 获取最常见的 top_n 个词
    if logger:
        logger.debug(f"Top {top_n} words calculated: {top_words}")
    return top_words  # 返回最常见的 top_n 个词和频次

# 生成词云图
def generate_word_cloud(danmaku_data, logger=None):
    if not danmaku_data or not isinstance(danmaku_data, list):  # 如果弹幕数据为空或格式错误
        if logger:
            logger.debug("Danmaku data is empty or invalid for word cloud")
        raise ValueError("未获取到弹幕数据")

    top_words = calculate_word_frequency(danmaku_data, logger=logger, top_n=200)  # 获取前 200 个词
    word_freq = {word: freq for word, freq in top_words}  # 构建词频字典

    # 读取蒙版图像（如果存在）
    mask = np.array(Image.open(MASK_PATH).convert('L')) if os.path.exists(MASK_PATH) else None
    # 生成词云
    wc = WordCloud(
        font_path=FONT_PATH,  # 设置字体路径
        width=800,
        height=600,
        mask=mask,  # 设置蒙版
        background_color=None,  # 背景透明
        mode='RGBA',
        max_words=150,  # 最多显示 150 个词
        min_font_size=12,  # 最小字体大小
        max_font_size=120,  # 最大字体大小
        prefer_horizontal=0.7,  # 词语显示横向的概率
        colormap='plasma',  # 词云颜色
        contour_width=2,  # 词云边框宽度
        contour_color='white',  # 词云边框颜色
        random_state=42  # 随机种子
    ).generate_from_frequencies(word_freq)  # 根据词频生成词云

    if mask is not None:  # 如果蒙版不为空，使用蒙版的颜色重新着色
        image_colors = ImageColorGenerator(np.array(wc.to_image()))
        wc.recolor(color_func=image_colors)

    # 将词云图保存为图片并转换为 Base64 格式
    img = wc.to_image()
    img_io = BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
    if logger:
        logger.debug("Word cloud image generated successfully")
    return f'data:image/png;base64,{img_base64}'  # 返回 base64 格式的图片



def generate_danmaku_timeline(danmaku_list, logger=None):
    try:
        # 定义字体路径，使用 Noto Sans SC 支持中文
        FONT_PATH = r'C:\Users\zzzwww\AppData\Local\Microsoft\Windows\Fonts\NotoSansSC-Regular.otf'  # 替换为 Noto Sans SC
        EMOJI_FONT_PATH = r'C:\Windows\Fonts\seguiemj.ttf'  # 表情符号字体

        # 检查输入数据是否为列表
        if not isinstance(danmaku_list, list):
            raise ValueError(f"弹幕数据格式错误: 期望列表，实际为 {type(danmaku_list)}")

        # 初始化时间线字典，统计每分钟的弹幕数量
        timeline = {}
        for danmaku in danmaku_list:
            if not isinstance(danmaku, dict):
                logger.error(f"Invalid danmaku item: type={type(danmaku)}, value={danmaku}")
                continue
            # 获取弹幕时间，默认为'00:00:00'
            time_str = danmaku.get('time', '00:00:00')
            # 将时间转换为分钟数（忽略秒数）
            minutes = int(time_str.split(":")[0]) * 60 + int(time_str.split(":")[1])
            # 累加该分钟的弹幕计数
            timeline[minutes] = timeline.get(minutes, 0) + 1

        # 提取时间轴（x）和弹幕数量（y）并排序
        x = sorted(timeline.keys())
        y = [timeline[min_] for min_ in x]

        # 创建画布和坐标轴，设置尺寸为12x6
        fig, ax = plt.subplots(figsize=(12, 6))
        # 设置坐标轴和画布背景色
        ax.set_facecolor('#e0f7fa')  # 浅蓝色背景
        fig.patch.set_facecolor('#e0f7fa')  # 统一背景

        # 检查数据点数量
        if len(x) < 4:
            # 数据点不足，使用简单折线图
            if logger:
                logger.warning(f"数据点不足（{len(x)}），使用简单折线图")
            ax.plot(x, y, color='#0077b6', linewidth=3)  # 蓝色折线
            ax.fill_between(x, y, color='#90e0ef', alpha=0.5)  # 浅蓝填充
        else:
            # 数据点足够，使用平滑曲线
            x_new = np.linspace(min(x), max(x), 500)
            spline = make_interp_spline(x, y, k=3)
            y_smooth = spline(x_new)
            y_smooth = np.maximum(y_smooth, 0)
            ax.fill_between(x_new, y_smooth, color='#90e0ef', alpha=0.5)  # 浅蓝填充
            ax.plot(x_new, y_smooth, color='#0077b6', linewidth=3)  # 蓝色曲线

        # 设置坐标轴边框样式
        for spine in ax.spines.values():
            spine.set_edgecolor('#b2ebf2')  # 浅蓝边框
            spine.set_linewidth=(2)
            spine.set_capstyle('round')  # 圆角边框

        # 加载字体属性
        font_prop = FontProperties(fname=FONT_PATH)

        # 设置标题和轴标签
        ax.set_title("弹幕随时间分布图", fontsize=20, fontproperties=font_prop, color='#023e8a', pad=15)
        ax.set_xlabel("时间（分钟）", fontsize=16, fontproperties=font_prop, color='#023e8a')
        ax.set_ylabel("弹幕数量", fontsize=16, fontproperties=font_prop, color='#023e8a')

        # 设置刻度颜色和网格
        ax.tick_params(colors='#666', labelsize=12, width=1.5)
        ax.grid(True, linestyle='--', alpha=0.4, color='#b2ebf2')

        # 检测峰值点（仅当数据点足够时）
        if len(x) >= 4:
            peaks, _ = find_peaks(y_smooth, distance=30, prominence=2)
            peak_points = [(x_new[i], y_smooth[i]) for i in peaks]
            max_index = np.argmax(y_smooth)
            max_point = (x_new[max_index], y_smooth[max_index])
            if max_point not in peak_points:
                peak_points.append(max_point)
            top_peaks = sorted(peak_points, key=lambda p: p[1], reverse=True)[:3]
            for x_val, y_val in top_peaks:
                ax.scatter(x_val, y_val, color='#ffd700', s=200, edgecolors='#ffffff', zorder=5)  # 黄色峰值点
                ax.text(x_val + 0.5, y_val + 5, '关键时刻', fontsize=14, fontproperties=font_prop, color='#023e8a')

        # 将图像保存到内存缓冲区
        buf = BytesIO()
        plt.tight_layout(pad=2)
        plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), dpi=150, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)

        # 将图像转换为base64编码
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
        # 1. 检查弹幕数据格式
        if not danmaku_list or not isinstance(danmaku_list, list):
            logger.error("弹幕数据为空或格式错误")
            raise ValueError("弹幕数据为空或格式错误")

        logger.debug(f"Processing {len(danmaku_list)} danmaku entries for time proportion, sample: {danmaku_list[:5]}")

        # 2. 提取每条弹幕的小时信息
        hours = []
        for i, d in enumerate(danmaku_list):
            if not isinstance(d, dict):
                logger.error(f"Invalid danmaku item {i}: type={type(d)}, value={d}")
                raise ValueError(f"弹幕数据元素格式错误: 期望字典，实际为 {type(d)}")

            send_time = d.get('send_time', '1970-01-01 00:00:00')
            try:
                hour = int(send_time.split(' ')[1].split(':')[0]) % 24
                hours.append(hour)
            except (ValueError, IndexError) as e:
                logger.warning(f"Invalid send_time format in danmaku: {send_time}, error: {str(e)}, skipping")

        if not hours:
            logger.error("没有有效的弹幕发送时间数据")
            raise ValueError("没有有效的弹幕发送时间数据")

        # 3. 统计每小时的弹幕数量
        hour_counts = Counter(hours)
        labels = [f"{h}时" for h in range(24)]
        sizes = [hour_counts.get(h, 0) for h in range(24)]
        total = sum(sizes)
        if total == 0:
            logger.error("弹幕数量总和为 0")
            raise ValueError("弹幕数量总和为 0")

        # 4. 合并小于 1% 的占比为“其他”
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

        # 5. 创建画布和配置样式
        fig, ax = plt.subplots(figsize=(6, 6), dpi=150)
        fig.patch.set_facecolor('#e0f7fa')  # 浅蓝色背景
        ax.set_facecolor('none')

        # 6. 定义蓝色渐变调色板
        colors = [
            '#0077b6', '#00b4d8', '#90e0ef', '#48cae4', '#0096c7',
            '#023e8a', '#66b3ff', '#3399ff', '#0066cc', '#b2ebf2',
            '#0077b6', '#00b4d8', '#90e0ef', '#48cae4', '#0096c7',
            '#023e8a', '#66b3ff', '#3399ff', '#0066cc', '#b2ebf2',
            '#0077b6', '#00b4d8', '#90e0ef', '#b2ebf2'  # 最后为“其他”
        ]

        # 7. 绘制甜甜圈图
        wedges, texts, autotexts = ax.pie(
            filtered_sizes,
            labels=filtered_labels,
            colors=colors[:len(filtered_sizes)],
            startangle=90,
            counterclock=False,
            wedgeprops={'width': 0.4, 'edgecolor': '#ffffff', 'linewidth': 3, 'antialiased': True},
            textprops={'fontproperties': FontProperties(fname=r'C:\Users\zzzwww\AppData\Local\Microsoft\Windows\Fonts\NotoSansSC-Regular.otf'), 'fontsize': 14, 'color': '#023e8a'},
            autopct=lambda p: f'{p:.1f}%' if p > 2 else '',
            pctdistance=0.82,
        )

        # 8. 美化标签和数字
        for text in texts:
            text.set_fontproperties(FontProperties(fname=r'C:\Users\zzzwww\AppData\Local\Microsoft\Windows\Fonts\NotoSansSC-Regular.otf'))
            text.set_fontsize(14)
        for autotext in autotexts:
            autotext.set_fontproperties(FontProperties(fname=r'C:\Users\zzzwww\AppData\Local\Microsoft\Windows\Fonts\NotoSansSC-Regular.otf'))
            autotext.set_fontsize(13)  # 增大字体
            autotext.set_color('#ffffff')
            autotext.set_weight('extra bold')  # 超粗体增强对比

        # 9. 绘制中心圆形
        centre_circle = plt.Circle((0, 0), 0.6, fc='white', ec='#b2ebf2', lw=2)
        ax.add_artist(centre_circle)

        # 10. 设置标题
        plt.title("弹幕发送时间分布", fontsize=20, fontproperties=FontProperties(fname=r'C:\Users\zzzwww\AppData\Local\Microsoft\Windows\Fonts\NotoSansSC-Regular.otf'), color='#023e8a', pad=25)

        # 11. 调整布局
        plt.subplots_adjust(left=0.15, right=0.85, top=0.85, bottom=0.15)

        # 12. 保存图像并转换为 Base64 格式
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, facecolor=fig.get_facecolor(), bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)

        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        logger.debug("Danmaku time proportion donut chart generated successfully")
        return f"data:image/png;base64,{img_base64}"

    except Exception as e:
        logger.error(f"生成弹幕时间占比图失败: {str(e)}")
        raise


def get_danmaku_length_distribution(danmaku_list, logger=None):
    try:
        if not danmaku_list or not isinstance(danmaku_list, list):
            logger.error("弹幕数据为空或格式错误")
            raise ValueError("弹幕数据为空或格式错误")

        logger.debug(f"Processing {len(danmaku_list)} danmaku entries for length distribution")

        # 设置中文字体，与 generate_danmaku_time_proportion 一致
        font_path = r'C:\Users\zzzwww\AppData\Local\Microsoft\Windows\Fonts\NotoSansSC-Regular.otf'
        font_prop = FontProperties(fname=font_path)

        # 统计弹幕长度
        short_count = 0  # 1-5字
        medium_count = 0  # 6-10字
        long_count = 0  # 11+字
        total_count = 0

        for d in danmaku_list:
            if not isinstance(d, dict) or 'content' not in d:
                logger.warning(f"Invalid danmaku item: {d}, skipping")
                continue
            content = d['content'] or ''
            length = len(content)
            total_count += 1
            if 1 <= length <= 5:
                short_count += 1
            elif 6 <= length <= 10:
                medium_count += 1
            elif length >= 11:
                long_count += 1

        if total_count == 0:
            logger.error("没有有效的弹幕数据")
            raise ValueError("没有有效的弹幕数据")

        # 计算占比
        short_percentage = (short_count / total_count * 100) if total_count > 0 else 0.0
        medium_percentage = (medium_count / total_count * 100) if total_count > 0 else 0.0
        long_percentage = (long_count / total_count * 100) if total_count > 0 else 0.0

        # 生成水平柱状图，匹配甜甜圈图的风格
        labels = ['短弹幕 (1-5字)', '中弹幕 (6-10字)', '长弹幕 (11+字)']
        percentages = [short_percentage, medium_percentage, long_percentage]
        colors = ['#0077b6', '#00b4d8', '#90e0ef']  # 蓝色系，与甜甜圈图一致
        edge_color = '#ffffff'  # 白色边框

        fig, ax = plt.subplots(figsize=(8, 4), dpi=150, facecolor='#e0f7fa')  # 浅蓝色背景
        ax.set_facecolor('none')  # 透明坐标轴背景
        bars = plt.barh(labels, percentages, color=colors, edgecolor=edge_color, linewidth=3, alpha=0.9)
        plt.xlabel('占比 (%)', fontsize=14, fontproperties=font_prop, color='#023e8a')
        plt.title('弹幕长度分布', fontsize=20, fontproperties=font_prop, color='#023e8a', pad=25)
        plt.grid(True, axis='x', linestyle='--', alpha=0.5, color='#b2ebf2')

        # 添加百分比标签
        for bar in bars:
            width = bar.get_width()
            plt.text(x=width + 1, y=bar.get_y() + bar.get_height()/2, s=f'{width:.1f}%', 
                     va='center', ha='left', fontsize=13, fontproperties=font_prop, 
                     color='#023e8a', weight='extra bold')

        # 美化样式
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#b2ebf2')
        ax.spines['bottom'].set_color('#b2ebf2')
        ax.tick_params(axis='both', colors='#023e8a', labelsize=14)
        for label in ax.get_yticklabels() + ax.get_xticklabels():
            label.set_fontproperties(font_prop)

        plt.subplots_adjust(left=0.15, right=0.85, top=0.85, bottom=0.15)

        # 保存为 Base64
        buf = BytesIO()
        plt.savefig(buf, format='PNG', dpi=150, facecolor=fig.get_facecolor(), bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        result = {
            "image": f"data:image/png;base64,{img_base64}"
        }

        logger.debug(f"Length distribution image generated: {result['image'][:50]}...")
        return result

    except Exception as e:
        logger.error(f"生成弹幕长度分布失败: {str(e)}")
        raise




def get_danmaku_color_distribution(danmaku_list, logger=None):
    try:
        if not danmaku_list or not isinstance(danmaku_list, list):
            logger.error("弹幕数据为空或格式错误")
            raise ValueError("弹幕数据为空或格式错误")

        logger.debug(f"Processing {len(danmaku_list)} danmaku entries for color distribution")

        # 统计颜色
        color_counts = Counter()
        total_count = 0

        for d in danmaku_list:
            if not isinstance(d, dict) or 'color' not in d:
                logger.warning(f"Invalid danmaku item: {d}, skipping")
                continue
            color_dec = d['color']
            try:
                # 将十进制颜色转换为十六进制
                color_hex = f"#{int(color_dec):06X}"
                color_counts[color_hex] += 1
                total_count += 1
            except (ValueError, TypeError):
                logger.warning(f"Invalid color value: {color_dec}, skipping")
                continue

        if total_count == 0:
            logger.error("没有有效的弹幕颜色数据")
            raise ValueError("没有有效的弹幕颜色数据")

        # 取前 5 种颜色，剩余归为“其他”
        top_colors = color_counts.most_common(5)
        other_count = total_count - sum(count for _, count in top_colors)

        result = []
        for color_hex, count in top_colors:
            result.append({
                "color": color_hex,
                "name": color_hex,  # 直接使用颜色代码
                "count": count,
                "percentage": (count / total_count * 100)
            })
        if other_count > 0:
            result.append({
                "color": "#CCCCCC",
                "name": "其他",
                "count": other_count,
                "percentage": (other_count / total_count * 100)
            })

        logger.debug(f"Color distribution: {result}")
        return result

    except Exception as e:
        logger.error(f"生成弹幕颜色分布失败: {str(e)}")
        raise

def calculate_active_users(danmaku_data, top_n=10):
    """
    统计弹幕数据中各发送者（hash）的发送次数，返回前 top_n 名列表。
    :param danmaku_data: list of dict, 每条弹幕包含 'hash' 字段
    :param top_n: int, 取前 N 名
    :return: list of dict, 如 [{'user_hash': 'abc123', 'count': 42}, ...]
    """
    # 1. 提取所有 hash
    hashes = [d.get('hash') for d in danmaku_data if 'hash' in d]
    # 2. 分组计数
    counts = Counter(hashes)  # collections.Counter 简洁统计��次数 :contentReference[oaicite:2]{index=2}
    # 3. 取前 N 名
    most_common = counts.most_common(top_n)  # 返回 [(hash, count), ...] :contentReference[oaicite:3]{index=3}
    # 4. 格式化输出
    return [{'user_hash': h, 'count': c} for h, c in most_common]
import openai
def get_danmaku_summary(danmaku_list, logger=None):
    try:
        if not danmaku_list or not isinstance(danmaku_list, list):
            if logger:
                logger.error("弹幕数据为空或格式错误")
            raise ValueError("弹幕数据为空或格式错误")

        if logger:
            logger.debug(f"Processing {len(danmaku_list)} danmaku entries for summary")

        # 格式化弹幕数据，使用 'hash' 作为发送者字段
        danmaku_text = ""
        for d in danmaku_list:
            if not isinstance(d, dict) or 'content' not in d or 'send_time' not in d or 'hash' not in d:
                if logger:
                    logger.warning(f"Invalid danmaku item: {d}, skipping")
                continue
            send_time = d['send_time']
            content = d['content'] or ''
            sender = d['hash'] or '匿名'
            danmaku_text += f"时间: {send_time}, 发送者: {sender}, 内容: {content}\n"

        if not danmaku_text:
            if logger:
                logger.error("没有有效的弹幕数据用于总结")
            raise ValueError("没有有效的弹幕数据用于总结")

        # DeepSeek API 调用，基于用户成功运行的代码
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            if logger:
                logger.error("未配置 DeepSeek API 密钥")
            raise ValueError("未配置 DeepSeek API 密钥")

        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        prompt = (
            "你是一个专业的弹幕分析助手。请根据以下弹幕数据，生成一份简洁的总结，突出关键内容、时间段和发送者的特点。总结应包括主要话题、情绪倾向（如积极、消极、幽默）以及重要的时间点。数据格式为：时间, 发送者, 内容。\n\n"
            f"{danmaku_text}\n"
            "请以简洁的段落形式输出总结，控制在 200 字以内。"
        )
        try:
            response = client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": "你是一个乐于助人的助手"},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            if not response.choices or not response.choices[0].message.content:
                if logger:
                    logger.error("DeepSeek API 返回无效响应")
                raise ValueError("DeepSeek API 返回无效响应")
            summary = response.choices[0].message.content
        except openai.APIConnectionError as e:
            if logger:
                logger.error(f"Connection error: {str(e)}")
            raise ValueError(f"Connection error: {str(e)}")
        except openai.AuthenticationError as e:
            if logger:
                logger.error(f"Authentication error: {str(e)}")
            raise ValueError(f"Authentication error: {str(e)}")
        except openai.RateLimitError as e:
            if logger:
                logger.error(f"Rate limit exceeded: {str(e)}")
            raise ValueError(f"Rate limit exceeded: {str(e)}")
        except Exception as e:
            if logger:
                logger.error(f"Unexpected error: {type(e).__name__} - {str(e)}")
            raise ValueError(f"Unexpected error: {type(e).__name__} - {str(e)}")

        if logger:
            logger.debug(f"Danmaku summary generated: {summary[:50]}...")

        return {"summary": summary}

    except Exception as e:
        if logger:
            logger.error(f"生成弹幕总结失败: {str(e)}")
        raise