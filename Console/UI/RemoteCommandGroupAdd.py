# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDialog, QListWidgetItem, QMessageBox
from PyQt5.QtCore import Qt, QCoreApplication
from .RemoteCommandGroupAddUI import Ui_RemoteCommandGroupAddDialog


class RemoteCommandGroupAddForm(QDialog):
    _translate = QCoreApplication.translate

    def __init__(self, parent=None):
        super(RemoteCommandGroupAddForm, self).__init__(parent)
        self.ui = Ui_RemoteCommandGroupAddDialog()
        self.parent = parent
        self.ui.setupUi(self)

    def accept(self):
        if self.ui.title.text() == '':
            QMessageBox.critical(self, self._translate('RemoteCommandGroupAddDialog', '错误'),
                                 self._translate('RemoteCommandGroupAddDialog', '请为命令设置一个名称'))
        elif self.ui.command.document().lineCount() != 1:
            QMessageBox.critical(self, self._translate('RemoteCommandGroupAddDialog', '错误'),
                                 self._translate('RemoteCommandGroupAddDialog',
                                                 '请输入单行命令'))
        elif '/' in self.ui.title.text():
            QMessageBox.critical(self, self._translate('RemoteCommandGroupAddDialog', '错误'),
                                 self._translate('RemoteCommandGroupAddDialog', "名称不能包含 '/'"))
        else:
            super(RemoteCommandGroupAddForm, self).accept()
