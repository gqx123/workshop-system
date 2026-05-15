"""数据库建表语句"""

SCHEMA = """
-- ============================================================
-- 系统配置表
-- ============================================================
CREATE TABLE IF NOT EXISTS system_config (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL DEFAULT ''
);

-- ============================================================
-- 机床设备表
-- ============================================================
CREATE TABLE IF NOT EXISTS machines (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_code        TEXT    NOT NULL UNIQUE,
    machine_name        TEXT    NOT NULL,
    machine_type        TEXT    NOT NULL DEFAULT '',
    location            TEXT    NOT NULL DEFAULT '',
    status              TEXT    NOT NULL DEFAULT '正常',
    operator_name       TEXT    NOT NULL DEFAULT '',
    instruction_image   TEXT    NOT NULL DEFAULT '',
    created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ============================================================
-- 生产记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS production_records (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id          INTEGER NOT NULL,
    product_name        TEXT    NOT NULL,
    product_batch       TEXT    NOT NULL DEFAULT '',
    plan_quantity       INTEGER NOT NULL DEFAULT 0,
    actual_quantity     INTEGER NOT NULL DEFAULT 0,
    defect_quantity     INTEGER NOT NULL DEFAULT 0,
    start_time          TEXT    NOT NULL,
    end_time            TEXT,
    operator_name       TEXT    NOT NULL DEFAULT '',
    operator_id         TEXT    NOT NULL DEFAULT '',
    remark              TEXT    NOT NULL DEFAULT '',
    created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

-- ============================================================
-- 保养记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS maintenance_records (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id              INTEGER NOT NULL,
    maintenance_type        TEXT    NOT NULL,
    description             TEXT    NOT NULL DEFAULT '',
    parts_replaced          TEXT    NOT NULL DEFAULT '',
    next_maintenance_date   TEXT,
    operator_name           TEXT    NOT NULL DEFAULT '',
    operator_id             TEXT    NOT NULL DEFAULT '',
    duration_minutes        INTEGER NOT NULL DEFAULT 0,
    created_at              TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

-- ============================================================
-- 故障记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS fault_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id      INTEGER NOT NULL,
    fault_type      TEXT    NOT NULL DEFAULT '',
    description     TEXT    NOT NULL DEFAULT '',
    severity        TEXT    NOT NULL DEFAULT '一般',
    status          TEXT    NOT NULL DEFAULT '待处理',
    operator_name   TEXT    NOT NULL DEFAULT '',
    resolution      TEXT    NOT NULL DEFAULT '',
    resolved_at     TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

-- ============================================================
-- 点检模板表
-- ============================================================
CREATE TABLE IF NOT EXISTS inspection_templates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id      INTEGER NOT NULL,
    item_name       TEXT    NOT NULL,
    item_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

-- ============================================================
-- 点检记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS inspection_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id      INTEGER NOT NULL,
    operator_name   TEXT    NOT NULL DEFAULT '',
    remark          TEXT    NOT NULL DEFAULT '',
    details         TEXT    NOT NULL DEFAULT '[]',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

-- ============================================================
-- 索引
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_production_machine ON production_records(machine_id);
CREATE INDEX IF NOT EXISTS idx_production_time ON production_records(start_time);
CREATE INDEX IF NOT EXISTS idx_maintenance_machine ON maintenance_records(machine_id);
CREATE INDEX IF NOT EXISTS idx_maintenance_time ON maintenance_records(created_at);
CREATE INDEX IF NOT EXISTS idx_fault_machine ON fault_records(machine_id);
CREATE INDEX IF NOT EXISTS idx_fault_status ON fault_records(status);
CREATE INDEX IF NOT EXISTS idx_fault_time ON fault_records(created_at);
CREATE INDEX IF NOT EXISTS idx_insp_tpl_machine ON inspection_templates(machine_id);
CREATE INDEX IF NOT EXISTS idx_insp_tpl_order ON inspection_templates(machine_id, item_order);
CREATE INDEX IF NOT EXISTS idx_insp_rec_machine ON inspection_records(machine_id);
CREATE INDEX IF NOT EXISTS idx_insp_rec_time ON inspection_records(created_at);
"""
