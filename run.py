"""启动入口 - 初始化数据库、注册路由、启动Flask服务器"""
import os
import logging
import socket
from flask import Flask, send_from_directory
from config import HOST, PORT, DEBUG, BASE_DIR, BASE_URL
from database.db import Database
from routes import register_routes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app():
    """工厂函数：创建并配置 Flask 应用"""
    app = Flask(
        __name__,
        static_folder=os.path.join(BASE_DIR, "frontend"),
        static_url_path="/frontend",
    )

    # 初始化数据库
    db = Database()
    db.init_db()
    db.seed_machines()

    # 注册所有 API 路由
    register_routes(app)

    # ---------- 前端页面路由 ----------

    @app.route("/")
    def index():
        """后台管理仪表盘"""
        return send_from_directory(app.static_folder, "dashboard.html")

    @app.route("/mobile/")
    def mobile_index():
        """手机扫码 - 记录类型选择页（/mobile/?machine_id=1）"""
        return send_from_directory(
            os.path.join(app.static_folder, "mobile"), "index.html"
        )

    @app.route("/mobile/<path:filename>")
    def mobile_page(filename):
        """手机扫码 - 具体填写页"""
        return send_from_directory(
            os.path.join(app.static_folder, "mobile"), filename
        )

    return app


def get_lan_ip():
    """获取本机局域网 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    app = create_app()
    lan_ip = get_lan_ip()
    print()
    print("=" * 50)
    print("  车间产线记录系统已启动")
    print("=" * 50)
    print(f"  本机访问:   http://localhost:{PORT}")
    print(f"  局域网访问: http://{lan_ip}:{PORT}")
    print(f"  当前 config.py 中 BASE_URL = {BASE_URL}")
    if lan_ip not in BASE_URL:
        print(f"  ⚠️  IP 不匹配！请更新 config.py 中的 BASE_URL 为:")
        print(f"      BASE_URL = \"http://{lan_ip}:{PORT}\"")
        print(f"      然后重新生成二维码: python tools/generate_qrcodes.py")
    print("=" * 50)
    print()
    app.run(host=HOST, port=PORT, debug=DEBUG)
