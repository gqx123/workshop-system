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

    # 会话密钥
    app.secret_key = SECRET_KEY

    # 初始化数据库
    db = Database()
    db.init_db()
    db.seed_machines()

    # 注册所有 API 路由
    register_routes(app)

    # ----------------------------------------------------------------
    # 登录鉴权装饰器
    # ----------------------------------------------------------------
    def login_required(f):
        """保护后台页面，未登录重定向到登录页"""
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get("logged_in"):
                # API 请求返回 401，页面请求重定向登录
                if request.path.startswith("/api/"):
                    return jsonify({"error": "未登录"}), 401
                return redirect("/login")
            return f(*args, **kwargs)
        return decorated

    # ----------------------------------------------------------------
    # API 鉴权中间件（保护所有 /api/ 路由）
    # ----------------------------------------------------------------
    @app.before_request
    def check_api_auth():
        """所有 /api/ 接口要求登录（手机扫码提交接口除外）"""
        if request.path.startswith("/api/"):
            # 手机端提交接口放行（POST 创建记录的接口）
            open_paths = [
                "/api/production",
                "/api/maintenance",
                "/api/faults",
            ]
            # GET 请求和 POST 创建记录放行，DELETE/PUT 需要登录
            if request.method in ("GET",) or (
                request.method == "POST"
                and not request.path.endswith("/resolve")
                and request.path.rstrip("/") in [p.rstrip("/") for p in open_paths]
            ):
                return None

            # 其余 API 需要登录
            if not session.get("logged_in"):
                return jsonify({"error": "未登录，请先登录"}), 401

    # ----------------------------------------------------------------
    # 登录/登出路由
    # ----------------------------------------------------------------
    @app.route("/login", methods=["GET"])
    def login_page():
        """登录页面"""
        if session.get("logged_in"):
            return redirect("/")
        return send_from_directory(app.static_folder, "login.html")

    @app.route("/login", methods=["POST"])
    def login_action():
        """处理登录"""
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求格式错误"}), 400

        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or not password:
            return jsonify({"error": "请输入用户名和密码"}), 400

        # 验证账号密码
        if username in ADMINS and ADMINS[username] == password:
            session["logged_in"] = True
            session["username"] = username
            return jsonify({"success": True, "username": username})

        return jsonify({"error": "用户名或密码错误"}), 401

    @app.route("/logout")
    def logout():
        """登出"""
        session.clear()
        return redirect("/login")

    # ----------------------------------------------------------------
    # 前端页面路由
    # ----------------------------------------------------------------
    @app.route("/")
    @login_required
    def index():
        """后台管理仪表盘（需要登录）"""
        return send_from_directory(app.static_folder, "dashboard.html")

    @app.route("/mobile/")
    def mobile_index():
        """手机扫码 - 记录类型选择页（无需登录）"""
        return send_from_directory(
            os.path.join(app.static_folder, "mobile"), "index.html"
        )

    @app.route("/mobile/<path:filename>")
    def mobile_page(filename):
        """手机扫码 - 具体填写页（无需登录）"""
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
    print(f"  管理员账号: admin / admin123")
    if lan_ip not in BASE_URL:
        print(f"  ⚠️  IP 不匹配！请更新 config.py 中的 BASE_URL 为:")
        print(f"      BASE_URL = \"http://{lan_ip}:{PORT}\"")
        print(f"      然后重新生成二维码: python tools/generate_qrcodes.py")
    print("=" * 50)
    print()
    app.run(host=HOST, port=PORT, debug=DEBUG)
