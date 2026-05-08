
import os
import time
import datetime
import json
import sys
import re
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- エンコーディング設定 ---
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

CONFIG_PATH = Path(__file__).parent / "config.json"

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "watch_directories": [str(Path.home() / "Downloads")],
        "ignore_extensions": [".crdownload", ".tmp", ".part"],
        "wait_seconds": 2,
        "rename_rule": "{date}_{stem}_v{suffix}"
    }

class RenameHandler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config
        # 日付パターンの正規表現 (例: 20240508_ or 20240508 )
        self.date_pattern = re.compile(r"^\d{8}[_ ]")

    def on_created(self, event):
        if not event.is_directory:
            self.process(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.process(event.dest_path)

    def process(self, filepath):
        path = Path(filepath)
        
        if path.suffix.lower() in self.config["ignore_extensions"]:
            return

        # 既にこのプログラムでリネーム済みか（日付 + _v があるか）
        filename = path.name
        if self.date_pattern.match(filename) and "_v" in path.stem:
            return

        print(f"Processing: {filename}")
        
        time.sleep(self.config["wait_seconds"])
        
        # 最新のパス状態を取得（待機中に消えたりしていないか）
        if not path.exists():
            return

        new_name = self.generate_new_name(path)
        if new_name == filename:
            return

        new_path = path.parent / new_name
        self.safe_rename(path, new_path)

    def generate_new_name(self, path):
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        stem = path.stem
        suffix = path.suffix
        
        # 1. すでに日付から始まっているかチェック
        has_date = self.date_pattern.match(stem)
        
        # 2. すでに _v がついているかチェック
        has_v = stem.endswith("_v") or re.search(r"_v\d+$", stem)

        new_stem = stem
        
        # 日付がなければ先頭に追加
        if not has_date:
            new_stem = f"{date_str}_{new_stem}"
        
        # _v がなければ末尾に追加
        if not has_v:
            new_stem = f"{new_stem}_v"
            
        new_name = f"{new_stem}{suffix}"
        
        # 重複回避
        counter = 2
        while (path.parent / new_name).exists() and new_name != path.name:
            # すでに _v がついている場合は _v2, _v3... としていく
            if "_v" in new_stem:
                base_stem = re.sub(r"_v\d*$", "", new_stem)
                new_name = f"{base_stem}_v{counter}{suffix}"
            else:
                new_name = f"{new_stem}_v{counter}{suffix}"
            counter += 1
            
        return new_name

    def safe_rename(self, old_path, new_path):
        if old_path == new_path:
            return True
            
        max_retries = 5
        for i in range(max_retries):
            try:
                os.rename(old_path, new_path)
                print(f"Renamed: {old_path.name} -> {new_path.name}")
                return True
            except PermissionError:
                time.sleep(1)
            except Exception as e:
                print(f"Error: {e}")
                break
        return False

def main():
    config = load_config()
    event_handler = RenameHandler(config)
    observer = Observer()
    
    for watch_dir in config["watch_directories"]:
        if os.path.exists(watch_dir):
            observer.schedule(event_handler, watch_dir, recursive=False)
            print(f"Watching: {watch_dir}")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
