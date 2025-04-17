import requests
import xml.etree.ElementTree as ET
from .utils import seconds_to_hms  # 引入秒转时分秒的工具函数
from config import Config  # 引入配置文件
from modules.logger import app_logger  # 引入日志模块，记录错误和调试信息
import datetime

# 请求头，模仿浏览器的请求
headers = {
    'User-Agent': Config.USER_AGENT  # 从配置文件中获取 User-Agent
}

# 获取视频的 cid（视频标识符）
def get_video_cid(bv):
    url = f'https://api.bilibili.com/x/player/pagelist?bvid={bv}'  # 构造视频的 API 地址
    try:
        # 发送请求，获取数据
        res = requests.get(url, headers=headers)
        res.raise_for_status()  # 检查是否请求成功
        data = res.json().get('data', [])  # 获取 JSON 数据中的 'data' 字段
        
        if not data:
            raise Exception("未能获取到视频的 CID 数据")  # 如果没有数据，抛出异常
        
        cid = data[0].get('cid')  # 获取 CID
        if cid:
            return cid  # 如果找到了 CID，返回它
        else:
            raise Exception("未能获取到有效的 CID")  # 如果 CID 无效，抛出异常
    except requests.exceptions.RequestException as e:
        raise Exception(f"网络请求错误: {e}")  # 如果请求错误，抛出网络请求异常
    except Exception as e:
        raise Exception(f"获取视频 CID 失败: {e}")  # 其他异常，说明获取 CID 失败

# 爬取弹幕数据的函数
def fetch_danmaku(cid):
    danmaku_url = f'https://comment.bilibili.com/{cid}.xml'  # 根据 cid 获取弹幕 XML 数据的 URL
    try:
        # 发送请求获取弹幕 XML 数据
        res = requests.get(danmaku_url, headers=headers)
        res.raise_for_status()  # 检查是否请求成功
        root = ET.fromstring(res.content)  # 解析返回的 XML 数据
        
        danmaku_list = []  # 存储弹幕数据的列表
        # 遍历 XML 中的所有弹幕元素
        for d in root.findall('d'):
            # 解析弹幕的各个属性，使用逗号分割
            attributes = d.attrib.get('p', '').split(',')
            time_in_seconds = attributes[0] if len(attributes) > 0 else '0'  # 弹幕时间（秒）
            color_dec = attributes[3] if len(attributes) > 3 else '16777215'  # 默认白色 (#FFFFFF)
            date_timestamp = attributes[4] if len(attributes) > 4 else '0'  # 弹幕发送时间的时间戳
            sender_hash = attributes[6] if len(attributes) > 6 else ''  # 发送者的唯一标识
            danmaku_content = d.text if d.text else ''  # 弹幕内容
            
            try:
                # 将时间戳转换为可读的时间格式：YYYY-MM-DD HH:MM:SS
                send_time = datetime.datetime.fromtimestamp(float(date_timestamp)).strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                app_logger.warning(f"Invalid timestamp: {date_timestamp}, using default")  # 如果时间戳无效，使用默认值
                send_time = '1970-01-01 00:00:00'  # 默认时间戳（1970-01-01 00:00:00）
            
            # 将每条弹幕的信息添加到列表中
            danmaku_list.append({
                'time': seconds_to_hms(time_in_seconds),  # 转换秒数为时分秒格式
                'send_time': send_time,  # 发送时间
                'hash': sender_hash,  # 发送者的唯一标识
                'content': danmaku_content,  # 弹幕内容
                'color': color_dec  # 十进制颜色
            })
        
        if not danmaku_list:
            raise Exception("未能获取到弹幕数据")  # 如果没有获取到弹幕，抛出异常
        
        app_logger.debug(f"Fetched {len(danmaku_list)} danmaku entries, sample: {danmaku_list[:5]}")  # 打印调试信息，显示前 5 条弹幕
        return danmaku_list  # 返回弹幕列表
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"网络请求错误: {e}")  # 如果请求出错，抛出异常
    except ET.ParseError as e:
        raise Exception(f"XML 解析错误: {e}")  # 如果 XML 解析出错，抛出异常
    except Exception as e:
        raise Exception(f"获取弹幕数据失败: {e}")  # 其他未知错误，抛出异常
