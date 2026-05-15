"""点检模板与点检记录业务逻辑层"""
import json
import os
import uuid
from werkzeug.utils import secure_filename
from database.db import Database

db = Database()


# ================================================================
# 点检模板 CRUD
# ================================================================

def get_templates(machine_id: int) -> list[dict]:
    """获取某台设备的所有点检模板项目"""
    return db.execute(
        "SELECT id, machine_id, item_name, item_order, requires_photo, created_at "
        "FROM inspection_templates "
        "WHERE machine_id = ? "
        "ORDER BY item_order, id",
        (machine_id,),
    )


def create_template(data: dict) -> int:
    """新增一个点检模板项目"""
    if not data.get("machine_id"):
        raise ValueError("缺少字段: machine_id")
    if not data.get("item_name"):
        raise ValueError("缺少字段: item_name")

    row = db.execute_one(
        "SELECT COALESCE(MAX(item_order), 0) AS max_order "
        "FROM inspection_templates WHERE machine_id = ?",
        (data["machine_id"],),
    )
    next_order = (row["max_order"] if row else 0) + 1

    db.execute_write(
        "INSERT INTO inspection_templates (machine_id, item_name, item_order, requires_photo) "
        "VALUES (?, ?, ?, ?)",
        (data["machine_id"], data["item_name"].strip(), next_order,
         1 if data.get("requires_photo") else 0),
    )
    row = db.execute_one("SELECT last_insert_rowid() AS id")
    return row["id"]


def update_template(template_id: int, data: dict) -> bool:
    """更新点检模板项目"""
    allowed = {"item_name", "item_order", "requires_photo"}
    updates, params = [], []
    for key, val in data.items():
        if key in allowed:
            if key == "requires_photo":
                val = 1 if val else 0
            updates.append(f"{key} = ?")
            params.append(val)
    if not updates:
        return False
    params.append(template_id)
    rows = db.execute_write(
        f"UPDATE inspection_templates SET {', '.join(updates)} WHERE id = ?",
        tuple(params),
    )
    return rows > 0


def delete_template(template_id: int) -> bool:
    """删除点检模板项目"""
    rows = db.execute_write(
        "DELETE FROM inspection_templates WHERE id = ?", (template_id,)
    )
    return rows > 0


def copy_templates(source_machine_id: int, target_machine_id: int) -> int:
    """将源设备的点检模板复制到目标设备（含 requires_photo）"""
    if source_machine_id == target_machine_id:
        raise ValueError("源设备和目标设备不能相同")

    source_items = get_templates(source_machine_id)
    if not source_items:
        raise ValueError("源设备没有点检模板，无法复制")

    db.execute_write(
        "DELETE FROM inspection_templates WHERE machine_id = ?",
        (target_machine_id,),
    )

    params_list = [
        (target_machine_id, item["item_name"], item["item_order"],
         item.get("requires_photo", 0))
        for item in source_items
    ]
    db.execute_many(
        "INSERT INTO inspection_templates (machine_id, item_name, item_order, requires_photo) "
        "VALUES (?, ?, ?, ?)",
        params_list,
    )
    return len(params_list)


# ================================================================
# 点检记录 CRUD
# ================================================================

def create_inspection(data: dict) -> int:
    """提交点检记录"""
    if not data.get("machine_id"):
        raise ValueError("缺少字段: machine_id")
    if not data.get("operator_name"):
        raise ValueError("缺少字段: operator_name")

    details = data.get("details", [])
    details_json = json.dumps(details, ensure_ascii=False)

    db.execute_write(
        "INSERT INTO inspection_records (machine_id, operator_name, remark, details) "
        "VALUES (?, ?, ?, ?)",
        (data["machine_id"], data["operator_name"], data.get("remark", ""), details_json),
    )
    row = db.execute_one("SELECT last_insert_rowid() AS id")
    return row["id"]


def list_inspections(
    machine_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 200,
) -> list[dict]:
    """查询点检记录"""
    sql = (
        "SELECT ir.*, m.machine_code, m.machine_name "
        "FROM inspection_records ir "
        "JOIN machines m ON ir.machine_id = m.id "
        "WHERE 1=1"
    )
    params: list = []
    if machine_id is not None:
        sql += " AND ir.machine_id = ?"
        params.append(machine_id)
    if date_from is not None:
        sql += " AND ir.created_at >= ?"
        params.append(date_from)
    if date_to is not None:
        sql += " AND ir.created_at <= ?"
        params.append(date_to)
    sql += " ORDER BY ir.created_at DESC LIMIT ?"
    params.append(limit)
    rows = db.execute(sql, tuple(params))
    for r in rows:
        try:
            r["details"] = json.loads(r["details"])
        except (json.JSONDecodeError, TypeError):
            r["details"] = []
    return rows


def get_inspection_by_id(record_id: int) -> dict | None:
    """获取单条点检记录"""
    row = db.execute_one(
        "SELECT ir.*, m.machine_code, m.machine_name "
        "FROM inspection_records ir "
        "JOIN machines m ON ir.machine_id = m.id "
        "WHERE ir.id = ?",
        (record_id,),
    )
    if row:
        try:
            row["details"] = json.loads(row["details"])
        except (json.JSONDecodeError, TypeError):
            row["details"] = []
    return row


def delete_inspection(record_id: int) -> bool:
    """删除点检记录（同时清理关联照片文件）"""
    record = get_inspection_by_id(record_id)
    if not record:
        return False

    # 清理照片文件
    if record.get("details"):
        for d in record["details"]:
            photo = d.get("photo", "")
            if photo:
                _delete_inspection_photo(photo)

    rows = db.execute_write(
        "DELETE FROM inspection_records WHERE id = ?", (record_id,)
    )
    return rows > 0


def check_today_inspected(machine_id: int) -> bool:
    """检查某设备今日是否已点检"""
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    row = db.execute_one(
        "SELECT COUNT(*) AS cnt FROM inspection_records "
        "WHERE machine_id = ? AND created_at >= ? AND created_at <= ?",
        (machine_id, f"{today} 00:00:00", f"{today} 23:59:59"),
    )
    return row and row["cnt"] > 0


def import_templates(machine_id: int, items: list[str]) -> int:
    """批量导入点检模板（覆盖模式），导入的项目默认不需要拍照"""
    if not machine_id:
        raise ValueError("缺少 machine_id")

    db.execute_write(
        "DELETE FROM inspection_templates WHERE machine_id = ?",
        (machine_id,),
    )

    valid_items = [name.strip() for name in items if name.strip()]
    if not valid_items:
        raise ValueError("CSV 中没有有效的点检项目")

    params_list = [
        (machine_id, name, i + 1, 0)
        for i, name in enumerate(valid_items)
    ]
    db.execute_many(
        "INSERT INTO inspection_templates (machine_id, item_name, item_order, requires_photo) "
        "VALUES (?, ?, ?, ?)",
        params_list,
    )
    return len(params_list)


# ================================================================
# 点检照片
# ================================================================

def save_inspection_photo(machine_id: int, file_storage) -> str:
    """上传点检照片，返回文件名"""
    from config import UPLOAD_DIR
    photo_dir = os.path.join(UPLOAD_DIR, "inspection_photos")
    os.makedirs(photo_dir, exist_ok=True)

    ext = os.path.splitext(secure_filename(file_storage.filename))[1] or ".jpg"
    filename = f"insp_{machine_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(photo_dir, filename)
    file_storage.save(filepath)
    return filename


def get_inspection_photo_path(filename: str) -> str | None:
    """获取点检照片完整路径"""
    from config import UPLOAD_DIR
    filepath = os.path.join(UPLOAD_DIR, "inspection_photos", filename)
    if os.path.exists(filepath):
        return filepath
    return None


def _delete_inspection_photo(filename: str):
    """删除单张点检照片"""
    from config import UPLOAD_DIR
    filepath = os.path.join(UPLOAD_DIR, "inspection_photos", filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except OSError:
            pass
