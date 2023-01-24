from PyQt5 import QtCore, QtGui, QtWidgets, QtSerialPort
from PyQt5.QtCore import QIODevice, QThread
from GUI.SDM import Ui_SDM
import sys, os
from vxi11 import vxi11
import struct
from Worker import Worker
from USBTMC import USBTMC
from Device import Device
from ExpWorker import ExpWorker
import numpy as np

class SDM_window(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_SDM()
        self.ui.setupUi(self)
        #shortcuts:
        self.portWidget = self.ui.com_params_widget.ui  # shortcut
        # Globals:
        self.comDevice = None
        self.tcpDevice = None
        self.usbDevice = None
        self.comEnding = None
        self.str = None
        self.int = None
        self.cmds = [] # empty list for commands
        #for the first device
        self.init_cmds = []
        self.exp_cmds = []
        self.end_cmds = []
        # for the second device:
        self.init_cmds_2nd = []
        self.exp_cmds_2nd = []
        self.end_cmds_2nd = []
        self._thread = None
        self._worker = None
        self._threads = []
        self._active_device = None
        self._is_exp = False
        # functions:
        self.update_ports()
        # new line:
        self.new_line = '\n'
        self.err = -1
        self.out = 0
        self.outd = 1
        icon = QtGui.QIcon('GUI/comport.png')
        self.setWindowIcon(icon)
        self._set_actions()
        pass

    def _set_actions(self):
        # signals:
        self.ui.quitButton.clicked.connect(self.quit_fn)
        self.ui.rescanButton.clicked.connect(self.ui.com_params_widget.rescan_ports)
        self.ui.com_params_widget.returnPorts.connect(self.rescan_ports)
        self.ui.comPortBox.currentIndexChanged.connect(self.idx_fn)
        self.portWidget.comPortBox.currentIndexChanged.connect(self.idx)
        self.ui.connectButton.clicked.connect(self.connectComPort)
        self.ui.sendButton.clicked.connect(self.send_fn)
        self.ui.queryButton.clicked.connect(self.query_fn)
        self.ui.useIPButton.clicked.connect(self.connectVXIDevice)
        self.ui.strCheckBox.toggled.connect(self.changeStrIntState)
        self.ui.intCheckBox.toggled.connect(self.changeStrIntState)
        self.ui.fileCommands.clicked.connect(self.cmd_from_file)
        self.ui.executeCmdsButton.clicked.connect(self.execute_fn)
        self.ui.connect_usbtmc_Button.clicked.connect(self.connect_usbtmc_fn)
        self.ui.activeDeviceBox.currentIndexChanged.connect(self.update_active_device)
        self.ui.saveButton.clicked.connect(self.save_fn)
        self.ui.actionClose.triggered.connect(self.quit_fn)
        self.quit_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self)
        self.ui.force_read.clicked.connect(self.comInf)
        # events of shortcuts:
        self.quit_shortcut.activated.connect(self.quit_fn)
        # exp commands:
        self.ui.init_file_Button.clicked.connect(self.load_init_file_fn)
        self.ui.exec_file_Button.clicked.connect(self.load_exp_file_fn)
        self.ui.end_file_Button.clicked.connect(self.load_end_file_fn)
        # Exec fns:
        self.ui.execute_init.clicked.connect(self.exec_init_fn)
        self.ui.execute_exp.clicked.connect(self.exec_exp_fn)
        self.ui.execute_end.clicked.connect(self.exec_end_fn)
        # for the second device:
        self.ui.init2_file_btn.clicked.connect(self.init2fn)
        self.ui.exec2_file_btn.clicked.connect(self.exp2fn)
        self.ui.end2_file_btn.clicked.connect(self.end2fn)
        #
        self.ui.save_exp_btn.clicked.connect(self.save_exp_fn)
        self.ui.clear_exp_btn.clicked.connect(self.clear_exp_fn)

        self.ui.cycle_prams_btn.clicked.connect(self.cycle_tab)
        self.ui.return_exp_btn.clicked.connect(self.exp_tab_fn)

        self.ui.clearButton.clicked.connect(self.clearButton_fn)
        pass

    def clearButton_fn(self):
        self.ui.output_box.clear()
        pass

    def exp_tab_fn(self):
        self.ui.tabWidget.setCurrentIndex(3)
        pass


    def cycle_tab(self):
        self.ui.tabWidget.setCurrentIndex(4)
        pass

    def update_new_line(self):
        self.new_line = os.linesep
        pass

    def save_exp_fn(self):
        fname, _ = QtWidgets.QFileDialog().getSaveFileName(None, 'File name to save under?')
        if fname:
            txt = self.ui.exp_output_box.toPlainText()
            f = open(fname, 'w')
            f.write(txt)
            f.close()
            self.ui.statusbar.setText('File was saved!')
        pass

    def clear_exp_fn(self):
        self.ui.exp_output_box.clear()
        pass

    def exec_init_fn(self):
        '''
        Thread will be used just for tcp and usb devices,
        because I can not solve mystery with QtSerialPort and thread
        :return:
        '''
        try:
            self._is_exp = False
            active_device = 0
            delay = self.ui.delay_between_commands_box.value()
            if self.ui.active_exp_devBox.currentText() == 'comDevice':
                active_device = 0
            elif self.ui.active_exp_devBox.currentText() == 'tcpDevice':
                active_device = 1
            elif self.ui.active_exp_devBox.currentText() == 'usbDevice':
                active_device = 2
            self._thread = QThread(self)  # pretty weired
            self._worker = Worker()
            self._threads.append((self._thread, self._worker))
            self._worker.set_cmds(self.init_cmds)
            self._worker.assign_device(com=self.comDevice, tcp=self.tcpDevice, usb=self.usbDevice)
            self._worker.set_active_device(active_device)
            # code section for the second device in thread:
            # =============================================
            if self.ui.second_exp_devBox.currentIndex() != -1 or self.ui.second_exp_devBox.currentText() == '[not set]':
                print(self.ui.second_exp_devBox.currentIndex(), ' index of the second device')
            #     set all parameters for the second device:
                self._worker.set_cmds_2nd(self.init_cmds_2nd)
                self._worker.set_active_device_2nd(self.ui.second_exp_devBox.currentText())
                pass

            else:
                print(self.ui.second_exp_devBox.currentIndex(), ' index of the second device')
                pass
            # =============================================
            self._worker.set_delay(delay)
            self._worker.set_com_ending(self.comEnding)
            # signals:
            self._worker.output.connect(self.update_output)
            self._worker.errors.connect(self.errors_fn)
            self._worker.command.connect(self.update_command)
            self._worker.comport.connect(self.send_com_fn)
            # main magic:
            self._worker.moveToThread(self._thread)
            self._thread.started.connect(self._worker.run)
            self._thread.start()
        except Exception as ex:
            # self.ui.output_box.append(str(ex))
            self.append_html_paragraph(str(ex), self.err)
            pass
        pass

    def exec_exp_fn(self):
        try:
            dct = {} # empty dictionary
            self._is_exp = True
            active_device = 0
            delay = self.ui.delay_between_commands_box.value()
            if self.ui.active_exp_devBox.currentText() == 'comDevice':
                active_device = 0
            elif self.ui.active_exp_devBox.currentText() == 'tcpDevice':
                active_device = 1
            elif self.ui.active_exp_devBox.currentText() == 'usbDevice':
                active_device = 2
            self._thread = QThread(self)  # pretty weired
            self._worker = ExpWorker()
            self._threads.append((self._thread, self._worker))
            self._worker.set_cmds(self.exp_cmds)
            self._worker.enable_cycle(self.ui.use_cycle_box.isChecked())
            #  get all parameters into the dictionary:
            dct = {
                'counts':self.ui.counts_box.value(),
                'use_c':self.ui.counts_radio.isChecked(),
                'use_step':self.ui.step_radio.isChecked(),
                'from':self.ui.from_box.value(),
                'to':self.ui.to_box.value(),
                'step':self.ui.step_box.value(),
                'replace':self.ui.replace_variable_box.isChecked(),
                'out':self.ui.out_variable_box.isChecked(),
                'script_delay':self.ui.delay_scripts_box.value(),
                'replacement':self.ui.var_box.text(),
                'entry_sep':self.ui.entry_separator_box.text()
            }
            self._worker.set_cycle_parameters(dct)
            self._worker.assign_device(com=self.comDevice, tcp=self.tcpDevice, usb=self.usbDevice)
            self._worker.set_active_device(active_device)

            if self.ui.second_exp_devBox.currentIndex() != -1 or self.ui.second_exp_devBox.currentText() == '[not set]':
                print(self.ui.second_exp_devBox.currentIndex(), ' index of the second device')
            #     set all parameters for the second device:
                self._worker.set_cmds_2nd(self.exp_cmds_2nd)
                self._worker.set_second_device(self.ui.second_exp_devBox.currentText())
                pass
            else:
                print(self.ui.second_exp_devBox.currentIndex(), ' index of the second device')
                pass
            self._worker.set_delay(delay)
            self._worker.set_com_ending(self.comEnding)
            # signals:
            self._worker.output.connect(self.update_exp_output)
            self._worker.errors.connect(self.errors_fn)
            self._worker.command.connect(self.update_exp_command)
            self._worker.comport.connect(self.send_com_fn)
            self._worker.entry_out.connect(self.update_entry_box)
            self._worker.final.connect(self.final)
            # main magic:
            self._worker.moveToThread(self._thread)
            self._thread.started.connect(self._worker.run)
            self._thread.start()
        except Exception as ex:
            self.ui.statusbar.setText(str(ex))
        pass

    def update_entry_box(self, string:str):
        self.ui.expIterEntry.setText(string)
        pass

    def update_exp_output(self, status, string):
        if status == 0:
            pass
        if status == 1:
            self.append_exp_text(string, self.outd)
            pass
        pass
        pass

    def update_exp_command(self, string):
        self.append_exp_paragraph(self.ui.expIterEntry.text()+string)
        pass

    def final(self, i, string):
        self.append_html_paragraph(string, i)
        pass

    def exec_end_fn(self):
        '''
        Thread will be used just for tcp and usb devices,
        because I can not solve mystery with QtSerialPort and thread
        :return:
        '''
        try:
            self._is_exp = False
            active_device = 0
            delay = self.ui.delay_between_commands_box.value()
            if self.ui.active_exp_devBox.currentText() == 'comDevice':
                active_device = 0
            elif self.ui.active_exp_devBox.currentText() == 'tcpDevice':
                active_device = 1
            elif self.ui.active_exp_devBox.currentText() == 'usbDevice':
                active_device = 2
            self._thread = QThread(self)  # pretty weired
            self._worker = Worker()
            self._threads.append((self._thread, self._worker))
            self._worker.set_cmds(self.end_cmds)
            self._worker.assign_device(com=self.comDevice, tcp=self.tcpDevice, usb=self.usbDevice)
            self._worker.set_active_device(active_device)
            self._worker.set_delay(delay)
            self._worker.set_com_ending(self.comEnding)
            if self.ui.second_exp_devBox.currentIndex() != -1 or self.ui.second_exp_devBox.currentText() == '[not set]':
                print(self.ui.second_exp_devBox.currentIndex(), ' index of the second device')
            #     set all parameters for the second device:
                self._worker.set_cmds_2nd(self.end_cmds_2nd)
                self._worker.set_active_device_2nd(self.ui.second_exp_devBox.currentText())
                pass

            else:
                print(self.ui.second_exp_devBox.currentIndex(), ' index of the second device')
                pass
            # signals:
            self._worker.output.connect(self.update_output)
            self._worker.errors.connect(self.errors_fn)
            self._worker.command.connect(self.update_command)
            self._worker.comport.connect(self.send_com_fn)
            # main magic:
            self._worker.moveToThread(self._thread)
            self._thread.started.connect(self._worker.run)
            self._thread.start()
        except Exception as ex:
            # self.ui.output_box.append(str(ex))
            self.append_html_paragraph(str(ex), self.err)
            pass
        pass

    # self.ui.init2_file_btn.clicked.connect(self.init2fn)
    # self.ui.exec2_file_btn.clicked.connect(self.exp2fn)
    # self.ui.end2_file_btn.clicked.connect(self.end2fn)

    def exp2fn(self):
        fname, _ = QtWidgets.QFileDialog().getOpenFileName(None, 'Select experiment commands file')
        if fname:
            try:
                f = open(fname, 'r')
                lines = f.readlines()
                content = [x.strip() for x in lines]
                self.exp_cmds_2nd = content
                # for i in self.ini:
                #     self.ui.commands_view.append(i)
                f.close()
                fnm = QtCore.QFileInfo(fname).fileName()
                self.ui.exec2_label.setText(str(fnm))
            except Exception as ex:
                self.ui.statusbar.setText('ERR:' + str(ex))
        pass

    def end2fn(self):
        fname, _ = QtWidgets.QFileDialog().getOpenFileName(None, 'Select end file')
        if fname:
            try:
                f = open(fname, 'r')
                lines = f.readlines()
                content = [x.strip() for x in lines]
                self.end_cmds_2nd = content
                # for i in self.ini:
                #     self.ui.commands_view.append(i)
                f.close()
                fnm = QtCore.QFileInfo(fname).fileName()
                self.ui.end2_label.setText(str(fnm))
            except Exception as ex:
                self.ui.statusbar.setText('ERR:' + str(ex))
        pass

    def init2fn(self):
        fname, _ = QtWidgets.QFileDialog().getOpenFileName(None, 'Select init file')
        if fname:
            try:
                f = open(fname, 'r')
                lines = f.readlines()
                content = [x.strip() for x in lines]
                self.init_cmds_2nd = content
                # for i in self.ini:
                #     self.ui.commands_view.append(i)
                f.close()
                fnm = QtCore.QFileInfo(fname).fileName()
                self.ui.init2_label.setText(str(fnm))
            except Exception as ex:
                self.ui.statusbar.setText('ERR:' + str(ex))
        pass

    def load_init_file_fn(self):
        fname, _ = QtWidgets.QFileDialog().getOpenFileName(None, 'Select init file')
        if fname:
            try:
                f = open(fname, 'r')
                lines = f.readlines()
                content = [x.strip() for x in lines]
                self.init_cmds = content
                # for i in self.ini:
                #     self.ui.commands_view.append(i)
                f.close()
                fnm = QtCore.QFileInfo(fname).fileName()
                self.ui.initfileLabel.setText(str(fnm))
            except Exception as ex:
                self.ui.statusbar.setText('ERR:'+str(ex))
        pass

    def load_exp_file_fn(self):
        fname, _ = QtWidgets.QFileDialog().getOpenFileName(None, 'Select experiment commands file')
        if fname:
            try:
                f = open(fname, 'r')
                lines = f.readlines()
                content = [x.strip() for x in lines]
                self.exp_cmds = content
                # for i in self.ini:
                #     self.ui.commands_view.append(i)
                f.close()
                fnm = QtCore.QFileInfo(fname).fileName()
                self.ui.expfileLabel.setText(str(fnm))
            except Exception as ex:
                self.ui.statusbar.setText('ERR:'+str(ex))
        pass

    def load_end_file_fn(self):
        fname, _ = QtWidgets.QFileDialog().getOpenFileName(None, 'Select end file')
        if fname:
            try:
                f = open(fname, 'r')
                lines = f.readlines()
                content = [x.strip() for x in lines]
                self.end_cmds = content
                # for i in self.ini:
                #     self.ui.commands_view.append(i)
                f.close()
                fnm = QtCore.QFileInfo(fname).fileName()
                self.ui.endfileLabel.setText(str(fnm))
            except Exception as ex:
                self.ui.statusbar.setText('ERR:'+str(ex))
        pass

    def save_fn(self):
        fname, _ = QtWidgets.QFileDialog().getSaveFileName(None, 'File name to save under?')
        if fname:
            txt = self.ui.output_box.toPlainText()
            f = open(fname, 'w')
            f.write(txt)
            f.close()
            self.ui.statusbar.setText('File was saved!')
        pass

    def update_active_device(self):
        if self.ui.activeDeviceBox.currentText() == 'comDevice':
            self._active_device = 0
            idx = self.ui.active_exp_devBox.findText('comDevice')
            self.ui.active_exp_devBox.setCurrentIndex(idx)
        elif self.ui.activeDeviceBox.currentText() == 'tcpDevice':
            self._active_device = 1
            idx = self.ui.active_exp_devBox.findText('tcpDevice')
            self.ui.active_exp_devBox.setCurrentIndex(idx)
        elif self.ui.activeDeviceBox.currentText() == 'usbDevice':
            self._active_device = 2
            idx = self.ui.active_exp_devBox.findText('usbDevice')
            self.ui.active_exp_devBox.setCurrentIndex(idx)
        pass

    def connect_usbtmc_fn(self):
        try:
            self.usbDevice = USBTMC(self.ui.usbtmcBox.currentText())
            self.ui.activeDeviceBox.addItem('usbDevice')
            idx = self.ui.activeDeviceBox.findText('usbDevice')
            self.ui.activeDeviceBox.setCurrentIndex(idx)
            # :
            self.ui.active_exp_devBox.addItem('usbDevice')
            idx = self.ui.active_exp_devBox.findText('usbDevice')
            self.ui.active_exp_devBox.setCurrentIndex(idx)
            #second device for the experiment
            self.ui.second_exp_devBox.addItem('usbDevice')
            idx = self.ui.second_exp_devBox.findText('usbDevice')
            self.ui.second_exp_devBox.setCurrentIndex(-1)
        except Exception as ex:
            self.ui.infoLabel.setText(str(ex))
        pass

    def execute_fn(self):
        '''
        Thread will be used just for tcp and usb devices,
        because I can not solve mystery with QtSerialPort and thread
        :return:
        '''
        try:
            active_device = 0
            delay = self.ui.delay_between_commands_box.value()
            if self.ui.activeDeviceBox.currentText() == 'comDevice':
                active_device = 0
            elif self.ui.activeDeviceBox.currentText() == 'tcpDevice':
                active_device = 1
            elif self.ui.activeDeviceBox.currentText() == 'usbDevice':
                active_device = 2
            self._thread = QThread(self) # pretty weired
            self._worker = Worker()
            self._threads.append((self._thread, self._worker))
            self._worker.set_cmds(self.cmds)
            self._worker.assign_device(com=self.comDevice, tcp=self.tcpDevice, usb=self.usbDevice)
            self._worker.set_active_device(active_device)
            self._worker.set_delay(delay)
            self._worker.set_com_ending(self.comEnding)
            #signals:
            self._worker.output.connect(self.update_output)
            self._worker.errors.connect(self.errors_fn)
            self._worker.command.connect(self.update_command)
            self._worker.comport.connect(self.send_com_fn)
            # main magic:
            self._worker.moveToThread(self._thread)
            self._thread.started.connect(self._worker.run)
            self._thread.start()
        except Exception as ex:
            # self.ui.output_box.append(str(ex))
            self.append_html_paragraph(str(ex), self.err)
            pass
        pass

    def append_text(self, text):
        self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
        self.ui.output_box.insertPlainText(text)
        self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
        pass

    def append_paragraph(self,text):
        self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
        self.ui.output_box.insertPlainText(text+'\n')
        self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
        pass

    def update_command(self, string):
        # self.ui.output_box.setAlignment(QtCore.Qt.AlignLeft)
        # self.ui.output_box.currentFont().setBold(True)
        self.append_html_paragraph(string, self.out) # new line will be added automatically
        pass

    def errors_fn(self, status, string):
        self.append_html_paragraph('ERR from Thread: '+string, self.err)
        pass

    def update_output(self, status, string):
        if status == 0:
            pass
        if status == 1:
            self.append_html_paragraph(string, self.outd)
            pass
        pass

    def append_exp_paragraph(self, text, status=0):
        html_red = '<font color="red">{x}</font>'
        html_black='<font color="black">{x}</font>'
        html_magenta='<font color="purple">{x}</font>'
        txt = str(text)
        if status == 0:
            self.ui.exp_output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.exp_output_box.insertPlainText(self.new_line)
            self.ui.exp_output_box.setAlignment(QtCore.Qt.AlignLeft)
            self.ui.exp_output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.exp_output_box.insertHtml(html_black.replace('{x}', txt))
            self.ui.exp_output_box.moveCursor(QtGui.QTextCursor.End)
        elif status == 1:
            self.ui.exp_output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.exp_output_box.insertPlainText(self.new_line)
            self.ui.exp_output_box.setAlignment(QtCore.Qt.AlignRight)
            # self.ui.output_box.setFontWeight(QtGui.QFont.Bold)
            self.ui.exp_output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.exp_output_box.insertHtml(html_magenta.replace('{x}', txt))
            self.ui.exp_output_box.moveCursor(QtGui.QTextCursor.End)
        elif status == -1:
            self.ui.exp_output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.exp_output_box.insertPlainText(self.new_line)
            self.ui.exp_output_box.setAlignment(QtCore.Qt.AlignLeft)
            self.ui.exp_output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.exp_output_box.insertHtml(html_red.replace('{x}', txt))
            self.ui.exp_output_box.moveCursor(QtGui.QTextCursor.End)
        pass

    def append_exp_text(self, text, status=0):
        html_red = '<font color="red">{x}</font>'
        html_black='<font color="black">{x}</font>'
        html_magenta='<font color="blue">{x}</font>'
        txt = str(text)
        if status == 0:
            self.ui.exp_output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.exp_output_box.insertHtml(html_black.replace('{x}',txt))
            self.ui.exp_output_box.moveCursor(QtGui.QTextCursor.End)
        elif status == 1:
            self.ui.exp_output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.exp_output_box.setFontWeight(QtGui.QFont.Bold)
            self.ui.exp_output_box.insertHtml(html_magenta.replace('{x}',txt))
            self.ui.exp_output_box.moveCursor(QtGui.QTextCursor.End)
        elif status == -1:
            self.ui.exp_output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.exp_output_box.insertHtml(html_red.replace('{x}', txt))
            self.ui.exp_output_box.moveCursor(QtGui.QTextCursor.End)
        pass

    def append_html_paragraph(self, text, status=0, c=1):
        txt = ""
        if c == 1:
            txt = str(text)
        elif c == 0:
            skip_points = int(self.ui.skipBox.value())
            data = np.frombuffer(text.encode('ascii')[skip_points:], 'B')
            txt = str(data)
            pass
        html_red = '<font color="red">{x}</font>'
        html_black='<font color="black">{x}</font>'
        html_magenta='<font color="purple">{x}</font>'
        if status == 0:
            self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.output_box.insertPlainText(self.new_line)
            self.ui.output_box.setAlignment(QtCore.Qt.AlignLeft)
            self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.output_box.insertHtml(html_black.replace('{x}', txt))
            self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
        elif status == 1:
            self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.output_box.insertPlainText(self.new_line)
            self.ui.output_box.setAlignment(QtCore.Qt.AlignRight)
            # self.ui.output_box.setFontWeight(QtGui.QFont.Bold)
            self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.output_box.insertHtml(html_magenta.replace('{x}', txt))
            self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
        elif status == -1:
            self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.output_box.insertPlainText(self.new_line)
            self.ui.output_box.setAlignment(QtCore.Qt.AlignLeft)
            self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.output_box.insertHtml(html_red.replace('{x}', txt))
            self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
        pass

    def append_html_text(self, text, status=0):
        txt = str(text)
        html_red = '<font color="red">{x}</font>'
        html_black='<font color="black">{x}</font>'
        html_magenta='<font color="blue">{x}</font>'
        if status == 0:
            self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.output_box.insertHtml(html_black.replace('{x}',txt))
            self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
        elif status == 1:
            self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.output_box.setFontWeight(QtGui.QFont.Bold)
            # self.ui.output_box.setAlignment(QtCore.Qt.AlignRight)
            self.ui.output_box.insertHtml('<br/>'+html_magenta.replace('{x}',txt))
            self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
        elif status == -1:
            self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
            self.ui.output_box.setAlignment(QtCore.Qt.AlignRight)
            self.ui.output_box.insertHtml(html_red.replace('{x}', txt))
            self.ui.output_box.moveCursor(QtGui.QTextCursor.End)
        pass

    def fill_cmds_fn(self, f_name):
        try:
            self.ui.commands_view.clear()
            f = open(f_name, 'r')
            lines = f.readlines()
            content = [x.strip() for x in lines]
            self.cmds = content
            for i in self.cmds:
                self.ui.commands_view.append(i)
            # short info about file:
            l = len(self.cmds)
            self.ui.infoLabel.setText(str(l)+' line(s) were read.')
        except Exception as ex:
            self.ui.statusbar.setText(str(ex))
            pass
        pass

    def cmd_from_file(self):
        print("cmd file?")
        qf_dlg = QtWidgets.QFileDialog()
        file_name, rest = qf_dlg.getOpenFileName(None, caption='Open command set!')
        if file_name:
            fname = QtCore.QFileInfo(file_name).fileName()
            self.ui.statusbar.setText(str(fname)+' was opened.')
            self.fill_cmds_fn(file_name)
        pass

    def changeStrIntState(self):
        if self.ui.strCheckBox.isChecked():
            self.str = True
            self.int = False
        if self.ui.intCheckBox.isChecked():
            self.str = False
            self.int = True
        pass

    def connectVXIDevice(self):
        try:
            ip = self.ui.ipBox.currentText()
            self.tcpDevice = vxi11.Instrument(ip)
            self.tcpDevice.open()
            self.ui.statusbar.setText('Connected to the TCP device@'+ip)
            self.ui.activeDeviceBox.addItem('tcpDevice')
            idx = self.ui.activeDeviceBox.findText('tcpDevice')
            self.ui.activeDeviceBox.setCurrentIndex(idx)
            # :
            self.ui.active_exp_devBox.addItem('tcpDevice')
            idx = self.ui.active_exp_devBox.findText('tcpDevice')
            self.ui.active_exp_devBox.setCurrentIndex(idx)
        #
            self.ui.second_exp_devBox.addItem('tcpDevice')
            # idx = self.ui.active_exp_devBox.findText('tcpDevice')
            self.ui.active_exp_devBox.setCurrentIndex(-1)
            pass
        except Exception as ex:
            print(ex)
            self.append_html_paragraph(str(ex), -1)
            self.ui.statusbar.setText('Failed to connect!')
        pass


    def query_fn(self):
        encoding = self.ui.encodingBox.currentIndex()
        cmd = self.ui.command_entry.currentText()
        if self._active_device is not None and self._active_device == 0:
            self.send_fn()
        elif self._active_device is not None and self._active_device == 1:
            answer = self.tcpDevice.ask(cmd)
            # self.ui.output_box.append(answer)
            self.append_html_paragraph(answer, self.outd, encoding)
        elif self._active_device is not None and self._active_device == 2:
            result = self.usbDevice.ask(cmd)
            self.append_html_paragraph(result, self.outd, encoding)

        idx = self.ui.command_entry.findText(cmd)
        if idx == -1:
            self.ui.command_entry.addItem(cmd)
        self.ui.command_entry.setCurrentIndex(-1)
        pass

    def send_fn(self):
        cmd = self.ui.command_entry.currentText()
        self.update_active_device()
        # print(self.comEnding)
        self.append_html_paragraph(cmd)
        if self._active_device is not None and self._active_device == 0:
            if self.comDevice is not None and self.comDevice.isOpen():
                try:
                    status = self.comDevice.write(bytes(cmd+self.comEnding, 'utf-8'))
                    if (status < 0):
                        # self.ui.statusbar.showMessage(str(status), 0)
                        error = self.comDevice.error()
                        error_string = self.comDevice.errorString()
                        self.ui.output_box.append(error_string)
                        self.ui.output_box.append(str(error))
                except Exception as ex:
                    # self.ui.statusbar.showMessage(str(ex))
                    self.ui.output_box.append(str(ex))
            pass
        elif self._active_device is not None and self._active_device == 1:
            try:
                self.tcpDevice.write(cmd)
            except Exception as ex:
                self.append_paragraph('ERR: '+str(ex))
        elif self._active_device is not None and self._active_device == 2:
            self.usbDevice.write(cmd)
            pass
        idx = self.ui.command_entry.findText(cmd)
        if idx == -1:
            self.ui.command_entry.addItem(cmd)
        self.ui.command_entry.setCurrentIndex(-1)

    def send_com_fn(self, string):
        cmd = string
        # print(self.comEnding)
        if self.comDevice is not None and self.comDevice.isOpen():
            try:
                status = self.comDevice.write(bytes(cmd + self.comEnding, 'utf-8'))
                if (status < 0):
                    # self.ui.statusbar.showMessage(str(status), 0)
                    error = self.comDevice.error()
                    error_string = self.comDevice.errorString()
                    self.ui.output_box.append(error_string)
                    self.ui.output_box.append(str(error))
            except Exception as ex:
                # self.ui.statusbar.showMessage(str(ex))
                self.ui.output_box.append(str(ex))
        pass

    def connectComPort(self):
        self.comDevice = self.ui.com_params_widget.getSerialPort()
        try:
            status = self.comDevice.open(QIODevice.ReadWrite)
            if status:
                # self.ui.output_box.appendPlainText("Connected\n")
                self.ui.statusbar.setText('Connected to the COM port '+self.ui.comPortBox.currentText())
                self.ui.activeDeviceBox.addItem('comDevice')
                idx = self.ui.activeDeviceBox.findText('comDevice')
                self.ui.activeDeviceBox.setCurrentIndex(idx)
                # :
                self.ui.active_exp_devBox.addItem('comDevice')
                idx = self.ui.active_exp_devBox.findText('comDevice')
                self.ui.active_exp_devBox.setCurrentIndex(idx)
                #
                self.ui.second_exp_devBox.addItem('comDevice')
                # idx = self.ui.active_exp_devBox.findText('comDevice')
                self.ui.second_exp_devBox.setCurrentIndex(-1)
                #
                self.comDevice.readyRead.connect(self.comInfo)
                idx = self.portWidget.lineBox.currentIndex()
                if idx == 0:
                    self.comEnding = '\n'
                if idx == 1:
                    self.comEnding = '\r'
                if idx == 2:
                    self.comEnding = '\r\n'
                if self.ui.strCheckBox.isChecked():
                    self.str = True
                    self.int = False
                if self.ui.intCheckBox.isChecked():
                    self.str = False
                    self.int = True

        except Exception as ex:
            print("Err")
            print(ex)
        pass

    def comInf(self):
        bytes_waiting = self.comDevice.bytesAvailable()
        print('Bytes '+str(bytes_waiting))
        self.append_html_paragraph('Bytes from forced COM port: '+str(bytes_waiting))
        if bytes_waiting > 0:
            baitai = self.comDevice.readAll()
            self.append_html_paragraph('FORCED answer:\n'+str(baitai))
        pass

    def comInfo(self):
        # print("TRIGGERED")
        bytes_from_port = self.comDevice.readAll()
        # print('Bytes from port', bytes_from_port)
        # text = self.ui.Continuous_output.toPlainText()
        # print(bytes_from_port, "   OUTPUT")
        try:
            if not self._is_exp:
                if self.str:
                    text = (((str(bytes_from_port, 'utf-8'))))#.replace("\r\n", "\n")))
                    # self.ui.output_box.setAlignment(QtCore.Qt.AlignRight)
                    self.append_html_text(text, self.outd)
                elif self.int:
                    txt = int.from_bytes(bytes_from_port, byteorder='big')
                    self.append_html_paragraph(str(txt), self.outd)
                pass
            elif self._is_exp:
                if self.str:
                    text = (((str(bytes_from_port, 'utf-8'))))#.replace("\r\n", "\n")))
                    # self.ui.exp_output_box.setAlignment(QtCore.Qt.AlignRight)
                    self.append_exp_text(text, self.outd)
                elif self.int:
                    txt = int.from_bytes(bytes_from_port, byteorder='big')
                    self.append_exp_paragraph(str(txt), self.outd)
                pass
        except Exception as ex:
            print(ex, ' Exception occurred in output')
            pass
        # self.ui.output_box.appendPlainText(text)
        pass

    def idx(self, index):
        self.ui.comPortBox.setCurrentIndex(index)
        pass

    def idx_fn(self, index):
        # self.ui.com_params_widget.ui.comPortBox.setCurrentIndex(index)
        self.portWidget.comPortBox.setCurrentIndex(index)
        pass


    def quit_fn(self):
        print("APP exiting")
        if self.comDevice is not None and self.comDevice.isOpen():
            print("Closing COM port")
            self.comDevice.close()
        sys.exit(0)
        pass

    def update_ports(self):
        ports = self.ui.com_params_widget.get_port_names()
        self.ui.comPortBox.insertItems(0, [str(x.portName()) for x in ports])
        self.get_usbtmc_devices()
        pass

    def rescan_ports(self, ports):
        self.ui.comPortBox.clear()
        self.ui.comPortBox.insertItems(0, [str(x.portName()) for x in ports])
        self.get_usbtmc_devices()
        pass

    def get_usbtmc_devices(self):
        try:
            self.ui.usbtmcBox.clear()
            mypath = "/dev"
            for f in os.listdir(mypath):
                if f.startswith('usbtmc'):
                    self.ui.usbtmcBox.addItem(mypath+"/"+f)
        except Exception as ex:
            pass


