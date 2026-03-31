"""配置中心 - 所有可配置项集中在这里"""
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据库
DB_PATH = os.path.join(BASE_DIR, "workshop.db")

# 服务器
HOST = "0.0.0.0"
PORT = 5000
DEBUG = True

# 二维码
QR_DIR = os.path.join(BASE_DIR, "qrcodes")
# 二维码中的基础URL（局域网IP，根据实际修改）
BASE_URL = "http://192.168.13.99:5000"

# 预置机床（编号, 名称, 类型, 位置）
DEFAULT_MACHINES = [
    ("MC-001", "数控车床A", "数控车床", "A区-1号位"),
    ("MC-002", "数控车床B", "数控车床", "A区-2号位"),
    ("MC-003", "立式铣床",   "铣床",     "B区-1号位"),
    ("MC-004", "平面磨床",   "磨床",     "B区-2号位"),
    ("MC-005", "钻床",       "钻床",     "C区-1号位"),
]
