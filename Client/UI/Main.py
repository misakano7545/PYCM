# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget, QSystemTrayIcon, QAction, QMenu, QMessageBox, QApplication
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal, QCoreApplication
from PyQt5.QtGui import QMouseEvent, QIcon, QCloseEvent
import socket
import platform
import subprocess

from .MainUI import Ui_MainForm
from .FileSend import FileSendForm
from .ScreenBroadcast import ScreenBroadcastForm
from .SendMessage import SendMessageForm
from .NetworkDeviceSelect import NetworkDeviceSelectForm
from .About import AboutDialog

from Module.Threadings import NetworkDiscoverThread, ClassBroadcastThread, ScreenBroadcastThread, RemoteSpyThread
from Module.PrivateMessage import PrivateMessage


# noinspection PyAttributeOutsideInit
class MainForm(QWidget):
    config = None
    net_discover_thread = None
    class_broadcast_thread = None
    screen_broadcast_thread = None
    remote_spy_thread = None
    private_message_object = None
    server_ip = None
    screen_spy_timer = QTimer()
    file_client_password = ''
    _start_pos = None
    _end_pos = None
    _is_tracking = False
    _force_quit = False
    _translate = QCoreApplication.translate

    def __init__(self, parent=None):
        super(MainForm, self).__init__()
        self.ui = Ui_MainForm()
        self.parent = parent
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        desktop = QApplication.desktop()
        self.move(int(desktop.width() - 450), 65)
        self.screen_broadcast_window = ScreenBroadcastForm(parent)
        self.file_send_window = FileSendForm(self.parent)
        self.messaging_window = SendMessageForm(self.parent)
        self.init_tray()
        self.init_file_button()

    def load_network_device(self):
        devices = NetworkDeviceSelectForm.get_devices()
        default_device = self.parent.config.get_item('Network/Local/Device')
        for device in devices:
            if device[1]['NAME'] == default_device:
                return device[1]

    def init_threadings(self):
        self.net_discover_thread = NetworkDiscoverThread(self.config)
        self.class_broadcast_thread = ClassBroadcastThread(self.config)
        self.screen_broadcast_thread = ScreenBroadcastThread(self.config)
        self.remote_spy_thread = RemoteSpyThread(self.config)
        self.private_message_object = PrivateMessage(self.config)
        self.init_connections()
        self.net_discover_thread.start()

    def init_connections(self):
        self.net_discover_thread.server_info.connect(self.server_found)
        self.class_broadcast_thread.message_received.connect(self.message_received)
        self.class_broadcast_thread.reset_all.connect(self.reset_all_threadings)
        self.class_broadcast_thread.toggle_screen_broadcats.connect(self.__toggle_screen_broadcast)
        self.class_broadcast_thread.quit_self.connect(self.quit_self)
        self.class_broadcast_thread.start_remote_spy.connect(self.start_remote_spy)
        self.class_broadcast_thread.toggle_file_server.connect(self.toggle_file_client)
        self.screen_broadcast_thread.frame_received.connect(self.screen_broadcast_window.update_frame)
        self.screen_spy_timer.timeout.connect(self.private_message_object.screen_spy_send)

    def reset_all_threadings(self):
        self.screen_spy_timer.stop()
        self.class_broadcast_thread.quit()
        self.remote_spy_thread.safe_stop()
        self.class_broadcast_thread.wait()
        self.remote_spy_thread.wait()
        self.net_discover_thread = NetworkDiscoverThread(self.config)
        self.class_broadcast_thread = ClassBroadcastThread(self.config)
        self.remote_spy_thread = RemoteSpyThread(self.config)
        self.private_message_object = PrivateMessage(self.config)
        self.init_connections()
        self.ui.title_label.setText(self._translate('MainForm', 'PYCM 客户端 - 离线'))
        self.update_tray_tooltip()
        self.ui.notify_button.setEnabled(False)
        self.ui.file_button.setEnabled(False)
        self.ui.private_message_button.setEnabled(False)
        self.server_ip = None
        self.net_discover_thread.start()

    # noinspection PyArgumentList
    def init_tray(self):
        self.tray_icon_menu = QMenu(self)
        self.tray_icon_menu.addAction(QAction(self._translate('MainForm', '显示工具栏'), self, triggered=self.show))
        self.tray_icon_menu.addAction(QAction(self._translate('MainForm', '网络配置'),
                                              self, triggered=self.show_network_config_window))
        self.tray_icon_menu.addAction(QAction(self._translate('MainForm', '关于'),
                                              self, triggered=self.show_about))
        self.tray_icon_menu.addAction(QAction(self._translate('MainForm', '退出'), self, triggered=self.close))
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(':/Core/Core/Logo.png'))
        self.tray_icon.setContextMenu(self.tray_icon_menu)
        self.tray_icon.activated[QSystemTrayIcon.ActivationReason].connect(self.iconActivated)
        self.update_tray_tooltip()
        self.tray_icon.show()

    # noinspection PyArgumentList
    def init_file_button(self):
        self.file_button_menu = QMenu()
        self.file_client_action = QAction(self._translate('MainForm', '文件客户端'), self,
                                          triggered=self.show_file_client_window)
        self.file_client_action.setEnabled(False)
        file_send_action = QAction(self._translate('MainForm', '发送文件'), self,
                                   triggered=self.show_file_send_window)
        self.file_button_menu.addActions([self.file_client_action, file_send_action])
        self.ui.file_button.setMenu(self.file_button_menu)

    def show_network_config_window(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self._translate('MainForm', '警告'))
        msg_box.setText(self._translate('MainForm', '确定要修改网络配置吗？此操作可能导致客户端无法正常启动！'))
        msg_box.setIcon(QMessageBox.Question)
        yes_btn = msg_box.addButton('是', QMessageBox.YesRole)
        no_btn = msg_box.addButton('否', QMessageBox.NoRole)
        msg_box.setDefaultButton(no_btn)
        msg_box.exec_()
        if msg_box.clickedButton() == yes_btn:
            result = self.config.modify_network_device()
            if result:
                QMessageBox.information(self, self._translate('MainForm', '提示'),
                                        self._translate('MainForm', '配置成功！请重启客户端以使配置生效'),
                                        QMessageBox.Ok)

    def show_file_send_window(self):
        self.file_send_window = FileSendForm(self.parent)
        self.class_broadcast_thread.client_file_received.connect(self.file_send_window.file_received)
        self.file_send_window.show()

    def show_file_client_window(self):
        file_client_port = self.parent.config.get_item('Network/FileServer/Port')
        ftp_url = f'ftp://pycm:{self.file_client_password}@{self.server_ip}:{file_client_port}'
        system = platform.system().lower()
        if system == 'windows':
            subprocess.call(['explorer.exe', ftp_url], shell=False)
        elif system == 'darwin':
            subprocess.call(['open', ftp_url], shell=False)
        elif system == 'linux':
            subprocess.call(['xdg-open', ftp_url], shell=False)

    def show_messaging_window(self):
        self.messaging_window.show()

    def show_about(self):
        AboutDialog(self).exec_()

    def start_remote_spy(self):
        self.remote_spy_thread.start()

    def message_received(self, message):
        icon = QSystemTrayIcon.MessageIcon()
        self.tray_icon.showMessage(self._translate('MainForm', '消息'), message, icon, 1000)
        self.messaging_window.add_message(True, message)

    def notify_console(self):
        self.private_message_object.notify_console()

    def server_found(self, server_ip, screen_broadcast_status, file_server_status, file_server_password):
        self.server_ip = server_ip
        self.private_message_object.set_socket_ip(self.server_ip)
        self.remote_spy_thread.set_socket_ip(self.server_ip)
        self.private_message_object.online_notify()
        self.class_broadcast_thread.start()
        self.ui.title_label.setText(self._translate('MainForm', 'PYCM 客户端 - 在线'))
        self.update_tray_tooltip()
        self.ui.notify_button.setEnabled(True)
        self.ui.file_button.setEnabled(True)
        self.ui.private_message_button.setEnabled(True)
        self.screen_spy_timer.start(3000)
        if screen_broadcast_status:
            self.__toggle_screen_broadcast(True)
        if file_server_status:
            self.toggle_file_client(True, file_server_password)

    def init_network_device(self, device):
        self.config.save('Network/Local/IP', device['IP'])
        self.config.save('Network/Local/MAC', device['MAC'])

    def __toggle_screen_broadcast(self, work):
        self.screen_broadcast_thread.socket.working = work
        if work:
            self.screen_broadcast_thread.start()
            self.screen_broadcast_window.show()
        else:
            self.screen_broadcast_thread.safe_stop()
            self.screen_broadcast_window.hide()

    def update_tray_tooltip(self):
        local_ip = self.config.get_item('Network/Local/IP')
        if self.server_ip:
            online_status = self._translate('MainForm', '在线')
        else:
            online_status = self._translate('MainForm', '离线')
        self.tray_icon.setToolTip(self._translate('MainForm', 'PYCM 客户端\n') +
                                  self._translate('MainForm', '本地IP: %s\n') % local_ip +
                                  self._translate('MainForm', '状态: %s') % online_status)

    def quit_self(self):
        self._force_quit = True
        self.close()

    def toggle_file_client(self, working, password):
        if working:
            self.file_client_password = password
            self.file_client_action.setEnabled(True)
        else:
            self.file_client_action.setEnabled(False)

    def mouseMoveEvent(self, e: QMouseEvent):
        if self._start_pos and self._is_tracking:
            self._end_pos = e.pos() - self._start_pos
            self.move(self.pos() + self._end_pos)

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._is_tracking = True
            self._start_pos = QPoint(e.x(), e.y())

    def mouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._is_tracking = False
            self._start_pos = None
            self._end_pos = None

    def iconActivated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def closeEvent(self, event: QCloseEvent):
        if not self._force_quit:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(self._translate('MainForm', '警告'))
            msg_box.setText(self._translate('MainForm', '确定要退出吗？'))
            msg_box.setIcon(QMessageBox.Question)
            yes_btn = msg_box.addButton('是', QMessageBox.YesRole)
            no_btn = msg_box.addButton('否', QMessageBox.NoRole)
            msg_box.setDefaultButton(no_btn)
            msg_box.exec_()
            if msg_box.clickedButton() != yes_btn:
                event.ignore()
                return
        if self.server_ip is not None:
            self.private_message_object.offline_notify()
        if self.tray_icon.isVisible():
            self.tray_icon.hide()
        self.tray_icon = None
        QApplication.instance().quit()
