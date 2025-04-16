import requests
import xml.etree.ElementTree as ET
from .utils import seconds_to_hms
from config import Config
from modules.logger import app_logger
import datetime

# 请求头
headers = {
    'User-Agent': Config.USER_AGENT
}

# 获取视频的 cid
def get_video_cid(bv):
    url = f'https://api.bilibili.com/x/player/pagelist?bvid={bv}'
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        data = res.json().get('data', [])
        
        if not data:
            raise Exception("未能获取到视频的 CID 数据")
        
        cid = data[0].get('cid')
        if cid:
            return cid
        else:
            raise Exception("未能获取到有效的 CID")
    except requests.exceptions.RequestException as e:
        raise Exception(f"网络请求错误: {e}")
    except Exception as e:
        raise Exception(f"获取视频 CID 失败: {e}")

# 爬取弹幕数据
def fetch_danmaku(cid):
    danmaku_url = f'https://comment.bilibili.com/{cid}.xml'
    try:
        res = requests.get(danmaku_url, headers=headers)
        res.raise_for_status()
        root = ET.fromstring(res.content)
        
        danmaku_list = []
        for d in root.findall('d'):
            attributes = d.attrib.get('p', '').split(',')
            time_in_seconds = attributes[0] if len(attributes) > 0 else '0'
            date_timestamp = attributes[4] if len(attributes) > 4 else '0'
            sender_hash = attributes[6] if len(attributes) > 6 else ''
            danmaku_content = d.text if d.text else ''
            
            try:
                # 转换为可读时间 YYYY-MM-DD HH:MM:SS
                send_time = datetime.datetime.fromtimestamp(float(date_timestamp)).strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                app_logger.warning(f"Invalid timestamp: {date_timestamp}, using default")
                send_time = '1970-01-01 00:00:00'
            
            danmaku_list.append({
                'time': seconds_to_hms(time_in_seconds),
                'send_time': send_time,
                'hash': sender_hash,
                'content': danmaku_content
            })
        
        if not danmaku_list:
            raise Exception("未能获取到弹幕数据")
        
        app_logger.debug(f"Fetched {len(danmaku_list)} danmaku entries, sample: {danmaku_list[:5]}")
        return danmaku_list
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"网络请求错误: {e}")
    except ET.ParseError as e:
        raise Exception(f"XML 解析错误: {e}")
    except Exception as e:
        raise Exception(f"获取弹幕数据失败: {e}")