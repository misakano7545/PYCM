# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget, QSystemTrayIcon, QAction, QMenu
from PyQt5.QtCore import Qt, QPoint, QCoreApplication
from PyQt5.QtGui import QMouseEvent, QCloseEvent, QIcon, QShowEvent
from .ScreenBroadcastUI import Ui_ScreenBroadcastForm


class ScreenBroadcastForm(QWidget):
    parent = None
    _translate = QCoreApplication.translate
    _start_pos = None
    _end_pos = None
    _is_tracking = False

    def __init__(self, parent=None):
        super(ScreenBroadcastForm, self).__init__()
        self.parent = parent
        self.ui = Ui_ScreenBroadcastForm()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 初始化系统托盘图标
        self._init_tray_icon()

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


    def toggle_window_broadcast(self, is_fullscreen):
        """切换窗口广播和全屏广播"""
        if is_fullscreen:
            # 切换到全屏广播
            self.ui.window_broadcast.setText(self._translate('ScreenBroadcastForm', '全屏广播'))
            # 通知客户端切换到全屏模式
            if self.parent and hasattr(self.parent, 'class_broadcast_object'):
                # 发送 '2' 表示全屏模式
                self.parent.class_broadcast_object.screen_broadcast_mode_notify(2)
        else:
            # 切换到窗口广播
            self.ui.window_broadcast.setText(self._translate('ScreenBroadcastForm', '窗口广播'))
            # 通知客户端切换到窗口模式
            if self.parent and hasattr(self.parent, 'class_broadcast_object'):
                # 发送 '1' 表示窗口模式
                self.parent.class_broadcast_object.screen_broadcast_mode_notify(1)

    def _init_tray_icon(self):
        """初始化系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(':/Core/Core/Logo.png'))
        self.tray_icon.setToolTip(self._translate('ScreenBroadcastForm', '屏幕广播工具栏'))
        # 创建托盘图标菜单
        self.tray_menu = QMenu(self)
        self.tray_menu.addAction(QAction(self._translate('ScreenBroadcastForm', '显示工具栏'), self, triggered=self.show_toolbar))
        self.tray_menu.addAction(QAction(self._translate('ScreenBroadcastForm', '结束广播'), self, triggered=self.stop_broadcast))
        self.tray_icon.setContextMenu(self.tray_menu)
        # 点击托盘图标时显示工具栏
        self.tray_icon.activated[QSystemTrayIcon.ActivationReason].connect(self._tray_icon_activated)

    def _tray_icon_activated(self, reason):
        """托盘图标激活事件处理"""
        if reason == QSystemTrayIcon.DoubleClick or reason == QSystemTrayIcon.Trigger:
            self.show_toolbar()

    def show_toolbar(self):
        """显示工具栏并隐藏托盘图标"""
        self.show()
        if self.tray_icon.isVisible():
            self.tray_icon.hide()

    def hide_toolbar(self):
        """隐藏工具栏并显示托盘图标"""
        self.hide()
        if not self.tray_icon.isVisible():
            self.tray_icon.show()

    def stop_broadcast(self):
        """结束广播"""
        # 隐藏屏幕广播工具栏的托盘图标
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.hide()
        if self.parent:
            self.parent.ui.toggle_broadcast.setChecked(False)
            self.parent.toggle_broadcast(False)

    def closeEvent(self, event: QCloseEvent):
        # 忽略关闭事件，只停止广播，不关闭窗口
        event.ignore()
        if self.parent:
            self.parent.ui.toggle_broadcast.setChecked(False)
            self.parent.toggle_broadcast(False)
        # 隐藏托盘图标
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.hide()

    def showEvent(self, event: QShowEvent):
        """窗口显示时隐藏托盘图标"""
        super(ScreenBroadcastForm, self).showEvent(event)
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.hide()

