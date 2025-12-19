import os
import sqlite3
import hashlib
import argparse
import sys
from datetime import datetime

# ================= 配置区域 =================
# 数据库文件名
DB_NAME = '../docs/mods_metadata.db'
# 默认扫描的文件夹路径 (你可以修改这里，或者运行时指定)
DEFAULT_FOLDER = '..\\mods'

# 核心表结构：必须包含 sha 和 filename，其他字段你可以动态添加
# 这里的 keys 对应数据库列名，values 是类型
CORE_FIELDS = {
    'sha': 'TEXT PRIMARY KEY',
    'filename': 'TEXT',
    'filepath': 'TEXT',
    'created_at': 'TIMESTAMP'
}
# ===========================================

class AssetManager:
    def __init__(self, db_path, folder_path):
        self.db_path = db_path
        self.folder_path = folder_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # 让查询结果像字典一样访问
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        fields_sql = ", ".join([f"{k} {v}" for k, v in CORE_FIELDS.items()])
        create_table_sql = f"CREATE TABLE IF NOT EXISTS files ({fields_sql})"
        self.cursor.execute(create_table_sql)
        self.conn.commit()

    def get_file_sha256(self, filepath):
        """计算文件的 SHA256 哈希值 (流式读取，防内存溢出)"""
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return None

    def add_custom_field(self, field_name, field_type='TEXT'):
        """
        [功能 1] 动态添加字段
        用户希望自己添加信息字段。
        """
        try:
            self.cursor.execute(f"ALTER TABLE files ADD COLUMN {field_name} {field_type}")
            self.conn.commit()
            print(f"✅ 成功添加字段: {field_name} ({field_type})")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"⚠️ 字段 {field_name} 已存在。")
            else:
                print(f"❌ 添加字段失败: {e}")

    def sync_folder(self):
        """
        [功能 2] 文件夹更新检查
        - 识别新增
        - 识别减少 (需确认)
        - 更新文件名 (如果内容没变但改名了)
        """
        if not os.path.exists(self.folder_path):
            print(f"❌ 文件夹不存在: {self.folder_path}")
            return

        print(f"🔍 正在扫描文件夹: {self.folder_path} ...")
        
        # 1. 获取磁盘上的现状
        disk_files = {} # {sha: {filepath, filename}}
        for root, _, files in os.walk(self.folder_path):
            for file in files:
                if file.startswith('.'): continue # 跳过隐藏文件
                path = os.path.join(root, file)
                sha = self.get_file_sha256(path)
                if sha:
                    disk_files[sha] = {'path': path, 'name': file}

        # 2. 获取数据库现状
        self.cursor.execute("SELECT sha, filename, filepath FROM files")
        db_rows = self.cursor.fetchall()
        db_shas = {row['sha']: row for row in db_rows}

        disk_sha_set = set(disk_files.keys())
        db_sha_set = set(db_shas.keys())

        # 3. 比较差异
        added_shas = disk_sha_set - db_sha_set
        removed_shas = db_sha_set - disk_sha_set
        common_shas = disk_sha_set & db_sha_set

        # 处理新增
        if added_shas:
            print(f"\n🟢 发现 {len(added_shas)} 个新文件:")
            for sha in added_shas:
                info = disk_files[sha]
                print(f"   + {info['name']}")
                # 写入数据库
                self.cursor.execute(
                    "INSERT INTO files (sha, filename, filepath, created_at) VALUES (?, ?, ?, ?)",
                    (sha, info['name'], info['path'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                )
            self.conn.commit()
            print("✅ 新增文件已录入数据库。")
        else:
            print("\n⚪ 没有检测到新文件。")

        # 处理移动/重命名 (在 common_shas 中检查路径是否变化)
        updated_count = 0
        for sha in common_shas:
            new_path = disk_files[sha]['path']
            new_name = disk_files[sha]['name']
            old_path = db_shas[sha]['filepath']
            
            if new_path != old_path:
                self.cursor.execute(
                    "UPDATE files SET filepath = ?, filename = ? WHERE sha = ?",
                    (new_path, new_name, sha)
                )
                updated_count += 1
        if updated_count > 0:
            self.conn.commit()
            print(f"🔵 更新了 {updated_count} 个文件的路径/名称信息。")

        # 处理删除 (需要用户确认)
        if removed_shas:
            print(f"\n🔴 数据库中有 {len(removed_shas)} 个文件在本地文件夹找不到:")
            for sha in removed_shas:
                print(f"   - {db_shas[sha]['filename']} (SHA: {sha[:8]}...)")
            
            confirm = input("\n⚠️ 是否从数据库中删除这些记录? (输入 'yes' 确认): ")
            if confirm.lower() == 'yes':
                for sha in removed_shas:
                    self.cursor.execute("DELETE FROM files WHERE sha = ?", (sha,))
                self.conn.commit()
                print("✅ 记录已删除。")
            else:
                print("🚫 操作取消，数据库保持原样。")
        else:
            print("⚪ 没有检测到文件丢失。")

    def list_missing_fields(self, field):
        """
        [功能 3] 展示字段缺失的项
        """
        try:
            # 检查列是否存在
            self.cursor.execute("SELECT * FROM files LIMIT 0")
            col_names = [description[0] for description in self.cursor.description]
            if field not in col_names:
                print(f"❌ 数据库中不存在字段: {field}")
                return

            sql = f"SELECT sha, filename FROM files WHERE {field} IS NULL OR {field} = ''"
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()

            if not rows:
                print(f"✨ 所有文件的 '{field}' 字段都已填写完整！")
            else:
                print(f"\n🟠 共有 {len(rows)} 个文件缺失 '{field}':")
                for row in rows:
                    print(f"   [SHA: {row['sha'][:8]}] {row['filename']}")
        except Exception as e:
            print(f"Error: {e}")

    def update_single_item(self, sha_prefix, field, value):
        """
        [功能 3] 填入接口 (单个)
        """
        # 模糊匹配 SHA
        self.cursor.execute("SELECT sha, filename FROM files WHERE sha LIKE ?", (sha_prefix + '%',))
        rows = self.cursor.fetchall()
        
        if len(rows) == 0:
            print("❌ 找不到对应的 SHA。")
            return
        elif len(rows) > 1:
            print("❌ SHA 前缀不唯一，匹配到多个文件。请提供更长的 SHA。")
            return
        
        target_sha = rows[0]['sha']
        filename = rows[0]['filename']

        try:
            self.cursor.execute(f"UPDATE files SET {field} = ? WHERE sha = ?", (value, target_sha))
            self.conn.commit()
            print(f"✅ 已更新 [{filename}] 的 {field} = {value}")
        except Exception as e:
            print(f"❌ 更新失败: {e}")

    def batch_update(self, field, value, filter_sql=None):
        """
        [功能 4] 大规模对项进行某一字段的写
        filter_sql: 可选的 WHERE 子句，用于限定范围
        """
        print(f"\n⚠️ 准备将所有记录的 '{field}' 字段修改为 '{value}'")
        if filter_sql:
            print(f"   过滤条件: {filter_sql}")
        
        confirm = input("此操作将影响大量数据，确认执行吗? (输入 'yes' 确认): ")
        if confirm.lower() != 'yes':
            print("🚫 操作取消。")
            return

        try:
            sql = f"UPDATE files SET {field} = ?"
            if filter_sql:
                sql += f" WHERE {filter_sql}"
            
            self.cursor.execute(sql, (value,))
            self.conn.commit()
            print(f"✅ 成功更新了 {self.cursor.rowcount} 条记录。")
        except Exception as e:
            print(f"❌ 批量更新失败: {e}")
            print("提示: 确保字段存在。如果是新字段，请先使用 'add_field' 命令。")

    def show_columns(self):
        self.cursor.execute("PRAGMA table_info(files)")
        columns = self.cursor.fetchall()
        print("\n📊 当前数据库字段:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")

    def delete_field(self, field_name):
        """
        [功能 5] 删除数据库字段
        注意：SQLite不支持直接删除字段，需要重建表
        """
        try:
            # 检查列是否存在
            self.cursor.execute("PRAGMA table_info(files)")
            columns = self.cursor.fetchall()
            col_names = [col[1] for col in columns]

            if field_name not in col_names:
                print(f"❌ 字段 '{field_name}' 不存在")
                return

            # 检查是否为核心字段（不允许删除）
            if field_name in CORE_FIELDS:
                print(f"❌ 不能删除核心字段 '{field_name}'")
                return

            print(f"\n⚠️ 准备删除字段: {field_name}")
            confirm = input("此操作将重建数据库表，确认执行吗? (输入 'yes' 确认): ")
            if confirm.lower() != 'yes':
                print("🚫 操作取消。")
                return

            # 获取当前表的所有数据
            self.cursor.execute(f"SELECT * FROM files")
            rows = self.cursor.fetchall()

            # 获取除了要删除列之外的所有列名
            other_columns = [col for col in col_names if col != field_name]
            other_columns_str = ", ".join(other_columns)

            # 创建临时表
            temp_table_sql = f"CREATE TABLE temp_files AS SELECT {other_columns_str} FROM files"
            self.cursor.execute(temp_table_sql)

            # 删除原表
            self.cursor.execute("DROP TABLE files")

            # 重新创建表（去掉要删除的列）
            fields_sql = ", ".join([f"{k} {v}" for k, v in CORE_FIELDS.items() if k != field_name])
            # 添加其他非核心字段
            for col_name in other_columns:
                if col_name not in CORE_FIELDS:
                    # 获取列类型
                    for col in columns:
                        if col[1] == col_name:
                            fields_sql += f", {col_name} {col[2]}"
                            break

            create_table_sql = f"CREATE TABLE files ({fields_sql})"
            self.cursor.execute(create_table_sql)

            # 从临时表复制数据回来
            if other_columns:
                insert_sql = f"INSERT INTO files ({other_columns_str}) SELECT {other_columns_str} FROM temp_files"
                self.cursor.execute(insert_sql)

            # 删除临时表
            self.cursor.execute("DROP TABLE temp_files")

            self.conn.commit()
            print(f"✅ 成功删除字段: {field_name}")

        except Exception as e:
            print(f"❌ 删除字段失败: {e}")
            self.conn.rollback()

    def rename_field(self, old_name, new_name):
        """
        [功能 6] 重命名字段
        注意：SQLite 3.25.0+支持直接重命名，这里使用兼容性更好的重建表方法
        """
        try:
            # 检查旧字段是否存在
            self.cursor.execute("PRAGMA table_info(files)")
            columns = self.cursor.fetchall()
            col_names = [col[1] for col in columns]

            if old_name not in col_names:
                print(f"❌ 字段 '{old_name}' 不存在")
                return

            if new_name in col_names:
                print(f"❌ 字段 '{new_name}' 已存在")
                return

            print(f"\n⚠️ 准备重命名字段: {old_name} -> {new_name}")
            confirm = input("此操作将重建数据库表，确认执行吗? (输入 'yes' 确认): ")
            if confirm.lower() != 'yes':
                print("🚫 操作取消。")
                return

            # 获取当前表的所有数据
            self.cursor.execute(f"SELECT * FROM files")
            rows = self.cursor.fetchall()

            # 创建新的列名列表（替换旧名称为新名称）
            new_columns = [new_name if col == old_name else col for col in col_names]
            new_columns_str = ", ".join(new_columns)
            old_columns_str = ", ".join(col_names)

            # 创建临时表（使用新的列名）
            temp_table_sql = f"CREATE TABLE temp_files ({new_columns_str})"
            self.cursor.execute(temp_table_sql)

            # 复制数据到临时表
            if rows:
                # 构建INSERT语句，将旧列名映射到新列名
                insert_cols = ", ".join([f'"{col}"' for col in new_columns])
                select_cols = ", ".join([f'"{old_col}"' for old_col in col_names])
                insert_sql = f"INSERT INTO temp_files ({insert_cols}) SELECT {select_cols} FROM files"
                self.cursor.execute(insert_sql)

            # 删除原表
            self.cursor.execute("DROP TABLE files")

            # 重新创建表（使用新的列名和类型）
            fields_sql = []
            for col in columns:
                col_name = new_name if col[1] == old_name else col[1]
                fields_sql.append(f"{col_name} {col[2]}")

            create_table_sql = f"CREATE TABLE files ({', '.join(fields_sql)})"
            self.cursor.execute(create_table_sql)

            # 从临时表复制数据回来
            if rows:
                insert_sql = f"INSERT INTO files ({new_columns_str}) SELECT {new_columns_str} FROM temp_files"
                self.cursor.execute(insert_sql)

            # 删除临时表
            self.cursor.execute("DROP TABLE temp_files")

            self.conn.commit()
            print(f"✅ 成功重命名字段: {old_name} -> {new_name}")

        except Exception as e:
            print(f"❌ 重命名字段失败: {e}")
            self.conn.rollback()

# ================= 命令行接口逻辑 =================
def main():
    parser = argparse.ArgumentParser(description="本地文件资产管理脚本")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 1. Sync: 同步文件夹到数据库
    parser_sync = subparsers.add_parser('sync', help='同步文件夹内容到数据库')
    parser_sync.add_argument('--folder', type=str, default=DEFAULT_FOLDER, help='指定扫描文件夹路径')

    # 2. Add Field: 添加新字段
    parser_add = subparsers.add_parser('add_field', help='添加新的信息字段')
    parser_add.add_argument('name', type=str, help='字段名称 (英文)')
    parser_add.add_argument('--type', type=str, default='TEXT', help='字段类型 (TEXT, INTEGER, REAL)')

    # 3. Check Missing: 检查缺失项
    parser_miss = subparsers.add_parser('check', help='检查某字段缺失的项')
    parser_miss.add_argument('field', type=str, help='要检查的字段名')

    # 4. Update Single: 单个更新
    parser_upd = subparsers.add_parser('update', help='更新单个文件的字段')
    parser_upd.add_argument('sha', type=str, help='文件 SHA 前几位')
    parser_upd.add_argument('field', type=str, help='字段名')
    parser_upd.add_argument('value', type=str, help='值')

    # 5. Batch Update: 批量更新
    parser_batch = subparsers.add_parser('batch_write', help='批量写入字段')
    parser_batch.add_argument('field', type=str, help='字段名')
    parser_batch.add_argument('value', type=str, help='值')
    parser_batch.add_argument('--where', type=str, default=None, help='SQL WHERE 条件 (可选，例如 "author IS NULL")')

    # 6. Show Columns: 查看字段
    subparsers.add_parser('info', help='查看当前所有字段')

    # 7. Delete Field: 删除字段
    parser_del = subparsers.add_parser('delete_field', help='删除指定的字段')
    parser_del.add_argument('name', type=str, help='要删除的字段名')

    # 8. Rename Field: 重命名字段
    parser_rename = subparsers.add_parser('rename_field', help='重命名指定的字段')
    parser_rename.add_argument('old_name', type=str, help='原字段名')
    parser_rename.add_argument('new_name', type=str, help='新字段名')

    args = parser.parse_args()

    # 初始化管理器
    manager = AssetManager(DB_NAME, args.folder if hasattr(args, 'folder') else DEFAULT_FOLDER)

    if args.command == 'sync':
        manager.sync_folder()
    elif args.command == 'add_field':
        manager.add_custom_field(args.name, args.type)
    elif args.command == 'check':
        manager.list_missing_fields(args.field)
    elif args.command == 'update':
        manager.update_single_item(args.sha, args.field, args.value)
    elif args.command == 'batch_write':
        manager.batch_update(args.field, args.value, args.where)
    elif args.command == 'info':
        manager.show_columns()
    elif args.command == 'delete_field':
        manager.delete_field(args.name)
    elif args.command == 'rename_field':
        manager.rename_field(args.old_name, args.new_name)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()