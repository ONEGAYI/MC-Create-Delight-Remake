#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_modname.py
从模组 JAR 文件中提取模组名称

功能：
1. 读取 JAR 文件内的 pack.mcmeta 获取 description
2. 降级使用文件名规则提取（备用方案）
3. 批量更新 modname 字段
"""

import sys
import os
import re
import shutil
import argparse
import json
import zipfile
from datetime import datetime
from pathlib import Path

# 添加脚本目录到 Python 路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# 导入现有的 AssetManager
from mods_manager import AssetManager


class ModnameExtractor:
    """从JAR文件中提取模组名称"""

    # 加载器标识列表
    LOADERS = ['forge', 'fabric', 'neoforge', 'quilt']

    # 版本号正则模式
    VERSION_PATTERNS = [
        r'^\d+\.\d+',           # 5.2, 1.20.1
        r'^\d+$',                # 纯数字
        r'^mc\d',                # mc1.20.1
        r'^MC\d',                # MC1.20.1 (大写)
        r'^r\d+',                # r5.5.1
        r'^\d+\.\d+\.\d+',       # 1.2.3
    ]

    @staticmethod
    def extract_from_jar(jar_path):
        """
        从 JAR 文件中读取 pack.mcmeta 获取模组名称

        Args:
            jar_path: JAR 文件的完整路径

        Returns:
            str: 模组名称，如果读取失败则返回 None
        """
        # 通用占位符模式列表（正则表达式）
        GENERIC_PATTERNS = [
            r'^examplemod$',           # examplemod
            r'^example\s+mod$',        # example mod
            r'^examplemod\s+resources?$',  # examplemod resources/examplemod resource
            r'^mod\s*resources?$',     # mod resources/mod resource
            r'^mod$',                  # 单独的 mod
            r'^resources$',            # 单独的 resources
            r'^minecraft\s+mod$',      # minecraft mod
        ]

        try:
            with zipfile.ZipFile(jar_path, 'r') as jar:
                # 尝试读取 pack.mcmeta
                if 'pack.mcmeta' in jar.namelist():
                    with jar.open('pack.mcmeta') as mcmeta_file:
                        content = mcmeta_file.read().decode('utf-8')
                        data = json.loads(content)
                        description = data.get('pack', {}).get('description', '')
                        if description:
                            # 处理 JSON 文本组件格式 {'text': 'xxx'}
                            if isinstance(description, dict):
                                description = description.get('text', str(description))

                            # 跳过包含占位符的描述
                            if '${' in description:
                                return None

                            # **在清理后缀之前先检查占位符模式**
                            desc_lower = description.lower().strip()
                            for pattern in GENERIC_PATTERNS:
                                if re.match(pattern, desc_lower):
                                    return None  # 匹配到占位符，返回 None

                            # 清理常见的后缀
                            # 移除 " resources", " Resources" 等后缀
                            description = re.sub(r'\s+[Rr]esources?$', '', description)
                            description = re.sub(r'\s+[Mm]od\s+[Rr]esources?$', '', description)

                            # 再次检查清理后是否是占位符
                            desc_cleaned = description.lower().strip()
                            for pattern in GENERIC_PATTERNS:
                                if re.match(pattern, desc_cleaned):
                                    return None

                            # 如果清理后为空或太短，返回 None
                            if len(description.strip()) < 2:
                                return None

                            return description.strip()
        except Exception as e:
            pass  # 静默失败，返回 None
        return None

    @staticmethod
    def extract_from_filename(filename):
        """
        从 filename 中提取模组名称（降级方案）

        Args:
            filename: 模组文件名，如 "supplementaries-1.20-3.1.37.jar"

        Returns:
            str: 提取的模组名称，如 "supplementaries"
        """
        # 移除 .jar 后缀
        name = filename.replace('.jar', '')

        # 先处理下划线分隔的文件（如 drippyloadingscreen_forge_3.0.12_MC_1.20.1.jar）
        if '_' in name:
            # 尝试将下划线转换为连字符后处理
            name_underscore = name.replace('_', '-')
            # 如果转换后效果更好（没有纯数字段），则使用转换后的版本
            parts_underscore = name_underscore.split('-')
            has_version = any(any(re.match(p, part) for p in ModnameExtractor.VERSION_PATTERNS)
                            for part in parts_underscore)
            if has_version:
                name = name_underscore

        # 分割
        parts = name.split('-')

        result = []
        for part in parts:
            # 跳过空段
            if not part:
                continue
            # 跳过加载器
            if part.lower() in ModnameExtractor.LOADERS:
                continue
            # 跳过版本号（包括各种格式）
            if any(re.match(pattern, part) for pattern in ModnameExtractor.VERSION_PATTERNS):
                continue
            # 跳过 build.xxx 后缀
            if re.match(r'^build\.\d+$', part):
                continue
            # 跳过 rc/beta/alpha 等后缀带版本号的情况（如 alpha3.0.1）
            if re.match(r'^(rc|beta|alpha|b|a)\d+\.?\d*$', part.lower()):
                continue
            # 跳过 v+数字+a/b 等混合后缀（如 v1a）
            if re.match(r'^v\d+[a-z]?$', part.lower()):
                continue
            # 跳过单独的 v+数字 后缀
            if re.match(r'^v\d+\.?\d*$', part.lower()):
                continue
            # 跳过 hotfix/forge/fabric 等单独段（前面已经处理了加载器）
            if part.lower() in ['hotfix', 'all', 'merged', 'universal']:
                continue
            # 跳过括号内容（如 (1.20.1-forge)）
            if part.startswith('(') and part.endswith(')'):
                continue
            result.append(part)

        modname = '-'.join(result) if result else name

        # 清理末尾可能残留的后缀
        modname = re.sub(r'-?(build|rc|beta|alpha|hotfix|all|merged|universal)\d*\.?\d*$', '', modname, flags=re.IGNORECASE)
        modname = re.sub(r'-?v\d+[a-z]?$', '', modname, flags=re.IGNORECASE)
        modname = re.sub(r'-?v\d+\.?\d*$', '', modname, flags=re.IGNORECASE)
        # 清理 MC 前缀段残留（如 -MC）
        modname = re.sub(r'-?MC$', '', modname)
        modname = re.sub(r'-?mc$', '', modname)
        # 清理 alpha/beta/rc 版本号残留（如 -alpha3.0.1，可能有多个点）
        modname = re.sub(r'-?(alpha|beta|rc|b|a)[\d.]+$', '', modname, flags=re.IGNORECASE)

        return modname

    @staticmethod
    def extract(jar_path, filename):
        """
        提取模组名称（优先从 JAR 读取，降级使用文件名）

        Args:
            jar_path: JAR 文件的完整路径
            filename: 文件名（用于降级方案）

        Returns:
            tuple: (模组名称, 来源) 来源为 'jar' 或 'filename'
        """
        # 首先尝试从 JAR 文件读取
        modname = ModnameExtractor.extract_from_jar(jar_path)
        if modname:
            return modname, 'jar'

        # 降级到文件名提取
        modname = ModnameExtractor.extract_from_filename(filename)
        return modname, 'filename'


class BatchModnameUpdater:
    """批量更新modname字段"""

    def __init__(self, db_path, mods_folder='../mods'):
        self.db_path = db_path
        self.mods_folder = mods_folder
        self.manager = None

        # 统计信息
        self.stats = {
            'total': 0,
            'updated': 0,
            'from_jar': 0,
            'from_filename': 0,
            'failed': 0,
        }

        # 错误记录
        self.errors = []

    def initialize(self):
        """初始化管理器"""
        try:
            self.manager = AssetManager(self.db_path, "__dummy__")
            print(f"✓ 成功初始化 AssetManager")
            return True
        except Exception as e:
            print(f"✗ 初始化失败: {e}")
            return False

    def backup_database(self):
        """备份数据库"""
        try:
            backup_dir = Path(self.db_path).parent / 'backups'
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"mods_metadata_backup_{timestamp}.db"
            backup_path = backup_dir / backup_name

            shutil.copy2(self.db_path, backup_path)
            print(f"✓ 数据库已备份到: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"⚠ 备份数据库失败: {e}")
            return None

    def get_all_records(self):
        """获取所有记录"""
        import sqlite3
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT sha, filename, filepath FROM files")
            records = cursor.fetchall()
            conn.close()
            return records
        except Exception as e:
            print(f"✗ 读取数据库失败: {e}")
            return []

    def update_modname(self, sha, modname):
        """更新单条记录的modname"""
        import sqlite3
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE files SET modname = ? WHERE sha = ?", (modname, sha))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            return False

    def batch_update(self, dry_run=False):
        """执行批量更新"""
        print("\n正在读取数据库...")
        records = self.get_all_records()
        self.stats['total'] = len(records)

        if not records:
            print("✗ 数据库为空或读取失败")
            return False

        print(f"✓ 读取到 {len(records)} 条记录\n")

        print("=" * 80)
        print("开始提取和更新 modname...")
        print("=" * 80)

        for i, (sha, filename, filepath) in enumerate(records, 1):
            progress = f"\r[{i:3d}/{self.stats['total']:3d}]"
            filename_short = filename[:45] + "..." if len(filename) > 45 else filename
            print(f"{progress} {filename_short:<48}", end='', flush=True)

            # 构建完整的 JAR 文件路径
            # filepath 可能是相对路径如 ../mods/xxx.jar
            jar_path = os.path.normpath(os.path.join(script_dir, filepath))

            # 检查文件是否存在
            if not os.path.exists(jar_path):
                # 尝试使用 mods_folder
                jar_path = os.path.normpath(os.path.join(script_dir, self.mods_folder, filename))

            # 提取 modname（优先从 JAR，降级使用文件名）
            modname, source = ModnameExtractor.extract(jar_path, filename)

            # 统计来源
            if source == 'jar':
                self.stats['from_jar'] += 1
            else:
                self.stats['from_filename'] += 1

            if dry_run:
                source_mark = '📦' if source == 'jar' else '📝'
                print(f" => {modname} {source_mark}")
            else:
                # 更新数据库
                if self.update_modname(sha, modname):
                    self.stats['updated'] += 1
                else:
                    self.stats['failed'] += 1
                    self.errors.append({'sha': sha, 'filename': filename, 'modname': modname})

        if not dry_run:
            print("\n" + "=" * 80)

        return True

    def show_preview(self):
        """显示预览示例"""
        print("\n提取预览:")
        print("-" * 80)
        print("📦 = 从 JAR pack.mcmeta 读取")
        print("📝 = 从文件名规则提取")
        print("-" * 80)

        test_cases = [
            # 常规格式
            "AlwaysEat-5.2.jar",
            "supplementaries-1.20-3.1.37.jar",
            "iris_shader_folder-1.1.1-forge.jar",
            "Create-Delight-Core-1.20.1-2.2.0.jar",
            "waystones-forge-1.20.1-14.1.17.jar",
            # 边缘情况
            "rhino-forge-2001.2.3-build.10.jar",
            "drippyloadingscreen_forge_3.0.12_MC_1.20.1.jar",
            "Xaeros_Minimap_25.2.10_Forge_1.20.jar",
            "modernfix-forge-5.24.4+mc1.20.1.jar",
            "kubejs-forge-2001.6.5-build.16.jar",
        ]

        mods_folder = os.path.normpath(os.path.join(script_dir, self.mods_folder))

        for fn in test_cases:
            jar_path = os.path.join(mods_folder, fn)
            if os.path.exists(jar_path):
                modname, source = ModnameExtractor.extract(jar_path, fn)
                source_mark = '📦' if source == 'jar' else '📝'
                # 截断过长的 modname
                modname_str = str(modname) if modname else ''
                display_name = (modname_str[:37] + '...') if len(modname_str) > 40 else modname_str
                print(f"{fn:55} => {display_name:40} {source_mark}")
            else:
                modname = ModnameExtractor.extract_from_filename(fn)
                modname_str = str(modname) if modname else ''
                display_name = (modname_str[:37] + '...') if len(modname_str) > 40 else modname_str
                print(f"{fn:55} => {display_name:40} 📝 (文件不存在)")

        print("-" * 80)

    def generate_report(self, dry_run=False):
        """生成更新报告"""
        print("\n" + "=" * 80)
        print("批量更新统计报告")
        print("=" * 80)
        print(f"总记录数:          {self.stats['total']}")

        if dry_run:
            print(f"预览模式:          是")
            print(f"从 JAR 读取:       {self.stats['from_jar']} 📦")
            print(f"从文件名提取:      {self.stats['from_filename']} 📝")
            print(f"\n💡 使用 --force 参数执行实际更新")
        else:
            print(f"成功更新:          {self.stats['updated']}")
            print(f"从 JAR 读取:       {self.stats['from_jar']} 📦")
            print(f"从文件名提取:      {self.stats['from_filename']} 📝")
            print(f"更新失败:          {self.stats['failed']}")

            if self.stats['total'] > 0:
                success_rate = self.stats['updated'] / self.stats['total'] * 100
                jar_rate = self.stats['from_jar'] / self.stats['total'] * 100
                print(f"成功率:            {success_rate:.1f}%")
                print(f"JAR 读取率:        {jar_rate:.1f}%")

            if self.errors:
                print(f"\n失败记录:")
                for err in self.errors[:10]:
                    print(f"  - {err['filename'][:40]}")

    def run(self, dry_run=False, no_backup=False):
        """执行批量更新流程"""
        print("=" * 80)
        print("批量提取 modname 工具")
        print("=" * 80)

        # 检查文件
        if not os.path.exists(self.db_path):
            print(f"✗ 数据库文件不存在: {self.db_path}")
            return False

        # 初始化
        if not self.initialize():
            return False

        # 显示预览
        self.show_preview()

        # 确认执行
        if not dry_run:
            try:
                confirm = input("\n确认执行吗? (输入 'yes' 确认): ")
            except (EOFError, KeyboardInterrupt):
                print("\n🚫 操作取消")
                return False
            if confirm.lower() != 'yes':
                print("🚫 操作取消")
                return False

            # 备份数据库
            if not no_backup:
                print("\n正在备份数据库...")
                self.backup_database()

        # 执行批量更新
        self.batch_update(dry_run)

        # 生成报告
        self.generate_report(dry_run)

        return True


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='从模组 JAR 文件批量提取 modname 并更新数据库',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                 # 预览并交互式执行
  %(prog)s --dry-run       # 仅预览，不实际更新
  %(prog)s --force         # 跳过确认直接执行
  %(prog)s --no-backup     # 跳过数据库备份
        """
    )

    parser.add_argument(
        '--db',
        default='../docs/mods_metadata.db',
        help='数据库文件路径 (默认: ../docs/mods_metadata.db)'
    )

    parser.add_argument(
        '--mods',
        default='../mods',
        help='模组文件夹路径 (默认: ../mods)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，只显示将要提取的 modname，不实际更新数据库'
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

    updater = BatchModnameUpdater(
        db_path=os.path.normpath(os.path.join(script_dir, args.db)),
        mods_folder=os.path.normpath(os.path.join(script_dir, args.mods))
    )

    success = updater.run(
        dry_run=args.dry_run,
        no_backup=args.no_backup
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
