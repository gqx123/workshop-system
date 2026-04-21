"""启动入口 - 初始化数据库、注册路由、启动Flask服务器"""
import os
import logging
import socket
from functools import wraps
from flask import (
    Flask, send_from_directory, request,
    session, redirect, url_for, jsonify,
)
from config import HOST, PORT, DEBUG, BASE_DIR, BASE_URL, SECRET_KEY, ADMINS
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

    app.secret_key = SECRET_KEY

    db = Database()
    db.init_db()
    db.seed_machines()

    register_routes(app)

    def login_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get("logged_in"):
                if request.path.startswith("/api/"):
                    return jsonify({"error": "未登录"}), 401
                return redirect("/login")
            return f(*args, **kwargs)
        return decorated

    @app.before_request
    def check_api_auth():
        if not request.path.startswith("/api/"):
            return None

        open_post_paths = [
            "/api/production",
            "/api/maintenance",
            "/api/faults",
            "/api/inspection",
        ]

        if request.method == "GET":
            return None

        if request.method == "POST" and not request.path.endswith("/resolve"):
            clean_path = request.path.rstrip("/")
            if clean_path in [p.rstrip("/") for p in open_post_paths]:
                return None

        if not session.get("logged_in"):
            return jsonify({"error": "未登录，请先登录"}), 401

    @app.route("/login", methods=["GET"])
    def login_page():
        if session.get("logged_in"):
            return redirect("/")
        return send_from_directory(app.static_folder, "login.html")

    @app.route("/login", methods=["POST"])
    def login_action():
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求格式错误"}), 400

        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or not password:
            return jsonify({"error": "请输入用户名和密码"}), 400

        if username in ADMINS and ADMINS[username] == password:
            session["logged_in"] = True
            session["username"] = username
            return jsonify({"success": True, "username": username})

        return jsonify({"error": "用户名或密码错误"}), 401

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("/login")

    @app.route("/")
    @login_required
    def index():
        return send_from_directory(app.static_folder, "dashboard.html")

    @app.route("/mobile/")
    def mobile_index():
        mobile_dir = os.path.join(app.static_folder, "mobile")
        return send_from_directory(mobile_dir, "index.html")

    @app.route("/mobile/<path:filename>")
    def mobile_page(filename):
        mobile_dir = os.path.join(app.static_folder, "mobile")
        return send_from_directory(mobile_dir, filename)

    return app


def get_lan_ip():
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
    print("=" * 55)
    print("  车间产线记录系统已启动")
    print("=" * 55)
    print(f"  本机访问:     http://localhost:{PORT}")
    print(f"  局域网访问:   http://{lan_ip}:{PORT}")
    print(f"  管理员账号:   admin / admin123")
    print("-" * 55)
    print(f"  config.py 中 BASE_URL = {BASE_URL}")
    if lan_ip not in BASE_URL and "localhost" not in BASE_URL and "127.0.0.1" not in BASE_URL:
        print(f"  ✓ 已配置外网地址（内网穿透），扫码可正常使用")
    elif lan_ip in BASE_URL:
        print(f"  ⚠️  当前 BASE_URL 是局域网地址，外网扫码无法访问")
        print(f"     请将 config.py 中的 BASE_URL 改为花生壳外网地址")
        print(f"     然后重新生成二维码: py tools/generate_qrcodes.py")
    print("=" * 55)
    print()
    app.run(host=HOST, port=PORT, debug=DEBUG)

