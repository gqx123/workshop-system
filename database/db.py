"""数据库操作封装 - 统一管理 SQLite 连接与基础 CRUD"""
import sqlite3
import logging
from config import DB_PATH
from database.schema import SCHEMA

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """数据库操作异常"""
    pass


class Database:

    def get_connection(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA busy_timeout=5000")
            return conn
        except sqlite3.Error as e:
            logger.error("数据库连接失败: %s", e)
            raise DatabaseError(f"数据库连接失败: {e}") from e

    def execute(self, sql, params=()):
        conn = self.get_connection()
        try:
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error("查询失败 [%s] params=%s: %s", sql, params, e)
            raise DatabaseError(f"查询失败: {e}") from e
        finally:
            conn.close()

    def execute_one(self, sql, params=()):
        conn = self.get_connection()
        try:
            cursor = conn.execute(sql, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error("查询失败 [%s] params=%s: %s", sql, params, e)
            raise DatabaseError(f"查询失败: {e}") from e
        finally:
            conn.close()

    def execute_write(self, sql, params=()):
        conn = self.get_connection()
        try:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            conn.rollback()
            logger.error("写入失败 [%s] params=%s: %s", sql, params, e)
            raise DatabaseError(f"写入失败: {e}") from e
        finally:
            conn.close()

    def execute_many(self, sql, params_list):
        conn = self.get_connection()
        try:
            cursor = conn.executemany(sql, params_list)
            conn.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            conn.rollback()
            logger.error("批量写入失败 [%s]: %s", sql, e)
            raise DatabaseError(f"批量写入失败: {e}") from e
        finally:
            conn.close()

    def execute_transaction(self, operations):
        conn = self.get_connection()
        try:
            for sql, params in operations:
                conn.execute(sql, params)
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error("事务执行失败，已回滚: %s", e)
            raise DatabaseError(f"事务执行失败: {e}") from e
        finally:
            conn.close()

    def init_db(self):
        conn = self.get_connection()
        try:
            conn.executescript(SCHEMA)
            # 迁移：machines 表加 instruction_image 字段（兼容旧数据库）
            try:
                conn.execute("ALTER TABLE machines ADD COLUMN instruction_image TEXT NOT NULL DEFAULT ''")
            except sqlite3.OperationalError:
                pass  # 字段已存在
            conn.commit()
            logger.info("数据库表初始化完成")
        except sqlite3.Error as e:
            logger.error("数据库初始化失败: %s", e)
            raise DatabaseError(f"数据库初始化失败: {e}") from e
        finally:
            conn.close()

    def seed_machines(self):
        row = self.execute_one("SELECT value FROM system_config WHERE key = 'seed_done'")
        if row and row["value"] == "yes":
            logger.info("预置数据已初始化过，跳过")
            return
        from config import DEFAULT_MACHINES
        if not DEFAULT_MACHINES:
            logger.warning("DEFAULT_MACHINES 为空，无预置数据")
            self.execute_write("INSERT OR REPLACE INTO system_config (key, value) VALUES ('seed_done', 'yes')")
            return
        conn = self.get_connection()
        try:
            conn.executemany(
                "INSERT INTO machines (machine_code, machine_name, machine_type, location) VALUES (?, ?, ?, ?)",
                DEFAULT_MACHINES,
            )
            conn.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('seed_done', 'yes')")
            conn.commit()
            logger.info("预置 %d 台机床数据完成", len(DEFAULT_MACHINES))
        except sqlite3.Error as e:
            conn.rollback()
            logger.error("预置机床数据失败: %s", e)
            raise DatabaseError(f"预置机床数据失败: {e}") from e
        finally:
            conn.close()

    def table_exists(self, table_name):
        row = self.execute_one("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        return row is not None

    def get_table_row_count(self, table_name):
        row = self.execute_one(f"SELECT COUNT(*) AS cnt FROM {table_name}")
        return row["cnt"] if row else 0

    def vacuum(self):
        conn = self.get_connection()
        try:
            conn.execute("VACUUM")
        except sqlite3.Error as e:
            logger.error("VACUUM 失败: %s", e)
        finally:
            conn.close()
