import os
from vxi11 import vxi11
import sys
import time
from USBTMC import USBTMC
from PyQt5.QtCore import QIODevice
from PyQt5 import QtSerialPort

class Device:
    def __init__(self):
        super(Device, self).__init__(self)
        self.name = None
        self.IDN = None
        self.path = None
        self.type = None # 0,1,2 - for com, tcp or usb connection
        self.delay = None
        self.commands = []
        self.init_commands = []
        self.experiment_commands = []
        self.end_commands = []
        self._device = None

    def write(self, cmd):
        pass

    def read(self, length = 4000):
        pass

    def ask(self, cmd, length = 4000, delay = 1):
        pass

    def get_idn(self):
        pass

    def close(self):
        pass

    def set_cmds(self, cmds):
        pass

    def set_init_cmds(self, cmds):
        pass

    def set_exp_cmds(self, cmds):
        pass

    def set_end_cmds(self, cmds):
        pass

    def set_device_type(self, c):
        pass

    def set_device_path(self, node):
        pass