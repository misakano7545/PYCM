# -*- coding: utf-8 -*-


class NetworkDiscoverFlag(object):
    ConsoleFlag = 1
    ClientFlag = 2


class ClassBroadcastFlag(object):
    Message = 1
    ToggleScreenBroadcast = 2
    ConsoleQuit = 3
    Command = 4
    RemoteSpyStart = 5
    RemoteQuit = 6
    ClientFileReceived = 7
    ToggleFileServer = 8


class PrivateMessageFlag(object):
    ClientLogin = 1
    ClientLogout = 2
    ClientMessage = 3
    ClientScreen = 4
    ClientFileInfo = 5
    ClientFileData = 6
    ClientNotify = 7


class RemoteSpyFlag(object):
    PackInfo = 1
    RemoteSpyStop = 2


class ScreenBroadcastFlag(object):
    PackInfo = 1
    PackData = 2
