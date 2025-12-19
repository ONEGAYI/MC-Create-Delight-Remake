#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch_update_manager.py
批量更新数据库中的模组信息

功能：
1. 从 updated_info.csv 读取更新数据
2. 通过 SHA 前缀匹配数据库记录
3. 批量调用 update_single_item 方法更新字段
4. 提供详细的进度显示和错误报告
"""

import sys
import os
import csv
import argparse
import shutil
from datetime import datetime
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout

# 添加脚本目录到 Python 路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# 导入现有的 AssetManager
from mods_manager import AssetManager


class BatchUpdateManager:
    def __init__(self, db_path, csv_path):
        self.db_path = db_path
        self.csv_path = csv_path
        self.manager = None

        # 统计信息
        self.stats = {
            'total_records': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'not_found': 0,
            'invalid_fields': 0,
            'skipped': 0,
            'skipped_fields': 0  # 跳过的字段数
        }

        # 错误记录
        self.error_records = []

        # 可更新的字段（sha 和 filename 仅用于识别，不更新）
        self.updatable_fields = {'env', 'tags', 'description', 'updated_at'}

        # 特殊占位符
        self.skip_placeholder = '<safely-jump>'

    def initialize(self):
        """初始化管理器"""
        try:
            # 创建 AssetManager 实例（使用 dummy folder_path）
            self.manager = AssetManager(self.db_path, "__dummy__")
            print(f"✓ 成功初始化 AssetManager")
            return True
        except Exception as e:
            print(f"✗ 初始化失败: {e}")
            return False

    def read_csv_data(self):
        """读取 CSV 数据"""
        csv_data = []

        try:
            with open(self.csv_path, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)

                # 验证必要的列
                required_columns = ['sha', 'filename', 'env', 'tags', 'description']
                if not all(col in reader.fieldnames for col in required_columns):
                    missing = [col for col in required_columns if col not in reader.fieldnames]
                    print(f"✗ CSV 文件缺少必要的列: {missing}")
                    print(f"现有列: {reader.fieldnames}")
                    return None

                for row_num, row in enumerate(reader, 2):  # +2 因为有表头行
                    # 跳过空行或只有 SHA 的行
                    sha = row.get('sha', '').strip()
                    if not sha:
                        self.stats['skipped'] += 1
                        self.error_records.append({
                            'type': 'missing_sha',
                            'row': row_num,
                            'filename': row.get('filename', 'N/A'),
                            'reason': 'SHA 值为空'
                        })
                        continue

                    # 清理数据
                    updated_at = row.get('updated_at', '').strip()
                    # 如果 updated_at 为空，则自动填充当前时间戳
                    if not updated_at:
                        updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    cleaned_row = {
                        'sha': sha,
                        'updated_at': updated_at,
                        'filename': row.get('filename', '').strip(),
                        'env': row.get('env', '').strip(),
                        'tags': row.get('tags', '').strip(),
                        'description': row.get('description', '').strip()
                    }

                    csv_data.append(cleaned_row)

            print(f"✓ 成功读取 CSV，共 {len(csv_data)} 条记录")
            return csv_data

        except FileNotFoundError:
            print(f"✗ CSV 文件不存在: {self.csv_path}")
            return None
        except Exception as e:
            print(f"✗ 读取 CSV 失败: {e}")
            return None

    def backup_database(self):
        """备份数据库"""
        try:
            # 使用 AssetManager 的备份功能
            backup_dir = Path(self.db_path).parent / 'backups'
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"mods_metadata_backup_{timestamp}.db"
            backup_path = backup_dir / backup_name

            # 复制数据库文件
            shutil.copy2(self.db_path, backup_path)

            print(f"✓ 数据库已备份到: {backup_path}")
            return backup_path

        except Exception as e:
            print(f"⚠ 备份数据库失败: {e}")
            return None

    def batch_update(self, csv_data, dry_run=False):
        """执行批量更新"""
        self.stats['total_records'] = len(csv_data)

        print(f"\n{'[DRY RUN] ' if dry_run else ''}开始批量更新...")
        print("-" * 80)

        for i, record in enumerate(csv_data, 1):
            # 显示进度
            progress = f"\r[{i:3d}/{self.stats['total_records']:3d}]"
            filename = record.get('filename', 'Unknown')[:40]
            print(f"{progress} 正在处理: {filename:<40}", end='', flush=True)

            # 检查 SHA
            sha_prefix = record['sha']
            if not sha_prefix:
                self.stats['skipped'] += 1
                continue

            # 获取需要更新的字段
            updates = {}
            for field in self.updatable_fields:
                value = record.get(field, '').strip()
                if value == self.skip_placeholder:
                    # 跳过该字段
                    self.stats['skipped_fields'] += 1
                    continue
                elif value != '':
                    # 非空字段，需要更新
                    updates[field] = value
                else:
                    # 空字符串，也要更新（用户选择）
                    updates[field] = ''

            if not updates:
                self.stats['skipped'] += 1
                continue

            # 执行更新
            success = True
            updated_fields = []

            for field, value in updates.items():
                if dry_run:
                    # 干运行模式，只打印不执行
                    if not any(err['field'] == field and err['sha_prefix'] == sha_prefix
                             for err in self.error_records if err.get('type') == 'dry_run'):
                        print(f"\n[DRY RUN] 将更新 {sha_prefix[:12]}... 的 {field} = {value[:30] if len(str(value)) > 30 else value}")
                        self.error_records.append({
                            'type': 'dry_run',
                            'sha_prefix': sha_prefix,
                            'filename': record.get('filename', 'N/A'),
                            'field': field,
                            'value': str(value)[:50]
                        })
                else:
                    # 调用 AssetManager 的 update_single_item 方法
                    try:
                        # 临时重定向输出以捕获结果
                        f = StringIO()
                        with redirect_stdout(f):
                            self.manager.update_single_item(sha_prefix, field, value)

                        output = f.getvalue()
                        if "✅" in output:
                            # 更新成功
                            updated_fields.append(field)
                        elif "找不到对应的 SHA" in output or "SHA 前缀不唯一" in output:
                            self.stats['not_found'] += 1
                            self.error_records.append({
                                'type': 'sha_not_found',
                                'sha_prefix': sha_prefix,
                                'filename': record.get('filename', 'N/A'),
                                'field': field,
                                'error': output.strip()
                            })
                            success = False
                            break
                        else:
                            # 其他错误
                            self.stats['failed_updates'] += 1
                            self.error_records.append({
                                'type': 'update_error',
                                'sha_prefix': sha_prefix,
                                'filename': record.get('filename', 'N/A'),
                                'field': field,
                                'error': output.strip()
                            })
                            success = False
                            break

                    except Exception as e:
                        self.stats['failed_updates'] += 1
                        self.error_records.append({
                            'type': 'exception',
                            'sha_prefix': sha_prefix,
                            'filename': record.get('filename', 'N/A'),
                            'field': field,
                            'error': str(e)
                        })
                        success = False
                        break

            if success and not dry_run and updated_fields:
                self.stats['successful_updates'] += 1
            elif not success and not dry_run:
                pass  # 错误已在上面记录

        print("\n" + "-" * 80)

    def generate_report(self):
        """生成更新报告"""
        print("\n" + "=" * 80)
        print("批量更新统计报告")
        print("=" * 80)
        print(f"总记录数:          {self.stats['total_records']}")
        print(f"成功更新:          {self.stats['successful_updates']}")
        print(f"SHA 未找到:        {self.stats['not_found']}")
        print(f"更新失败:          {self.stats['failed_updates']}")
        print(f"跳过记录:          {self.stats['skipped']}")
        print(f"跳过字段数:        {self.stats['skipped_fields']}")

        if self.stats['total_records'] > 0:
            success_rate = self.stats['successful_updates'] / self.stats['total_records'] * 100
            print(f"成功率:            {success_rate:.1f}%")

        # 显示错误详情
        if self.error_records:
            print("\n" + "-" * 80)
            print("错误记录详情")
            print("-" * 80)

            # 过滤掉干运行记录
            error_records_filtered = [e for e in self.error_records if e.get('type') != 'dry_run']

            if not error_records_filtered:
                print("无错误记录")
            else:
                # 按错误类型分组
                error_types = {}
                for error in error_records_filtered:
                    error_type = error['type']
                    if error_type not in error_types:
                        error_types[error_type] = []
                    error_types[error_type].append(error)

                # 显示每种错误的前几条
                for error_type, errors in error_types.items():
                    print(f"\n[{error_type}] ({len(errors)}个):")
                    for error in errors[:5]:
                        if error_type == 'sha_not_found':
                            print(f"  SHA {error['sha_prefix'][:12]}... 未找到 (文件: {error['filename']})")
                        elif error_type == 'update_error':
                            print(f"  {error['filename']}: {error['error'][:80]}...")
                        elif error_type == 'exception':
                            print(f"  {error['filename']}: {error['error'][:80]}...")
                        else:
                            print(f"  {error}")

                    if len(errors) > 5:
                        print(f"  ... 还有 {len(errors) - 5} 个未显示")

    def save_error_records(self):
        """保存错误记录到文件"""
        if not self.error_records:
            return

        # 过滤掉干运行记录
        error_records_filtered = [e for e in self.error_records if e.get('type') != 'dry_run']

        if not error_records_filtered:
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        error_log_path = Path(script_dir) / f'batch_update_errors_{timestamp}.log'

        try:
            with open(error_log_path, 'w', encoding='utf-8') as f:
                f.write(f"批量更新错误日志 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")

                for error in error_records_filtered:
                    f.write(f"类型: {error['type']}\n")
                    f.write(f"文件名: {error.get('filename', 'N/A')}\n")
                    if 'sha_prefix' in error:
                        f.write(f"SHA: {error['sha_prefix']}\n")
                    if 'field' in error:
                        f.write(f"字段: {error['field']}\n")
                    if 'error' in error:
                        f.write(f"错误: {error['error']}\n")
                    if 'reason' in error:
                        f.write(f"原因: {error['reason']}\n")
                    if 'row' in error:
                        f.write(f"行号: {error['row']}\n")
                    f.write("-" * 40 + "\n")

            print(f"\n✓ 错误记录已保存到: {error_log_path}")

        except Exception as e:
            print(f"\n⚠ 保存错误记录失败: {e}")

    def show_preview(self, csv_data):
        """显示预览数据"""
        print("\n数据预览:")
        print("-" * 80)
        print(f"{'SHA':<12} {'文件名':<40} {'环境':<10} {'标签':<20}")
        print("-" * 80)

        for record in csv_data[:5]:
            sha = record['sha'][:12] + "..." if len(record['sha']) > 12 else record['sha']
            filename = record['filename'][:37] + "..." if len(record['filename']) > 40 else record['filename']
            env = record['env'][:7] + "..." if len(record['env']) > 10 else record['env']
            tags = record['tags'][:17] + "..." if len(record['tags']) > 20 else record['tags']
            print(f"{sha:<12} {filename:<40} {env:<10} {tags:<20}")

        if len(csv_data) > 5:
            print(f"... 还有 {len(csv_data) - 5} 条记录")

        print("-" * 80)

    def run(self, dry_run=False, force=False, no_backup=False):
        """执行批量更新流程"""
        print("=" * 80)
        print("批量更新模组数据库工具")
        print("=" * 80)

        # 检查文件
        if not os.path.exists(self.db_path):
            print(f"✗ 数据库文件不存在: {self.db_path}")
            return False

        if not os.path.exists(self.csv_path):
            print(f"✗ CSV 文件不存在: {self.csv_path}")
            return False

        # 初始化
        if not self.initialize():
            return False

        # 读取 CSV 数据
        print("\n正在读取 CSV 文件...")
        csv_data = self.read_csv_data()
        if not csv_data:
            print("✗ 无法读取 CSV 数据或 CSV 文件为空")
            return False

        # 显示预览
        self.show_preview(csv_data)

        # 确认执行
        if not dry_run and not force:
            print(f"\n准备更新 {len(csv_data)} 条记录")
            confirm = input("确认执行吗? (输入 'yes' 确认): ")
            if confirm.lower() != 'yes':
                print("🚫 操作取消")
                return False

        # 备份数据库
        if not dry_run and not no_backup:
            print("\n正在备份数据库...")
            self.backup_database()

        # 执行批量更新
        self.batch_update(csv_data, dry_run)

        # 生成报告
        self.generate_report()

        # 保存错误记录
        if self.error_records:
            self.save_error_records()

        return True


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='批量更新模组数据库信息',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                          # 使用默认路径，交互式执行
  %(prog)s --dry-run                # 干运行，查看将要更新的内容
  %(prog)s --force                  # 跳过确认直接执行
  %(prog)s --csv custom.csv         # 指定自定义 CSV 文件
  %(prog)s --db custom.db           # 指定自定义数据库文件
        """
    )

    parser.add_argument(
        '--csv',
        default='../.claude/skills/search-mods-info/configs/updated_info.csv',
        help='CSV 文件路径 (默认: ../.claude/skills/search-mods-info/configs/updated_info.csv)'
    )

    parser.add_argument(
        '--db',
        default='../docs/mods_metadata.db',
        help='数据库文件路径 (默认: ../docs/mods_metadata.db)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='干运行模式，只显示将要执行的操作，不实际更新数据库'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='跳过确认提示，直接执行'
    )

    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='跳过数据库备份（不推荐）'
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()

    # 创建批量更新管理器
    manager = BatchUpdateManager(
        db_path=os.path.normpath(os.path.join(script_dir, args.db)),
        csv_path=os.path.normpath(os.path.join(script_dir, args.csv))
    )

    # 执行批量更新
    success = manager.run(
        dry_run=args.dry_run,
        force=args.force,
        no_backup=args.no_backup
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()