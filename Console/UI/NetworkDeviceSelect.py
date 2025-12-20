# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt
from PyQt5.QtNetwork import QNetworkInterface, QAbstractSocket
import socket
from .NetworkDeviceSelectUI import Ui_NetworkDeviceSelectDialog


class NetworkDeviceSelectForm(QDialog):
    def __init__(self, parent=None):
        super(NetworkDeviceSelectForm, self).__init__(parent)
        self.devices = []
        self.ui = Ui_NetworkDeviceSelectDialog()
        self.setFixedSize(413, 120)
        self.setWindowModality(Qt.ApplicationModal)
        self.ui.setupUi(self)
        self.default_device = parent.config.get_item('Network/Local/Device')
        self.load_network_devices()

    def sync_network_devices(self):
        self.ui.network_device_list.clear()
        for idx, device in enumerate(self.devices):
            device_name, device_info = device
            self.ui.network_device_list.addItem(device_name, device_info)
            if device_info['NAME'] == self.default_device:
                self.ui.network_device_list.setCurrentIndex(idx)

    def load_network_devices(self):
        devices_list = QNetworkInterface.allInterfaces()
        self.devices.clear()
        for device in devices_list:
            for address in device.addressEntries():
                ip = address.ip()
                if ip.protocol() == QAbstractSocket.IPv4Protocol and not ip.isNull():
                    self.devices.append((device.humanReadableName(),
                                         {'IP': ip.toString(),
                                          'MAC': device.hardwareAddress(),
                                          'NAME': device.name()}))
                    break
        self.sync_network_devices()

    def get_selected_device(self):
        obj_data = self.ui.network_device_list.currentData()
        self.parent().config.save('Network/Local/Device', obj_data['NAME'])
        return obj_data
