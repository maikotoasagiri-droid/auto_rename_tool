
import os
import copy
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"

DEFAULT_CONFIG = {
    "watch_directories": [],
    "ignore_extensions": [".crdownload", ".tmp", ".part"],
    "wait_seconds": 2,
    "rename_rule": "{date}_{stem}_v{suffix}"
}

def to_display_path(path_str):
    home = os.path.expanduser("~")
    abs_path = os.path.abspath(path_str)
    if abs_path.startswith(home):
        rel = abs_path[len(home):].lstrip("\\/").replace("\\", "/")
        return f"~/{rel}" if rel else "~"
    return abs_path

class ConfigGui:
    def __init__(self, root):
        self.root = root
        root.title("自動リネームツール - 監視フォルダ設定")
        self.config = self.load_raw_config()

        tk.Label(root, text="監視フォルダ一覧").pack(padx=10, pady=(10, 0), anchor="w")

        self.listbox = tk.Listbox(root, width=60, height=10)
        self.listbox.pack(padx=10, pady=10)
        self.refresh_list()

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=(0, 10))
        tk.Button(btn_frame, text="追加", width=10, command=self.add_dir).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="削除", width=10, command=self.remove_dir).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="保存", width=10, command=self.save).pack(side=tk.LEFT, padx=5)

    def load_raw_config(self):
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                if not isinstance(config, dict):
                    raise ValueError(f"設定はオブジェクト形式が必要です (実際: {type(config).__name__})")
            except (json.JSONDecodeError, UnicodeDecodeError, OSError, ValueError) as e:
                messagebox.showwarning(
                    "設定ファイル読み込みエラー",
                    f"config.json が読み込めませんでした。\n({e})\n\n"
                    "デフォルト設定で起動します。\n"
                    "このまま保存すると config.json は上書きされます。"
                )
                return copy.deepcopy(DEFAULT_CONFIG)
            config.setdefault("watch_directories", [])
            return config
        return copy.deepcopy(DEFAULT_CONFIG)

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for d in self.config["watch_directories"]:
            self.listbox.insert(tk.END, d)

    def add_dir(self):
        selected = filedialog.askdirectory()
        if not selected:
            return
        display = to_display_path(selected)
        if display in self.config["watch_directories"]:
            messagebox.showinfo("確認", "既に登録されています。")
            return
        self.config["watch_directories"].append(display)
        self.refresh_list()

    def remove_dir(self):
        selection = self.listbox.curselection()
        if not selection:
            return
        del self.config["watch_directories"][selection[0]]
        self.refresh_list()

    def save(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        messagebox.showinfo(
            "保存完了",
            "config.json に保存しました。\n変更を反映するには自動リネームツールの再起動が必要です。"
        )

def main():
    root = tk.Tk()
    ConfigGui(root)
    root.mainloop()

if __name__ == "__main__":
    main()
