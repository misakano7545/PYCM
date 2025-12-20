# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtNetwork import QNetworkInterface, QAbstractSocket
import socket
from .NetworkDeviceSelectUI import Ui_NetworkDeviceSelectDialog


class NetworkDeviceSelectForm(QDialog):
    _translate = QCoreApplication.translate

    def __init__(self, force=False):
        super(NetworkDeviceSelectForm, self).__init__()
        self.devices = []
        self.ui = Ui_NetworkDeviceSelectDialog()
        self.setFixedSize(413, 120)
        self.setWindowModality(Qt.ApplicationModal)
        self.ui.setupUi(self)
        self.force = force
        self.load_network_devices()

    def sync_network_devices(self):
        self.ui.network_device_list.clear()
        for idx, device in enumerate(self.devices):
            device_name, device_info = device
            self.ui.network_device_list.addItem(device_name, device_info)

    @staticmethod
    def get_devices():
        devices_list = QNetworkInterface.allInterfaces()
        devices = []
        for device in devices_list:
            for address in device.addressEntries():
                ip = address.ip()
                if ip.protocol() == QAbstractSocket.IPv4Protocol and not ip.isNull():
                    devices.append((device.humanReadableName(),
                                    {'IP': ip.toString(),
                                     'MAC': device.hardwareAddress(),
                                     'NAME': device.name()}))
                    break
        return devices

    def load_network_devices(self):
        devices_list = QNetworkInterface.allInterfaces()
        self.devices = self.get_devices()
        self.sync_network_devices()

    def get_selected_device(self, only_name=True):
        obj_data = self.ui.network_device_list.currentData()
        if only_name:
            return obj_data['NAME']
        else:
            return obj_data

    def reject(self):
        if self.force:
            QMessageBox.critical(self, self._translate('NetworkDeviceSelectDialog', '错误'),
                                 self._translate('NetworkDeviceSelectDialog', '请选择一个网络设备'))
        else:
            super(NetworkDeviceSelectForm, self).reject()
