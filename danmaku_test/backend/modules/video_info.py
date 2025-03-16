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
def get_video_info(bv):
    app_logger.debug("Fetching video info...")
    url = f'https://api.bilibili.com/x/web-interface/view?bvid={bv}'

    # 更新 Referer 字段为视频页面的 URL
    headers['Referer'] = f'https://www.bilibili.com/video/{bv}'
    
    try:
        res = requests.get(url, headers=headers)  # 使用正确的 url
        app_logger.debug(f"API Response Status Code: {res.status_code}")
        
        if res.status_code == 200:
            data = res.json()['data']
            title = data['title']
            cover = data['pic']
            up_name = data['owner']['name']
            up_link = f'https://space.bilibili.com/{data["owner"]["mid"]}'

            # 如果封面图片是 http 开头的，替换为 https
            if cover.startswith('http://'):
                cover = cover.replace('http://', 'https://')

            cover_path = download_cover_image(cover)
            return title, cover_path, up_name, up_link
        else:
            app_logger.error(f"Failed to fetch video info, Status Code: {res.status_code}")
            raise Exception(f"获取视频信息失败，状态码：{res.status_code}")
    except Exception as e:
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
