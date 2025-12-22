import urllib.parse
import os
import hashlib
import json
import boto3
import pathspec
import urllib.request
import urllib.error
import threading
import sys
from botocore.config import Config
from botocore.exceptions import ClientError
from concurrent.futures import ThreadPoolExecutor, as_completed

# === 配置区域 ===
def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Uploader_config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"错误: 配置文件 {config_path} 不存在")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"错误: 配置文件 {config_path} 格式错误: {e}")
        exit(1)

config = load_config()
env_config = config["env"]
R2_ENDPOINT = env_config["R2_ENDPOINT"]
ACCESS_KEY = env_config["ACCESS_KEY"]
SECRET_KEY = env_config["SECRET_KEY"]
BUCKET_NAME = env_config["BUCKET_NAME"]
PUBLIC_URL_BASE = env_config["PUBLIC_URL_BASE"]

MAX_WORKERS = 64
QUICK_COMPARE = True 

MANIFEST_FILENAME = "manifest-update.json"
MANIFEST_URL = f"{PUBLIC_URL_BASE}/{MANIFEST_FILENAME}"

ALWAYS_IGNORE = {
    ".git", ".vscode", ".idea", "__pycache__",
    "manifest.json", MANIFEST_FILENAME,
    "Uploader.py", "Updater.exe", "Updater.py",
    "Uploader_config.json", ".forceupload", ".gitignore"
}
ALWAYS_UPLOAD = {}

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# === 初始化 R2 ===
boto_config = Config(
    max_pool_connections=MAX_WORKERS + 20,
    retries={'max_attempts': 3},
    connect_timeout=15, 
    read_timeout=60
)

s3 = boto3.client('s3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    config=boto_config
)

# === 工具类：进度监控 ===
class ProgressPercentage(object):
    """文件上传进度回调"""
    def __init__(self, filename, filesize):
        self._filename = filename
        self._size = filesize
        self._seen_so_far = 0
        self._lock = threading.Lock()
        self._last_printed_percent = 0

    def __call__(self, bytes_amount):
        # 只有大于 1MB 的文件才显示详细进度，避免小文件刷屏
        if self._size < 1024 * 1024: 
            return

        with self._lock:
            self._seen_so_far += bytes_amount
            if self._size > 0:
                percentage = int((self._seen_so_far / self._size) * 100)
                # 每走 20% 打印一次，或者刚开始时打印
                if percentage - self._last_printed_percent >= 20:
                    self._last_printed_percent = percentage
                    # 使用 print 防止多线程光标混乱
                    print(f"    ... {self._filename} 已上传 {percentage}%")

def format_size(size):
    """格式化文件大小"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f} KB"
    else:
        return f"{size/(1024*1024):.1f} MB"

def load_gitignore(root_dir):
    gitignore_path = os.path.join(root_dir, ".gitignore")
    lines = list(ALWAYS_IGNORE)
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            lines.extend(f.readlines())
    return pathspec.PathSpec.from_lines("gitwildmatch", lines)

def load_force_include(root_dir):
    force_path = os.path.join(root_dir, ".forceupload")
    lines = list(ALWAYS_UPLOAD)
    if os.path.exists(force_path):
        with open(force_path, "r", encoding="utf-8") as f:
            lines.extend(f.readlines())
    return pathspec.PathSpec.from_lines("gitwildmatch", lines)

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def normalize_path(path):
    return path.replace(os.sep, '/')

def get_remote_manifest():
    print(f"正在获取远程清单 ({MANIFEST_FILENAME})...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = urllib.request.Request(MANIFEST_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception:
        print(f"[提示] 无法获取远程清单，视为全量模式。")
        return {}

def fetch_all_remote_files(bucket_name):
    print("正在预扫描云端所有文件列表 (这通常很快)...")
    remote_files = {}
    paginator = s3.get_paginator('list_objects_v2')
    try:
        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' in page:
                for obj in page['Contents']:
                    remote_files[obj['Key']] = obj['Size']
    except Exception as e:
        print(f"[警告] 无法预扫描云端文件列表: {e}")
        return None
    return remote_files

def get_remote_file_hash(bucket, key):
    try:
        response = s3.head_object(Bucket=bucket, Key=key)
        metadata = response.get('Metadata', {})
        return metadata.get('filehash')
    except ClientError:
        return None

# === 核心处理逻辑 ===
def process_file_upload(file_info, remote_files_map):
    abs_path, web_path, old_manifest = file_info
    try:
        current_hash = calculate_sha256(abs_path)
        file_size = os.path.getsize(abs_path)
        encoded_path = urllib.parse.quote(web_path, safe='/')
        final_url = f"{PUBLIC_URL_BASE}/{encoded_path}"
        
        should_upload = True
        
        # 1. Manifest 检查
        if web_path in old_manifest:
            remote_info = old_manifest[web_path]
            remote_hash = remote_info.get('fileHash') or remote_info.get('h')
            if remote_hash == current_hash:
                should_upload = False
        
        # 2. 结合 List Objects 检查
        if should_upload and remote_files_map is not None:
            if web_path not in remote_files_map:
                should_upload = True
            elif remote_files_map[web_path] != file_size:
                should_upload = True
            else:
                if QUICK_COMPARE:
                    should_upload = False
                else:
                    remote_real_hash = get_remote_file_hash(BUCKET_NAME, web_path)
                    if remote_real_hash == current_hash:
                        should_upload = False

        status = "skip"
        if should_upload:
            # === 修改点：上传前立即提示，防止用户以为卡死 ===
            size_str = format_size(file_size)
            print(f"--> [开始上传] {web_path} ({size_str})")
            
            # 使用回调监控进度
            progress_callback = ProgressPercentage(web_path, file_size)

            s3.upload_file(
                abs_path, 
                BUCKET_NAME, 
                web_path,
                ExtraArgs={
                    "Metadata": {"filehash": current_hash},
                    "ContentType": "application/octet-stream"
                },
                Callback=progress_callback
            )
            status = "upload"
        
        return {
            "action": "scan",
            "web_path": web_path,
            "fileHash": current_hash,
            "fileSize": file_size,
            "url": final_url,
            "status": status
        }
    except Exception as e:
        return {"action": "scan", "status": "error", "web_path": web_path, "msg": str(e)}

def process_file_delete(web_path):
    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=web_path)
        return {"action": "delete", "status": "success", "web_path": web_path}
    except Exception as e:
        return {"action": "delete", "status": "error", "web_path": web_path, "msg": str(e)}

def main():
    ignore_spec = load_gitignore(ROOT_DIR)
    include_spec = load_force_include(ROOT_DIR)
    
    old_manifest = get_remote_manifest()
    remote_files_map = fetch_all_remote_files(BUCKET_NAME)
    
    new_manifest = {}
    upload_tasks = []
    
    print(f"\n=== 阶段 1: 扫描与上传 (快速模式: {'开启' if QUICK_COMPARE else '关闭'}) ===")
    
    for root, dirs, files in os.walk(ROOT_DIR):
        valid_dirs = []
        for d in dirs:
            if d in ALWAYS_IGNORE: continue
            d_rel = os.path.relpath(os.path.join(root, d), ROOT_DIR)
            is_forced = include_spec.match_file(d_rel) or include_spec.match_file(d_rel + "/")
            if is_forced or not ignore_spec.match_file(d_rel):
                valid_dirs.append(d)
        dirs[:] = valid_dirs

        for file in files:
            if file in ALWAYS_IGNORE: continue
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, start=ROOT_DIR)
            is_forced = include_spec.match_file(rel_path)
            is_ignored = ignore_spec.match_file(rel_path)
            if is_ignored and not is_forced:
                continue
            web_path = normalize_path(rel_path)
            upload_tasks.append((abs_path, web_path, old_manifest))

    upload_count = 0
    skip_count = 0
    delete_count = 0
    
    print(f"待处理文件数: {len(upload_tasks)}")
    print(f"正在并发处理 (线程数: {MAX_WORKERS})...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_upload = {
            executor.submit(process_file_upload, task, remote_files_map): task[1] 
            for task in upload_tasks
        }
        
        total = len(future_upload)
        completed = 0

        for future in as_completed(future_upload):
            completed += 1
            try:
                res = future.result(timeout=300) # 给大文件上传留足时间
                
                # 仅每 100 个文件汇报一次总体进度，避免刷屏
                if completed % 100 == 0:
                    print(f"[总体进度] {completed}/{total} 已处理...")

                if res['status'] == 'error':
                    print(f"[错误] {res['web_path']}: {res['msg']}")
                else:
                    new_manifest[res['web_path']] = {
                        "fileHash": res['fileHash'],
                        "fileSize": res['fileSize'],
                        "url": res['url']
                    }
                    if res['status'] == 'upload':
                        print(f"√ [上传完成] {res['web_path']}")
                        upload_count += 1
                    else:
                        skip_count += 1
            except Exception as e:
                print(f"[严重错误] 任务异常: {e}")

        # === 阶段 2 ===
        files_to_delete = set(old_manifest.keys()) - set(new_manifest.keys())
        
        if files_to_delete:
            print(f"\n=== 阶段 2: 清理检测 ({len(files_to_delete)} 个废弃文件) ===")
            sorted_files = sorted(list(files_to_delete))
            for f in sorted_files[:10]:
                print(f"  [-] {f}")
            if len(sorted_files) > 10:
                print(f"  ... 以及其他 {len(sorted_files) - 10} 个")
            
            user_input = input(f"\n⚠️  确认删除？(y/n): ").strip().lower()
            if user_input == 'y':
                print(f"正在删除...")
                delete_futures = {executor.submit(process_file_delete, path): path for path in files_to_delete}
                for future in as_completed(delete_futures):
                    res = future.result()
                    if res['status'] == 'success':
                        delete_count += 1
            else:
                print("已跳过删除。")
                for path in files_to_delete:
                    new_manifest[path] = old_manifest[path]
        else:
            print(f"\n=== 阶段 2: 无需清理 ===")

    print(f"\n正在更新 {MANIFEST_FILENAME} ...")
    with open(MANIFEST_FILENAME, "w", encoding='utf-8') as f:
        json.dump(new_manifest, f, indent=None, separators=(',', ':'))
    
    s3.upload_file(MANIFEST_FILENAME, BUCKET_NAME, MANIFEST_FILENAME)
    
    print(f"\n=== 完成: 上传 {upload_count} / 跳过 {skip_count} / 删除 {delete_count} ===")

if __name__ == "__main__":
    main()