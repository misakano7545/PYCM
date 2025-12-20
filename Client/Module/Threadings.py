# -*- coding: utf-8 -*-

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from Module.ClassBroadcast import ClassBroadcast
from Module.NetworkDiscover import NetworkDiscover
from Module.ScreenBroadcast import ScreenBroadcast
from Module.RemoteSpy import RemoteSpy


class ClassBroadcastThread(QThread):
    message_received = pyqtSignal(str)
    reset_all = pyqtSignal()
    toggle_screen_broadcats = pyqtSignal(bool)
    screen_broadcast_mode = pyqtSignal(int)  # 1 = 窗口模式, 2 = 全屏模式
    start_remote_spy = pyqtSignal()
    quit_self = pyqtSignal()
    client_file_received = pyqtSignal()
    toggle_file_server = pyqtSignal(bool, str)

    def __init__(self, config):
        super(ClassBroadcastThread, self).__init__()
        self.current_ip = config.get_item('Network/Local/IP')
        self.socket_ip = config.get_item('Network/ClassBroadcast/IP')
        self.socket_port = config.get_item('Network/ClassBroadcast/Port')
        self.socket_buffer = config.get_item('Network/ClassBroadcast/Buffer')
        self.socket = ClassBroadcast(self, self.current_ip, self.socket_ip, self.socket_port, self.socket_buffer)

    def run(self):
        self.socket.start()


class NetworkDiscoverThread(QThread):
    server_info = pyqtSignal(str, bool, bool, str)

    def __init__(self, config):
        super(NetworkDiscoverThread, self).__init__()
        self.current_ip = config.get_item('Network/Local/IP')
        self.socket_ip = config.get_item('Network/NetworkDiscover/IP')
        self.socket_port = config.get_item('Network/NetworkDiscover/Port')
        self.socket = NetworkDiscover(self.current_ip, self.socket_ip, self.socket_port)

    def run(self):
        server_ip, screen_broadcast, file_server, file_server_password = self.socket.wait_for_console()
        self.server_info.emit(server_ip, screen_broadcast, file_server, file_server_password)


class ScreenBroadcastThread(QThread):
    frame_received = pyqtSignal(QPixmap)

    def __init__(self, config):
        super(ScreenBroadcastThread, self).__init__()
        self.current_ip = config.get_item('Network/Local/IP')
        self.socket_ip = config.get_item('Network/ScreenBroadcast/IP')
        self.socket_port = config.get_item('Network/ScreenBroadcast/Port')
        self.socket_buffer = config.get_item('Network/ScreenBroadcast/Buffer')
        self.socket = ScreenBroadcast(self, self.current_ip, self.socket_ip, self.socket_port, self.socket_buffer)

    def run(self):
        self.socket.working = True
        self.socket.start()

    def safe_stop(self):
        self.socket.working = False
        self.wait(3000)  # 等待最多3秒让线程自然结束
        if self.isRunning():
            self.terminate()
            self.wait(1000)  # 如果还在运行，强制终止并等待


class RemoteSpyThread(QThread):
    def __init__(self, config):
        super(RemoteSpyThread, self).__init__()
        self.socket_ip = None
        self.socket_port = config.get_item('Network/RemoteSpy/Port')
        self.socket = RemoteSpy(self.socket_port)

    def set_socket_ip(self, socket_ip):
        self.socket_ip = socket_ip
        self.socket.set_socket_ip(self.socket_ip)

    def safe_stop(self):
        self.socket.stop()
        self.wait()

    def run(self):
        if self.socket_ip is not None:
            self.socket.init_socket_obj()
            self.socket.set_socket_ip(self.socket_ip)
        self.socket.working = True
        self.socket.start()
