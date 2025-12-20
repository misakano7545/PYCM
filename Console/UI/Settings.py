# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtNetwork import QNetworkInterface, QAbstractSocket
import hashlib
from .SettingsUI import Ui_SettingsDialog
from Module.Database import Database


def encode_password(password):
    """加密密码"""
    return hashlib.sha256(str(password).encode()).hexdigest()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.parent = parent
        self.ui = Ui_SettingsDialog()
        self.ui.setupUi(self)
        self.db = Database()
        self.load_settings()
        self.load_network_devices()
    
    def load_settings(self):
        """从数据库加载设置"""
        # 加载登录设置
        username = self.db.get('Login/Username', 'admin')
        password = self.db.get('Login/Password', '')
        self.ui.username_input.setText(username)
        # 密码不显示，留空让用户重新输入
    
    def load_network_devices(self):
        """加载网络设备列表"""
        devices_list = QNetworkInterface.allInterfaces()
        self.devices = []
        default_device_name = self.db.get('Network/Local/Device', '')
        
        for device in devices_list:
            for address in device.addressEntries():
                ip = address.ip()
                if ip.protocol() == QAbstractSocket.IPv4Protocol and not ip.isNull():
                    device_name = device.humanReadableName()
                    device_info = {
                        'IP': ip.toString(),
                        'MAC': device.hardwareAddress(),
                        'NAME': device.name()
                    }
                    self.devices.append((device_name, device_info))
                    self.ui.network_device_combo.addItem(device_name, device_info)
                    # 设置默认选中的设备
                    if device_info['NAME'] == default_device_name:
                        self.ui.network_device_combo.setCurrentIndex(self.ui.network_device_combo.count() - 1)
                    break
        
        # 确保下拉箭头可见
        # 使用与 NetworkDeviceSelect 对话框相同的设置方式
        # 不设置任何自定义样式，完全依赖全局样式表
        # 确保 QComboBox 有足够的宽度来显示下拉箭头
        self.ui.network_device_combo.setMinimumWidth(250)
        
        # 确保 QComboBox 不可编辑，这样下拉箭头才会显示
        self.ui.network_device_combo.setEditable(False)
    
    def accept(self):
        """保存设置"""
        # 验证登录设置
        username = self.ui.username_input.text().strip()
        password = self.ui.password_input.text()
        password_confirm = self.ui.password_confirm_input.text()
        
        if not username:
            QMessageBox.warning(self, '警告', '用户名不能为空')
            return
        
        # 如果输入了密码，需要确认
        if password:
            if password != password_confirm:
                QMessageBox.warning(self, '警告', '两次输入的密码不一致')
                return
            if len(password) < 6:
                QMessageBox.warning(self, '警告', '密码长度至少为6位')
                return
        
        # 验证网络设备
        if self.ui.network_device_combo.currentIndex() < 0:
            QMessageBox.warning(self, '警告', '请选择一个网络设备')
            return
        
        # 保存登录设置
        self.db.set('Login/Username', username)
        if password:
            encoded_password = encode_password(password)
            self.db.set('Login/Password', encoded_password)
        
        # 保存网络设备设置
        device_info = self.ui.network_device_combo.currentData()
        if device_info:
            self.db.set('Network/Local/Device', device_info['NAME'])
            self.db.set('Network/Local/IP', device_info['IP'])
            self.db.set('Network/Local/MAC', device_info['MAC'])
            # 同时更新到父窗口的配置中（如果存在）
            if self.parent and hasattr(self.parent, 'config'):
                self.parent.config.save('Network/Local/Device', device_info['NAME'])
                self.parent.config.save('Network/Local/IP', device_info['IP'])
                self.parent.config.save('Network/Local/MAC', device_info['MAC'])
                # 如果网络设备已更改，需要重新初始化网络设备
                if hasattr(self.parent, 'init_network_device'):
                    self.parent.init_network_device(device_info)
        
        QMessageBox.information(self, '提示', '设置已保存')
        
        super(SettingsDialog, self).accept()

