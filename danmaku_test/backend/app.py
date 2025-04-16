# 导入需要的库和模块
from flask import Flask, request, jsonify, send_from_directory  # Flask 框架核心组件及静态文件支持
from flask_cors import CORS  # 允许跨域请求
from modules.video_info import get_video_info, get_video_cid  # 获取视频信息和 CID
from modules.danmaku import fetch_danmaku  # 获取弹幕数据
from modules.cover_image import download_cover_image  # 下载封面图片
from modules.utils import handle_bv_input  # 处理 BV 号输入
from modules.logger import app_logger  # 日志工具
from modules.danmaku_analysis import calculate_word_frequency, generate_word_cloud, generate_danmaku_timeline
from modules.sentiment_analysis import analyze_sentiment
# python D:\Lernen\danmaku_test\danmaku_test\backend\app.py


# 创建 Flask 应用
app = Flask(__name__)
# 配置 CORS，允许特定来源（包括前端可能的地址和通配符）
CORS(app, resources={r"/api/*": {"origins": ["http://127.0.0.1:5000", "http://127.0.0.1:8000", "*"]}})

# 定义常量
save_folder = './static/danmaku'  # 保存弹幕文件的文件夹
headers = {  # 模拟浏览器请求头
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 提供前端静态文件
@app.route('/')
def serve_index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

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
        title, cover_path, up_name, up_link, video_duration, formatted_duration = get_video_info(bv)  # 获取视频信息
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

# API 路由：获取弹幕数据（新增搜索功能）
@app.route('/api/danmaku', methods=['POST'])
def danmaku():
    """处理前端发送的弹幕请求，支持分页和关键字搜索"""
    data = request.json
    bv_input = data.get('bv', '')  # 获取 BV 号
    page = data.get('page', 1)  # 获取页码，默认第 1 页
    per_page = data.get('per_page', 50)  # 每页条数，默认 50
    keyword = data.get('keyword', '').strip()  # 获取搜索关键字，默认空字符串，去除首尾空格
    app_logger.debug(f"Received request for danmaku: BV={bv_input}, page={page}, per_page={per_page}, keyword='{keyword}'")
    
    try:
        # 验证输入
        if not bv_input:
            raise ValueError("BV 号不能为空")
        if not isinstance(page, int) or page < 1:
            raise ValueError("页码必须是正整数")
        if not isinstance(per_page, int) or per_page < 1:
            raise ValueError("每页条数必须是正整数")

        bv = handle_bv_input(bv_input)  # 格式化 BV 号
        cid = get_video_cid(bv)  # 获取视频的 CID
        danmaku_data = fetch_danmaku(cid)  # 获取所有弹幕数据
        
        # 统一弹幕数据格式
        if isinstance(danmaku_data, dict):
            danmaku_data = danmaku_data.get('danmaku_list', [])
        if not isinstance(danmaku_data, (list, tuple)):
            raise ValueError("弹幕数据格式错误")
        if not danmaku_data:
            raise ValueError("未获取到弹幕数据")
        
        app_logger.debug(f"Total danmaku fetched: {len(danmaku_data)}")
        
        # 根据关键字过滤弹幕
        if keyword:
            filtered_danmaku = []
            for d in danmaku_data:
                content = str(d.get('content', ''))  # 强制转换为字符串
                if keyword in content:  # 直接匹配，保留原始大小写
                    filtered_danmaku.append(d)
            app_logger.debug(f"Filtered danmaku count with keyword '{keyword}': {len(filtered_danmaku)}")
            if not filtered_danmaku:
                app_logger.warning(f"No danmaku matched keyword '{keyword}', sample contents: {[d.get('content', '')[:20] for d in danmaku_data[:5]]}")
        else:
            filtered_danmaku = danmaku_data
            app_logger.debug(f"Total danmaku count (no keyword): {len(filtered_danmaku)}")

        # 分页处理
        total_items = len(filtered_danmaku)
        total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 1
        start = (page - 1) * per_page
        end = start + per_page
        paginated_danmaku = filtered_danmaku[start:end]

        return jsonify({
            'danmaku': paginated_danmaku,
            'total_pages': total_pages,
            'current_page': page,
            'total_items': total_items
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

# API：生成弹幕时间分布图
@app.route('/api/danmaku_timeline', methods=['POST', 'OPTIONS'])
def danmaku_timeline():
    if request.method == 'OPTIONS':
        response = jsonify({"message": "CORS preflight successful"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        response.headers.add('Access-Control-Max-Age', '86400')  # 缓存预检结果 24 小时
        return response, 200
    data = request.json
    bv_input = data.get('bv', '')
    app_logger.debug(f"Received request for danmaku timeline: BV={bv_input}")
    try:
        bv = handle_bv_input(bv_input)
        cid = get_video_cid(bv)
        danmaku_data = fetch_danmaku(cid)
        if isinstance(danmaku_data, dict):
            danmaku_data = danmaku_data.get('danmaku_list', [])
        if not danmaku_data:
            raise ValueError("未获取到弹幕数据")
        
        timeline_image = generate_danmaku_timeline(danmaku_data, logger=app_logger)
        
        response = jsonify({'image': timeline_image})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        app_logger.error(f"Error in danmaku timeline generation: {str(e)}")
        return jsonify({'error': f"时间分布图生成失败: {str(e)}"}), 400

@app.route('/api/sentiment', methods=['POST'])
def sentiment_analysis():
    """处理情感分析请求"""
    data = request.json
    bv_input = data.get('bv', '')
    try:
        bv = handle_bv_input(bv_input)
        cid = get_video_cid(bv)
        danmaku_data = fetch_danmaku(cid)
        if isinstance(danmaku_data, dict):
            danmaku_data = danmaku_data.get('danmaku_list', [])
        analysis_result = analyze_sentiment(danmaku_data)
        return jsonify(analysis_result)
    except Exception as e:
        app_logger.error(f"情感分析失败: {str(e)}")
        return jsonify({'error': f"情感分析失败: {str(e)}"}), 400
    
# 启动 Flask 应用
if __name__ == '__main__':
    app.run(debug=True, port=5000)