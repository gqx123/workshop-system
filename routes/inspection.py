"""点检模板与点检记录相关路由"""
from flask import Blueprint, jsonify, request, make_response
from services.inspection_service import (
    get_templates, create_template, update_template,
    delete_template, copy_templates, import_templates,
    create_inspection, list_inspections,
    get_inspection_by_id, delete_inspection,
    check_today_inspected,
)
import openpyxl
from openpyxl.utils import get_column_letter
from io import BytesIO

inspection_bp = Blueprint("inspection", __name__)


@inspection_bp.route("/api/inspection-templates", methods=["GET"])
def query_templates():
    try:
        machine_id = request.args.get("machine_id", type=int)
        if not machine_id:
            return jsonify({"error": "缺少 machine_id 参数"}), 400
        return jsonify(get_templates(machine_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inspection_bp.route("/api/inspection-templates", methods=["POST"])
def add_template():
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
def edit_template(template_id):
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
def remove_template(template_id):
    try:
        ok = delete_template(template_id)
        if not ok:
            return jsonify({"error": "记录不存在"}), 404
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inspection_bp.route("/api/inspection-templates/copy", methods=["POST"])
def copy_template():
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


@inspection_bp.route("/api/inspection-templates/import", methods=["POST"])
def import_template():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求体必须为 JSON"}), 400
        machine_id = data.get("machine_id")
        items = data.get("items", [])
        if not machine_id:
            return jsonify({"error": "缺少 machine_id"}), 400
        if not items:
            return jsonify({"error": "没有可导入的项目"}), 400
        count = import_templates(machine_id, items)
        return jsonify({"success": True, "imported": count})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inspection_bp.route("/api/inspection", methods=["POST"])
def add_inspection():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "请求体必须为 JSON"}), 400
        # 检查今日是否已点检
        mid = data.get("machine_id")
        if mid and check_today_inspected(int(mid)):
            return jsonify({"error": "该设备今日已点检，不能重复提交。如需重新填写，请联系管理员删除今日记录后重试"}), 400
        new_id = create_inspection(data)
        return jsonify({"success": True, "id": new_id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inspection_bp.route("/api/inspection", methods=["GET"])
def query_inspections():
    try:
        machine_id = request.args.get("machine_id", type=int)
        return jsonify(list_inspections(machine_id=machine_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inspection_bp.route("/api/inspection/<int:record_id>", methods=["GET"])
def get_inspection(record_id):
    try:
        r = get_inspection_by_id(record_id)
        if r is None:
            return jsonify({"error": "记录不存在"}), 404
        return jsonify(r)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inspection_bp.route("/api/inspection/<int:record_id>", methods=["DELETE"])
def remove_inspection(record_id):
    try:
        ok = delete_inspection(record_id)
        if not ok:
            return jsonify({"error": "记录不存在"}), 404
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inspection_bp.route("/api/inspection/export", methods=["GET"])
def export_inspections():
    try:
        machine_id = request.args.get("machine_id", type=int)
        records = list_inspections(machine_id=machine_id, limit=1000)
        if not records:
            return jsonify({"error": "没有可导出的点检记录"}), 400

        # 按机床分组
        grouped = {}
        for r in records:
            key = r.get("machine_code", "未知机床")
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(r)

        # 创建 Excel
        wb = openpyxl.Workbook()
        wb.remove(wb.active)

        for machine_code, recs in grouped.items():
            sheet_name = machine_code[:31]
            ws = wb.create_sheet(title=sheet_name)

            # 收集所有点检项目名称（取第一次记录的明细顺序）
            all_items = []
            if recs[0].get("details"):
                for d in recs[0]["details"]:
                    all_items.append(d.get("item_name", ""))

            # 第一行：点检人
            ws.cell(row=1, column=1, value="点检人")
            # 第二行：日期
            ws.cell(row=2, column=1, value="日期")

            # 从第三行开始：点检项目
            for i, item_name in enumerate(all_items):
                ws.cell(row=i + 3, column=1, value=item_name)

            # 从第二列开始，每列是一次点检记录
            for col_idx, rec in enumerate(recs):
                col = col_idx + 2

                # 点检人
                ws.cell(row=1, column=col, value=rec.get("operator_name", ""))

                # 日期
                ws.cell(row=2, column=col, value=rec.get("created_at", ""))

                # 点检结果
                details = rec.get("details", [])
                for i, d in enumerate(details):
                    result = d.get("result", "")
                    note = d.get("note", "")
                    if note:
                        result = result + "（" + note + "）"
                    ws.cell(row=i + 3, column=col, value=result)

            # 设置列宽
            ws.column_dimensions['A'].width = 45
            for ci in range(len(recs)):
                ws.column_dimensions[get_column_letter(ci + 2)].width = 25

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        resp = make_response(output.read())
        resp.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        resp.headers["Content-Disposition"] = "attachment; filename=inspection_records.xlsx"
        return resp
    except Exception as e:
        return jsonify({"error": str(e)}), 500

