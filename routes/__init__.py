"""路由注册中心 - 集中注册所有 Blueprint"""
from routes.machines import machines_bp
from routes.production import production_bp
from routes.maintenance import maintenance_bp
from routes.faults import faults_bp
from routes.stats import stats_bp


def register_routes(app):
    """
    将所有 Blueprint 注册到 Flask app。

    注册后的路由前缀：
        /api/machines    — 机床
        /api/production  — 生产记录
        /api/maintenance — 保养记录
        /api/faults      — 故障记录
        /api/stats       — 统计
    """
    app.register_blueprint(machines_bp)
    app.register_blueprint(production_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(faults_bp)
    app.register_blueprint(stats_bp)
