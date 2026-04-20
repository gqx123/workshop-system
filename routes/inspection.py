"""点检模板与点检记录相关路由"""
import json
from flask import Blueprint, jsonify, request
from services.inspection_service import (
    get_templates, create_template, update_template,
    delete_template, copy_templates,
    create_inspection, list_inspections,
    get_inspection_by_id, delete_inspection,
)

inspection_bp = Blueprint("inspection", __name__)


# ================================================================
# 点检模板 API
# ================================================================

@inspection_bp.route("/api/inspection-templates", methods=["GET"])
def query_templates():
    """GET /api/inspection-templates?machine_id= — 获取某设备的点检模板"""
    try:
        machine_id = request.args.get("machine_id", type=int)
        if not machine_id:
            return jsonify({"error": "缺少 machine_id 参数"}), 400
        return jsonify(get_templates(machine_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inspection_bp.route("/api/inspection-templates", methods=["POST"])
def add_template():
    """POST /api/inspection-templates — 新增点检模板项目"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求体必须为 JSON"}), 400
        new_id = create_template(data)
        return jsonify({"success": True, "id": new_id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inspection_bp.route("/api/inspection-templates/<int:template_id>", methods=["PUT"])
def edit_template(template_id: int):
    """PUT /api/inspection-templates/<id> — 更新点检模板项目"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求体必须为 JSON"}), 400
        ok = update_template(template_id, data)
        if not ok:
            return jsonify({"error": "更新失败"}), 404
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inspection_bp.route("/api/inspection-templates/<int:template_id>", methods=["DELETE"])
def remove_template(template_id: int):
    """DELETE /api/inspection-templates/<id> — 删除点检模板项目"""
    try:
        ok = delete_template(template_id)
        if not ok:
            return jsonify({"error": "记录不存在"}), 404
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inspection_bp.route("/api/inspection-templates/copy", methods=["POST"])
def copy_template():
    """POST /api/inspection-templates/copy — 从其他设备复制模板"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求体必须为 JSON"}), 400
        source_id = data.get("source_machine_id")
        target_id = data.get("target_machine_id")
        if not source_id or not target_id:
            return jsonify({"error": "缺少 source_machine_id 或 target_machine_id"}), 400
        count = copy_templates(source_id, target_id)
        return jsonify({"success": True, "copied": count})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================================================================
# 点检记录 API
# ================================================================

@inspection_bp.route("/api/inspection", methods=["POST"])
def add_inspection():
    """POST /api/inspection — 提交点检记录"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求体必须为 JSON"}), 400
        new_id = create_inspection(data)
        return jsonify({"success": True, "id": new_id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inspection_bp.route("/api/inspection", methods=["GET"])
def query_inspections():
    """GET /api/inspection?machine_id= — 查询点检记录"""
    try:
        machine_id = request.args.get("machine_id", type=int)
        return jsonify(list_inspections(machine_id=machine_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inspection_bp.route("/api/inspection/<int:record_id>", methods=["GET"])
def get_inspection(record_id: int):
    """GET /api/inspection/<id> — 获取单条点检记录"""
    try:
        r = get_inspection_by_id(record_id)
        if r is None:
            return jsonify({"error": "记录不存在"}), 404
        return jsonify(r)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inspection_bp.route("/api/inspection/<int:record_id>", methods=["DELETE"])
def remove_inspection(record_id: int):
    """DELETE /api/inspection/<id> — 删除点检记录"""
    try:
        ok = delete_inspection(record_id)
        if not ok:
            return jsonify({"error": "记录不存在"}), 404
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
