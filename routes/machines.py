"""机床相关路由"""
import os
from flask import Blueprint, jsonify, request, make_response, send_file
from services.machine_service import (
    get_all_machines, get_machine_by_id, create_machine,
    update_machine, delete_machine,
    get_machine_qrcode, export_machines_qrcodes_pdf,
    upload_instruction_image, delete_instruction_image,
    copy_instruction_image, get_instruction_image_path,
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


# ---- 二维码 ----

@machines_bp.route("/<int:machine_id>/qrcode", methods=["GET"])
def machine_qrcode(machine_id: int):
    """GET /api/machines/<id>/qrcode — 获取单台机床二维码 PNG"""
    try:
        result = get_machine_qrcode(machine_id)
        if result is None:
            return jsonify({"error": "机床不存在"}), 404
        png, filename = result
        resp = make_response(png)
        resp.headers["Content-Type"] = "image/png"
        resp.headers["Content-Disposition"] = f"inline; filename={filename}"
        return resp
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@machines_bp.route("/qrcodes/export", methods=["POST"])
def export_qrcodes():
    """POST /api/machines/qrcodes/export — 批量导出二维码 PDF"""
    try:
        data = request.get_json(silent=True)
        if not data or not data.get("machine_ids"):
            return jsonify({"error": "缺少 machine_ids"}), 400
        machine_ids = data["machine_ids"]
        if not isinstance(machine_ids, list):
            return jsonify({"error": "machine_ids 必须是数组"}), 400
        pdf_bytes = export_machines_qrcodes_pdf(machine_ids)
        if pdf_bytes is None:
            return jsonify({"error": "没有有效的机床数据"}), 400
        resp = make_response(pdf_bytes)
        resp.headers["Content-Type"] = "application/pdf"
        resp.headers["Content-Disposition"] = "attachment; filename=machine_qrcodes.pdf"
        return resp
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---- 作业指导书 ----

@machines_bp.route("/<int:machine_id>/instruction/image", methods=["GET"])
def get_instruction_img(machine_id: int):
    """GET /api/machines/<id>/instruction/image — 获取作业指导书图片"""
    try:
        path = get_instruction_image_path(machine_id)
        if not path:
            return jsonify({"error": "暂无作业指导书"}), 404
        return send_file(path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@machines_bp.route("/<int:machine_id>/instruction", methods=["POST"])
def upload_instruction(machine_id: int):
    """POST /api/machines/<id>/instruction — 上传作业指导书"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "没有上传文件"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "未选择文件"}), 400
        upload_instruction_image(machine_id, file)
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@machines_bp.route("/<int:machine_id>/instruction", methods=["DELETE"])
def remove_instruction(machine_id: int):
    """DELETE /api/machines/<id>/instruction — 删除作业指导书"""
    try:
        ok = delete_instruction_image(machine_id)
        if not ok:
            return jsonify({"error": "该设备没有作业指导书"}), 404
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@machines_bp.route("/instruction/copy", methods=["POST"])
def copy_instr():
    """POST /api/machines/instruction/copy — 复制作业指导书"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求体必须为 JSON"}), 400
        source_id = data.get("source_machine_id")
        target_id = data.get("target_machine_id")
        if not source_id or not target_id:
            return jsonify({"error": "缺少 source_machine_id 或 target_machine_id"}), 400
        copy_instruction_image(int(source_id), int(target_id))
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
