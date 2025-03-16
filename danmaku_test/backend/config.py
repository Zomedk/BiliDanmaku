import os

class Config:
    # 服务器配置
    DEBUG = True
    # 用户代理
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    
    # 文件存储路径
    SAVE_FOLDER = './static/danmaku'
    COVER_FOLDER = './static/covers'
    
    # 日志配置
    LOG_LEVEL = 'DEBUG'
