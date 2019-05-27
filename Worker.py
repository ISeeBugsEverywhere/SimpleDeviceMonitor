from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QIODevice
from PyQt5 import QtSerialPort
import sys
import os
from vxi11 import vxi11 as vx
import time

class Worker(QObject):
    output = pyqtSignal(int, str)
    errors = pyqtSignal(int, str)
    command = pyqtSignal(str)
    comport = pyqtSignal(str) # weird solution: return cmd to write into comport

    def __init__(self):
        super().__init__()
        self.cmds = None
        self.comDevice = None
        self.tcpDevice = None
        self.usbDevice = None
        self.active_device = 0
        self.active_device_2nd = -1
        self.comEnding = None
        self.delay = 0
        self._require_stop = False
        self.cmds_2nd = None

    def assign_device(self, com=None, tcp=None, usb=None):
        if com is not None:
            self.comDevice = com
        if tcp is not None:
            self.tcpDevice = tcp
        if usb is not None:
            self.usbDevice = usb
            pass
        pass

    def set_active_device(self, dev):
        self.active_device = dev #0,1,2
        pass

    def set_active_device_2nd(self, dev):
        if type(dev) is int:
            self.active_device_2nd = dev
        else:
            if dev == 'usbDevice':
                self.active_device_2nd = 2
            elif dev == 'lxiDevce':
                self.active_device_2nd = 1
            elif dev == 'comDevice':
                self.active_device_2nd = 0
            pass

    def set_com_ending(self, ending='\n'):
        self.comEnding = ending
        pass

    def set_cmds(self, cmds):
        if cmds is not None:
            self.cmds = cmds
        pass

    def set_cmds_2nd(self, cmds):
        if cmds is not None:
            self.cmds_2nd = cmds
        pass

    def set_delay(self, delay=1):
        self.delay = delay
        pass

    def run_first_dev(self):
        # there will be the main code of this thread
        script_delay = 0
        if self.comDevice is not None and self.active_device == 0 and not self._require_stop:
            for i in self.cmds:
                if 'delay' in i:
                    s, d = i.split('=')
                    script_delay = int(d)
                    time.sleep(script_delay)
                    pass
                if not self._require_stop and 'delay' not in i and '//' not in i:
                    self.command.emit(str(i))
                    self.comport.emit(str(i))
                    time.sleep(self.delay)
                pass
            self.command.emit('==END OF SCRIPT==')
        elif self.tcpDevice is not None and self.active_device == 1 and not self._require_stop:
            print('tcp connected?')
            for i in self.cmds:
                if 'delay' in i:
                    s, d = i.split('=')
                    script_delay = int(d)
                    time.sleep(script_delay)
                    pass
                if not self._require_stop and 'delay' not in i and '//' not in i:
                    if '?' in i and not self._require_stop:
                        self.command.emit(str(i))
                        answer = self.tcpDevice.ask(str(i))
                        self.output.emit(1, str(answer))
                        time.sleep(self.delay)
                        pass
                    else:
                        self.command.emit(str(i))
                        self.tcpDevice.write(str(i))
                        # self.output.emit(str(answer))
                        time.sleep(self.delay)
                        pass
                    pass
            self.command.emit('==END OF SCRIPT==')
        elif self.usbDevice is not None and self.active_device == 2 and not self._require_stop:
            print('usb connected?')
            for i in self.cmds:
                if 'delay' in i:
                    s, d = i.split('=')
                    script_delay = int(d)
                    time.sleep(script_delay)
                    pass
                if not self._require_stop and 'delay' not in i and '//' not in i:
                    if '?' in i and not self._require_stop:
                        self.command.emit(str(i))
                        answer = self.usbDevice.ask(str(i))
                        self.output.emit(1, str(answer))
                        time.sleep(self.delay)
                        pass
                    else:
                        self.command.emit(str(i))
                        self.usbDevice.write(str(i))
                        # self.output.emit(str(answer))
                        time.sleep(self.delay)
                        pass
                    pass
            self.command.emit('==END OF SCRIPT==')
        pass

    def run_second_dev(self):
        # there will be the main code of this thread
        script_delay = 0
        if self.comDevice is not None and self.active_device_2nd == 0 and not self._require_stop:
            for i in self.cmds_2nd:
                if 'delay' in i:
                    s, d = i.split('=')
                    script_delay = int(d)
                    time.sleep(script_delay)
                    pass
                if not self._require_stop and 'delay' not in i and '//' not in i:
                    self.command.emit(str(i))
                    self.comport.emit(str(i))
                    time.sleep(self.delay)
                pass
            self.command.emit('==END OF SCRIPT==')
        elif self.tcpDevice is not None and self.active_device_2nd == 1 and not self._require_stop:
            print('tcp connected?')
            for i in self.cmds_2nd:
                if 'delay' in i:
                    s, d = i.split('=')
                    script_delay = int(d)
                    time.sleep(script_delay)
                    pass
                if not self._require_stop and 'delay' not in i and '//' not in i:
                    if '?' in i and not self._require_stop:
                        self.command.emit(str(i))
                        answer = self.tcpDevice.ask(str(i))
                        self.output.emit(1, str(answer))
                        time.sleep(self.delay)
                        pass
                    else:
                        self.command.emit(str(i))
                        self.tcpDevice.write(str(i))
                        # self.output.emit(str(answer))
                        time.sleep(self.delay)
                        pass
                    pass
            self.command.emit('==END OF SCRIPT==')
        elif self.usbDevice is not None and self.active_device_2nd == 2 and not self._require_stop:
            print('usb connected?')
            for i in self.cmds_2nd:
                if 'delay' in i:
                    s, d = i.split('=')
                    script_delay = int(d)
                    time.sleep(script_delay)
                    pass
                if not self._require_stop and 'delay' not in i and '//' not in i:
                    if '?' in i and not self._require_stop:
                        self.command.emit(str(i))
                        answer = self.usbDevice.ask(str(i))
                        self.output.emit(1, str(answer))
                        time.sleep(self.delay)
                        pass
                    else:
                        self.command.emit(str(i))
                        self.usbDevice.write(str(i))
                        # self.output.emit(str(answer))
                        time.sleep(self.delay)
                        pass
                    pass
            self.command.emit('==END OF SCRIPT==')
        pass

    @pyqtSlot()
    def run(self):
        try:
            self.run_first_dev()
            self.run_second_dev()
            pass
        except Exception as ex:
            self.errors.emit(-42, str(ex))
            pass
        finally:
            pass

    @pyqtSlot()
    def stop(self):
        self._require_stop = True
        pass
