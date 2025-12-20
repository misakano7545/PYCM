# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
import socket
from .SendMessageUI import Ui_SendMessageForm


class SendMessageForm(QWidget):
    def __init__(self, parent=None):
        super(SendMessageForm, self).__init__()
        self.parent = parent
        self.ui = Ui_SendMessageForm()
        self.ui.setupUi(self)

    def add_message(self, is_receive, message):
        if is_receive:
            direction = '收到'
        else:
            direction = '发送'
        self.ui.message_area.append('%s: %s' % (direction, message))

    def send_message(self):
        message = self.ui.message_input.text()
        self.parent.private_message_object.send_message(message)
        self.add_message(False, message)
        self.ui.message_input.clear()

    def update_input_text(self):
        self.ui.send.setEnabled(len(self.ui.message_input.text()) > 0)
