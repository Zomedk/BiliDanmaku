# C:\Users\zzw\AppData\Local\Programs\Python\Python38\python.exe D:\Lernen\danmaku_test\backend\app.py
# python D:\Lernen\danmaku_test\danmaku_test\backend\app.py
# https://www.bilibili.com/video/BV1PCwLe2Ei6/?spm_id_from=333.999.0.0
from flask import Flask, request, jsonify  # 从Flask框架导入Flask、request和jsonify模块
from flask_cors import CORS  # 从flask_cors库导入CORS模块，用于跨域请求
from modules.video_info import get_video_info, get_video_cid  # 从video_info模块导入获取视频信息和视频CID的函数
from modules.danmaku import fetch_danmaku  # 从danmaku模块导入获取弹幕数据的函数
from modules.cover_image import download_cover_image  # 从cover_image模块导入下载封面图片的函数
from modules.utils import handle_bv_input  # 从utils模块导入处理BV号的函数
from modules.logger import app_logger  # 使用app_logger作为日志记录器
from modules.danmaku_analysis import calculate_word_frequency

app = Flask(__name__)  # 创建Flask应用实例
# 启用 CORS，允许所有来源访问
CORS(app)  # 跨域资源共享设置，允许跨域请求

# 用于保存弹幕文件的文件夹路径
save_folder = './static/danmaku'

# 请求头设置，用于模拟浏览器发送请求
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# API 路由：处理视频信息请求
@app.route('/api/video', methods=['POST'])
def video_info():
    # 从请求体中获取JSON数据
    data = request.json
    bv_input = data.get('bv', '')  # 从请求中获取BV号（视频ID）
    
    # 打印收到的 BV 输入数据到日志
    app_logger.debug(f"Received BV input: {bv_input}")
    
    try:
        app_logger.debug("Processing video info")
        # 调用处理 BV 输入的函数，获取正确的BV号（用于解析）
        bv = handle_bv_input(bv_input)
        
        # 获取视频信息，包括标题、封面图片路径、UP主名称和链接
        title, cover_path, up_name, up_link = get_video_info(bv)
        
        # 打印返回的视频信息到日志
        app_logger.debug(f"Video Info: {title}, {cover_path}, {up_name}, {up_link}")
        
        # 将视频信息返回给前端，使用jsonify将字典转换为JSON响应
        return jsonify({
            'title': title,
            'cover': cover_path,
            'up_name': up_name,
            'up_link': up_link
        })
    except Exception as e:
        # 捕获异常并记录错误日志
        app_logger.error(f"Error: {str(e)}")
        # 如果发生错误，返回错误信息给前端，状态码为400（Bad Request）
        return jsonify({'error': str(e)}), 400
    
# API 路由：爬取弹幕数据 
# 弹幕数据接口：处理分页
@app.route('/api/danmaku', methods=['POST'])
def danmaku():
    # 从请求体中获取JSON数据
    data = request.json
    bv_input = data.get('bv', '')  # 从前端获取 BV 号
    page = data.get('page', 1)  # 获取当前页码，默认为第1页
    per_page = data.get('per_page', 50)  # 获取每页显示的弹幕数，默认为10条
    
    # 打印收到的请求数据到日志
    app_logger.debug(f"Received request for danmaku: BV={bv_input}, page={page}, per_page={per_page}")
    
    try:
        # 调用处理 BV 输入的函数，获取视频的 CID（视频的唯一标识符）
        bv = handle_bv_input(bv_input)
        cid = get_video_cid(bv)  # 获取该视频的CID
        
        # 获取完整的弹幕数据
        danmaku_data = fetch_danmaku(cid)
        
        # 检查danmaku_data是否为列表类型
        app_logger.debug(f"Fetched danmaku data type: {type(danmaku_data)}")
        
        # 如果 danmaku_data 是字典，尝试获取 'danmaku_list' 键的值
        if isinstance(danmaku_data, dict):
            danmaku_data = danmaku_data.get('danmaku_list', [])
        
        # 如果 danmaku_data 仍然为空，则抛出异常
        if not danmaku_data:
            raise Exception("未获取到弹幕数据")
        
        # 计算分页范围
        start = (page - 1) * per_page  # 当前页的起始索引
        end = start + per_page  # 当前页的结束索引
        paginated_danmaku = danmaku_data[start:end]  # 获取当前页的弹幕数据
        
        # 计算总页数
        total_pages = (len(danmaku_data) + per_page - 1) // per_page
        
        # 将分页后的弹幕数据返回给前端
        return jsonify({
            'danmaku': paginated_danmaku,  # 当前页的弹幕数据
            'total_pages': total_pages,    # 总页数
            'current_page': page           # 当前页码
        })
    except Exception as e:
        # 捕获异常并记录错误日志
        app_logger.error(f"Error fetching danmaku: {str(e)}")
        # 如果发生错误，返回错误信息给前端，状态码为400（Bad Request）
        return jsonify({'error': str(e)}), 400

# API 路由：获取词频统计数据
@app.route('/api/word_frequency', methods=['POST'])
def word_frequency():
    data = request.json
    bv_input = data.get('bv', '')  # 获取 BV 号
    try:
        # 获取视频的 CID
        bv = handle_bv_input(bv_input)
        cid = get_video_cid(bv)
        
        # 获取弹幕数据
        danmaku_data = fetch_danmaku(cid)
        
        # 获取词频统计结果
        top_words = calculate_word_frequency(danmaku_data)
        
        # 返回词频统计数据
        return jsonify({'top_words': top_words})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# 启动Flask应用
if __name__ == '__main__':
    app.run(debug=True)  # 在调试模式下启动Flask应用
