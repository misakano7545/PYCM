# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox
import random
import string
import os
from .FileServerUI import Ui_FileServerForm


class FileServerForm(QDialog):
    working = False
    working_folder = None

    def __init__(self, parent=None):
        super(FileServerForm, self).__init__(parent)
        self.ui = Ui_FileServerForm()
        self.parent = parent
        self.ui.setupUi(self)

    @staticmethod
    def __generate_ftp_password():
        source = string.ascii_lowercase + string.digits
        password = random.sample(source, 16)
        return ''.join(password)

    def change_working_folder(self):
        directory = QFileDialog.getExistingDirectory(self, '选择工作文件夹', os.path.expanduser('~'))
        if not directory:
            return
        self.working_folder = directory
        self.parent.file_server_thread.set_working_dir(directory)
        self.ui.working_folder.setText(directory)

    def toggle_server(self):
        if not self.working:
            if self.working_folder is None:
                QMessageBox.critical(self, '错误', '未设置工作文件夹！')
            else:
                ftp_password = self.__generate_ftp_password()
                self.parent.file_server_thread.set_password(ftp_password)
                self.parent.file_server_thread.start()
                self.parent.class_broadcast_object.file_server_status_notify(True, ftp_password)
                self.working = True
        else:
            self.parent.class_broadcast_object.file_server_status_notify(False)
            self.parent.file_server_thread.safe_stop()
            self.working = False
        self.update_status()

    def update_status(self):
        if self.working:
            self.ui.server_info.setText('服务器状态: 运行中')
            self.ui.toggle_working.setText('停止')
        else:
            self.ui.server_info.setText('服务器状态: 已停止')
            self.ui.toggle_working.setText('启动')
