# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDialog, QListWidgetItem, QMessageBox
from PyQt5.QtCore import Qt
from .RemoteCommandGroupUI import Ui_RemoteCommandGroupDialog
from .RemoteCommandGroupAdd import RemoteCommandGroupAddForm


class RemoteCommandGroupForm(QDialog):
    def __init__(self, parent=None):
        super(RemoteCommandGroupForm, self).__init__(parent)
        self.ui = Ui_RemoteCommandGroupDialog()
        self.parent = parent
        self.ui.setupUi(self)
        self.load_commands()

    def load_commands(self):
        available_commands = self.parent.config.get_all('Client/AvailableRemoteCommands')
        self.ui.command_select.clear()
        for label, command in available_commands.items():
            new_item = QListWidgetItem(label)
            new_item.setData(Qt.UserRole, command)
            self.ui.command_select.addItem(new_item)

    def add_command(self):
        add_form = RemoteCommandGroupAddForm(self)
        result = add_form.exec_()
        if result != add_form.Accepted:
            return
        title = add_form.ui.title.text()
        command = add_form.ui.command.toPlainText()
        self.parent.config.save(f'Client/AvailableRemoteCommands/{title}', command)
        self.load_commands()

    def remove_command(self):
        selected = self.ui.command_select.selectedItems()
        if len(selected) == 0:
            QMessageBox.warning(self, '警告', '请选择要删除的命令')
            return
        selected = selected[0].text()
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('警告')
        msg_box.setText('确定要删除此命令: ' + str(selected))
        msg_box.setIcon(QMessageBox.Question)
        yes_btn = msg_box.addButton('是', QMessageBox.YesRole)
        no_btn = msg_box.addButton('否', QMessageBox.NoRole)
        msg_box.setDefaultButton(no_btn)
        msg_box.exec_()
        if msg_box.clickedButton() == yes_btn:
            self.parent.config.remove(f'Client/AvailableRemoteCommands/{selected}')
            self.load_commands()
