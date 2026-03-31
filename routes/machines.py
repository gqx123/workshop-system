"""机床相关路由"""
from flask import Blueprint, jsonify, request
from services.machine_service import (
    get_all_machines, get_machine_by_id, create_machine, update_machine, delete_machine,
)

machines_bp = Blueprint("machines", __name__, url_prefix="/api/machines")


@machines_bp.route("/", methods=["GET"])
def list_machines():
    """GET /api/machines — 获取所有机床"""
    try:
        return jsonify(get_all_machines())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@machines_bp.route("/<int:machine_id>", methods=["GET"])
def get_machine(machine_id: int):
    """GET /api/machines/<id> — 获取单台机床"""
    try:
        m = get_machine_by_id(machine_id)
        if m is None:
            return jsonify({"error": "机床不存在"}), 404
        return jsonify(m)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@machines_bp.route("/", methods=["POST"])
def add_machine():
    """POST /api/machines — 新增机床"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求体必须为 JSON"}), 400
        for f in ["machine_code", "machine_name"]:
            if not data.get(f):
                return jsonify({"error": f"缺少字段: {f}"}), 400
        new_id = create_machine(data)
        return jsonify({"success": True, "id": new_id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@machines_bp.route("/<int:machine_id>", methods=["PUT"])
def edit_machine(machine_id: int):
    """PUT /api/machines/<id> — 更新机床信息"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求体必须为 JSON"}), 400
        ok = update_machine(machine_id, data)
        if not ok:
            return jsonify({"error": "更新失败，机床不存在或无数据变更"}), 404
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@machines_bp.route("/<int:machine_id>", methods=["DELETE"])
def remove_machine(machine_id: int):
    """DELETE /api/machines/<id> — 删除机床"""
    try:
        ok = delete_machine(machine_id)
        if not ok:
            return jsonify({"error": "机床不存在"}), 404
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
