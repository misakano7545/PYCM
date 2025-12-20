# -*- coding: utf-8 -*-

import PyQt5.sip
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox
from PyQt5.QtCore import Qt
import sys
import os
import logging

from Module.LoadConfig import Config

from Resources import Resources
from Module import Theme

from UI.Main import MainForm

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
QApplication.setAttribute(Qt.AA_DisableWindowContextHelpButton)
app = QApplication(sys.argv)
app.setStyleSheet(Theme.load_stylesheet())
app.setQuitOnLastWindowClosed(False)

config = Config()

debug_flag_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'DEBUG'))
logging.basicConfig(level=logging.DEBUG if os.path.isfile(debug_flag_path) else logging.CRITICAL,
                    format='%(asctime)s %(name)s [%(levelname)s] %(module)s.%(funcName)s | %(message)s',
                    datefmt='%Y-%m-%d  %H:%M:%S %a'
                    )


class MainWindow(MainForm):
    config = config
    def __init__(self):
        super(MainWindow, self).__init__(self)
        network_device = self.load_network_device()
        if not network_device:
            QMessageBox.critical(self, '错误', '网络设备错误，请选择另一个设备！')
            device = config.force_get_network_device(only_name=False)
            config.save('Network/Local/Device', device['NAME'])
            self.init_network_device(device)
        else:
            self.init_network_device(network_device)
        self.init_threadings()


main_window = MainWindow()

if __name__ == '__main__':
    main_window.show()
    sys.exit(app.exec_())
