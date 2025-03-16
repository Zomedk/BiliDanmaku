import os
import requests

# 下载封面图片到本地
def download_cover_image(cover_url):
    cover_path = 'D:/Lernen/danmaku_test/backend/static/covers/video_cover.jpg'  # 本地保存路径
    
    # 创建目录（如果不存在）
    if not os.path.exists(os.path.dirname(cover_path)):
        os.makedirs(os.path.dirname(cover_path))

    # 下载图片
    response = requests.get(cover_url)
    if response.status_code == 200:
        with open(cover_path, 'wb') as f:
            f.write(response.content)
        return cover_path
    else:
        raise Exception(f"无法下载封面图片，状态码：{response.status_code}")
