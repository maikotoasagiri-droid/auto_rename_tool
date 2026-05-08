
import os
import sys
from pathlib import Path

def register_startup():
    # 実行中のスクリプトのパス
    current_dir = Path(__file__).parent.absolute()
    script_path = current_dir / "auto_renamer.py"
    
    # スタートアップフォルダのパス (Windows)
    startup_folder = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    vbs_path = startup_folder / "auto_renamer_hidden.vbs"
    
    # pythonw.exe のパスを取得
    pythonw_path = Path(sys.executable).parent / "pythonw.exe"
    if not pythonw_path.exists():
        pythonw_path = "pythonw.exe"

    # VBSスクリプトの内容
    vbs_content = 'Set WshShell = CreateObject("WScript.Shell")\n'
    vbs_content += f'WshShell.Run "{pythonw_path} \\"{script_path}\\"", 0, False\n'
    vbs_content += 'Set WshShell = Nothing\n'
    
    try:
        with open(vbs_path, "w", encoding="shift_jis") as f:
            f.write(vbs_content)
        print(f"Success: Startup script created at {vbs_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    register_startup()
