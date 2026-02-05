# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject, QBuffer, QIODevice
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage, QPainter, QCursor, QPixmap
from PyQt5.sip import voidptr
from Module.Packages import ScreenBroadcastFlag
import socket
import struct
import zlib
import logging


class ScreenBroadcast(QObject):
    def __init__(self, parent, current_ip, socket_ip, socket_port, socket_buffer, quality=60):
        super(ScreenBroadcast, self).__init__()
        self.parent = parent
        self.current_ip = current_ip
        self.socket_ip = socket_ip
        self.socket_port = socket_port
        self.socket_buffer = socket_buffer
        self.quality = quality
        self.socket_obj = None
        self.working = False
        self.init_socket_obj()

    def init_socket_obj(self):
        self.socket_obj = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # 设置 socket 选项，允许地址重用
        self.socket_obj.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_obj.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        self.socket_obj.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self.socket_buffer)
        
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
        pack_index = 0
        payload_size = self.socket_buffer - struct.calcsize('!2i')
        target = (self.socket_ip, self.socket_port)
        cursor = QCursor()
        cursor_icon = QImage(':/Core/Core/Pointer.png')
        painter = QPainter()
        screen = QApplication.primaryScreen()
        while self.working:
            try:
                cursor_pos = cursor.pos()
                # noinspection PyTypeChecker
                img = screen.grabWindow(0)
                painter.begin(img)
                painter.drawImage(cursor_pos, cursor_icon)
                painter.end()
                # 控制台不需要显示画面，只发送给客户端
                buffer = QBuffer()
                buffer.open(QIODevice.ReadWrite)
                img.save(buffer, 'JPEG', quality=self.quality)
                img_encoded = zlib.compress(buffer.data())
                buffer.close()
                rounds = len(img_encoded) // payload_size
                looped_size = rounds * payload_size
                header = struct.pack('!4i', ScreenBroadcastFlag.PackInfo, pack_index, len(img_encoded), rounds)
                self.socket_obj.sendto(header, target)
                for i in range(rounds):
                    pack = img_encoded[i * payload_size: (i + 1) * payload_size]
                    data = struct.pack(f'!2i{payload_size}s', ScreenBroadcastFlag.PackData, len(pack), pack)
                    self.socket_obj.sendto(data, target)
                if looped_size < len(img_encoded):
                    pack = img_encoded[looped_size:]
                    data = struct.pack(f'!2i{payload_size}s', ScreenBroadcastFlag.PackData, len(pack), pack)
                    self.socket_obj.sendto(data, target)
                pack_index = (pack_index + 1) % 1000
            except Exception as e:
                logging.warning(f'Screen send thread unexpected error: {e}')
