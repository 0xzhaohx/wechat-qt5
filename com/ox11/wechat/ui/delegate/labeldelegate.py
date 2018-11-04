#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年4月10號

@author: zhaohongxing
'''
import os

from PyQt5.Qt import QStyledItemDelegate, QColor, QPixmap
from PyQt5.QtWidgets import QStyle

class LabelDelegate(QStyledItemDelegate):
    
    HEAD_IMG_WIDTH = HEAD_IMG_HEIGHT = 45
    
    Editable, ReadOnly = range(2)
    
    USER_NAME_COLUMN = 0
    
    MSG_COUNT_COLUMN = 3
    
    DEFAULT_IMAGE = "./resource/images/default.png"
    
    #CONTACT_HEAD_HOME = ("/heads/contact/")
    APP_HOME = ("%s\\.wechat")%(os.path.expanduser('~'))
    CUSTOM_FACE = "%s\\customface"%(APP_HOME)
    IMAGE_RECIVE = "%s\\imageRec"%(APP_HOME)
    
    def paint(self, painter, option,index):
        if index.column() ==1:
            painter.save()
            model = index.model()
            userNameIndex = model.index(index.row(),LabelDelegate.USER_NAME_COLUMN)
            msgCountIndex = model.index(index.row(),LabelDelegate.MSG_COUNT_COLUMN)
            '''
            userName = model.data(userNameIndex).toString()
            msgCount = model.data(msgCountIndex).toString()
            '''
            userName = model.data(userNameIndex)
            msgCount = model.data(msgCountIndex)
            
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            rect_x = option.rect.x()
            rect_y = option.rect.y()
            head_image_x_offset = 5
            head_image_y_offset = 10
            head_image_x = rect_x + head_image_x_offset
            head_image_y = rect_y + head_image_y_offset
            image = ("%s\\%s.jpg")%(LabelDelegate.CUSTOM_FACE,userName)
            if not os.path.exists(image):
                image = LabelDelegate.DEFAULT_IMAGE
            painter.drawPixmap(head_image_x,head_image_y,LabelDelegate.HEAD_IMG_WIDTH,LabelDelegate.HEAD_IMG_HEIGHT, QPixmap(image))
            if msgCount and int(msgCount) > 0:
                
                msgCount = int(msgCount)
                white = QColor(255, 0, 0)
                painter.setPen(white)
                painter.setBrush(white)
                ellipse_r = 20
                ellipse_x = rect_x + LabelDelegate.HEAD_IMG_WIDTH - 5
                ellipse_y = rect_y + head_image_y_offset - 7.5
                
                painter.drawEllipse(ellipse_x,ellipse_y,ellipse_r,ellipse_r)
                red = QColor(255, 255, 255)
                painter.setPen(red)
                painter.setBrush(red)
                
                msg_count_x = rect_x + LabelDelegate.HEAD_IMG_WIDTH + 2.5
                
                if msgCount >= 10 and msgCount < 100:
                    msg_count_x = msg_count_x - 0.5
                elif msgCount >= 100 and msgCount < 1000:
                    msg_count_x = msg_count_x - 3.5
                elif msgCount >= 1000 and msgCount < 10000:
                    msg_count_x = msg_count_x - 5
                msg_count_y = rect_y + head_image_y_offset + 5
                painter.drawText(msg_count_x,msg_count_y, "%d"%msgCount)
            painter.restore()
        else:
            super(LabelDelegate, self).paint(painter, option, index)