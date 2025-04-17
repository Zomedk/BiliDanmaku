import sqlite3
import hashlib
import os

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'users.db')

def init_db():
    """初始化数据库，创建用户表并插入默认用户"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    # 检查是否已有默认用户
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ('123',))
    if cursor.fetchone()[0] == 0:
        # 插入默认用户：用户名123，密码123（哈希存储）
        hashed_password = hashlib.sha256('123'.encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('123', hashed_password))
    conn.commit()
    conn.close()

def register_user(username, password):
    """注册新用户"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # 用户名已存在
    finally:
        conn.close()

def login_user(username, password):
    """验证用户登录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("SELECT 1 FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# 初始化数据库
init_db()