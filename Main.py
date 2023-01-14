# Import module
import math
import threading
import time
from typing import Union, Any
from D3Gui import ExecDraw
from Function import WinTool, GetWinRect, FindWindowPid
from tkinter import *
from tkinter import ttk, messagebox
from pynput import keyboard


wintool = WinTool("goose goose duck")


class Player:
    def __init__(self, player_num: int):
        """
        func: 玩家类
        :param player_num: 玩家序号
        """
        self.player_num = player_num
        self.GameAssembly_addr = wintool.GetPointerAddress(wintool.Get_moduladdr('GameAssembly.dll')
                                                           + 0x3D97140,
                                                           offsets=[0xb8, 0x20, 0x18, 0x30 + self.player_num * 0x18, 0])
        self.Unity_addr = wintool.GetPointerAddress(wintool.Get_moduladdr('UnityPlayer.dll')
                                                    + 0x01ACA7C0, offsets=[0x48, 0x370, 0x10, 0x60, 0x2C])
        self.valid = None  # 是否有效
        self.x = None  # x
        self.y = None  # y
        self.color = (255, 255, 0)  # 绘制颜色
        self.eaten = None  # 被吃
        self.isGhost = None  # 灵魂
        self.isSpectator = None  # 观战
        self.killRound = None  # 这轮是否杀人
        self.has_Bomb = None  # 身上有无炸弹
        self.nickname = ""  # 用户名
        self.die_flag = False  # 判断是不是刚刚死
        self.in_flag = True  # 用来判断用户是不是刚刚离开

    def GetNickName(self):
        """
        func: 获取用户名
        :return:
        """
        name = ""
        try:
            nickname_addr = wintool.GetPointerAddress(wintool.Get_moduladdr('GameAssembly.dll')
                                                      + 0x3D97140,
                                                      offsets=[0xb8, 0x20, 0x18, 0x30 + self.player_num * 0x18, 0x1D0,
                                                               0])
            lens = wintool.Game.read_int(nickname_addr + 0x10)
            name_hex = wintool.Game.read_bytes(nickname_addr + 0x14, 2 * lens).hex()
            for i in range(0, len(name_hex) - 1, 4):
                name += chr(int(name_hex[i + 2:i + 4] + name_hex[i:i + 2], 16))
            self.nickname = name
        except:
            print("名字获取错误")

    def update(self):
        self.valid = wintool.Game.read_int(self.Unity_addr + self.player_num * 0xE0 - 0x28) == 58  # 58则是有人
        if self.valid:
            try:
                if self.in_flag:  # key为真，则刚刚加入，初始化名字
                    self.GetNickName()
                    self.in_flag = False
                    # print(f"用户{self.nickname} 加入")
                self.x = wintool.Game.read_float(self.GameAssembly_addr + 0x2C8)
                self.y = wintool.Game.read_float(self.GameAssembly_addr + 0x2C8 + 0x4)
                self.isGhost = wintool.Game.read_int(self.GameAssembly_addr + 0x188)
                self.isSpectator = wintool.Game.read_int(self.GameAssembly_addr + 0x37A)
                self.killRound = wintool.Game.read_int(self.GameAssembly_addr + 0x2EC)
                self.has_Bomb = wintool.Game.read_int(self.GameAssembly_addr + 0x134)
                # print(f"序号:{self.player_num} 名字{self.nickname} 幽灵{self.isGhost} 旁观{self.isSpectator} 杀人{self.killRound}\n x{self.x} y{self.y}")
            except:
                print(f"序号{self.player_num} 读取错误")
        elif not self.in_flag:
            self.in_flag = True  # 退出key为True
            # print(f"用户{self.nickname} 退出")


class Application(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.master.geometry('150x200')
        self.master.config(bg='white')
        self.master.protocol('WM_DELETE_WINDOW', self._Destory)
        ###
        self.player_list = []
        self.draw = ExecDraw(FindWindowPid(None, "Goose Goose Duck")[0])  # 启动PyGame
        self.board = []  # 信息列表
        self.draw_state = BooleanVar(False)  # PyGame绘制标志
        self.cd_state = BooleanVar(False)  # CD标志
        self.speed = 5.0  # 人物速度
        self.through_state = IntVar(value=1)  # 穿墙状态
        self.record_state = BooleanVar(False)  # 记录信息标志
        self.mist_state = IntVar(value=1)  # 迷雾标志
        self.color = (255, 51, 0)  # 绘制颜色
        self.die_flag = False  # 记录是否刚刚死亡
        ###
        Button(self.master, text="TP", width=8, command=self.TP, bg="white").place(x=80, y=160)
        self.combobox = ttk.Combobox(self.master, state="readonly", width=7, postcommand=self.ChangeCombobox)
        self.combobox.place(x=1, y=165)
        Checkbutton(
            self.master, text="无迷雾", background="white", activebackground="white", font=("Arial", 10),
            onvalue=0, offvalue=1, variable=self.mist_state, command=self.Mist).place(x=0, y=20)
        Checkbutton(
            self.master, text="记录信息", background="white", activebackground="white", font=("Arial", 10),
            variable=self.record_state).place(x=0, y=40)
        Checkbutton(
            self.master, text="方框透视", background="white", activebackground="white", font=("Arial", 10),
            variable=self.draw_state).place(x=0, y=60)
        Checkbutton(
            self.master, text="技能无cd", background="white", activebackground="white", font=("Arial", 10),
            variable=self.cd_state,
            command=lambda: threading.Thread(target=self.Cd_Rewrite).start()).place(x=0, y=80)
        Checkbutton(
            self.master, text="穿墙", background="white", activebackground="white", font=("Arial", 10),
            onvalue=0, offvalue=1, variable=self.through_state, command=self.Through).place(x=0, y=100)

        threading.Thread(target=self.Pygame_Thread, daemon=True).start()  # 开始PyGame线程
        self.listen_key_nblock()  # 开始键盘监听

    def Mist(self):
        """
        func：除迷雾
        :return:
        """
        wintool.Game.write_bytes(self.mist_addr, self.mist_state.get())

    def Cd_Rewrite(self):
        """
        func: 复写无cd
        :return:
        """
        while self.cd_state.get():
            # 读内存比写内存占用小
            if wintool.Game.read_float(self.cd_addr) != 0:
                wintool.Game.write_float(self.cd_addr, 0.0)

    def ChangeCombobox(self):
        """
        func: 动态改变combobox内容
        :return:
        """
        name_list = []
        for i in self.player_list:
            if i.valid: name_list.append(i.nickname)
        self.combobox['value'] = name_list

    def _Destory(self):
        """
        func: 程序关闭
        :return:
        """
        self.draw.clear()  # 结束PyGame
        self.master.destroy()  # 关闭应用

    def Update_screen(self):
        """
        func: 更新屏幕信息
        :return: None
        """
        self.box_width = self.draw.Width / 20  # 人物方框宽度
        self.box_height = self.draw.Height / 6  # 人物方框高度
        Window_Mid_X, Window_Mid_Y, FullScreen = self.draw.Get_Window_Mid(self.draw.Width,
                                                                          self.draw.Height)  # 游戏中心x和y坐标，是否全屏
        self.times = 0.2494 * Window_Mid_Y  # 游戏距离与屏幕比例
        self.p_x = Window_Mid_X - self.box_width / 2  # 我的x坐标
        self.p_y = Window_Mid_Y - self.box_height / 2 + self.draw.Height * 0.0324  # 人物中心到 屏幕中心距离
        if not FullScreen: self.p_y += 30  # 未全屏加白条

    def Update(self):
        """
        func: 绘制方框和连线
        :return:
        """
        self.Update_screen()  # 更新屏幕信息
        for player in self.player_list:
            if player == self.player_list[0] or not player.valid or player.isSpectator:  # 人物无效(观战、幽灵)则跳过
                continue
            d_x, d_y = self.times * (player.x - self.player_list[0].x), self.times * (player.y - self.player_list[0].y)
            self.draw.drawText(player.nickname, 18, self.p_x + d_x, self.p_y - d_y - 20, player.color)
            self.draw.drawRect(self.p_x + d_x, self.p_y - d_y,
                               self.box_width, self.box_height, 1, player.color)  # 绘制人物方框
            self.draw.drawLine(self.p_x, self.p_y, self.p_x + d_x, self.p_y - d_y, 1, player.color)  # 绘制人物连线

    def Die_info_output(self):
        """
        func: 死亡信息输出
        :return:
        """
        for i in self.player_list:
            if i.valid:
                if i.isGhost and not i.die_flag:  # 刚刚死
                    i.color = (128, 128, 128)
                    i.die_flag = True
                    distance_list = []
                    for j in self.player_list:
                        if not (j.isGhost and j.isSpectator) and j.valid and i != j:
                            distance_list.append((self.Calculation(i.x, i.y, j.x, j.y), j.nickname))
                    distance_list.sort(key=lambda x: x[0])
                    self.board.append(
                        f"玩家:{i.nickname}死亡, 附近有{distance_list[0][1]}{round(distance_list[0][0], 2)}米, {distance_list[1][1]}{round(distance_list[1][0], 2)}米")
        for i in range(len(self.board)):
            self.draw.drawText(self.board[i], 14, 0, i * 18 + 150, (255, 255, 0))

    def Calculation(self, x1, y1, x2, y2):
        """
        func: 勾股距离计算
        :return:
        """
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def TP(self):
        """
        func: 传送
        :return:
        """
        x_addr = self.player_list[0].Unity_addr
        y_addr = self.player_list[0].Unity_addr + 0x4
        wintool.Game.write_float(x_addr, self.player_list[int(self.combobox.current())].x)
        wintool.Game.write_float(y_addr, self.player_list[int(self.combobox.current())].y)

    def Through(self):
        """
        func: 穿墙
        :return:
        """
        wintool.Game.write_int(self.through_addr, self.through_state.get())

    def Pygame_Thread(self):
        """
        func: pygame主循环
        :return:
        """
        while True:
            for player in self.player_list:
                player.update()  # 更新人物信息
            self.draw.startLoop()
            self.draw.drawText("请在进入游戏后按F2初始化游戏", 16, 5, 40, (255, 255, 0))
            if self.record_state.get(): self.Die_info_output()  # 信息记录
            if self.draw_state.get():  self.Update()  # 绘制
            self.draw.endLoop()

    def on_press(self, key):
        """定义按下时候的响应，参数传入key"""
        if key == keyboard.Key.f2:
            try:
                self.through_addr = wintool.GetPointerAddress(wintool.Get_moduladdr('GameAssembly.dll')
                                                              + 0x3D97140,
                                                              offsets=[0xb8, 0x20, 0x18, 0x30, 0xa8, 0x30, 0x39])
                self.mist_addr = wintool.GetPointerAddress(wintool.Get_moduladdr('GameAssembly.dll')
                                                           + 0x3D97140,
                                                           offsets=[0xb8, 0x20, 0x18, 0x30, 0xa8, 0x30, 0x379])
                self.speed_addr = wintool.GetPointerAddress(wintool.Get_moduladdr('GameAssembly.dll')
                                                           + 0x3D69DF0,
                                                           offsets=[0xb8, 0x0, 0x0, 0xb8, 0x10])
                self.cd_addr = wintool.GetPointerAddress(wintool.Get_moduladdr('GameAssembly.dll')
                                                           + 0x3D690C0,
                                                           offsets=[0x1580,0x20, 0x150, 0x28, 0x70])
                self.player_list = [Player(i) for i in range(16)]
                self.die_flag = False
                self.board.clear()
            except Exception as e:
                messagebox.showwarning(message="请在进入游戏后按F2初始化")

        elif key == keyboard.Key.page_up:
            self.speed += 1
            wintool.Game.write_float(self.speed_addr, self.speed)

        elif key == keyboard.Key.page_down:
            self.speed = max(5.0, self.speed - 1.0)
            wintool.Game.write_float(self.speed_addr, self.speed)

    def listen_key_nblock(self):
        """
        func: 监听键盘事件
        :return:
        """
        listener = keyboard.Listener(
            on_press=self.on_press)
        listener.start()  # 启动线程


if __name__ == "__main__":
    root = Tk()
    root.resizable(False, False)
    app = Application(master=root)
    root.mainloop()
