import os
import sys
import traceback
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

try:
    from app.window import MainWindow
except ImportError as e:
    app = QApplication(sys.argv)
    QMessageBox.critical(None, "启动错误", f"无法加载程序模块：\n{e}\n\n{traceback.format_exc()}")
    sys.exit(1)


def _find_app_icon() -> Path | None:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        candidate = base / "icon.ico"
        if candidate.exists():
            return candidate
        exe_dir_candidate = Path(sys.executable).parent / "icon.ico"
        if exe_dir_candidate.exists():
            return exe_dir_candidate
        return None
    candidate = Path(__file__).resolve().parent / "icon.ico"
    if candidate.exists():
        return candidate
    return None


def main() -> int:
    try:
        if getattr(sys, "frozen", False):
            base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
            plugin_dir = base / "PyQt6" / "Qt6" / "plugins"
            platform_dir = plugin_dir / "platforms"
            if plugin_dir.exists():
                os.environ.setdefault("QT_PLUGIN_PATH", str(plugin_dir))
            if platform_dir.exists():
                os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(platform_dir))
        app = QApplication(sys.argv)
        app.setApplicationName("代码检测")
        app.setOrganizationName("代码检测")
        icon_path = _find_app_icon()
        if icon_path is not None:
            app_icon = QIcon(str(icon_path))
            app.setWindowIcon(app_icon)
        window = MainWindow()
        if icon_path is not None:
            window.setWindowIcon(QIcon(str(icon_path)))
        window.show()
        return app.exec()
    except Exception as e:
        QMessageBox.critical(None, "致命错误", f"程序发生未处理的异常：\n{e}\n\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
