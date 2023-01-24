# Import module
import math
import threading
import time
import os
import pymem.exception
import win32api, win32con
from D3Gui import ExecDraw
from Function import WinTool, GetWinRect, FindWindowPid
from tkinter import *
from tkinter import ttk, messagebox
from pynput import keyboard

countdown = 3
while countdown:
    try:
        wintool = WinTool("goose goose duck")
        break
    except pymem.exception.ProcessNotFound:
        time.sleep(5)
        countdown -=1
    except pymem.exception.CouldNotOpenProcess:
        win32api.MessageBox(0, "请以管理员身份运行", "Goose Goose Duck辅助", win32con.MB_OK)
        os._exit(0)

if not countdown:
    win32api.MessageBox(0, "未找到游戏，程序退出", "Goose Goose Duck辅助", win32con.MB_OK)
    os._exit(0)

class Player:
    def __init__(self, player_num: int):
        """
        func: 玩家类
        :param player_num: 玩家序号
        """
        self.player_num = player_num
        self.Unity_addr = wintool.GetPointerAddress(wintool.Get_moduladdr('UnityPlayer.dll')
                                                    + 0x01ACA7C0, offsets=[0x48, 0x370, 0x10, 0x60, 0x2C])
        try:
            self.GameAssembly_addr = wintool.GetPointerAddress(wintool.Get_moduladdr('GameAssembly.dll')
                                                           + 0x3C98478, offsets=[0xb8, 0x20, 0x18, 0x30 + self.player_num * 0x18, 0])
        except:
            self.GameAssembly_addr = 0
        self.valid = False  # 是否有效
        self.x = None  # x
        self.y = None  # y
        self.color = (255, 255, 0)  # 绘制颜色
        self.eaten = None  # 被吃
        self.isGhost = None  # 灵魂
        self.isInfected = None  # 感染
        self.isSpectator = None  # 观战
        self.killRound = None  # 这轮是否杀人
        self.has_Bomb = None  # 身上有无炸弹
        self.nickname = ""  # 用户名
        self.die_flag = False  # 判断是不是刚刚死
        self.infect_flag = False  # 判断是不是刚刚感染
        self.in_flag = False  # 用来判断用户是不是刚刚离开
        self.wait_update = False  # 是否在等待更新
        self.eaten_flag = False

    def CheckStatus(self):
        """
        func: 等待4秒后监听，重新尝试
        :return:
        """
        time.sleep(5)
        self.GameAssembly_addr = wintool.GetPointerAddress(wintool.Get_moduladdr('GameAssembly.dll')
                                                           + 0x3C98478,
                                                           offsets=[0xb8, 0x20, 0x18, 0x30 + self.player_num * 0x18, 0])
        if app.inGame: self.Update()

    def GetNickName(self):
        """
        func: 获取用户名
        :return:
        """
        name = ""
        try:
            nickname_addr = wintool.GetPointerAddress(wintool.Get_moduladdr('GameAssembly.dll')
                                                      + 0x3C98478,
                                                      offsets=[0xb8, 0x20, 0x18, 0x30 + self.player_num * 0x18, 0x1E0,
                                                               0])
            lens = wintool.Game.read_int(nickname_addr + 0x10)
            name_hex = wintool.Game.read_bytes(nickname_addr + 0x14, 2 * lens).hex()
            for i in range(0, len(name_hex) - 1, 4):
                name += chr(int(name_hex[i + 2:i + 4] + name_hex[i:i + 2], 16))
            self.nickname = name
        except:
            pass
            #print(f"[{self.player_num}]名字获取错误")


    def Update(self):
        """
        note: 目前策略是通过try...except...来判断用户是否存在，如果不存在，则启动一个线程监听
        4s后再次判断，如果不存在如上继续监听
        :return:
        """
        try:
            self.x = wintool.Game.read_float(self.GameAssembly_addr + 0x2D8)
            self.y = wintool.Game.read_float(self.GameAssembly_addr + 0x2D8 + 0x4)
            self.eaten = wintool.Game.read_int(self.GameAssembly_addr + 0x404)
            self.isGhost = wintool.Game.read_int(self.GameAssembly_addr + 0x198)
            self.isInfected = wintool.Game.read_int(self.GameAssembly_addr + 0xD3)
            self.isSpectator = wintool.Game.read_int(self.GameAssembly_addr + 0x38A)
            self.has_Bomb = wintool.Game.read_int(self.GameAssembly_addr + 0x144)
            self.valid = True
            self.wait_update = False
            if not self.in_flag:  # key为真，则刚刚加入，初始化名字
                self.GetNickName()
                self.in_flag = True
                #print(f"用户{self.nickname} 加入")
            #print(f"序号:{self.player_num} 名字{self.nickname} 幽灵{self.isGhost} 旁观{self.isSpectator} 杀人{self.killRound}\n x{self.x} y{self.y}")
        except pymem.exception.MemoryReadError:
            #print(f"玩家{self.player_num}搜索错误，4秒后重新加载")
            self.valid = False
            self.wait_update = True  # 进入等待更新
            self.in_flag = False  # 退出key为True
            threading.Thread(target=self.CheckStatus).start()

class Application(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.master.geometry('150x20+100+100')
        self.master.config(bg='white')
        self.master.protocol('WM_DELETE_WINDOW', self._Destory)
        self.master.attributes('-topmost', True)
        self.master.attributes("-alpha", 0.8)
        ###
        self.player_list = []
        self.draw = ExecDraw(FindWindowPid(None, "Goose Goose Duck")[0])  # 启动PyGame
        self.board = []  # 信息列表
        self.infect_num = 0  # 被感染人数
        self.draw_state = BooleanVar(False)  # PyGame绘制标志
        self.cd_state = BooleanVar(False)  # CD标志
        self.speed = DoubleVar(value=5.0)
        self.through_state = IntVar(value=1)  # 穿墙状态
        self.record_state = BooleanVar(False)  # 记录信息标志
        self.mist_state = IntVar(value=1)  # 迷雾标志
        self.color = (255, 51, 0)  # 绘制颜色
        ###
        self.inGame = False  # 是否在游戏
        ###
        ttk.Separator(self.master, orient=HORIZONTAL).place(x=0, y=19, relwidth=150)
        Scale(self.master, from_=5.0, to=15.0, variable=self.speed, length=150, resolution=1.0 ,orient=HORIZONTAL,
              command=self.ChangeSpeed).place(x=0, y=125)
        self.btn_label = Label(self.master, text="▼", font=("Arial",12),background="white")
        self.btn_label.place(x=120, y=-5)
        self.btn_label.bind("<Button-1>", self.Stretch)
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
        threading.Thread(target=self.Monitor_Thread, daemon=True).start()  # 开始监控线程
        threading.Thread(target=self.Pygame_Thread, daemon=True).start()  # 开始PyGame线程
        self.listen_key_nblock()  # 开始键盘监听

    def Stretch(self, events):
        if self.master.winfo_height() == 20:
            self.master.geometry('150x170+100+100')
        else:
            self.master.geometry('150x20+100+100')

    def Mist(self):
        """
        func：除迷雾
        :return:
        """
        try:
            mist_addr = wintool.GetPointerAddress(wintool.Get_moduladdr('GameAssembly.dll')
                                                       + 0x3C98478,
                                                       offsets=[0xb8, 0x20, 0x18, 0x30, 0x389])
            wintool.Game.write_int(mist_addr, self.mist_state.get())
        except:
            messagebox.showerror(message="请检查是否进入游戏")
            self.mist_state.set(1)

    def Cd_Rewrite(self):
        """
        func: 复写无cd
        :return:
        """
        messagebox.showwarning(message="cd待完善")
        # cd_addr = wintool.GetPointerAddress(wintool.Get_moduladdr('GameAssembly.dll')
        #                                     + 0x3D690C0,
        #                                     offsets=[0x1580, 0x20, 0x150, 0x28, 0x70])
        # while self.cd_state.get():
        #     # 读内存比写内存占用小
        #     if wintool.Game.read_float(cd_addr) != 0:
        #         wintool.Game.write_float(cd_addr, 0.0)

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
            if player == self.player_list[0] or not player.valid or player.isSpectator or player.eaten:  # 人物无效(观战、被吃)则跳过
                continue
            #print(f"[{player.player_num}] {player.nickname} {player.x} {player.y}")
            d_x, d_y = self.times * (player.x - self.player_list[0].x), self.times * (player.y - self.player_list[0].y)
            self.draw.drawRect(self.p_x + d_x, self.p_y - d_y,
                               self.box_width, self.box_height, 1, player.color)  # 绘制人物方框
            self.draw.drawLine(self.p_x, self.p_y, self.p_x + d_x, self.p_y - d_y, 1, player.color)  # 绘制人物连线
            self.draw.drawText(player.nickname, 18, self.p_x + d_x, self.p_y - d_y - 20, player.color)

    def Info_output(self):
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
                        if not (j.isGhost or j.isSpectator or j.eaten) and j.valid and i != j:
                            distance_list.append((self.Calculation(i.x, i.y, j.x, j.y), j.nickname))
                    distance_list.sort(key=lambda x: x[0])
                    self.board.append(
                        f"玩家:{i.nickname}死亡, 附近有{distance_list[0][1]}{round(distance_list[0][0], 2)}米, {distance_list[1][1]}{round(distance_list[1][0], 2)}米")
                elif i.eaten and not i.eaten_flag:  # 刚刚被吃
                    i.eaten_flag = True
                    distance_list = []
                    for j in self.player_list:
                        if not (j.isGhost or j.isSpectator or j.eaten) and j.valid and i != j:
                            distance_list.append((self.Calculation(i.x, i.y, j.x, j.y), j.nickname))
                    distance_list.sort(key=lambda x: x[0])
                    self.board.append(
                        f"玩家:{i.nickname}被吃, 附近有{distance_list[0][1]}{round(distance_list[0][0], 2)}米")
                elif i.isInfected and not i.infect_flag:  # 刚刚被感染
                    self.infect_num += 1
                    self.board.append(f"玩家:{i.nickname}被感染，总计{self.infect_num}人")
                    i.infect_flag = True
        for i in range(len(self.board)):
            self.draw.drawText(self.board[i], 14, 0, i * 18 + 100, (255, 255, 0))

    def Calculation(self, x1, y1, x2, y2):
        """
        func: 勾股距离计算
        :return:
        """
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def Through(self):
        """
        func: 穿墙
        :return:
        """
        try:
            through_addr = wintool.GetPointerAddress(wintool.Get_moduladdr('GameAssembly.dll')
                                                          + 0x3C98478,
                                                          offsets=[0xb8, 0x20, 0x18, 0x30, 0xa8, 0x30, 0x39])

            wintool.Game.write_int(through_addr, self.through_state.get())
        except:
            messagebox.showerror(message="请检查是否进入游戏")
            self.through_state.set(1)

    def ChangeSpeed(self, value):
        speed_addr = wintool.GetPointerAddress(wintool.Get_moduladdr('GameAssembly.dll')
                                                    + 0x3C6B510,
                                                    offsets=[0xb8, 0x0, 0x0, 0xb8, 0x10])
        #print(self.speed.get())
        wintool.Game.write_float(speed_addr, self.speed.get())

    def Pygame_Thread(self):
        """
        func: pygame主循环
        :return:
        """
        while True:
            for player in self.player_list:
                if not player.wait_update:
                    player.Update()  # 更新人物信息
            self.draw.startLoop()
            self.draw.drawText("请在每局游戏开始按F2初始化", 16, 5, 40, (255, 255, 0))
            if self.record_state.get(): self.Info_output()  # 信息记录
            if self.draw_state.get():  self.Update()  # 绘制
            self.draw.endLoop()

    def Monitor_Thread(self):
        while True:
            try:
                self.isPlayerRoleSet = wintool.GetPointerAddress(wintool.Get_moduladdr('GameAssembly.dll')
                                                           + 0x3C98478, offsets=[0xb8, 0x20, 0x18, 0x30, 0x100])
                break
            except pymem.exception.WinAPIError:
                time.sleep(2)

        while True:
            state = wintool.Game.read_int(self.isPlayerRoleSet)
            if state and not self.inGame:  # 刚刚进游戏
                self.inGame = True
                self.Reset()
                #print("游戏开始")
            elif not state and self.inGame:  # 刚刚退出
                self.inGame = False
                self.record_state.set(False)
                self.draw_state.set(False)
                self.player_list = []
                #print("游戏结束")
            time.sleep(4)

    def Reset(self):
        self.player_list = [Player(i) for i in range(16)]
        self.infect_num = 0
        self.board.clear()

    def on_press(self, key):
        """定义按下时候的响应，参数传入key"""
        if key == keyboard.Key.f2:
            try:
                self.Reset()  # 重置
            except:
                messagebox.showwarning(message="请在进入游戏后按F2初始化")

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
    #root.overrideredirect(True)
    app = Application(master=root)
    root.mainloop()
