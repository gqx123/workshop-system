"""故障记录相关路由"""
from flask import Blueprint, jsonify, request
from services.fault_service import (
    create_fault, list_faults, get_fault_by_id,
    update_fault, resolve_fault, delete_fault,
)

faults_bp = Blueprint("faults", __name__, url_prefix="/api/faults")


@faults_bp.route("/", methods=["POST"])
def add_fault():
    """POST /api/faults — 新增故障记录"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求体必须为 JSON"}), 400
        for f in ["machine_id", "operator_name"]:
            if f not in data or data[f] is None:
                return jsonify({"error": f"缺少字段: {f}"}), 400
        new_id = create_fault(data)
        return jsonify({"success": True, "id": new_id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@faults_bp.route("/", methods=["GET"])
def query_faults():
    """GET /api/faults?status= — 查询故障记录"""
    try:
        status = request.args.get("status")
        return jsonify(list_faults(status=status))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@faults_bp.route("/<int:fault_id>", methods=["GET"])
def get_fault(fault_id: int):
    """GET /api/faults/<id> — 获取单条故障记录"""
    try:
        r = get_fault_by_id(fault_id)
        if r is None:
            return jsonify({"error": "记录不存在"}), 404
        return jsonify(r)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@faults_bp.route("/<int:fault_id>", methods=["PUT"])
def edit_fault(fault_id: int):
    """PUT /api/faults/<id> — 更新故障记录"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求体必须为 JSON"}), 400
        ok = update_fault(fault_id, data)
        if not ok:
            return jsonify({"error": "更新失败"}), 404
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@faults_bp.route("/<int:fault_id>/resolve", methods=["POST"])
def resolve(fault_id: int):
    """POST /api/faults/<id>/resolve — 标记故障已解决"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求体必须为 JSON"}), 400
        text = data.get("resolution", "").strip()
        if not text:
            return jsonify({"error": "缺少字段: resolution"}), 400
        ok = resolve_fault(fault_id, text)
        if not ok:
            return jsonify({"error": "记录不存在"}), 404
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@faults_bp.route("/<int:fault_id>", methods=["DELETE"])
def remove_fault(fault_id: int):
    """DELETE /api/faults/<id> — 删除故障记录"""
    try:
        ok = delete_fault(fault_id)
        if not ok:
            return jsonify({"error": "记录不存在"}), 404
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
