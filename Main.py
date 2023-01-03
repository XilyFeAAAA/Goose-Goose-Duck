# Import module
import math
import threading
from Struct import Player
from D3Gui import ExecDraw
from Function import WinTool, GetWinRect, FindWindowPid
from tkinter import *
from tkinter import ttk


class Application(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.master.geometry('150x200')
        self.master.config(bg='white')
        self.wintool = WinTool("goose goose duck")
        self.addr = self.wintool.GetPointerAddress(self.wintool.Get_moduladdr('UnityPlayer.dll')
                                                   + 0x01ACA7C0, offsets=[0x48, 0x370, 0x10, 0x60, 0x2C])
        self.times = 134.667
        ###
        self.tp_btn = Button(self.master, text="TP", width=8, command=self.TP, bg="white")
        self.tp_btn.place(x=80, y=27)
        self.combobox1 = ttk.Combobox(self.master, state="readonly", width=7, values=[i for i in range(16)])
        self.combobox1.place(x=0, y=30)
        self._init_pygame()

    def _update_screen(self):
        '''
        func: 更新屏幕信息
        :return: None
        '''
        self.times = 0.1247 * self.draw.Height
        self.box_width = self.draw.Width / 20
        self.box_height = self.draw.Height / 6
        Window_Mid_X, Window_Mid_Y, FullScreen = self.draw.Get_Window_Mid(self.draw.Width, self.draw.Height)
        self.p_x = Window_Mid_X - self.box_width / 2
        self.p_y = Window_Mid_Y - self.box_height / 2 + self.draw.Height * 0.0324 # 人物中心到 屏幕中心距离
        if not FullScreen: self.p_y += 30 #未全屏加白条

    def _update(self):
        '''
        func: 更新player_list信息
        :return:
        '''
        self._update_screen()
        #self.draw.drawRect(self.p_x, self.p_y, self.box_width, self.box_height, 1, (255, 255, 0))
        for i in range(1, 16):
            player = self._cal(i)
            if player.state != 58: continue
            self.draw.drawRect(self.p_x + player.x, self.p_y - player.y,
                               self.box_width, self.box_height, 1, (255, 255, 255))
            self.draw.drawLine(self.p_x, self.p_y, self.p_x + player.x, self.p_y - player.y, 1, (255, 255, 255))

    def Read_Player_Memory(self, i):
        '''
        :param i: 玩家编号
        :return: (x, y)
        '''
        x = self.wintool.Game.read_float(self.addr + i * 0xE0)
        y = self.wintool.Game.read_float(self.addr + i * 0xE0 + 0x4)
        state = self.wintool.Game.read_int(self.addr + i * 0xE0 - 0x28)
        return Player(x, y, state)

    def _cal(self, i):
        '''
        :param i: 对方id
        :return: x和y坐标偏移值
        '''
        loc = self.Read_Player_Memory(0)
        enemy = self.Read_Player_Memory(i)
        d_x, d_y = enemy.x - loc.x, enemy.y - loc.y
        return Player(d_x * self.times, d_y * self.times, enemy.state)

    def TP(self):
        x2 = self.wintool.Game.read_float(self.addr + int(self.combobox1.get()) * 0xE0)
        y2 = self.wintool.Game.read_float(self.addr + int(self.combobox1.get()) * 0xE0 + 0x4)
        self.wintool.Game.write_float(self.addr, x2)
        self.wintool.Game.write_float(self.addr + 0x4, y2)

    def _init_pygame(self):
        hwnd = FindWindowPid(None, "Goose Goose Duck")[0]
        self.draw = ExecDraw(hwnd)
        self.Draw_thread = threading.Thread(target=self._GameLoop, daemon=True)
        self.Draw_thread.start()

    def _GameLoop(self):
        while True:
            self.draw.startLoop()
            self._update()
            self.draw.endLoop()


if __name__ == "__main__":
    root = Tk()
    root.resizable(False, False)
    app = Application(master=root)
    root.mainloop()
