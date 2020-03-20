#!/usr/bin/python3

from SDM_GUI import SDM_window
import sys
from PyQt5 import QtWidgets

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = SDM_window()
    window.show()
    sys.exit(app.exec_())
