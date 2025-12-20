# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QCoreApplication
from .AboutUI import Ui_AboutDialog

try:
    from BuildInfo import BUILD_INFO
except ImportError:
    BUILD_INFO = None


class AboutDialog(QDialog):
    _translate = QCoreApplication.translate

    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.ui = Ui_AboutDialog()
        self.parent = parent
        self.ui.setupUi(self)
        build_info = BUILD_INFO
        if build_info is None:
            build_info = self._translate('AboutDialog', '无构建信息')
        self.ui.buildInfo.setText(self._translate('AboutDialog', '构建信息: %s') % build_info)
