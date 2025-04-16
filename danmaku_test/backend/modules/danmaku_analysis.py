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

# 生成弹幕时间分布图
def generate_danmaku_timeline(danmaku_list, logger=None):
    try:
        # 定义字体路径，用于支持中文和表情符号显示
        FONT_PATH = r'C:\Windows\Fonts\simhei.ttf'  # 中文字体
        EMOJI_FONT_PATH = r'C:\Windows\Fonts\seguiemj.ttf'  # 表情符号字体

        # 检查输入数据是否为列表
        if not isinstance(danmaku_list, list):
            raise ValueError(f"弹幕数据格式错误: 期望列表，实际为 {type(danmaku_list)}")

        # 初始化时间线字典，统计每分钟的弹幕数量
        timeline = {}
        for danmaku in danmaku_list:
            if not isinstance(danmaku, dict):
                # 记录无效弹幕数据并跳过
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

        # 创建平滑曲线：生成500个均匀分布的x值
        x_new = np.linspace(min(x), max(x), 500)
        # 使用三次样条插值生成平滑曲线
        spline = make_interp_spline(x, y, k=3)
        y_smooth = spline(x_new)
        # 确保弹幕数量非负，修复样条插值可能产生的负值
        y_smooth = np.maximum(y_smooth, 0)

        # 创建画布和坐标轴，设置尺寸为12x6
        fig, ax = plt.subplots(figsize=(12, 6))
        # 设置坐标轴和画布背景色
        ax.set_facecolor('#fef3f3')
        fig.patch.set_facecolor('#fef3f3')

        # 绘制填充区域和曲线
        ax.fill_between(x_new, y_smooth, color='#fbc2eb', alpha=0.4)  # 粉色填充
        ax.plot(x_new, y_smooth, color='#f67070', linewidth=2.5)  # 红色曲线

        # 设置坐标轴边框样式
        for spine in ax.spines.values():
            spine.set_edgecolor('#dddddd')
            spine.set_linewidth(1.5)

        # 加载字体属性
        font_prop = FontProperties(fname=FONT_PATH)  # 中文字体
        emoji_font = FontProperties(fname=EMOJI_FONT_PATH)  # 表情符号字体（未使用）

        # 设置标题和轴标签
        ax.set_title("弹幕随时间分布图", fontsize=18, fontproperties=font_prop, color='#444')
        ax.set_xlabel("时间（分钟）", fontsize=14, fontproperties=font_prop, color='#666')
        ax.set_ylabel("弹幕数量", fontsize=14, fontproperties=font_prop, color='#666')

        # 设置刻度颜色和网格
        ax.tick_params(colors='#999', labelsize=10)
        ax.grid(alpha=0.3)

        # 检测峰值点（关键时刻）
        peaks, _ = find_peaks(y_smooth, distance=30, prominence=2)
        peak_points = [(x_new[i], y_smooth[i]) for i in peaks]
        # 找到最大值点，确保包含在峰值列表中
        max_index = np.argmax(y_smooth)
        max_point = (x_new[max_index], y_smooth[max_index])
        if max_point not in peak_points:
            peak_points.append(max_point)

        # 选择最大的三个峰值点
        top_peaks = sorted(peak_points, key=lambda p: p[1], reverse=True)[:3]
        for x_val, y_val in top_peaks:
            # 在峰值点绘制金色圆点
            ax.scatter(x_val, y_val, color='gold', s=150, edgecolors='white', zorder=5)
            # 添加“关键时刻”标注
            ax.text(x_val + 0.5, y_val + 5, '关键时刻', fontsize=13,
                    fontproperties=font_prop, color='crimson')

        # 将图像保存到内存缓冲区
        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', facecolor=fig.get_facecolor())
        plt.close(fig)  # 关闭画布，释放内存
        buf.seek(0)

        # 将图像转换为base64编码
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        if logger:
            logger.debug("Danmaku timeline chart generated successfully")
        # 返回图像的base64数据URL
        return f"data:image/png;base64,{img_base64}"

    except Exception as e:
        # 记录错误并抛出异常
        if logger:
            logger.error(f"生成时间分布图失败: {str(e)}")
        raise


def generate_danmaku_time_proportion(danmaku_list, logger=None):
    try:
        # 1. 检查弹幕数据格式
        if not danmaku_list or not isinstance(danmaku_list, list):
            app_logger.error("弹幕数据为空或格式错误")  # 如果数据为空或格式不对，记录错误
            raise ValueError("弹幕数据为空或格式错误")

        app_logger.debug(f"Processing {len(danmaku_list)} danmaku entries for time proportion, sample: {danmaku_list[:5]}")  # 调试：显示前 5 条弹幕数据

        # 2. 提取每条弹幕的小时信息
        hours = []  # 用来存储每条弹幕发送的小时
        for i, d in enumerate(danmaku_list):
            if not isinstance(d, dict):  # 如果弹幕数据不是字典类型
                app_logger.error(f"Invalid danmaku item {i}: type={type(d)}, value={d}")  # 记录错误日志
                raise ValueError(f"弹幕数据元素格式错误: 期望字典，实际为 {type(d)}")

            send_time = d.get('send_time', '1970-01-01 00:00:00')  # 获取弹幕的发送时间，默认为一个无效时间
            try:
                # 提取小时信息，取24小时制
                hour = int(send_time.split(' ')[1].split(':')[0]) % 24  # 获取小时并处理为 24 小时制
                hours.append(hour)  # 将小时添加到列表中
            except (ValueError, IndexError) as e:
                app_logger.warning(f"Invalid send_time format in danmaku: {send_time}, error: {str(e)}, skipping")  # 弹幕时间格式错误时，记录警告并跳过

        if not hours:  # 如果没有有效的小时数据
            app_logger.error("没有有效的弹幕发送时间数据")
            raise ValueError("没有有效的弹幕发送时间数据")

        # 3. 统计每小时的弹幕数量
        hour_counts = Counter(hours)  # 计算每个小时的弹幕数量
        labels = [f"{h}时" for h in range(24)]  # 每小时的标签（例如：0时，1时，...）
        sizes = [hour_counts.get(h, 0) for h in range(24)]  # 获取每小时的弹幕数量
        total = sum(sizes)  # 计算总弹幕数
        if total == 0:  # 如果总弹幕数为 0
            app_logger.error("弹幕数量总和为 0")
            raise ValueError("弹幕数量总和为 0")

        # 4. 合并小于 1% 的占比为“其他”
        threshold = total * 0.01  # 设置 1% 的占比作为阈值
        other_size = 0  # 统计小于 1% 的占比
        filtered_labels = []  # 过滤后的标签列表
        filtered_sizes = []  # 过滤后的数量列表
        for label, size in zip(labels, sizes):
            if size < threshold:  # 如果该小时的占比小于 1%
                other_size += size  # 将其合并到“其他”
            else:
                filtered_labels.append(label)  # 保留大于 1% 的标签
                filtered_sizes.append(size)  # 保留大于 1% 的数量
        if other_size > 0:  # 如果有小占比的数据合并为“其他”
            filtered_labels.append("其他")  # 添加“其他”标签
            filtered_sizes.append(other_size)  # 添加“其他”占比

        # 5. 创建画布和配置样式
        fig, ax = plt.subplots(figsize=(6, 6), dpi=150)  # 创建一个 6x6 英寸的画布，分辨率为 150
        fig.patch.set_facecolor('#E8ECEF')  # 设置画布背景颜色
        ax.set_facecolor('none')  # 设置坐标轴背景透明

        # 6. 选择高对比颜色方案
        colors = [
            '#FF6699', '#00A1D6', '#9966FF', '#FFCC33', '#66CC99',
            '#FF99CC', '#33B5E5', '#CC99FF', '#FFD700', '#99FF99',
            '#FF6666', '#3399FF', '#CC66CC', '#FFAA33', '#66CCCC',
            '#FF99AA', '#66B3FF', '#AA66CC', '#FFCC66', '#99CCCC',
            '#FF3366', '#0066CC', '#9933CC', '#CCCCCC'  # 最后为“其他”
        ]

        # 7. 绘制甜甜圈图
        wedges, texts, autotexts = ax.pie(
            filtered_sizes,  # 使用过滤后的弹幕数量
            labels=filtered_labels,  # 使用过滤后的标签
            colors=colors[:len(filtered_sizes)],  # 使用高对比色
            startangle=90,  # 从顶部开始绘制
            counterclock=False,  # 顺时针方向绘制
            wedgeprops={'width': 0.4, 'edgecolor': 'white', 'linewidth': 2.5, 'antialiased': True},  # 设置甜甜圈的样式
            textprops={'fontproperties': FontProperties(fname=r'C:\Windows\Fonts\simhei.ttf'), 'fontsize': 12, 'color': '#1A1A1A'},  # 设置文字样式
            autopct=lambda p: f'{p:.1f}%' if p > 2 else '',  # 小于 2% 的占比不显示
            pctdistance=0.82,  # 设置文本的距离
        )

        # 8. 美化标签和数字
        for text in texts:
            text.set_fontproperties(FontProperties(fname=r'C:\Windows\Fonts\simhei.ttf'))  # 设置标签字体
            text.set_fontsize(12)  # 设置字体大小
        for autotext in autotexts:
            autotext.set_fontproperties(FontProperties(fname=r'C:\Windows\Fonts\simhei.ttf'))  # 设置数字字体
            autotext.set_fontsize(10)  # 设置数字字体大小
            autotext.set_color('white')  # 设置数字字体颜色为白色
            autotext.set_weight('bold')  # 设置数字字体为粗体

        # 9. 绘制中心圆形
        centre_circle = plt.Circle((0, 0), 0.6, fc='white')  # 绘制一个半径为 0.6 的白色圆形
        ax.add_artist(centre_circle)  # 添加到图形中

        # 10. 设置标题
        plt.title("弹幕发送时间分布", fontsize=18, fontproperties=FontProperties(fname=r'C:\Windows\Fonts\simhei.ttf'), color='#1A1A1A', pad=25)

        # 11. 调整布局，保证图表居中
        plt.subplots_adjust(left=0.15, right=0.85, top=0.85, bottom=0.15)

        # 12. 保存图像并转换为 Base64 格式
        buf = BytesIO()  # 创建字节流对象
        plt.savefig(buf, format='png', dpi=150, facecolor=fig.get_facecolor())  # 保存为 PNG 格式
        plt.close(fig)  # 关闭图形，释放内存
        buf.seek(0)  # 将指针移回文件开始位置

        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')  # 将图像转换为 Base64 格式
        app_logger.debug("Danmaku time proportion donut chart generated successfully")  # 记录成功日志
        return f"data:image/png;base64,{img_base64}"  # 返回图像的 Base64 编码

    except Exception as e:
        app_logger.error(f"生成弹幕时间占比图失败: {str(e)}")  # 捕获异常并记录错误日志
        raise  # 重新抛出异常
