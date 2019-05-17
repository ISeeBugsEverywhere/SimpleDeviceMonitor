from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QIODevice
from PyQt5 import QtSerialPort
import sys
import os
from vxi11 import vxi11 as vx
import time

class ExpWorker(QObject):
    output = pyqtSignal(int, str)
    errors = pyqtSignal(int, str)
    command = pyqtSignal(str)
    comport = pyqtSignal(str) # weird solution: return cmd to write into comport
    entry_out = pyqtSignal(str)
    final = pyqtSignal(int, str)

    def __init__(self):
        super().__init__()
        self.cmds = None
        self.comDevice = None
        self.tcpDevice = None
        self.usbDevice = None
        self.active_device = 0
        self.active_device_2nd = -1 # already unset
        self.comEnding = None
        self.delay = 0
        self._require_stop = False
        self._cycle = False
        # parameters of a cycle
        self._counts = 0
        self._from = 0
        self._to = 0
        self._step = 0
        self._replace = False
        self._out = False
        self._use_counts = False
        self._use_step = False
        self._script_delay = 0
        self._out_sep = ';'

    def enable_cycle(self, status:bool):
        self._cycle = status
        pass

    def set_cycle_parameters(self, dct:dict):
        self._counts = dct['counts']
        self._use_counts = dct['use_c']
        self._use_step = dct['use_step']
        self._from = dct['from']
        self._to = dct['to']
        self._step = dct['step']
        self._replace = dct['replace']
        self._out = dct['out']
        self._script_delay = dct['script_delay']
        self._replacement = dct['replacement']
        self._out_sep = dct['entry_sep']
        pass

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

    def set_second_device(self, device_string):
        print('Device string: ', device_string)
        pass

    def set_com_ending(self, ending='\n'):
        self.comEnding = ending
        pass

    def set_cmds(self, cmds):
        if cmds is not None:
            self.cmds = cmds
        pass

    def set_delay(self, delay=1):
        self.delay = delay
        pass

    def exec_exp(self, rpl=''):
        # there will be the main code of this thread
        script_delay = 0
        if self.comDevice is not None and self.active_device == 0 and not self._require_stop:
            for i in self.cmds:
                if 'delay' in i:
                    s, d = i.split('=')
                    script_delay = int(d)
                    time.sleep(script_delay)
                    pass
                if not self._require_stop and 'delay' not in i and '//' not in i and not self._replace:
                    self.command.emit('')
                    self.comport.emit(str(i))
                    time.sleep(self.delay)
                    pass
                if not self._require_stop and 'delay' not in i and '//' not in i and self._replace:
                    self.command.emit('')
                    self.comport.emit(str(i).replace(self._replacement, rpl))
                    time.sleep(self.delay)
                    pass
                pass
            # self.command.emit('==END OF SCRIPT==')
        elif self.tcpDevice is not None and self.active_device == 1 and not self._require_stop:
            # print('tcp connected?')
            for i in self.cmds:
                if 'delay' in i:
                    s, d = i.split('=')
                    script_delay = int(d)
                    time.sleep(script_delay)
                    pass
                if not self._require_stop and 'delay' not in i and '//' not in i and not self._replace:
                    if '?' in i and not self._require_stop:
                        self.command.emit('')
                        answer = self.tcpDevice.ask(str(i))
                        self.output.emit(1, str(answer))
                        time.sleep(self.delay)
                        pass
                    else:
                        # self.command.emit('')
                        self.tcpDevice.write(str(i))
                        # self.output.emit(str(answer))
                        time.sleep(self.delay)
                        pass
                    pass
                if not self._require_stop and 'delay' not in i and '//' not in i and self._replace:
                    if '?' in i and not self._require_stop:
                        self.command.emit('')
                        answer = self.tcpDevice.ask(str(i).replace(self._replacement, rpl))
                        self.output.emit(1, str(answer))
                        time.sleep(self.delay)
                        pass
                    else:
                        # self.command.emit('')
                        self.tcpDevice.write(str(i).replace(self._replacement, rpl))
                        # self.output.emit(str(answer))
                        time.sleep(self.delay)
                        pass
                    pass
            # self.command.emit('==END OF SCRIPT==')
        elif self.usbDevice is not None and self.active_device == 2 and not self._require_stop:
            # print('usb connected?')
            for i in self.cmds:
                if 'delay' in i:
                    s, d = i.split('=')
                    script_delay = int(d)
                    time.sleep(script_delay)
                    pass
                if not self._require_stop and 'delay' not in i and '//' not in i and not self._replace:
                    if '?' in i and not self._require_stop:
                        self.command.emit('')
                        answer = self.usbDevice.ask(str(i))
                        self.output.emit(1, str(answer))
                        time.sleep(self.delay)
                        pass
                    else:
                        # self.command.emit('')
                        self.usbDevice.write(str(i))
                        # self.output.emit(str(answer))
                        time.sleep(self.delay)
                        pass
                    pass
                if not self._require_stop and 'delay' not in i and '//' not in i and self._replace:
                    if '?' in i and not self._require_stop:
                        self.command.emit('')
                        answer = self.usbDevice.ask(str(i).replace(self._replacement, rpl))
                        self.output.emit(1, str(answer))
                        time.sleep(self.delay)
                        pass
                    else:
                        # self.command.emit('')
                        self.usbDevice.write(str(i).replace(self._replacement, rpl))
                        # self.output.emit(str(answer))
                        time.sleep(self.delay)
                        pass
                    pass
            # self.command.emit('==END OF SCRIPT==')
        pass

    @pyqtSlot()
    def run(self):
        try:
            if self._cycle:
                if self._use_counts:
                    index = 0
                    while index < self._counts and not self._require_stop:
                        self.exec_exp()
                        time.sleep(self._script_delay)
                        index = index + 1
                        pass
                    pass
                elif self._use_step:
                    # not implemented yet
                    idx = self._from
                    while idx < self._to+self._step and not self._require_stop:
                        if self._out:
                            self.entry_out.emit(str(idx)+self._out_sep)
                        if not self._replace:
                            self.exec_exp()
                        elif self._replace:
                            self.exec_exp(str(idx))
                        idx = round((idx + self._step), 4)
                        time.sleep(self._script_delay)
                        pass
                    pass
            elif not self._cycle:
                self.exec_exp()
                pass
            # self.final.emit(0, '==END OF EXPERIMENT==')
        except Exception as ex:
            self.errors.emit(-42, str(ex))
            pass
        finally:
            self.final.emit(0, '==END OF EXPERIMENT==')

    @pyqtSlot()
    def stop(self):
        self._require_stop = True
        pass
