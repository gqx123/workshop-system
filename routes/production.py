"""生产记录相关路由"""
from flask import Blueprint, jsonify, request
from services.production_service import (
    create_production, list_production, get_production_by_id,
    update_production, delete_production,
)

production_bp = Blueprint("production", __name__, url_prefix="/api/production")


@production_bp.route("/", methods=["POST"])
def add_production():
    """POST /api/production — 新增生产记录"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求体必须为 JSON"}), 400
        for f in ["machine_id", "product_name", "start_time", "operator_name"]:
            if f not in data or data[f] is None:
                return jsonify({"error": f"缺少字段: {f}"}), 400
        new_id = create_production(data)
        return jsonify({"success": True, "id": new_id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@production_bp.route("/", methods=["GET"])
def query_production():
    """GET /api/production?machine_id=&from=&to= — 查询生产记录"""
    try:
        machine_id = request.args.get("machine_id", type=int)
        date_from = request.args.get("from")
        date_to = request.args.get("to")
        return jsonify(list_production(machine_id=machine_id, date_from=date_from, date_to=date_to))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@production_bp.route("/<int:record_id>", methods=["GET"])
def get_production(record_id: int):
    """GET /api/production/<id> — 获取单条生产记录"""
    try:
        r = get_production_by_id(record_id)
        if r is None:
            return jsonify({"error": "记录不存在"}), 404
        return jsonify(r)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@production_bp.route("/<int:record_id>", methods=["PUT"])
def edit_production(record_id: int):
    """PUT /api/production/<id> — 更新生产记录"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求体必须为 JSON"}), 400
        ok = update_production(record_id, data)
        if not ok:
            return jsonify({"error": "更新失败"}), 404
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@production_bp.route("/<int:record_id>", methods=["DELETE"])
def remove_production(record_id: int):
    """DELETE /api/production/<id> — 删除生产记录"""
    try:
        ok = delete_production(record_id)
        if not ok:
            return jsonify({"error": "记录不存在"}), 404
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
