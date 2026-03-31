"""保养记录相关路由"""
from flask import Blueprint, jsonify, request
from services.maintenance_service import (
    create_maintenance, list_maintenance, get_maintenance_by_id,
    update_maintenance, delete_maintenance,
)

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/api/maintenance")


@maintenance_bp.route("/", methods=["POST"])
def add_maintenance():
    """POST /api/maintenance — 新增保养记录"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求体必须为 JSON"}), 400
        for f in ["machine_id", "maintenance_type", "operator_name"]:
            if f not in data or data[f] is None:
                return jsonify({"error": f"缺少字段: {f}"}), 400
        new_id = create_maintenance(data)
        return jsonify({"success": True, "id": new_id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@maintenance_bp.route("/", methods=["GET"])
def query_maintenance():
    """GET /api/maintenance?machine_id= — 查询保养记录"""
    try:
        machine_id = request.args.get("machine_id", type=int)
        return jsonify(list_maintenance(machine_id=machine_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@maintenance_bp.route("/<int:record_id>", methods=["GET"])
def get_maintenance(record_id: int):
    """GET /api/maintenance/<id> — 获取单条保养记录"""
    try:
        r = get_maintenance_by_id(record_id)
        if r is None:
            return jsonify({"error": "记录不存在"}), 404
        return jsonify(r)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@maintenance_bp.route("/<int:record_id>", methods=["PUT"])
def edit_maintenance(record_id: int):
    """PUT /api/maintenance/<id> — 更新保养记录"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求体必须为 JSON"}), 400
        ok = update_maintenance(record_id, data)
        if not ok:
            return jsonify({"error": "更新失败"}), 404
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@maintenance_bp.route("/<int:record_id>", methods=["DELETE"])
def remove_maintenance(record_id: int):
    """DELETE /api/maintenance/<id> — 删除保养记录"""
    try:
        ok = delete_maintenance(record_id)
        if not ok:
            return jsonify({"error": "记录不存在"}), 404
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
