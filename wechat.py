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

from PyQt5.Qt import QIcon, Qt
from PyQt5 import QtGui, uic
from PyQt5.QtWidgets import QApplication,QDialog,QMainWindow, QVBoxLayout,\
    QLabel, QHBoxLayout

from wechatweb import WeChatWeb
from config import WechatConfig
from com.ox11.wechat.wechatwin import WeChatWin

#LauncherWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

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

class WeChatLauncher(QDialog):#, LauncherWindow

    timeout = login_state = False
    LOG_FILE = '%s/wechat.log'
    def __init__(self):
        QMainWindow.__init__(self)
        #LauncherWindow.__init__(self)
        #threading.Thread.__init__(self,name='wechat launcher')
        #self.setDaemon(True)
        self.setWindowTitle("WeChat網頁版")
        self.resize(260,360)
        
        self.wechat_web = WeChatWeb()
        self.config = WechatConfig()
        logging.basicConfig(filename=(WeChatLauncher.LOG_FILE)%(self.config.getAppHome()),filemode='w',level=logging.DEBUG,format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
        self.clean_log()
        main_loyout = QVBoxLayout()
        
        self.qrLabel = QLabel()
        qr_label_h_layout = QHBoxLayout()
        qr_label_h_layout.addStretch(1)
        qr_label_h_layout.addWidget(self.qrLabel)
        qr_label_h_layout.addStretch(1)
        
        qr_label_v_layout = QVBoxLayout()
        qr_label_v_layout.addStretch(1)
        qr_label_v_layout.addLayout(qr_label_h_layout)
        qr_label_v_layout.addStretch(1)
        
        self.label = QLabel("使用手機微信掃碼登錄")
        self.label.setAlignment(Qt.AlignHCenter)
        self.label_3 = QLabel("網頁版微信需要配合手機使用")
        self.label_3.setAlignment(Qt.AlignHCenter)
        main_loyout.addLayout(qr_label_v_layout)
        #main_loyout.addStretch(1)
        main_loyout.addWidget(self.label)
        main_loyout.addWidget(self.label_3)
        #main_loyout.addStretch(1)
        
        self.setLayout(main_loyout)
        
        #self.setupUi(self)
        self.setWindowIcon(QIcon("resource/icons/hicolor/32x32/apps/wechat.png"))
        self.setWindowIconText("WeChatWin 0.5")
        self.generate_qrcode()
        self.load_qr_code_image()
        self.login_timer = threading.Timer(0, self.login)
        self.login_timer.setDaemon(True)
        self.login_timer.start()

    def set_qr_timeout(self):
        WeChatLauncher.timeout = True
        self.generate_qrcode()
        self.load_qr_code_image()

    def load_qr_code_image(self):
        qrcode_path = self.config.getAppHome()+"/qrcode.jpg"
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
        if "200" == code:
            WeChatLauncher.login_state = True
        else:
            code = self.wechat_web.wait4login(0)
            WeChatLauncher.login_state = (True if "200" == code else False)
        logging.debug("code is %s"%code)
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
        logging.debug("closed")

def main():
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
        
