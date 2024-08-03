import subprocess
import sys
import threading

from qtpy.QtCore import QLockFile, QDir
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication


class TrayIcon(QSystemTrayIcon):
    def __init__(self):
        super(TrayIcon, self).__init__()
        
        self.titleAction = QAction("Kevinbot Streamer")
        self.titleAction.setDisabled(True)
        self.quitAction = QAction("&Quit", self, triggered=self.end)
        
        self.trayIconMenu = QMenu()
        self.trayIconMenu.addAction(self.titleAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.quitAction)
        
        self.setContextMenu(self.trayIconMenu)
        
        self.setIcon(QIcon().fromTheme("camera"))
        self.setToolTip("Kevinbot Streamer is Running")
        
        self.show()

    @staticmethod
    def end():
        streamer.terminate()
        QApplication.instance().quit()


def run_server():
    import app as server_app
    
    streamer = threading.Thread(target=server_app.run)
    streamer.start()


if __name__ == '__main__':
    lockfile = QLockFile(QDir.tempPath() + '/kbot_streamer.lock')
    if lockfile.tryLock(100):
        app = QApplication(sys.argv)
        run_server()
        QApplication.setQuitOnLastWindowClosed(False)
        icon = TrayIcon()
        # streamer.terminate()
        subprocess.run(["notify-send", "Kevinbot Streamer", "Kevinbot is now streaming"])
        sys.exit(app.exec_())
    else:
        subprocess.run(["notify-send", "Kevinbot Streamer", "Another instance is already running."])
        sys.exit(0)
