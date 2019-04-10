#Introduction

The **Simple Device Monitor** is quite simple application targeted to control or watch laboratory devices under Linux operating system.

The other purpose was to have general application able to connect any device and test an output from it.

This applications can connect to **RS232** ( COM ) port-attached devices, as well as to **USB** and **Network** devices. There are few requirements for **USB** and **Network**-based devices:

-  **USB** devices should be compatible with *USBTMC* protocol. In other words - Linux should detect them as **USBTMC** devices and create node */dev/usbtmcN*, where N - {0, 1, 2, ... }
- **Network**-based devices should be compatible with *SCPI* protocol. 
- **RS232** devices should work without any quirks, if these devices do not use very specific protocol.

The Simple Device Monitor uses *python-vxi11* library to communicate with **Network**-based devices, **QtSerialPort** to communicate with *RS232* devices. **USBTMC** devices are treated as regular files, therefore **USBTMC** devices will work under Linux OS only. 

All necessary requirements can be installed using regular package managers such *apt*, *yum* and so on, or using *pip* command, if preferred. 

In order to run this application, a host computer has to have:

- Pyhton 3
- python-vxi11
- QtSerialPort
- PyQt5

Everything can be installed using the following commands (tested under Ubuntu 18.04 LTS):
>sudo apt-get install python3 python3-pyqt5 python3-pyqt5.qtserialport python3-pip
>
>sudo pip3 install python-vxi11

If everything is OK, there will be all necessary dependencies automatically installed.

For Windows users, there is a standalone version in a *../Windows* directory, tested under Windows 10, 64-bit.


#Usage and Limitations

![](SDM.png)

The Simple Device Monitor able to connect up to three different-connected devices. For example, it is possible to connect to one **RS232** device, to one **USBTMC** device and to one *Networked* device, but it is impossible to have more than one **RS232** device at the same time.

It is impossible to send commands to all devices at the same time - you need to specify exact device to work with.

There is an ability to load a bunch of commands from file and it is possible to run very basic experiment with one specified device.
For example, if you need to measure solar cell, resistor and so on and if you have quite expensive source meter such *Keysight B2980*, you can do with this application.

#Command sets

It is possible to write all commands into one file, and send them all without entering command by command.
The structure of command sets is very simple: just write regular **SCPI** commands line by line:
>\*idn?
>\*rst

It is possible to write comments using two backslashes in the beginning of line:
>//comment
>\*idn?
>//other comment
>\*rst

It is even possible to specify delay between commands with keyword *delay*:
>//comment
>\*idn?
>delay=5
>//other comment
>\*rst

It will delay an execution of the next statement for the 5 seconds. You can specify any time amount you need.