# 导入需要的库和模块
from flask import Flask, request, jsonify  # Flask 框架核心组件
from flask_cors import CORS  # 允许跨域请求
from modules.video_info import get_video_info, get_video_cid  # 获取视频信息和 CID
from modules.danmaku import fetch_danmaku  # 获取弹幕数据
from modules.cover_image import download_cover_image  # 下载封面图片
from modules.utils import handle_bv_input  # 处理 BV 号输入
from modules.logger import app_logger  # 日志工具
from modules.danmaku_analysis import calculate_word_frequency, generate_word_cloud  # 词频和词云生成

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 定义常量
save_folder = './static/danmaku'  # 保存弹幕文件的文件夹
headers = {  # 模拟浏览器请求头
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# API 路由：获取视频信息
@app.route('/api/video', methods=['POST'])
def video_info():
    """处理前端发送的视频信息请求"""
    data = request.json  # 获取前端发送的 JSON 数据
    bv_input = data.get('bv', '')  # 从 JSON 中提取 BV 号，默认空字符串
    app_logger.debug(f"Received BV input: {bv_input}")  # 记录收到的 BV 号
    try:
        app_logger.debug("Processing video info")  # 记录处理开始
        bv = handle_bv_input(bv_input)  # 格式化 BV 号
        title, cover_path, up_name, up_link = get_video_info(bv)  # 获取视频信息
        app_logger.debug(f"Video Info: {title}, {cover_path}, {up_name}, {up_link}")  # 记录结果
        return jsonify({  # 返回 JSON 数据给前端
            'title': title,
            'cover': cover_path,
            'up_name': up_name,
            'up_link': up_link
        })
    except Exception as e:  # 捕获任何错误
        app_logger.error(f"Error: {str(e)}")  # 记录错误
        return jsonify({'error': str(e)}), 400  # 返回错误信息，状态码 400

# API 路由：获取弹幕数据
@app.route('/api/danmaku', methods=['POST'])
def danmaku():
    """处理前端发送的弹幕请求，支持分页"""
    data = request.json
    bv_input = data.get('bv', '')  # 获取 BV 号
    page = data.get('page', 1)  # 获取页码，默认第 1 页
    per_page = data.get('per_page', 50)  # 每页条数，默认 50
    app_logger.debug(f"Received request for danmaku: BV={bv_input}, page={page}, per_page={per_page}")
    try:
        bv = handle_bv_input(bv_input)  # 格式化 BV 号
        cid = get_video_cid(bv)  # 获取视频的 CID
        danmaku_data = fetch_danmaku(cid)  # 获取弹幕数据
        if isinstance(danmaku_data, dict):  # 如果返回的是字典
            danmaku_data = danmaku_data.get('danmaku_list', [])  # 提取弹幕列表
        if not danmaku_data:  # 如果没有数据
            raise Exception("未获取到弹幕数据")
        start = (page - 1) * per_page  # 计算分页起始位置
        end = start + per_page  # 计算结束位置
        paginated_danmaku = danmaku_data[start:end]  # 分页数据
        total_pages = (len(danmaku_data) + per_page - 1) // per_page  # 计算总页数
        return jsonify({  # 返回分页结果
            'danmaku': paginated_danmaku,
            'total_pages': total_pages,
            'current_page': page
        })
    except Exception as e:
        app_logger.error(f"Error fetching danmaku: {str(e)}")
        return jsonify({'error': str(e)}), 400

# API 路由：获取词频统计
@app.route('/api/word_frequency', methods=['POST'])
def word_frequency():
    """处理前端发送的词频统计请求"""
    data = request.json
    bv_input = data.get('bv', '')
    app_logger.debug(f"Received request for word frequency: BV={bv_input}")
    try:
        bv = handle_bv_input(bv_input)
        cid = get_video_cid(bv)
        danmaku_data = fetch_danmaku(cid)
        if isinstance(danmaku_data, dict):
            danmaku_data = danmaku_data.get('danmaku_list', [])
        if not danmaku_data:
            raise ValueError("未获取到弹幕数据")
        top_words = calculate_word_frequency(danmaku_data, logger=app_logger)  # 计算词频，默认 top_n=10
        app_logger.debug(f"Word frequency calculated: {top_words[:5]}...")
        return jsonify({'top_words': top_words})
    except Exception as e:
        app_logger.error(f"Error in word frequency calculation: {str(e)}")
        return jsonify({'error': f"词频统计失败: {str(e)}"}), 400

# API 路由：生成词云图
@app.route('/api/word_cloud', methods=['POST'])
def word_cloud():
    """处理前端发送的词云图请求"""
    data = request.json
    bv_input = data.get('bv', '')
    app_logger.debug(f"Received request for word cloud: BV={bv_input}")
    try:
        bv = handle_bv_input(bv_input)
        cid = get_video_cid(bv)
        danmaku_data = fetch_danmaku(cid)
        if isinstance(danmaku_data, dict):
            danmaku_data = danmaku_data.get('danmaku_list', [])
        if not danmaku_data:
            raise ValueError("未获取到弹幕数据")
        
        # 调用生成词云函数
        word_cloud_image = generate_word_cloud(danmaku_data, logger=app_logger)
        
        return jsonify({'image': word_cloud_image})  # 返回 Base64 图片
    except Exception as e:
        app_logger.error(f"Error in word cloud generation: {str(e)}")
        return jsonify({'error': f"词云图生成失败: {str(e)}"}), 400

# 启动 Flask 应用
if __name__ == '__main__':
    app.run(debug=True)  # 调试模式运行，方便开发时查看错误