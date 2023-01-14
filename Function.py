#! /usr/bin/env python
# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         function.py
# Author:       Xilyfe
# Date:         2023/1/2
# Description:  
# -------------------------------------------------------------------------------
import pymem
import ctypes
from pymem.ptypes import RemotePointer
from Struct import RECT
from Libs import WINDOWS_LIBRARY

init_Library = WINDOWS_LIBRARY()


def FindWindowPid(className, windowName):
    '''
    :func: 通过窗口取进程id
    :param className: 类名称
    :param windowName: 窗口名称
    :return: 列表 [窗口句柄, 线程id, 进程id]
    '''
    hwnd = init_Library.findWindow(className, windowName)
    pid = ctypes.wintypes.DWORD()
    thre = init_Library.getThreadProcessId(hwnd, ctypes.byref(pid))
    return (hwnd, thre, pid.value)


def GetWinRect(hwnd):
    '''
    :func: 通过句柄去窗口大小
    :param hwnd: 句柄
    :return: 列表 [左边界, 上边界, 右边界, 下边界]
    '''
    try:
        f = ctypes.windll.dwmapi.DwmGetWindowAttribute
    except WindowsError:
        f = None
    if f:
        rect = ctypes.wintypes.RECT()
        f(ctypes.wintypes.HWND(hwnd), ctypes.wintypes.DWORD(9), ctypes.byref(rect), ctypes.sizeof(rect))
        return rect.left, rect.top, rect.right, rect.bottom


class WinTool():
    def __init__(self, name):
        '''
        :param game: 进程名
        '''
        self.Game = pymem.Pymem(name)

    def Get_moduladdr(self, dll):
        '''
        :func: 通过dll名称获取dll在窗口的内存地址
        :param dll: dll名称
        :return: dll内存地址
        '''
        modules = list(self.Game.list_modules())
        for module in modules:
            if module.name == dll:
                return module.lpBaseOfDll

    def GetPointerAddress(self, base, offsets):
        '''
        :param base: 内存基址
        :param offsets: 偏移列表
        :return: 内存地址
        '''
        remote_pointer = RemotePointer(self.Game.process_handle, base)
        for offset in offsets:
            if offset != offsets[-1]:
                remote_pointer = RemotePointer(self.Game.process_handle, remote_pointer.value + offset)
            else:
                return remote_pointer.value + offset