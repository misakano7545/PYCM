# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDialog, QListWidgetItem, QMessageBox
from PyQt5.QtCore import Qt
from .RemoteCommandGroupAddUI import Ui_RemoteCommandGroupAddDialog


class RemoteCommandGroupAddForm(QDialog):
    def __init__(self, parent=None):
        super(RemoteCommandGroupAddForm, self).__init__(parent)
        self.ui = Ui_RemoteCommandGroupAddDialog()
        self.parent = parent
        self.ui.setupUi(self)

    def accept(self):
        if self.ui.title.text() == '':
            QMessageBox.critical(self, '错误', '请为命令设置一个名称')
        elif self.ui.command.document().lineCount() != 1:
            QMessageBox.critical(self, '错误', '请输入单行命令')
        elif '/' in self.ui.title.text():
            QMessageBox.critical(self, '错误', "名称不能包含 '/'")
        else:
            super(RemoteCommandGroupAddForm, self).accept()
