#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_from_modlist.py
从CSV文件更新数据库中的模组信息

功能：
1. 从 ../docs/mods-list.csv 读取数据
2. 通过文件名匹配数据库记录
3. 更新 number, env, tags, description 字段
4. 提供详细的更新统计报告
"""

import sqlite3
import csv
import os
import sys
import re
from datetime import datetime
from pathlib import Path

# 配置
script_dir = Path(__file__).parent
DB_PATH = script_dir / '../docs/mods_metadata.db'
CSV_PATH = script_dir / '../docs/mods-list.csv'
BACKUP_PATH = script_dir / '../docs/mods_metadata_backup_{timestamp}.db'

class ModListUpdater:
    def __init__(self, db_path, csv_path):
        self.db_path = db_path
        self.csv_path = csv_path
        self.conn = None
        self.cursor = None

        # 统计信息
        self.stats = {
            'total_records': 0,
            'updated': 0,
            'not_found': 0,
            'errors': 0,
            'skipped': 0
        }

        # 错误记录
        self.error_records = []

    def connect_database(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            print(f"✓ 成功连接数据库: {self.db_path}")
            return True
        except Exception as e:
            print(f"✗ 连接数据库失败: {e}")
            return False

    def check_database_structure(self):
        """检查数据库表结构"""
        try:
            # 检查是否存在files表
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
            if not self.cursor.fetchone():
                print("✗ 未找到files表，请先运行mods_manager.py创建数据库")
                return False

            # 获取表结构
            self.cursor.execute("PRAGMA table_info(files)")
            columns = {row['name'] for row in self.cursor.fetchall()}

            # 检查必要的字段
            required_fields = {'filename', 'sha'}
            optional_fields = {'number', 'env', 'tags', 'description'}

            missing_required = required_fields - columns
            if missing_required:
                print(f"✗ 缺少必要字段: {missing_required}")
                return False

            # 添加缺失的可选字段
            missing_optional = optional_fields - columns
            for field in missing_optional:
                try:
                    self.cursor.execute(f"ALTER TABLE files ADD COLUMN {field} TEXT")
                    print(f"✓ 添加字段: {field}")
                except sqlite3.OperationalError:
                    pass  # 字段可能已存在

            self.conn.commit()
            return True

        except Exception as e:
            print(f"✗ 检查数据库结构失败: {e}")
            return False

    def read_csv_data(self):
        """读取CSV数据"""
        csv_data = []

        try:
            # 尝试不同的编码
            encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']

            for encoding in encodings:
                try:
                    with open(self.csv_path, 'r', encoding=encoding, newline='') as f:
                        # 读取所有行
                        lines = f.readlines()

                        # 查找表头行
                        header_idx = -1
                        for i, line in enumerate(lines):
                            if '编号' in line and '名称' in line and '环境' in line:
                                header_idx = i
                                break

                        if header_idx == -1:
                            print("✗ 未找到表头行")
                            continue

                        # 使用csv模块处理，指定quoting参数
                        f.seek(0)
                        reader = csv.reader(f, quoting=csv.QUOTE_MINIMAL)

                        # 跳过到表头
                        for _ in range(header_idx):
                            next(reader, None)

                        # 读取表头（但不使用）
                        header = next(reader, None)
                        if not header or len(header) < 5:
                            print("✗ 表头格式不正确")
                            continue

                        # 读取数据行
                        for row in reader:
                            # 跳过空行
                            if not row or not any(row):
                                continue

                            # 确保至少有5列
                            while len(row) < 5:
                                row.append('')

                            # 提取数据
                            if row[0].strip():  # 确保第一列（编号）不为空
                                try:
                                    number_str = row[0].strip()
                                    if number_str.isdigit():
                                        number = int(number_str)
                                    else:
                                        continue  # 跳过编号不是数字的行

                                    name = row[1].strip()

                                    # 处理可能包含逗号的字段
                                    # 环境、标签、描述可能包含逗号，需要小心处理
                                    if len(row) == 5:
                                        # 标准5列格式
                                        env = row[2].strip()
                                        tags = row[3].strip()
                                        description = row[4].strip()
                                    elif len(row) > 5:
                                        # 可能是标签包含逗号导致的多列
                                        env = row[2].strip()
                                        # 将第3列到倒数第二列合并为tags
                                        tags = ','.join(row[3:-1]).strip()
                                        description = row[-1].strip()
                                    else:
                                        continue

                                    # 清理标签中的引号
                                    tags = tags.replace('"', '').replace("'", "")
                                    # 标准化逗号后的空格
                                    tags = ','.join([tag.strip() for tag in tags.split(',')])

                                    if name:  # 确保有名称
                                        csv_data.append({
                                            'number': number,
                                            'name': name,
                                            'filename': name + '.jar',
                                            'env': env,
                                            'tags': tags,
                                            'description': description
                                        })
                                except (ValueError, IndexError) as e:
                                    # 只在调试模式下显示详细错误
                                    # print(f"⚠ 跳过无效行: {row[:2]} - {e}")
                                    continue

                    if csv_data:
                        print(f"✓ 成功读取CSV文件（编码: {encoding}），共{len(csv_data)}条记录")
                        return csv_data
                    else:
                        print(f"✗ 使用{encoding}编码未能读取到有效数据")
                        continue

                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"使用{encoding}编码读取时出错: {e}")
                    continue

            print(f"✗ 无法使用任何编码读取CSV文件")
            return None

        except Exception as e:
            print(f"✗ 读取CSV文件失败: {e}")
            return None

    def update_database(self, csv_data):
        """更新数据库记录"""
        print("\n开始更新数据库...")
        print("-" * 60)

        self.stats['total_records'] = len(csv_data)

        for i, record in enumerate(csv_data, 1):
            try:
                # 显示进度
                print(f"\r[{i:3d}/{self.stats['total_records']:3d}] 正在处理: {record['name'][:50]:<50}",
                      end='', flush=True)

                # 查找匹配的记录
                self.cursor.execute(
                    "SELECT rowid, * FROM files WHERE filename = ?",
                    (record['filename'],)
                )

                db_record = self.cursor.fetchone()

                if db_record:
                    # 更新记录
                    self.cursor.execute("""
                        UPDATE files
                        SET number = ?, env = ?, tags = ?, description = ?
                        WHERE rowid = ?
                    """, (
                        record['number'],
                        record['env'],
                        record['tags'],
                        record['description'],
                        db_record['rowid']
                    ))

                    self.stats['updated'] += 1
                else:
                    # 记录未找到的文件
                    self.stats['not_found'] += 1
                    self.error_records.append({
                        'type': 'not_found',
                        'filename': record['filename'],
                        'name': record['name'],
                        'number': record['number']
                    })

            except Exception as e:
                self.stats['errors'] += 1
                self.error_records.append({
                    'type': 'error',
                    'filename': record.get('filename', 'N/A'),
                    'name': record.get('name', 'N/A'),
                    'error': str(e)
                })

        print("\n" + "-" * 60)

        # 提交事务
        try:
            self.conn.commit()
            print("✓ 数据库更新已提交")
        except Exception as e:
            print(f"✗ 提交失败: {e}")
            self.conn.rollback()
            return False

        return True

    def generate_report(self):
        """生成更新报告"""
        print("\n" + "=" * 60)
        print("更新统计报告")
        print("=" * 60)
        print(f"总记录数:      {self.stats['total_records']}")
        print(f"成功更新:      {self.stats['updated']}")
        print(f"未找到匹配:    {self.stats['not_found']}")
        print(f"更新错误:      {self.stats['errors']}")
        print(f"成功率:        {self.stats['updated']/self.stats['total_records']*100:.1f}%")

        # 显示未找到的文件
        if self.error_records:
            print("\n" + "-" * 60)
            print("问题记录详情")
            print("-" * 60)

            not_found = [r for r in self.error_records if r['type'] == 'not_found']
            errors = [r for r in self.error_records if r['type'] == 'error']

            if not_found:
                print(f"\n[未找到的文件] ({len(not_found)}个):")
                for record in not_found[:10]:  # 只显示前10个
                    print(f"  #{record['number']:3d} {record['filename']}")
                if len(not_found) > 10:
                    print(f"  ... 还有 {len(not_found)-10} 个未显示")

            if errors:
                print(f"\n[更新错误] ({len(errors)}个):")
                for record in errors[:5]:  # 只显示前5个
                    print(f"  {record['filename']}: {record['error']}")

        # 保存未匹配的记录到文件
        if self.stats['not_found'] > 0:
            not_found_file = '../docs/unmatched_mods.txt'
            try:
                with open(not_found_file, 'w', encoding='utf-8') as f:
                    f.write("# 未匹配的模组文件\n")
                    f.write("# 格式: 编号 | 文件名 | 名称\n")
                    f.write("-" * 80 + "\n")

                    for record in self.error_records:
                        if record['type'] == 'not_found':
                            f.write(f"{record['number']:3d} | {record['filename']:<50} | {record['name']}\n")

                print(f"\n✓ 未匹配的记录已保存到: {not_found_file}")
            except Exception as e:
                print(f"\n✗ 保存未匹配记录失败: {e}")

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def run(self):
        """执行更新流程"""
        print("=" * 60)
        print("模组数据库更新工具")
        print("=" * 60)

        # 检查文件是否存在
        if not os.path.exists(self.db_path):
            print(f"✗ 数据库文件不存在: {self.db_path}")
            print("请先运行 mods_manager.py 扫描mods文件夹创建数据库")
            return False

        if not os.path.exists(self.csv_path):
            print(f"✗ CSV文件不存在: {self.csv_path}")
            return False

        # 连接数据库
        if not self.connect_database():
            return False

        # 检查数据库结构
        print("\n检查数据库结构...")
        if not self.check_database_structure():
            return False

        # 读取CSV数据
        print("\n正在读取CSV文件...")
        csv_data = self.read_csv_data()
        if not csv_data:
            print("✗ 无法读取CSV数据")
            return False

        # 更新数据库
        print("\n开始更新数据库记录...")
        if not self.update_database(csv_data):
            print("✗ 更新失败")
            return False

        # 生成报告
        self.generate_report()

        # 关闭连接
        self.close()

        print("\n✓ 更新完成！")
        return True


def main():
    """主函数"""
    updater = ModListUpdater(DB_PATH, CSV_PATH)

    try:
        success = updater.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ 用户中断操作")
        updater.close()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        updater.close()
        sys.exit(1)


if __name__ == "__main__":
    main()