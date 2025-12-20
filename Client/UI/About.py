# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDialog
from .AboutUI import Ui_AboutDialog

try:
    from BuildInfo import BUILD_INFO
except ImportError:
    BUILD_INFO = None


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.ui = Ui_AboutDialog()
        self.parent = parent
        self.ui.setupUi(self)
        build_info = BUILD_INFO
        if build_info is None:
            build_info = '无构建信息'
        self.ui.buildInfo.setText('构建信息: %s' % build_info)
