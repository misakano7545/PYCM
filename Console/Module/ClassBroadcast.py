# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject
import socket
import struct
import base64
import pickle
import zlib
import logging
from Module.Packages import ClassBroadcastFlag


class ClassBroadcast(QObject):
    current_ip = None
    socket_ip = None
    socket_port = None
    socket_buffer_size = None
    socket_obj = None

    def __init__(self, config, parent=None):
        super(ClassBroadcast, self).__init__(parent)
        self.current_ip = config.get_item('Network/Local/IP')
        self.socket_ip = config.get_item('Network/ClassBroadcast/IP')
        self.socket_port = config.get_item('Network/ClassBroadcast/Port')
        self.socket_buffer_size = config.get_item('Network/ClassBroadcast/Buffer')
        self.__init_socket_obj()

    def __init_socket_obj(self):
        self.socket_obj = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # 设置 socket 选项，允许地址重用
        self.socket_obj.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_obj.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        self.socket_obj.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self.socket_buffer_size)
        
        # 验证并处理 current_ip
        local_ip = None
        if self.current_ip:
            try:
                # 验证 current_ip 是否为有效的 IP 地址
                socket.inet_aton(self.current_ip)
                local_ip = self.current_ip
            except (OSError, socket.error):
                # current_ip 无效，使用 INADDR_ANY
                local_ip = None
        
        # 构建多播组加入请求
        try:
            if local_ip:
                # 使用指定的本地 IP 地址
                mreq = socket.inet_aton(self.socket_ip) + socket.inet_aton(local_ip)
            else:
                # 使用 INADDR_ANY (0.0.0.0)，让系统自动选择接口
                mreq = struct.pack('4sL', socket.inet_aton(self.socket_ip), socket.INADDR_ANY)
            
            self.socket_obj.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except OSError as e:
            logging.error(f'Failed to join multicast group {self.socket_ip} with local IP {local_ip}: {e}')
            # 如果加入多播组失败，尝试使用 INADDR_ANY
            try:
                mreq = struct.pack('4sL', socket.inet_aton(self.socket_ip), socket.INADDR_ANY)
                self.socket_obj.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            except OSError as e2:
                logging.error(f'Failed to join multicast group with INADDR_ANY: {e2}')
                raise

    def send_data(self, flag, data):
        payload_size = self.socket_buffer_size - struct.calcsize('!2i')
        socket_data = struct.pack(f'!2i{payload_size}s', flag, len(data), data)
        self.socket_obj.sendto(socket_data, (self.socket_ip, self.socket_port))

    def batch_send(self, flag, clients, payload):
        targets = pickle.dumps(clients)
        cksum = zlib.crc32(targets)
        full_data = struct.pack(f'!iL{len(targets)}s{len(payload)}s', len(targets), cksum, targets, payload)
        self.send_data(flag, full_data)

    def send_text(self, clients, text):
        text = base64.b64encode(str(text).encode('utf-8'))
        self.batch_send(ClassBroadcastFlag.Message, clients, text)

    def send_command(self, clients, command):
        command = base64.b64encode(str(command).encode('utf-8'))
        self.batch_send(ClassBroadcastFlag.Command, clients, command)

    def remote_spy_start_notify(self, client):
        self.batch_send(ClassBroadcastFlag.RemoteSpyStart, [client], b'1')

    def console_quit_notify(self):
        self.send_data(ClassBroadcastFlag.ConsoleQuit, b'')

    def screen_broadcast_notify(self, working):
        if working:
            self.send_data(ClassBroadcastFlag.ToggleScreenBroadcast, b'1')
        else:
            self.send_data(ClassBroadcastFlag.ToggleScreenBroadcast, b'0')

    def screen_broadcast_mode_notify(self, mode):
        """通知客户端切换屏幕广播模式
        mode: 1 = 窗口模式, 2 = 全屏模式
        """
        self.send_data(ClassBroadcastFlag.ToggleScreenBroadcast, str(mode).encode())

    def remote_quit_notify(self, clients):
        self.batch_send(ClassBroadcastFlag.RemoteQuit, clients, b'')

    def client_file_received_notify(self, client):
        self.batch_send(ClassBroadcastFlag.ClientFileReceived, [client], b'')

    def file_server_status_notify(self, working, password=''):
        if working:
            self.send_data(ClassBroadcastFlag.ToggleFileServer, b'1' + password.encode())
        else:
            self.send_data(ClassBroadcastFlag.ToggleFileServer, b'0')
