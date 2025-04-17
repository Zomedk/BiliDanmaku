import requests
from config import Config
from .cover_image import download_cover_image
from flask import Flask, request, jsonify
from .logger import app_logger  # 确保你已经定义了 app_logger


# 请求头设置
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 获取视频信息，包括封面图片 URL 和 UP 主信息
import requests
import time

def get_video_info(bv):
    app_logger.debug("Fetching video info...")

    # 构造 API 请求 URL，使用 bvid 参数获取视频信息
    url = f'https://api.bilibili.com/x/web-interface/view?bvid={bv}'

    # 设置请求头，尤其是 Referer，有助于避免部分反爬机制
    headers['Referer'] = f'https://www.bilibili.com/video/{bv}'
    
    try:
        # 发送 GET 请求获取视频数据
        res = requests.get(url, headers=headers)
        app_logger.debug(f"API Response Status Code: {res.status_code}")
        
        if res.status_code == 200:
            data = res.json()['data']  # 提取 JSON 数据中 "data" 字段
            title = data['title']      # 视频标题
            cover = data['pic']        # 封面图片 URL
            up_name = data['owner']['name']  # UP主昵称
            up_link = f'https://space.bilibili.com/{data["owner"]["mid"]}'  # UP主主页链接
            
            # 获取视频时长（单位为秒），默认为 0
            video_duration = data.get('duration', 0)

            # 检查视频时长是否合法，防止无效或为 0 的情况
            if not isinstance(video_duration, (int, float)) or video_duration <= 0:
                app_logger.warning(f"Invalid video_duration for BV{bv}: {video_duration}, setting to 60 seconds")
                video_duration = 60  # 设置默认值 60 秒

            # 如果封面 URL 使用的是 http 协议，替换为 https（更安全）
            if cover.startswith('http://'):
                cover = cover.replace('http://', 'https://')

            # 打印视频时长（秒）用于调试
            app_logger.debug(f"Video duration (seconds): {video_duration}")

            # 可选：格式化为可读时间格式，例如 "00:03:25"
            formatted_duration = time.strftime("%H:%M:%S", time.gmtime(video_duration))
            app_logger.debug(f"Formatted duration: {formatted_duration}")

            # 下载封面图片并获取相对路径
            cover_path = download_cover_image(cover)
            # 将本地路径转换为相对 URL
            cover_url = '/static/covers/video_cover.jpg'

            # 返回视频标题、封面相对 URL、UP主昵称、主页链接、时长（秒）、格式化时长
            return title, cover_url, up_name, up_link, video_duration, formatted_duration

        else:
            # 非200响应时抛出异常
            app_logger.error(f"Failed to fetch video info, Status Code: {res.status_code}")
            raise Exception(f"获取视频信息失败，状态码：{res.status_code}")
    
    except Exception as e:
        # 捕获所有异常并记录日志
        app_logger.error(f"Error in get_video_info: {str(e)}")
        raise Exception(f"获取视频信息失败: {e}")



# 获取视频的 cid
def get_video_cid(bv):
    url = f'https://api.bilibili.com/x/player/pagelist?bvid={bv}'
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()['data']
            if data:
                cid = data[0]['cid']  # 默认获取第一个分P的 cid
                return cid
            else:
                raise Exception("未能获取到视频的 CID")
        else:
            raise Exception(f"获取视频 CID 失败，状态码：{res.status_code}")
    except Exception as e:
        raise Exception(f"获取视频 CID 失败: {e}")
