# -------------------- 引入各种需要用的模块 --------------------
from flask import Flask, request, jsonify, send_from_directory  # Flask 的核心功能
from flask_cors import CORS  # 解决跨域问题用的

# 下面这些是自己写的模块，分别负责处理视频信息、弹幕、封面、工具函数、日志等等
from modules.video_info import get_video_info, get_video_cid
from modules.danmaku import fetch_danmaku
from modules.cover_image import download_cover_image
from modules.utils import handle_bv_input
from modules.logger import app_logger
from modules.danmaku_analysis import calculate_word_frequency, generate_word_cloud, generate_danmaku_timeline, generate_danmaku_time_proportion, calculate_active_users
from modules.sentiment_analysis import analyze_sentiment
import datetime  # 时间相关的操作要用到
from modules.hash_to_uid import hash_to_uid
from modules.auth import login_user, register_user
# -------------------- 初始化 Flask 应用 --------------------
app = Flask(__name__)

# 设置跨域允许的地址（本地前端访问后端要用）
CORS(app, resources={r"/api/*": {"origins": ["http://127.0.0.1:5000", "http://127.0.0.1:8000", "*"]}})

# 设置静态文件保存路径（比如弹幕图片、词云图什么的）
save_folder = './static/danmaku'

# 浏览器请求时用的 headers，这个是防止被 B 站拒绝访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# -------------------- 首页和静态资源 --------------------

# 打开网站首页（前端是静态页面）
@app.route('/')
def serve_index():
    return send_from_directory('../frontend', 'login.html')  # 改为返回login.html

@app.route('/index.html')
def serve_main():
    return send_from_directory('../frontend', 'index.html')

# 访问其他静态资源（比如 js、css 文件）
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

# -------------------- 获取视频信息接口 --------------------
@app.route('/api/video', methods=['POST'])
def video_info():
    data = request.json
    bv_input = data.get('bv', '')  # 拿到前端传来的 BV 号
    app_logger.debug(f"Received BV input: {bv_input}")
    try:
        bv = handle_bv_input(bv_input)  # 处理一下（防止用户乱输）
        app_logger.debug(f"Parsed BV: {bv}")

        # 获取视频信息（包括标题、封面、up主名、链接、时长等）
        title, cover_path, up_name, up_link, video_duration, formatted_duration = get_video_info(bv)
        app_logger.debug(f"Video Info: title={title}, cover={cover_path}, up_name={up_name}, up_link={up_link}, duration={video_duration}")

        # 把需要的内容打包返回给前端
        return jsonify({
            'title': title,
            'cover': cover_path,
            'up_name': up_name,
            'up_link': up_link
        })
    except Exception as e:
        app_logger.error(f"Error in video_info: {str(e)}")
        return jsonify({'error': str(e)}), 400

# -------------------- 获取弹幕接口（支持分页、关键词过滤） --------------------
@app.route('/api/danmaku', methods=['POST'])
def danmaku():
    data = request.json
    bv_input = data.get('bv', '')
    page = data.get('page', 1)
    per_page = data.get('per_page', 50)
    keyword = data.get('keyword', '').strip()
    sort_by = data.get('sort_by', 'time')  # 默认按 time 排序
    sort_order = data.get('sort_order', 'asc')  # 默认升序
    app_logger.debug(f"Received request for danmaku: BV={bv_input}, page={page}, per_page={per_page}, keyword='{keyword}', sort_by={sort_by}, sort_order={sort_order}")
    
    try:
        # 一些基础的参数校验
        if not bv_input:
            raise ValueError("BV 号不能为空")
        if not isinstance(page, int) or page < 1:
            raise ValueError("页码必须是正整数")
        if not isinstance(per_page, int) or per_page < 1:
            raise ValueError("每页条数必须是正整数")
        if sort_by not in ['time', 'send_time']:
            raise ValueError("sort_by 必须是 'time' 或 'send_time'")
        if sort_order not in ['asc', 'desc']:
            raise ValueError("sort_order 必须是 'asc' 或 'desc'")

        bv = handle_bv_input(bv_input)
        cid = get_video_cid(bv)  # 拿到这个 BV 对应的视频 CID
        danmaku_data = fetch_danmaku(cid)  # 抓取弹幕数据
        
        # 校验弹幕数据结构是否正确
        if not isinstance(danmaku_data, list):
            raise ValueError(f"弹幕数据格式错误: 期望列表，实际为 {type(danmaku_data)}")
        if not danmaku_data:
            raise ValueError("未获取到弹幕数据")
        
        for i, d in enumerate(danmaku_data[:5]):
            if not isinstance(d, dict):
                raise ValueError(f"弹幕数据元素格式错误: 期望字典，实际为 {type(d)}")
            if 'time' not in d or 'send_time' not in d or 'hash' not in d or 'content' not in d:
                raise ValueError(f"弹幕数据缺少必要字段: {d}")
        
        # 根据关键词筛选弹幕
        filtered_danmaku = []
        if keyword:
            for d in danmaku_data:
                content = str(d.get('content', ''))
                if keyword.lower() in content.lower():
                    filtered_danmaku.append(d)
        else:
            filtered_danmaku = danmaku_data

        # 定义排序规则（根据 time 或 send_time 转成数字/时间戳）
        def get_time_sort_key(d):
            try:
                if sort_by == 'time':
                    h, m, s = map(int, d.get('time', '00:00:00').split(':'))
                    return h * 3600 + m * 60 + s
                else:
                    return datetime.datetime.strptime(d.get('send_time', '1970-01-01 00:00:00'), '%Y-%m-%d %H:%M:%S').timestamp()
            except Exception:
                return 0

        # 排序
        filtered_danmaku.sort(key=get_time_sort_key, reverse=(sort_order == 'desc'))

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

# -------------------- 词频统计接口 --------------------
@app.route('/api/word_frequency', methods=['POST'])
def word_frequency():
    data = request.json
    bv_input = data.get('bv', '')
    try:
        bv = handle_bv_input(bv_input)
        cid = get_video_cid(bv)
        danmaku_data = fetch_danmaku(cid)

        if not isinstance(danmaku_data, list) or not danmaku_data:
            raise ValueError("弹幕数据格式错误或为空")
        
        top_words = calculate_word_frequency(danmaku_data, logger=app_logger)
        return jsonify({'top_words': top_words})
    except Exception as e:
        return jsonify({'error': f"词频统计失败: {str(e)}"}), 400

# -------------------- 词云图接口 --------------------
@app.route('/api/word_cloud', methods=['POST'])
def word_cloud():
    data = request.json
    bv_input = data.get('bv', '')
    try:
        bv = handle_bv_input(bv_input)
        cid = get_video_cid(bv)
        danmaku_data = fetch_danmaku(cid)

        if not isinstance(danmaku_data, list) or not danmaku_data:
            raise ValueError("弹幕数据格式错误或为空")
        
        word_cloud_image = generate_word_cloud(danmaku_data, logger=app_logger)
        return jsonify({'image': word_cloud_image})
    except Exception as e:
        return jsonify({'error': f"词云图生成失败: {str(e)}"}), 400

# -------------------- 弹幕时间线图接口（即弹幕随时间的分布） --------------------
@app.route('/api/danmaku_timeline', methods=['POST', 'OPTIONS'])
def danmaku_timeline():
    if request.method == 'OPTIONS':
        # 处理预检请求（跨域用）
        response = jsonify({"message": "CORS preflight successful"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        response.headers.add('Access-Control-Max-Age', '86400')
        return response, 200

    data = request.json
    bv_input = data.get('bv', '')
    try:
        bv = handle_bv_input(bv_input)
        cid = get_video_cid(bv)
        danmaku_data = fetch_danmaku(cid)

        if not isinstance(danmaku_data, list) or not danmaku_data:
            raise ValueError("弹幕数据格式错误或为空")
        
        timeline_image = generate_danmaku_timeline(danmaku_data, logger=app_logger)
        response = jsonify({'image': timeline_image})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        return jsonify({'error': f"时间分布图生成失败: {str(e)}"}), 400

# -------------------- 情感分析接口 --------------------
@app.route('/api/sentiment', methods=['POST'])
def sentiment_analysis():
    data = request.json
    bv_input = data.get('bv', '')
    try:
        bv = handle_bv_input(bv_input)
        cid = get_video_cid(bv)
        danmaku_data = fetch_danmaku(cid)

        if not isinstance(danmaku_data, list) or not danmaku_data:
            raise ValueError("弹幕数据格式错误或为空")
        
        analysis_result = analyze_sentiment(danmaku_data)
        return jsonify(analysis_result)
    except Exception as e:
        return jsonify({'error': f"情感分析失败: {str(e)}"}), 400

# -------------------- 弹幕时间占比图接口 --------------------
@app.route('/api/danmaku_time_proportion', methods=['POST'])
def danmaku_time_proportion():
    data = request.json
    bv_input = data.get('bv', '')
    try:
        if not bv_input:
            raise ValueError("BV 号不能为空")
        bv = handle_bv_input(bv_input)
        cid = get_video_cid(bv)
        danmaku_data = fetch_danmaku(cid)

        if not isinstance(danmaku_data, list) or not danmaku_data:
            raise ValueError("弹幕数据格式错误或为空")
        
        image = generate_danmaku_time_proportion(danmaku_data, logger=app_logger)
        return jsonify({'image': image})
    except Exception as e:
        return jsonify({'error': f"生成时间占比图失败: {str(e)}"}), 400
    


@app.route('/api/active_users', methods=['GET'])
def active_users():
  # 原始弹幕获取逻辑
   # 获取所有弹幕数据（可重用现有 fetch_danmaku + get_video_cid）
    bv_input = request.args.get('bv', '')
    bv = handle_bv_input(bv_input)
    cid = get_video_cid(bv)
    danmaku_data = fetch_danmaku(cid)
   # TODO: 调用统计函数，返回前 10 名活跃用户
    # 调用统计函数，取前 10 名
    top_users = calculate_active_users(danmaku_data, top_n=10)
    return jsonify({'active_users': top_users})

@app.route('/api/user_uid', methods=['GET'])
def user_uid():
    user_hash = request.args.get('hash', '')
    bv_input = request.args.get('bv', '')
    bv = handle_bv_input(bv_input)
    cid = get_video_cid(bv)
    _ = fetch_danmaku(cid)  # 这里只是为了和前端一致，实际不需要弹幕

    uid = hash_to_uid(user_hash)
    if uid == -1:
        return jsonify({'uid': None})
    return jsonify({'uid': uid})

# 登录接口
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'error': '用户名或密码不能为空'}), 400
    if login_user(username, password):
        return jsonify({'message': '登录成功'})
    return jsonify({'error': '用户名或密码错误'}), 401

# 注册接口
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'error': '用户名或密码不能为空'}), 400
    if register_user(username, password):
        return jsonify({'message': '注册成功'})
    return jsonify({'error': '用户名已存在'}), 400

# -------------------- 启动 Flask 应用 --------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)  # debug=True 可以看到详细错误信息（开发阶段用）
