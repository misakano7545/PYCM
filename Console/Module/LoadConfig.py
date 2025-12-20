# -*- coding: utf-8 -*-

from PyQt5.QtCore import QSettings
from Module.Database import Database


class Config(object):
    def __init__(self):
        self.settings = QSettings('HCC', 'PYCMConsole')
        self.db = Database()
        self.__default_config = {
            'FirstRun': True,
            'Network': {
                'Local': {'Device': ''},
                'NetworkDiscover': {
                    'IP': '224.50.50.50',
                    'Port': 4088,
                    'Interval': 5
                },
                'ClassBroadcast': {
                    'IP': '225.2.2.19',
                    'Port': 4089,
                    'Buffer': 65500
                },
                'PrivateMessage': {
                    'Port': 4091,
                    'Buffer': 32768
                },
                'ScreenBroadcast': {
                    'IP': '225.2.2.21',
                    'Port': 4092,
                    'Buffer': 65500,
                    'Quality': 60
                },
                'RemoteSpy': {
                    'Port': 4093
                },
                'FileServer': {
                    'Port': 4096
                },
            },
            'Login': {
                'Username': 'admin',
                'Password': '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92'
            },
            'Client': {
                'FileUploadPath': '',
                'ClientLabel': {

                },
                'AvailableRemoteCommands': {
                    '关机(Window)': 'shutdown -s -t 0',
                    '关机(OSX)': "osascript -e 'tell app \"System Events\" to shut down'",
                    '关机(Linux)': 'sudo poweroff',
                    '打开计算器(Windows)': 'calc'
                }
            }
        }
        self.__default_tree = []
        self.init_all()

    def get_item(self, path, default=None):
        # 优先从数据库读取
        value = self.db.get(str(path))
        if value is not None:
            return value
        # 如果数据库中没有，尝试从 QSettings 读取（向后兼容）
        value = self.settings.value(str(path), default)
        # 如果 QSettings 中有值，迁移到数据库
        if value is not None and value != default:
            self.db.set(str(path), value)
        return value

    def get_all(self, path, default=None):
        items = {}
        self.settings.beginGroup(str(path))
        for key in self.settings.allKeys():
            items[key] = self.settings.value(key, default)
        self.settings.endGroup()
        return items

    def save(self, path, value, sync=True):
        # 同时保存到数据库和 QSettings（向后兼容）
        self.db.set(str(path), value)
        self.settings.setValue(str(path), value)
        if sync:
            self.settings.sync()

    def remove(self, path, sync=True):
        self.settings.remove(str(path))
        if sync:
            self.settings.sync()

    def first_run(self):
        return self.get_item('FirstRun') is None

    def __generate_default_tree(self, current, path_list=None):
        if path_list is None:
            path_list = []
        if type(current) != dict:
            self.__default_tree.append(('/'.join(path_list), current))
            return
        for key, value in current.items():
            self.__generate_default_tree(value, path_list + [str(key)])

    def init_all(self):
        # 检查数据库是否已初始化
        first_run = self.db.get('FirstRun')
        if first_run is None:
            # 首次运行，初始化默认配置到数据库
            self.__default_tree.clear()
            self.__generate_default_tree(self.__default_config)
            for key, value in self.__default_tree:
                self.db.set(key, value)
            # 标记已初始化
            self.db.set('FirstRun', False)
        
        # 保持 QSettings 的向后兼容性
        if self.first_run():
            self.__default_tree.clear()
            self.__generate_default_tree(self.__default_config)
            for key, value in self.__default_tree:
                self.settings.setValue(key, value)
            self.settings.sync()
