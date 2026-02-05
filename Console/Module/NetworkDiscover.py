# -*- coding: utf-8 -*-

import socket
import time
import struct
import logging
from Module.Packages import NetworkDiscoverFlag


class NetworkDiscover(object):
    current_ip = None
    socket_ip = None
    socket_port = None
    socket_obj = None
    discover_interval = None

    def __init__(self, current_ip, socket_ip, socket_port, discover_interval=5, parent=None):
        self.current_ip = current_ip
        self.socket_ip = socket_ip
        self.socket_port = socket_port
        self.discover_interval = discover_interval
        self.parent = parent
        self.__init_socket_obj()

    def __init_socket_obj(self):
        self.socket_obj = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # 设置 socket 选项，允许地址重用
        self.socket_obj.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 在 Windows 上，需要先绑定 socket 才能加入多播组
        try:
            self.socket_obj.bind(('', self.socket_port))
        except OSError as e:
            logging.warning(f'Failed to bind socket to port {self.socket_port}: {e}')
            # 如果绑定失败，尝试绑定到任意端口
            try:
                self.socket_obj.bind(('', 0))
            except OSError as e2:
                logging.error(f'Failed to bind socket: {e2}')
                raise
        
        self.socket_obj.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        
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

    def start(self):
        while True:
            try:
                status = self.parent.get_threadings_status()
                socket_packet = struct.pack('!i2?16s', NetworkDiscoverFlag.ConsoleFlag, status['screen_broadcast'],
                                            status['file_server'], status['file_server_password'].encode())
                self.socket_obj.sendto(socket_packet, (self.socket_ip, self.socket_port))
                time.sleep(self.discover_interval)
            except Exception as e:
                logging.warning(f'Failed to send net discover pack: {e}')
