# -*- coding: utf-8 -*-

import os
import sys

if getattr(sys, 'frozen', False):
    os.environ['PATH'] = sys._MEIPASS + ';' + os.environ['PATH']
