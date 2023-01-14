#! /usr/bin/env python
# -*- coding: utf-8 -*-#

# -------------------------------------------------------------------------------
# Name:         D3Gui.py
# Author:       Xilyfe
# Date:         2023/1/2
# Description:
# -------------------------------------------------------------------------------
import sys
import pygame
import ctypes
import win32gui
import win32api
import win32con
from Function import GetWinRect,FindWindowPid,init_Library

class ExecDraw():
    def __init__(self, hwnd):
        pygame.init()
        self.firstHwnd = hwnd
        self.Timer = pygame.time.Clock()
        pygame.mouse.set_visible(False)
        pygame.display.set_caption('D3Gui')
        left, top, right, bottom = GetWinRect(self.firstHwnd)
        self.Width, self.Height = right - left, bottom - top
        print(f"{self.Width} {self.Height}")
        self.screen = pygame.display.set_mode([self.Width, self.Height], pygame.NOFRAME)
        self.hwnd = FindWindowPid('pygame', 'D3Gui')[0]
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, left, top, self.Width, self.Height, win32con.SWP_NOSIZE)
        ctypes.windll.user32.SetWindowLongA(self.hwnd, win32con.GWL_EXSTYLE,
                                            win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)  # 设置窗口穿透
        flag = ctypes.windll.user32.SetLayeredWindowAttributes(self.hwnd, 0, 0, 1)
        pygame.display.flip()

    def drawText(self, text, size, x, y, color):
        '''
        :func: 绘制文字
        :param text: 内容
        :param size: 文字大小
        :param x: 横坐标
        :param y: 纵坐标
        :param color: RGB 颜色 如: (255, 0, 0)
        :return:
        '''
        textFont = pygame.font.SysFont('simhei', size)
        text_fmt = textFont.render(text, True, color)
        self.screen.blit(text_fmt,(x,y))

    def drawRect(self, x, y, width, height, c, color):
        '''
        :func: 绘制矩形
        :param x: 横坐标
        :param y: 纵坐标
        :param width: 宽度
        :param height: 高度
        :param c: 粗细
        :param color: RGB 颜色
        :return:
        '''
        pygame.draw.rect(self.screen, color, (x, y, width, height), c)

    def drawLine(self,startX,startY, endX, endY, width, color):
        '''
        :func: 绘制直线
        :param startX: 开始x坐标
        :param startY: 开始y坐标
        :param endX: 结束x坐标
        :param endY: 结束y坐标
        :param width: 粗细
        :param color: RGB 颜色
        :return:
        '''
        pygame.draw.line(self.screen, color, (startX,startY),(endX,endY), width)

    def drawCircle(self,x, y, c, color):
        '''
        :func: 绘制圆
        :param x: 横坐标
        :param y: 纵坐标
        :param c: 粗细
        :param color: RGB 颜色
        :return:
        '''
        pygame.draw.circle(self.screen, color, (x, y), c)

    def Get_Window_Mid(self, Width, Height):
        '''
        func:返回屏幕中心坐标
        :param Width: 宽
        :param Height: 高
        :return: 中心坐标, 是否全屏
        '''
        if Width == 1920 and Height == 1080:
            return Width / 2, Height / 2, True
        else:
            return (Width - 2) / 2, (Height - 39) / 2, False

    def clear(self):
        pygame.quit()

    def startLoop(self):
        '''
        :func: 开始 (必须)
        :return:
        '''
        pygame.time.Clock().tick(30)
        self.screen.fill((0, 0, 0))
        left, top, right, bottom = GetWinRect(self.firstHwnd)
        self.Width, self.Height = right - left, bottom - top
        if not any([left, top, right, bottom]):
            sys.exit('进程不存在，已安全退出！')
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, left, top, self.Width, self.Height, win32con.SWP_NOSIZE)

    def endLoop(self):
        '''
        :func: 结束 (必须)
        :return:
        '''
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()