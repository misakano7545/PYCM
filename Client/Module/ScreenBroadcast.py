# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject
from PyQt5.QtGui import QImage, QPixmap
from Module.Packages import ScreenBroadcastFlag
import socket
import struct
import zlib
from threading import Thread, Lock
from queue import Queue
import logging


class ScreenBroadcast(QObject):
    def __init__(self, parent, current_ip, socket_ip, socket_port, socket_buffer):
        super(ScreenBroadcast, self).__init__()
        self.parent = parent
        self.current_ip = current_ip
        self.socket_ip = socket_ip
        self.socket_port = socket_port
        self.socket_buffer = socket_buffer
        self.frames_queue = Queue()
        self.working = False
        self.__init_socket_obj()

    def __init_socket_obj(self):
        self.socket_obj = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket_obj.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        self.socket_obj.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_obj.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.socket_buffer)
        self.socket_obj.bind(('', self.socket_port))
        
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

    def __receive_thread(self):
        header_size = struct.calcsize('!4i')
        payload_size = self.socket_buffer - struct.calcsize('!2i')
        frame_data = b''
        pack_drop_flag = False
        pack_drop_buffer = b''
        while self.working:
            try:
                if not pack_drop_flag:
                    socket_data, _ = self.socket_obj.recvfrom(header_size)
                else:
                    socket_data = pack_drop_buffer
                    pack_drop_flag = False
                    pack_drop_buffer = b''
                data_flag, data_index, data_length, data_rounds = struct.unpack('!4i', socket_data)
                if data_flag == ScreenBroadcastFlag.PackInfo:
                    while len(frame_data) < data_length:
                        socket_data, _ = self.socket_obj.recvfrom(self.socket_buffer)
                        data_flag, pack_length, pack = struct.unpack(f'!2i{payload_size}s', socket_data)
                        pack = pack[:pack_length]
                        if data_flag == ScreenBroadcastFlag.PackData:
                            frame_data += pack
                        elif data_flag == ScreenBroadcastFlag.PackInfo:
                            pack_drop_flag = True
                            pack_drop_buffer = socket_data
                            break
                    if pack_drop_flag:
                        continue
                    elif len(frame_data) == data_length:
                        frame = zlib.decompress(frame_data)
                        self.frames_queue.put(frame)
                        frame_data = b''
                    elif len(frame_data) > data_length:
                        frame_data = b''
            except (OSError, struct.error):
                continue
            except Exception as e:
                logging.warning(f'Failed to handle frame: {e}')

    def start(self):
        Thread(target=self.__receive_thread, daemon=True).start()
        from queue import Empty
        while self.working:
            try:
                frame_raw = self.frames_queue.get(timeout=0.1)
                frame_qimage = QImage.fromData(frame_raw)
                if not frame_qimage.isNull():
                    self.parent.frame_received.emit(QPixmap.fromImage(frame_qimage))
            except Empty:
                continue
            except Exception as e:
                logging.warning(f'Failed to process frame: {e}')
                continue
