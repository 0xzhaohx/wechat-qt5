#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年11月13日

@author: zhaohongxing
'''
import sys
import time
from PyQt5.QtWidgets import QVBoxLayout,QDialog,QLabel, QPushButton,\
    QApplication, QHBoxLayout
from PyQt5.QtCore import QSize

class Notice(QDialog):
    
    def __init__(self,parent=None):
        super(Notice,self).__init__(parent)
        self.setModal(True)
        self.resize(QSize(320,180))
        self.setFixedSize(self.width(),self.height())
        self.setWindowTitle("提示")
        self.about_initial()
        
    def about_initial(self):
        #
        mainLayout=QVBoxLayout()
        mainLayout.addStretch(1)
        st = time.strftime("%H:%M", time.localtime())
        tip_label = QLabel("目前賬號已於%s在其它裝置上登入。此用户端已退出。"%st)
        #label.setAlignment(Qt.AlignHCenter)
        tip_label.setWordWrap(True)
        mainLayout.addWidget(tip_label)
        mainLayout.addStretch(1)
        #水平部
        confirm_layout = QHBoxLayout()
        confirm_layout.addStretch(1)
        confirm = QPushButton("確定")
        confirm_layout.addWidget(confirm)
        confirm_layout.addStretch(1)
        mainLayout.addLayout(confirm_layout)
        #confirm_layout.addStretch(1)
        #mainLayout.addWidget(self.emotion_table)
        self.setLayout(mainLayout)
        confirm.clicked.connect(self.on_confirm_clicked)
        
    def on_confirm_clicked(self):
        self.accept()
        
def main():
    app = QApplication(sys.argv)
    launcher = Notice()
    if QDialog.Accepted == launcher.exec_():
        sys.exit(app.exec_())
        
if __name__ =="__main__":
    main()