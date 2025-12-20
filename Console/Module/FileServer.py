# -*- coding: utf-8 -*-

from Module.FTPLib.authorizers import DummyAuthorizer
from Module.FTPLib.handlers import FTPHandler
from Module.FTPLib.servers import FTPServer
import logging


class FileServer(object):
    working = False
    working_path = '.'
    current_ip = None
    ftp_port = None
    ftp_password = None
    authorizer = None
    handler = None
    server = None

    def __init__(self, parent, current_ip, ftp_port):
        self.parent = parent
        self.current_ip = current_ip
        self.ftp_port = ftp_port

    def __init_ftp_server(self):
        self.authorizer = DummyAuthorizer()
        self.authorizer.add_user('pycm', self.ftp_password, self.working_path, perm='elr')
        self.handler = FTPHandler
        self.handler.authorizer = self.authorizer
        self.handler.encoding = 'gbk'
        self.server = FTPServer((self.current_ip, self.ftp_port), self.handler)

    def start(self):
        self.__init_ftp_server()
        self.server.serve_forever()

    def stop(self):
        if self.server is not None:
            self.server.close_all()
        self.authorizer = None
        self.handler = None
        self.server = None
