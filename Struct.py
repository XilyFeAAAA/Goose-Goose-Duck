#! /usr/bin/env python
# -*- coding: utf-8 -*-#

# -------------------------------------------------------------------------------
# Name:         struct.py
# Author:       Xilyfe
# Date:         2023/1/2
# Description:  
# -------------------------------------------------------------------------------
import ctypes as _ctype

class RECT(_ctype.Structure):
    _fields_ = [
        ('Left', _ctype.c_long),
        ('Top', _ctype.c_long),
        ('Right', _ctype.c_long),
        ('Bottom', _ctype.c_long)]

class Player:
    def __init__(self, x, y, state):
        self.x = x
        self.y = y
        self.state = state