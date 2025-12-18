# -*- coding: utf-8 -*-
"""
    This file is part of PYCM project
    Copyright (C) 2021 Richard Yang  <zhongtian.yang@qq.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox
from PyQt5.QtCore import QCoreApplication
import os
import hashlib
from .LoginUI import Ui_LoginForm


def encode_password(password):
    return hashlib.sha256(str(password).encode()).hexdigest()


class LoginForm(QDialog):
    _translate = QCoreApplication.translate

    def __init__(self, parent=None):
        super(LoginForm, self).__init__(parent)
        self.ui = Ui_LoginForm()
        self.parent = parent
        self.ui.setupUi(self)

    def login(self):
        real_admin_username = self.parent.config.get_item('Login/Username')
        real_admin_password = self.parent.config.get_item('Login/Password')
        username = self.ui.username.text()
        password = self.ui.password.text()
        if not all([username, password]):
            QMessageBox.critical(self, self._translate('LoginForm', '警告'),
                                 self._translate('LoginForm', "用户名和密码不能为空"))
            return
        if self.ui.username.text() == real_admin_username:
            if encode_password(self.ui.password.text()) == real_admin_password:
                self.accept()
                self.close()
            else:
                QMessageBox.critical(self, self._translate('LoginForm', '警告'),
                                     self._translate('LoginForm', '密码错误'))
        else:
            QMessageBox.critical(self, self._translate('LoginForm', '警告'),
                                 self._translate('LoginForm', '用户名错误'))
