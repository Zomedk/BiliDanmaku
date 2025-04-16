from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from modules.video_info import get_video_info, get_video_cid
from modules.danmaku import fetch_danmaku
from modules.cover_image import download_cover_image
from modules.utils import handle_bv_input
from modules.logger import app_logger
from modules.danmaku_analysis import calculate_word_frequency, generate_word_cloud, generate_danmaku_timeline, generate_danmaku_time_proportion
from modules.sentiment_analysis import analyze_sentiment
import datetime

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://127.0.0.1:5000", "http://127.0.0.1:8000", "*"]}})

save_folder = './static/danmaku'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

@app.route('/')
def serve_index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

@app.route('/api/video', methods=['POST'])
def video_info():
    data = request.json
    bv_input = data.get('bv', '')
    app_logger.debug(f"Received BV input: {bv_input}")
    try:
        bv = handle_bv_input(bv_input)
        app_logger.debug(f"Parsed BV: {bv}")
        title, cover_path, up_name, up_link, video_duration, formatted_duration = get_video_info(bv)
        app_logger.debug(f"Video Info: title={title}, cover={cover_path}, up_name={up_name}, up_link={up_link}, duration={video_duration}")
        return jsonify({
            'title': title,
            'cover': cover_path,
            'up_name': up_name,
            'up_link': up_link
        })
    except Exception as e:
        app_logger.error(f"Error in video_info: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/danmaku', methods=['POST'])
def danmaku():
    data = request.json
    bv_input = data.get('bv', '')
    page = data.get('page', 1)
    per_page = data.get('per_page', 50)
    keyword = data.get('keyword', '').strip()
    sort_by = data.get('sort_by', 'time')
    sort_order = data.get('sort_order', 'asc')
    app_logger.debug(f"Received request for danmaku: BV={bv_input}, page={page}, per_page={per_page}, keyword='{keyword}', sort_by={sort_by}, sort_order={sort_order}")
    
    try:
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
        app_logger.debug(f"Parsed BV: {bv}")
        cid = get_video_cid(bv)
        app_logger.debug(f"Retrieved CID: {cid}")
        danmaku_data = fetch_danmaku(cid)
        
        app_logger.debug(f"Danmaku data type: {type(danmaku_data)}, length: {len(danmaku_data)}, sample: {danmaku_data[:5]}")
        if not isinstance(danmaku_data, list):
            raise ValueError(f"弹幕数据格式错误: 期望列表，实际为 {type(danmaku_data)}")
        if not danmaku_data:
            raise ValueError("未获取到弹幕数据")
        
        for i, d in enumerate(danmaku_data[:5]):
            if not isinstance(d, dict):
                app_logger.error(f"Invalid danmaku item {i}: type={type(d)}, value={d}")
                raise ValueError(f"弹幕数据元素格式错误: 期望字典，实际为 {type(d)}")
            if 'time' not in d or 'send_time' not in d or 'hash' not in d or 'content' not in d:
                app_logger.error(f"Missing required keys in danmaku item {i}: {d}")
                raise ValueError(f"弹幕数据缺少必要字段: {d}")
        
        filtered_danmaku = []
        if keyword:
            for d in danmaku_data:
                if not isinstance(d, dict):
                    app_logger.error(f"Invalid danmaku item in filter: type={type(d)}, value={d}")
                    continue
                content = str(d.get('content', ''))
                if keyword.lower() in content.lower():
                    filtered_danmaku.append(d)
            app_logger.debug(f"Filtered danmaku count with keyword '{keyword}': {len(filtered_danmaku)}")
        else:
            filtered_danmaku = danmaku_data
            app_logger.debug(f"Total danmaku count (no keyword): {len(filtered_danmaku)}")

        # 排序
        def get_time_sort_key(d):
            try:
                if sort_by == 'time':
                    time_str = d.get('time', '00:00:00')
                    if not isinstance(time_str, str) or not time_str:
                        app_logger.warning(f"Invalid time format: {time_str}")
                        return 0
                    h, m, s = map(int, time_str.split(':'))
                    return h * 3600 + m * 60 + s
                else:  # send_time
                    send_time_str = d.get('send_time', '1970-01-01 00:00:00')
                    if not isinstance(send_time_str, str) or not send_time_str:
                        app_logger.warning(f"Invalid send_time format: {send_time_str}")
                        return 0
                    return datetime.datetime.strptime(send_time_str, '%Y-%m-%d %H:%M:%S').timestamp()
            except Exception as e:
                app_logger.warning(f"Sort key error for danmaku: {d}, error: {str(e)}")
                return 0

        app_logger.debug(f"Before sorting (first 5): {[d.get(sort_by) for d in filtered_danmaku[:5]]}")
        filtered_danmaku.sort(key=get_time_sort_key, reverse=(sort_order == 'desc'))
        app_logger.debug(f"After sorting (first 5): {[d.get(sort_by) for d in filtered_danmaku[:5]]}")

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
    

@app.route('/api/word_frequency', methods=['POST'])
def word_frequency():
    data = request.json
    bv_input = data.get('bv', '')
    app_logger.debug(f"Received request for word frequency: BV={bv_input}")
    try:
        bv = handle_bv_input(bv_input)
        app_logger.debug(f"Parsed BV: {bv}")
        cid = get_video_cid(bv)
        app_logger.debug(f"Retrieved CID: {cid}")
        danmaku_data = fetch_danmaku(cid)
        
        app_logger.debug(f"Danmaku data type: {type(danmaku_data)}, length: {len(danmaku_data)}, sample: {danmaku_data[:5]}")
        if not isinstance(danmaku_data, list):
            raise ValueError(f"弹幕数据格式错误: 期望列表，实际为 {type(danmaku_data)}")
        if not danmaku_data:
            raise ValueError("未获取到弹幕数据")
        
        top_words = calculate_word_frequency(danmaku_data, logger=app_logger)
        app_logger.debug(f"Word frequency calculated: {top_words[:5]}...")
        return jsonify({'top_words': top_words})
    except Exception as e:
        app_logger.error(f"Error in word frequency calculation: {str(e)}")
        return jsonify({'error': f"词频统计失败: {str(e)}"}), 400

@app.route('/api/word_cloud', methods=['POST'])
def word_cloud():
    data = request.json
    bv_input = data.get('bv', '')
    app_logger.debug(f"Received request for word cloud: BV={bv_input}")
    try:
        bv = handle_bv_input(bv_input)
        app_logger.debug(f"Parsed BV: {bv}")
        cid = get_video_cid(bv)
        app_logger.debug(f"Retrieved CID: {cid}")
        danmaku_data = fetch_danmaku(cid)
        
        app_logger.debug(f"Danmaku data type: {type(danmaku_data)}, length: {len(danmaku_data)}, sample: {danmaku_data[:5]}")
        if not isinstance(danmaku_data, list):
            raise ValueError(f"弹幕数据格式错误: 期望列表，实际为 {type(danmaku_data)}")
        if not danmaku_data:
            raise ValueError("未获取到弹幕数据")
        
        word_cloud_image = generate_word_cloud(danmaku_data, logger=app_logger)
        return jsonify({'image': word_cloud_image})
    except Exception as e:
        app_logger.error(f"Error in word cloud generation: {str(e)}")
        return jsonify({'error': f"词云图生成失败: {str(e)}"}), 400

@app.route('/api/danmaku_timeline', methods=['POST', 'OPTIONS'])
def danmaku_timeline():
    if request.method == 'OPTIONS':
        response = jsonify({"message": "CORS preflight successful"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        response.headers.add('Access-Control-Max-Age', '86400')
        return response, 200
    data = request.json
    bv_input = data.get('bv', '')
    app_logger.debug(f"Received request for danmaku timeline: BV={bv_input}")
    try:
        bv = handle_bv_input(bv_input)
        app_logger.debug(f"Parsed BV: {bv}")
        cid = get_video_cid(bv)
        app_logger.debug(f"Retrieved CID: {cid}")
        danmaku_data = fetch_danmaku(cid)
        
        app_logger.debug(f"Danmaku data type: {type(danmaku_data)}, length: {len(danmaku_data)}, sample: {danmaku_data[:5]}")
        if not isinstance(danmaku_data, list):
            raise ValueError(f"弹幕数据格式错误: 期望列表，实际为 {type(danmaku_data)}")
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
    data = request.json
    bv_input = data.get('bv', '')
    app_logger.debug(f"Received request for sentiment analysis: BV={bv_input}")
    try:
        bv = handle_bv_input(bv_input)
        app_logger.debug(f"Parsed BV: {bv}")
        cid = get_video_cid(bv)
        app_logger.debug(f"Retrieved CID: {cid}")
        danmaku_data = fetch_danmaku(cid)
        
        app_logger.debug(f"Danmaku data type: {type(danmaku_data)}, length: {len(danmaku_data)}, sample: {danmaku_data[:5]}")
        if not isinstance(danmaku_data, list):
            raise ValueError(f"弹幕数据格式错误: 期望列表，实际为 {type(danmaku_data)}")
        if not danmaku_data:
            raise ValueError("未获取到弹幕数据")
        
        analysis_result = analyze_sentiment(danmaku_data)
        return jsonify(analysis_result)
    except Exception as e:
        app_logger.error(f"情感分析失败: {str(e)}")
        return jsonify({'error': f"情感分析失败: {str(e)}"}), 400

@app.route('/api/danmaku_time_proportion', methods=['POST'])
def danmaku_time_proportion():
    data = request.json
    bv_input = data.get('bv', '')
    app_logger.debug(f"Received request for danmaku time proportion: BV={bv_input}")
    try:
        if not bv_input:
            raise ValueError("BV 号不能为空")
        bv = handle_bv_input(bv_input)
        app_logger.debug(f"Parsed BV: {bv}")
        cid = get_video_cid(bv)
        app_logger.debug(f"Retrieved CID: {cid}")
        danmaku_data = fetch_danmaku(cid)
        
        app_logger.debug(f"Danmaku data type: {type(danmaku_data)}, length: {len(danmaku_data)}, sample: {danmaku_data[:5]}")
        if not isinstance(danmaku_data, list):
            raise ValueError(f"弹幕数据格式错误: 期望列表，实际为 {type(danmaku_data)}")
        if not danmaku_data:
            raise ValueError("未获取到弹幕数据")
        
        for i, d in enumerate(danmaku_data[:5]):
            if not isinstance(d, dict):
                app_logger.error(f"Invalid danmaku item {i}: type={type(d)}, value={d}")
                raise ValueError(f"弹幕数据元素格式错误: 期望字典，实际为 {type(d)}")
        
        image = generate_danmaku_time_proportion(danmaku_data, logger=app_logger)
        app_logger.debug("Danmaku time proportion image generated successfully")
        return jsonify({'image': image})
    except Exception as e:
        app_logger.error(f"生成时间占比图失败: {str(e)}")
        return jsonify({'error': f"生成时间占比图失败: {str(e)}"}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)