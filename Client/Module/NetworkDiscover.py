# -*- coding: utf-8 -*-

import socket
import struct
import logging
from Module.Packages import NetworkDiscoverFlag


class NetworkDiscover(object):
    current_ip = None
    socket_ip = None
    socket_port = None
    socket_client = None

    def __init__(self, current_ip, socket_ip, socket_port):
        self.current_ip = current_ip
        self.socket_ip = socket_ip
        self.socket_port = socket_port
        self.__init_socket_client()

    def __init_socket_client(self):
        self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_client.bind(('', self.socket_port))
        
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
            
            self.socket_client.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        except OSError as e:
            logging.error(f'Failed to join multicast group {self.socket_ip} with local IP {local_ip}: {e}')
            # 如果加入多播组失败，尝试使用 INADDR_ANY
            try:
                mreq = struct.pack('4sL', socket.inet_aton(self.socket_ip), socket.INADDR_ANY)
                self.socket_client.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            except OSError as e2:
                logging.error(f'Failed to join multicast group with INADDR_ANY: {e2}')
                raise

    def wait_for_console(self):
        while True:
            try:
                socket_data, socket_addr = self.socket_client.recvfrom(1024)
                flag, screen_broadcast, file_server, file_server_password = struct.unpack('!i2?16s', socket_data)
                if flag == NetworkDiscoverFlag.ConsoleFlag:
                    return socket_addr[0], screen_broadcast, file_server, file_server_password.decode()
            except Exception as e:
                logging.warning(f'Failed to decode socket data: {e}')
