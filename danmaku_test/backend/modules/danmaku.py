import requests
import xml.etree.ElementTree as ET
from .utils import seconds_to_hms  # 假设这个函数可以转换秒数到时分秒格式
from config import Config

# 请求头
headers = {
    'User-Agent': Config.USER_AGENT
}

# 获取视频的 cid
def get_video_cid(bv):
    url = f'https://api.bilibili.com/x/player/pagelist?bvid={bv}'
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()  # 如果响应状态码不是 200，抛出异常
        data = res.json().get('data', [])
        
        if not data:
            raise Exception("未能获取到视频的 CID 数据")
        
        # 默认获取第一个分P的 cid
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
        res.raise_for_status()  # 如果响应状态码不是 200，抛出异常
        # 解析 XML 数据
        root = ET.fromstring(res.content)
        
        danmaku_list = []
        for d in root.findall('d'):
            attributes = d.attrib.get('p', '').split(',')
            # 确保 attributes 列表有足够的长度
            time_in_seconds = attributes[0] if len(attributes) > 0 else '0'
            sender_hash = attributes[6] if len(attributes) > 6 else ''  # 获取发送者哈希值
            danmaku_content = d.text if d.text else ''
            
            danmaku_list.append({
                'time': seconds_to_hms(time_in_seconds),
                'hash': sender_hash,
                'content': danmaku_content
            })
        
        if not danmaku_list:
            raise Exception("未能获取到弹幕数据")
        
        return danmaku_list
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"网络请求错误: {e}")
    except ET.ParseError as e:
        raise Exception(f"XML 解析错误: {e}")
    except Exception as e:
        raise Exception(f"获取弹幕数据失败: {e}")
