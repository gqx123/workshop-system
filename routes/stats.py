"""统计与仪表盘数据路由"""
from flask import Blueprint, jsonify
from services.stats_service import get_overview_stats

stats_bp = Blueprint("stats", __name__, url_prefix="/api/stats")


@stats_bp.route("/", methods=["GET"])
def overview():
    """
    GET /api/stats
    获取仪表盘概览统计数据。

    返回：
        {
            "today": {"records": int, "total_quantity": int, "total_defects": int},
            "total_production_records": int,
            "pending_faults": int,
            "total_maintenance_records": int,
            "machine_today": [{"code": str, "name": str, "quantity": int, "defects": int}, ...]
        }
    """
    try:
        stats = get_overview_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": f"获取统计数据失败: {e}"}), 500
