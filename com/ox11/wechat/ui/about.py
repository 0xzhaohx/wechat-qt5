#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年4月13日

@author: zhaohongxing
'''
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QVBoxLayout,QDialog,QLabel
from PyQt5.QtCore import QSize

def __unicode(self,s):
    return s;

class About(QDialog):
    WIDTH = 460
    HEIGHT = 300
    
    def __init__(self,parent=None):
        super(About,self).__init__(parent)
        self.setModal(True)
        self.resize(QSize(About.WIDTH,About.HEIGHT))
        self.setWindowTitle(__unicode("關於"))
        self.about_initial()
        
    def about_initial(self):
        #
        mainLayout=QVBoxLayout()
        label = QLabel("v0.6")
        label.setAlignment(Qt.AlignHCenter)
        mainLayout.addWidget(label)
        #mainLayout.addWidget(self.emotion_table)
        self.setLayout(mainLayout)