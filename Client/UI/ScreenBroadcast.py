# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget, QFileDialog
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QPaintEvent, QCloseEvent
from .ScreenBroadcastUI import Ui_ScreenBroadcastForm


class ScreenBroadcastForm(QWidget):
    parent = None
    freeze = False
    first_frame = True

    def __init__(self, parent=None):
        super(ScreenBroadcastForm, self).__init__()
        self.parent = parent
        self.frame_proportion = 9 / 16
        self.ui = Ui_ScreenBroadcastForm()
        self.ui.setupUi(self)
        self.ui.screen_display.move(0, 0)
        self.setWindowFlags(Qt.WindowMinMaxButtonsHint | Qt.WindowStaysOnTopHint)

    def update_frame(self, frame):
        if not self.freeze:
            screen_display_object = self.ui.screen_display
            screen_display_object.setPixmap(frame)
        if self.first_frame:
            self.frame_proportion = frame.height() / frame.width()
            self.first_frame = False

    def freeze_frame(self, freeze=True):
        self.freeze = freeze

    def show_full_screen(self, fullscreen=True, hide_control_bar=False):
        """切换全屏模式
        Args:
            fullscreen: True 为全屏，False 为窗口模式
            hide_control_bar: True 时隐藏控制栏（控制台强制全屏时使用），False 时保持控制栏显示（客户端自己点击全屏时使用）
        """
        if fullscreen:
            self.showFullScreen()
            # 只有控制台强制全屏时才隐藏控制栏
            if hide_control_bar:
                self._hide_control_bar()
        else:
            self.showNormal()
            # 窗口模式下始终显示控制栏
            self._show_control_bar()

    def _hide_control_bar(self):
        """隐藏控制栏"""
        # 隐藏控制栏中的所有按钮
        for i in range(self.ui.control_box_layout.count()):
            item = self.ui.control_box_layout.itemAt(i)
            if item and item.widget():
                item.widget().hide()

    def _show_control_bar(self):
        """显示控制栏"""
        # 显示控制栏中的所有按钮
        for i in range(self.ui.control_box_layout.count()):
            item = self.ui.control_box_layout.itemAt(i)
            if item and item.widget():
                item.widget().show()

    def screen_shot(self):
        frame = self.ui.screen_display.pixmap()
        if frame is None or frame.isNull():
            return
        frame = frame.toImage()
        file_path, _ = QFileDialog.getSaveFileName(self, '选择保存路径', str(QDir.homePath()), 'JPEG 图像(*.jpg)')
        if file_path:
            frame.save(file_path, 'JPEG')

    def toggle_always_on_top(self, on_top):
        self.windowHandle().setFlag(Qt.WindowStaysOnTopHint, on_top)

    def paintEvent(self, event: QPaintEvent):
        container_size = self.ui.screen_widget.size()
        container_height = container_size.height()
        container_width = container_size.width()
        container_proportion = container_height / container_width
        screen_height = container_height
        screen_width = container_width
        if container_proportion > self.frame_proportion:
            screen_height = int(screen_width * self.frame_proportion)
            delta_height = container_height - screen_height
            self.ui.screen_display.move(0, delta_height // 2)
        elif container_proportion < self.frame_proportion:
            screen_width = int(screen_height / self.frame_proportion)
            delta_width = container_width - screen_width
            self.ui.screen_display.move(delta_width // 2, 0)
        self.ui.screen_display.resize(screen_width, screen_height)

    def closeEvent(self, event: QCloseEvent):
        event.ignore()
