"""生产记录业务逻辑层"""
from database.db import Database

db = Database()


def create_production(data: dict) -> int:
    """新建生产记录"""
    required = ["machine_id", "product_name", "start_time", "operator_name"]
    for f in required:
        if f not in data or data[f] is None:
            raise ValueError(f"缺少必填字段: {f}")

    db.execute_write(
        "INSERT INTO production_records ("
        "    machine_id, product_name, product_batch, "
        "    plan_quantity, actual_quantity, defect_quantity, "
        "    start_time, end_time, operator_name, operator_id, remark"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            data["machine_id"],
            data["product_name"],
            data.get("product_batch", ""),
            data.get("plan_quantity", 0),
            data.get("actual_quantity", 0),
            data.get("defect_quantity", 0),
            data["start_time"],
            data.get("end_time"),
            data["operator_name"],
            data.get("operator_id", ""),
            data.get("remark", ""),
        ),
    )
    row = db.execute_one("SELECT last_insert_rowid() AS id")
    return row["id"]


def list_production(
    machine_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 200,
) -> list[dict]:
    """查询生产记录"""
    sql = (
        "SELECT p.*, m.machine_code, m.machine_name "
        "FROM production_records p "
        "JOIN machines m ON p.machine_id = m.id "
        "WHERE 1=1"
    )
    params: list = []
    if machine_id is not None:
        sql += " AND p.machine_id = ?"
        params.append(machine_id)
    if date_from is not None:
        sql += " AND p.start_time >= ?"
        params.append(date_from)
    if date_to is not None:
        sql += " AND p.start_time <= ?"
        params.append(date_to)
    sql += " ORDER BY p.created_at DESC LIMIT ?"
    params.append(limit)
    return db.execute(sql, tuple(params))


def get_production_by_id(record_id: int) -> dict | None:
    """获取单条生产记录"""
    return db.execute_one(
        "SELECT p.*, m.machine_code, m.machine_name "
        "FROM production_records p "
        "JOIN machines m ON p.machine_id = m.id "
        "WHERE p.id = ?",
        (record_id,),
    )


def update_production(record_id: int, data: dict) -> bool:
    """更新生产记录"""
    allowed = {
        "machine_id", "product_name", "product_batch",
        "plan_quantity", "actual_quantity", "defect_quantity",
        "start_time", "end_time", "operator_name", "operator_id", "remark",
    }
    updates, params = [], []
    for key, val in data.items():
        if key in allowed:
            updates.append(f"{key} = ?")
            params.append(val)
    if not updates:
        return False
    params.append(record_id)
    rows = db.execute_write(
        f"UPDATE production_records SET {', '.join(updates)} WHERE id = ?", tuple(params)
    )
    return rows > 0


def delete_production(record_id: int) -> bool:
    """删除生产记录"""
    rows = db.execute_write("DELETE FROM production_records WHERE id = ?", (record_id,))
    return rows > 0
