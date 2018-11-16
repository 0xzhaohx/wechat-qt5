#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年3月25日

@author: zhaohongxing
'''

import os
import sys 
import threading
#from time import sleep
import time
import logging
import platform

from PyQt5.Qt import QIcon
from PyQt5 import QtGui, uic
from PyQt5.QtWidgets import QApplication,QDialog,QMainWindow

from wechatweb import WeChatWeb
from config import WechatConfig
from com.ox11.wechat.wechatwin import WeChatWin

qtCreatorFile = "resource/ui/wechat-1.0.ui"

LauncherWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

def getOSName():
    return platform.system()

def machine():
    if os.name == 'nt' and sys.version_info[:2] < (2,7):
        return os.environ.get("PROCESSOR_ARCHITEW6432",
               os.environ.get('PROCESSOR_ARCHITECTURE', ''))
    else:
        return platform.machine()

def osbits(machine=None):
    if not machine:
        machine =machine()
    machine2bits = {'AMD64': 64, 'x86_64': 64, 'i386': 32, 'x86': 32}
    return machine2bits.get(machine, None)

class WeChatLauncher(QDialog, LauncherWindow):

    timeout = login_state = False
    LOG_FILE = '%s/wechat.log'
    def __init__(self):
        QMainWindow.__init__(self)
        LauncherWindow.__init__(self)
        
        self.wechat_web = WeChatWeb()
        self.config = WechatConfig()
        self.clean_log()
        self.setupUi(self)
        self.setWindowIcon(QIcon("resource/icons/hicolor/32x32/apps/wechat.png"))
        self.setWindowIconText("WeChatWin 0.5")
        self.setWindowTitle("WeChat網頁版0.5")
        self.generate_qrcode()
        self.load_qr_code_image()
        #use threading.timer
        self.login_timer = threading.Timer(0, self.login)
        self.login_timer.setDaemon(True)
        self.login_timer.start()

    def set_qr_timeout(self):
        WeChatLauncher.timeout = True

    def load_qr_code_image(self):
        qrcode_path = self.config.getAppHome()+"/qrcode.jpg"
        logging.debug("qrcode_path:%s"%qrcode_path)
        qr_image = QtGui.QImage()
        if qr_image.load(qrcode_path):
            self.qrLabel.setPixmap(QtGui.QPixmap.fromImage(qr_image).scaled(215, 215))
            self.time_out_timer = threading.Timer(25, self.set_qr_timeout)
            self.time_out_timer.start()
        else:
            pass

    def login(self):
        #wait4login會一直等，直到用户扫描，如果扫描了，則一直等待在手機端確認
        code = self.wechat_web.wait4login()
        logging.debug("return code of wait4login() is %s"%code)
        if "200" == code:
            WeChatLauncher.login_state = True
        else:
            code = self.wechat_web.wait4login(0)
            logging.debug("return code of wait4login(0) is %s"%code)
            WeChatLauncher.login_state = (True if "200" == code else False)
        if "200" == code:
            self.accept()

    def generate_qrcode(self):
        self.wechat_web.generate_qrcode()

    def clean_log(self):
        if os.path.exists(WeChatLauncher.LOG_FILE%self.config.getAppHome()):
            with open(WeChatLauncher.LOG_FILE%self.config.getAppHome(),'w') as lf:
                lf.seek(0)
                lf.truncate()
                logging.debug(time.time())
                
    def closeEvent(self,event):
        self.login_timer.cancel()
        self.time_out_timer.cancel()
        logging.debug("user closed the window")

def main():
    logging.basicConfig(filename="./wechat.log",format="%(asctime)s %(levelname)s %(message)s",filemode="w",level=logging.DEBUG)
    app = QApplication(sys.argv)
    if getOSName() == "Windows":
        logging.warning("The OS name is Windows,will be exit!")
    launcher = WeChatLauncher()
    if QDialog.Accepted == launcher.exec_():
        window = WeChatWin()
        window.show()
        sys.exit(app.exec_())
        
if __name__ =="__main__":
    main()
        
