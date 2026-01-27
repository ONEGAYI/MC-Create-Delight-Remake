import os
import sqlite3
import hashlib
import argparse
import sys
import re
import shutil
from datetime import datetime
from pathlib import Path

# ================= 配置区域 =================
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)  # 切换工作目录到脚本所在目录
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

    def sync_folder(self, auto_confirm=False):
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
        
        # 1. 获取磁盘上的现状（只扫描第一层，不递归子文件夹）
        disk_files = {} # {sha: {filepath, filename}}
        for file in os.listdir(self.folder_path):
            # 跳过隐藏文件
            if file.startswith('.'): continue  # 隐藏文件
            path = os.path.join(self.folder_path, file)
            # 只处理文件，跳过子文件夹
            if not os.path.isfile(path): continue
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
            
            if auto_confirm:
                print("\n🔧 自动确认模式：删除缺失文件的数据库记录。")
                confirm = 'yes'
            else:
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

            # 获取总数
            self.cursor.execute("SELECT COUNT(*) as total FROM files")
            total_count = self.cursor.fetchone()['total']

            # 获取缺失项
            sql = f"SELECT sha, filename FROM files WHERE {field} IS NULL OR {field} = ''"
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()

            # 计算统计信息
            missing_count = len(rows)
            passed_count = total_count - missing_count

            print(f"检查了 '{field}' 字段，通过检查的有: {passed_count} / {total_count}")

            if not rows:
                print(f"✨ 所有文件的 '{field}' 字段都已填写完整！")
            else:
                print(f"\n🟠 共有 {missing_count} 个文件缺失 '{field}':")
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

    def search_items(self, field, target, use_regex=False):
        """
        [功能 7] 搜索数据库中的项
        field: 要搜索的字段名
        target: 搜索目标值
        use_regex: 是否使用正则表达式
        """
        try:
            # 检查字段是否存在
            self.cursor.execute("PRAGMA table_info(files)")
            columns = self.cursor.fetchall()
            col_names = [col[1] for col in columns]

            if field not in col_names:
                print(f"❌ 字段 '{field}' 不存在")
                print(f"\n可用字段: {', '.join(col_names)}")
                return

            # 构建SQL查询
            if use_regex:
                # 使用SQLite的REGEXP函数
                self.cursor.execute(f"SELECT sha, filename, {field}, filepath FROM files WHERE {field} IS NOT NULL AND {field} != ''")
                all_rows = self.cursor.fetchall()

                pattern = re.compile(target, re.IGNORECASE if not target.isupper() else 0)
                matched_rows = []

                for row in all_rows:
                    field_value = str(row[2]) if row[2] is not None else ""
                    if pattern.search(field_value):
                        matched_rows.append(row)

                matched_count = len(matched_rows)
            else:
                # 使用LIKE进行模糊匹配
                if target.startswith("'") and target.endswith("'"):
                    # 如果用引号包围，进行精确匹配
                    search_target = target.strip("'")
                    sql = f"SELECT sha, filename, {field}, filepath FROM files WHERE {field} = ?"
                    self.cursor.execute(sql, (search_target,))
                else:
                    # 否则进行模糊匹配
                    search_target = f"%{target}%"
                    sql = f"SELECT sha, filename, {field}, filepath FROM files WHERE {field} IS NOT NULL AND {field} != '' AND {field} LIKE ?"
                    self.cursor.execute(sql, (search_target,))

                matched_rows = self.cursor.fetchall()
                matched_count = len(matched_rows)

            # 显示结果
            if matched_count == 0:
                print(f"❌ 没有找到匹配项 (字段: {field}, 搜索值: {target})")
                if use_regex:
                    print("💡 提示: 正则表达式可能需要调整")
                else:
                    print("💡 提示: 尝试使用更简单的搜索词或添加引号进行精确匹配")
            else:
                mode = "正则表达式" if use_regex else ("模糊" if not target.startswith("'") else "精确")
                print(f"\n🔍 搜索结果 (模式: {mode}匹配, 字段: {field})")
                print(f"{'='*80}")
                print(f"共找到 {matched_count} 个匹配项:")
                print(f"{'='*80}")

                for i, row in enumerate(matched_rows, 1):
                    sha = row['sha'][:12] + "..."
                    filename = row['filename']
                    field_value = str(row[field]) if row[field] is not None else "(空)"
                    filepath = row['filepath']

                    print(f"\n{i:3d}. 【{filename}】")
                    print(f"     SHA: {sha}")
                    print(f"     {field}: {field_value}")
                    # 只显示相对路径，减少输出长度
                    rel_path = filepath.replace(DEFAULT_FOLDER, ".") if filepath.startswith(DEFAULT_FOLDER) else filepath
                    print(f"     路径: {rel_path}")

                print(f"\n{'='*80}")
                print(f"总计: {matched_count} 个匹配项")

        except re.error as e:
            print(f"❌ 正则表达式错误: {e}")
            print("💡 提示: 请检查正则表达式语法")
        except Exception as e:
            print(f"❌ 搜索失败: {e}")

    def backup_database(self, backup_dir=None):
        """
        [功能 8] 备份数据库
        将当前数据库备份到指定目录
        """
        try:
            # 获取数据库文件路径
            db_abs_path = os.path.abspath(self.db_path)
            db_dir = os.path.dirname(db_abs_path)
            db_name = os.path.basename(db_abs_path).replace('.db', '')

            # 确定备份目录
            if backup_dir is None:
                backup_dir = os.path.join(db_dir, 'bak')

            # 创建备份目录
            os.makedirs(backup_dir, exist_ok=True)

            # 生成备份文件名（带时间戳）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{db_name}_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)

            # 执行备份
            shutil.copy2(db_abs_path, backup_path)

            print(f"✅ 数据库已备份到: {backup_path}")

            # 列出所有备份文件
            backups = self.list_backups(backup_dir)
            print(f"📁 当前共有 {len(backups)} 个备份文件")

            return backup_path

        except Exception as e:
            print(f"❌ 备份失败: {e}")
            return None

    def list_backups(self, backup_dir=None):
        """
        列出所有备份文件
        按时间戳排序，最新的在前
        """
        try:
            # 获取数据库文件路径
            db_abs_path = os.path.abspath(self.db_path)
            db_dir = os.path.dirname(db_abs_path)
            db_name = os.path.basename(db_abs_path).replace('.db', '')

            # 确定备份目录
            if backup_dir is None:
                backup_dir = os.path.join(db_dir, 'bak')

            # 如果备份目录不存在，返回空列表
            if not os.path.exists(backup_dir):
                return []

            # 查找所有备份文件
            backups = []
            pattern = f"{db_name}_*.db"

            for filename in os.listdir(backup_dir):
                if filename.startswith(db_name + "_") and filename.endswith('.db'):
                    filepath = os.path.join(backup_dir, filename)
                    # 提取时间戳
                    timestamp_part = filename[len(db_name)+1:-3]  # 去掉前缀和.db
                    try:
                        # 尝试解析时间戳
                        timestamp = datetime.strptime(timestamp_part, '%Y%m%d_%H%M%S')
                        backups.append({
                            'path': filepath,
                            'filename': filename,
                            'timestamp': timestamp,
                            'size': os.path.getsize(filepath)
                        })
                    except ValueError:
                        # 如果时间戳格式不对，仍然保留但排在后面
                        backups.append({
                            'path': filepath,
                            'filename': filename,
                            'timestamp': None,
                            'size': os.path.getsize(filepath)
                        })

            # 按时间戳排序，有时间戳的在前，时间戳越新越前
            backups.sort(key=lambda x: (x['timestamp'] is None, x['timestamp']), reverse=True)

            return backups

        except Exception as e:
            print(f"❌ 列出备份失败: {e}")
            return []

    def restore_database(self, backup_dir=None, backup_file=None):
        """
        [功能 9] 恢复数据库
        从备份文件恢复数据库
        """
        try:
            # 获取数据库文件路径
            db_abs_path = os.path.abspath(self.db_path)

            # 确定备份目录
            if backup_dir is None:
                db_dir = os.path.dirname(db_abs_path)
                backup_dir = os.path.join(db_dir, 'bak')

            # 如果没有指定备份文件，选择最新的
            if backup_file is None:
                backups = self.list_backups(backup_dir)
                if not backups:
                    print("❌ 没有找到可用的备份文件")
                    return False

                backup_file = backups[0]['path']
                print(f"📋 自动选择最新备份: {os.path.basename(backup_file)}")
            else:
                # 如果是文件名，拼接完整路径
                if not os.path.isabs(backup_file):
                    backup_file = os.path.join(backup_dir, backup_file)

                if not os.path.exists(backup_file):
                    print(f"❌ 备份文件不存在: {backup_file}")
                    return False

            # 关闭当前数据库连接
            if self.conn:
                self.conn.close()
                self.conn = None

            # 执行恢复
            shutil.copy2(backup_file, db_abs_path)

            # 重新建立数据库连接
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()

            print(f"✅ 数据库已从备份恢复: {backup_file}")

            # 验证恢复后的数据库
            try:
                self.cursor.execute("SELECT COUNT(*) FROM files")
                count = self.cursor.fetchone()[0]
                print(f"📊 恢复完成，数据库中共有 {count} 条记录")
            except:
                print("⚠️ 警告：恢复后的数据库可能没有文件表，请先运行 sync 命令")

            return True

        except Exception as e:
            print(f"❌ 恢复失败: {e}")
            # 尝试重新建立连接
            try:
                if not self.conn:
                    self.conn = sqlite3.connect(self.db_path)
                    self.conn.row_factory = sqlite3.Row
                    self.cursor = self.conn.cursor()
            except:
                pass
            return False

    def export_to_csv(self, output_path=None, table_name='files'):
        """
        [功能 10] 导出数据库到CSV文件
        支持指定表名导出，兼容Excel打开

        Args:
            output_path: 输出文件路径（默认: ../docs/mods_metadata.csv）
            table_name: 要导出的表名（默认: files）
        """
        import csv
        import os

        try:
            # 参数处理和验证
            if output_path is None:
                output_path = '../docs/mods_metadata.csv'

            # 检查表是否存在
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in self.cursor.fetchall()]
            if table_name not in tables:
                print(f"❌ 表 '{table_name}' 不存在")
                print(f"可用表: {', '.join(tables)}")
                return False

            # 确保输出目录存在
            output_dir = os.path.dirname(os.path.abspath(output_path))
            os.makedirs(output_dir, exist_ok=True)

            # 获取表的字段信息
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = self.cursor.fetchall()

            # 构建查询语句 - 针对files表的特殊处理
            if table_name == 'files':
                query = """
                SELECT COALESCE(modname, '') as modname,
                       filename,
                       COALESCE(env, '') as env,
                       COALESCE(tags, '') as tags,
                       COALESCE(description, '') as description
                FROM files
                ORDER BY
                    CASE
                        WHEN modname IS NULL OR modname = '' THEN 2
                        ELSE 1
                    END,
                    modname,
                    filename
                """
                headers = ['模组名', '文件名', '环境', '标签', '描述']
            else:
                # 通用表处理
                column_names = [col[1] for col in columns]
                headers = column_names
                query = f"SELECT * FROM {table_name}"

            # 执行查询
            self.cursor.execute(query)
            rows = self.cursor.fetchall()

            if not rows:
                print(f"❌ 表 '{table_name}' 中没有记录可导出")
                return False

            # 写入CSV（UTF-8 BOM编码）
            with open(output_path, 'w', encoding='utf-8-sig', newline='') as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)

                # 写入标题行
                writer.writerow(headers)

                # 写入数据行
                for row in rows:
                    # 转换数据
                    if table_name == 'files':
                        # files表的特殊处理
                        modname = row[0] if row[0] else ''
                        filename = row[1] if row[1] else ''
                        env = row[2] if row[2] else ''
                        tags = row[3] if row[3] else ''
                        description = row[4] if row[4] else ''

                        # 处理包含逗号的字段 - 使用双引号包围
                        data_row = [modname, filename, env, tags, description]
                        formatted_row = []

                        for value in data_row:
                            # 先转换为字符串再检查
                            value_str = str(value)
                            if value and (',' in value_str or '"' in value_str or '\n' in value_str):
                                # 转义双引号并移除换行符
                                value_str = value_str.replace('"', '""').replace('\n', ' ').replace('\r', '')
                                formatted_row.append(f'"{value_str}"')
                            else:
                                formatted_row.append(value_str)

                        writer.writerow(formatted_row)
                    else:
                        # 通用表处理
                        data_row = list(row)
                        formatted_row = []

                        for value in data_row:
                            if value and (',' in str(value) or '"' in str(value) or '\n' in str(value)):
                                value = str(value).replace('"', '""').replace('\n', ' ').replace('\r', '')
                                formatted_row.append(f'"{value}"')
                            else:
                                formatted_row.append(value if value is not None else '')

                        writer.writerow(formatted_row)

            print(f"✅ 已导出表 '{table_name}' 到: {output_path}")
            print(f"📊 导出记录数: {len(rows)}")

            return True

        except PermissionError:
            print(f"❌ 权限错误: 无法写入文件 {output_path}")
            return False
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def show_by_sha(self, sha_prefix):
        """
        [功能 11] 根据SHA前缀显示完整信息
        sha_prefix: SHA前缀（至少12位）
        """
        try:
            # 验证SHA长度
            if len(sha_prefix) < 12:
                print("❌ SHA前缀长度不足，请提供至少12位SHA")
                return

            # 查询匹配的记录
            self.cursor.execute("SELECT * FROM files WHERE sha LIKE ?", (sha_prefix + '%',))
            rows = self.cursor.fetchall()

            if len(rows) == 0:
                print(f"❌ 没有找到SHA以 '{sha_prefix}' 开头的记录")
                return

            # 获取所有字段名
            self.cursor.execute("PRAGMA table_info(files)")
            columns = self.cursor.fetchall()
            col_names = [col[1] for col in columns]

            # 显示结果
            print(f"\n🔍 找到 {len(rows)} 个匹配项:")
            print(f"{'='*80}")

            for i, row in enumerate(rows, 1):
                filename = row['filename']
                print(f"\n{i}. 【{filename}】")
                print(f"   SHA: {row['sha']}")

                # 显示其他字段（排除 sha 和 filename，因为已经显示了）
                for col in col_names:
                    if col not in ['sha', 'filename']:
                        value = row[col]
                        if value is not None and value != '':
                            print(f"   {col}: {value}")

            print(f"\n{'='*80}")
            print(f"总计: {len(rows)} 个匹配项")

        except Exception as e:
            print(f"❌ 查询失败: {e}")

# ================= 命令行接口逻辑 =================
def main():
    parser = argparse.ArgumentParser(
        description="本地文件资产管理脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
命令分组:
  数据同步    sync            同步文件夹内容到数据库

  字段管理    add_field       添加新的信息字段
              delete_field    删除指定的字段
              rename_field    重命名指定的字段
              info            查看当前所有字段

  数据编辑    update          更新单个文件的字段
              batch_write     批量写入字段

  数据查询    search          搜索数据库中的项
              show            根据SHA前缀显示完整信息

  数据维护    check           检查某字段缺失的项
              backup          数据库备份和恢复
              export          导出数据库到CSV文件
        """)
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # ========== 数据同步 ==========
    parser_sync = subparsers.add_parser('sync', help='同步文件夹内容到数据库')
    parser_sync.add_argument('--folder', type=str, default=DEFAULT_FOLDER, help='指定扫描文件夹路径')
    parser_sync.add_argument('--force', action='store_true', help='自动确认删除数据库中缺失文件的记录，无需用户确认')

    # ========== 字段管理 ==========
    parser_add = subparsers.add_parser('add_field', help='添加新的信息字段')
    parser_add.add_argument('name', type=str, help='字段名称 (英文)')
    parser_add.add_argument('--type', type=str, default='TEXT', help='字段类型 (TEXT, INTEGER, REAL)')

    parser_del = subparsers.add_parser('delete_field', help='删除指定的字段')
    parser_del.add_argument('name', type=str, help='要删除的字段名')

    parser_rename = subparsers.add_parser('rename_field', help='重命名指定的字段')
    parser_rename.add_argument('old_name', type=str, help='原字段名')
    parser_rename.add_argument('new_name', type=str, help='新字段名')

    subparsers.add_parser('info', help='查看当前所有字段')

    # ========== 数据编辑 ==========
    parser_upd = subparsers.add_parser('update', help='更新单个文件的字段')
    parser_upd.add_argument('sha', type=str, help='文件 SHA 前几位')
    parser_upd.add_argument('field', type=str, help='字段名')
    parser_upd.add_argument('value', type=str, help='值')

    parser_batch = subparsers.add_parser('batch_write', help='批量写入字段')
    parser_batch.add_argument('field', type=str, help='字段名')
    parser_batch.add_argument('value', type=str, help='值')
    parser_batch.add_argument('--where', type=str, default=None, help='SQL WHERE 条件 (可选，例如 "author IS NULL")')

    # ========== 数据查询 ==========
    parser_search = subparsers.add_parser('search', help='搜索数据库中的项')
    parser_search.add_argument('field', type=str, help='要搜索的字段名')
    parser_search.add_argument('target', type=str, help='搜索目标值')
    parser_search.add_argument('-r', '--regex', action='store_true', help='使用正则表达式模式')

    parser_show = subparsers.add_parser('show', help='根据SHA前缀显示完整信息')
    parser_show.add_argument('sha', type=str, help='SHA前缀（至少12位）')

    # ========== 数据维护 ==========
    parser_miss = subparsers.add_parser('check', help='检查某字段缺失的项')
    parser_miss.add_argument('field', type=str, help='要检查的字段名')

    parser_backup = subparsers.add_parser('backup', help='数据库备份和恢复')
    backup_group = parser_backup.add_mutually_exclusive_group(required=True)
    backup_group.add_argument('-s', '--save', action='store_true', help='保存数据库备份')
    backup_group.add_argument('-l', '--load', action='store_true', help='从备份恢复数据库')
    parser_backup.add_argument('-d', '--dir', type=str, default=None, help='自定义备份目录路径')

    parser_export = subparsers.add_parser('export', help='导出数据库到CSV文件')
    parser_export.add_argument('-d', '--dir', type=str,
                             default='../docs/mods_metadata.csv',
                             help='指定导出路径（默认: docs/mods_metadata.csv）')
    parser_export.add_argument('-t', '--table', type=str, default='files',
                             help='指定要导出的表名（默认: files）')

    args = parser.parse_args()

    # 初始化管理器
    manager = AssetManager(DB_NAME, args.folder if hasattr(args, 'folder') else DEFAULT_FOLDER)

    if args.command == 'sync':
        manager.sync_folder(auto_confirm=args.force)
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
    elif args.command == 'search':
        manager.search_items(args.field, args.target, args.regex)
    elif args.command == 'backup':
        if args.save:
            # 备份数据库
            backup_path = manager.backup_database(args.dir)
            if backup_path:
                # 显示备份列表
                backups = manager.list_backups(args.dir)
                if backups:
                    print("\n📋 所有备份文件:")
                    for i, backup in enumerate(backups[:10], 1):  # 只显示前10个
                        timestamp_str = backup['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if backup['timestamp'] else "未知时间"
                        size_str = f"{backup['size']/1024:.1f} KB" if backup['size'] < 1024*1024 else f"{backup['size']/1024/1024:.1f} MB"
                        print(f"  {i}. {backup['filename']} - {timestamp_str} ({size_str})")
                    if len(backups) > 10:
                        print(f"  ... 还有 {len(backups)-10} 个备份")
        elif args.load:
            # 恢复数据库
            success = manager.restore_database(args.dir)
            if not success:
                print("❌ 恢复失败")
                sys.exit(1)
    elif args.command == 'export':
        manager.export_to_csv(
            output_path=args.dir,
            table_name=args.table
        )
    elif args.command == 'show':
        manager.show_by_sha(args.sha)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()