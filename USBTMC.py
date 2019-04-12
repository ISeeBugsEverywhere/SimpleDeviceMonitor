import os
import time
class USBTMC:
    """
    Very Simple usbmtc device
    """

    def __init__(self, device):
        self.device = device
        self.FILE = os.open(self.device, os.O_RDWR)

    def write(self, command):
        os.write(self.FILE, str.encode(command))

    def read(self, length=4000):
        '''

        :param length: length of data to read
        :return:
        '''
        return os.read(self.FILE, length)

    def getName(self):
        self.write("*IDN?")
        return self.read(300)

    def sendReset(self):
        self.write("*RST")

    def closeDevice(self):
        os.close(self.FILE)

    def ask(self, cmd, delay=1, length=4000):
        string = None
        try:
            self.write(cmd)
            time.sleep(delay)
            ret = self.read(length)
            string = str(ret, encoding='utf-8', errors='ignore')
        except Exception as ex:
            string = 'USBTMC failed!'
            print('USBTMC failed:')
            print(str(ex))
        return string
