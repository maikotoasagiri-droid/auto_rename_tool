
import os
import time
import datetime
import json
import sys
import re
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- ロギング設定 ---
LOG_FILE = Path(__file__).parent / "rename_log.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# --- エンコーディング設定 ---
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

CONFIG_PATH = Path(__file__).parent / "config.json"

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            # パスの自動調整 (~ をユーザーディレクトリに置換)
            config["watch_directories"] = [
                os.path.expanduser(d) for d in config["watch_directories"]
            ]
            return config
    
    # デフォルト設定
    return {
        "watch_directories": [os.path.expanduser("~/Downloads")],
        "ignore_extensions": [".crdownload", ".tmp", ".part"],
        "wait_seconds": 2,
        "rename_rule": "{date}_{stem}_v{suffix}"
    }

class RenameHandler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config
        self.date_pattern = re.compile(r"^\d{8}")

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

        filename = path.name
        if self.date_pattern.match(filename) and (path.stem.endswith("_v") or re.search(r"_v\d+$", path.stem)):
            return

        logger.info(f"Processing: {filename}")
        time.sleep(self.config["wait_seconds"])
        
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
        
        has_date = self.date_pattern.match(stem)
        has_v = stem.endswith("_v") or re.search(r"_v\d+$", stem)

        new_stem = stem
        if not has_date:
            new_stem = f"{date_str}_{new_stem}"
        if not has_v:
            new_stem = f"{new_stem}_v1"
            
        new_name = f"{new_stem}{suffix}"
        
        counter = 2
        while (path.parent / new_name).exists() and new_name != path.name:
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
                logger.info(f"Renamed: {old_path.name} -> {new_path.name}")
                return True
            except PermissionError:
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error renaming {old_path.name}: {e}")
                break
        return False

def main():
    config = load_config()
    event_handler = RenameHandler(config)
    observer = Observer()
    
    for watch_dir in config["watch_directories"]:
        if os.path.exists(watch_dir):
            observer.schedule(event_handler, watch_dir, recursive=False)
            logger.info(f"Watching: {watch_dir}")
        else:
            logger.warning(f"Directory not found, skipping: {watch_dir}")

    logger.info("Starting watcher... Press Ctrl+C to stop.")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping watcher...")
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
