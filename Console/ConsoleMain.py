# -*- coding: utf-8 -*-

import PyQt5.sip
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import sys
import os
import logging

from Module.LoadConfig import Config

from Resources import Resources
from Module import Theme

from UI.Login import LoginForm
from UI.Dashboard import DashboardForm
from UI.NetworkDeviceSelect import NetworkDeviceSelectForm

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
QApplication.setAttribute(Qt.AA_DisableWindowContextHelpButton)
app = QApplication(sys.argv)
app.setStyleSheet(Theme.load_stylesheet())
app.setQuitOnLastWindowClosed(False)

config = Config()

debug_flag_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'DEBUG'))
is_debug = os.path.isfile(debug_flag_path)
logging.basicConfig(level=logging.DEBUG if is_debug else logging.CRITICAL,
                    format='%(asctime)s %(name)s [%(levelname)s] %(module)s.%(funcName)s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S %a'
                    )


class DashboardWindow(DashboardForm):
    config = config

    def __init__(self):
        super(DashboardWindow, self).__init__(self)
        login = LoginForm(self)
        if is_debug:
            login.ui.username.setText('admin')
            login.ui.password.setText('123456')
        if login.exec_() != login.Accepted:
            sys.exit(0)
        
        # 检查是否已经配置过网卡设备
        network_device = self.load_network_device()
        if not network_device:
            # 如果没有配置过，显示网卡选择窗口
            network_devices_select_dialog = NetworkDeviceSelectForm(self)
            if network_devices_select_dialog.exec_() != network_devices_select_dialog.Accepted:
                sys.exit(0)
            network_device = network_devices_select_dialog.get_selected_device()
            self.init_network_device(network_device)
        else:
            # 如果已经配置过，直接使用配置的网卡
            self.init_network_device(network_device)
        
        self.init_threads()
        self.net_discover_thread.start()
        self.private_message_thread.start()
        self.init_tray()
        self.show()
    
    def load_network_device(self):
        """加载已配置的网络设备"""
        from PyQt5.QtNetwork import QNetworkInterface, QAbstractSocket
        
        # 获取已配置的设备名称
        device_name = self.config.get_item('Network/Local/Device', '')
        if not device_name:
            return None
        
        # 查找该设备是否仍然存在
        devices_list = QNetworkInterface.allInterfaces()
        for device in devices_list:
            if device.name() == device_name:
                # 找到设备，获取其IP和MAC
                for address in device.addressEntries():
                    ip = address.ip()
                    if ip.protocol() == QAbstractSocket.IPv4Protocol and not ip.isNull():
                        return {
                            'IP': ip.toString(),
                            'MAC': device.hardwareAddress(),
                            'NAME': device.name()
                        }
        
        # 如果设备不存在，返回None，需要重新选择
        return None


dashboard_window = DashboardWindow()

if __name__ == '__main__':
    sys.exit(app.exec_())
