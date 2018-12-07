#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年4月10號

@author: zhaohongxing
'''
import os

from PyQt5.Qt import QStyledItemDelegate, QColor, QPixmap
from PyQt5.QtWidgets import QStyle
import datetime

class LabelDelegate(QStyledItemDelegate):
    
    ##############################################
    #         # 张三                                    2018/11/15
    #         #
    #         #
    #         # 您好                                                             x                    
    ##############################################
    
    HEAD_IMG_WIDTH = HEAD_IMG_HEIGHT = 45
    
    HEAD_IMG_TOP_MARGIN = HEAD_IMG_BOTTOM_MARGIN= 10
    HEAD_IMG_LEFT_MARGIN = 5
    
    Editable, ReadOnly = range(2)
    
    USER_NAME_COLUMN = 0
    DISPLAY_NAME_COLUMN_INDEX = 2
    #屏弊狀態0,1
    ROOM_STATUES_COLUMN = 3
    MSG_COUNT_COLUMN = 4
    LAST_MSG_BODY_COLUMN_INDEX = 5
    LAST_MSG_TIME_COLUMN_INDEX = 6
    
    DEFAULT_IMAGE = "./resource/images/default.png"
    #DEFAULT_IMAGE = "C:/Users/zhaohongxing/Pictures/aaa.jpg"
    
    #CONTACT_HEAD_HOME = ("/heads/contact/")
    APP_HOME = ("%s%s.wechat")%(os.path.expanduser('~'),os.sep)
    CUSTOM_FACE = "%s%scustomface"%(APP_HOME,os.sep)
    IMAGE_RECIVE = "%s%simageRec"%(APP_HOME,os.sep)
    
    def paint_count(self, painter, option,index):
        pass
    
    def paint_last_message(self, painter, option,index):
        painter.save()
        rect_x = option.rect.x()
        rect_y = option.rect.y()
        txt_x = rect_x+LabelDelegate.HEAD_IMG_LEFT_MARGIN+LabelDelegate.HEAD_IMG_WIDTH+5
        txt_y = rect_y+LabelDelegate.HEAD_IMG_TOP_MARGIN+10
        model = index.model()
        display_name_index = model.index(index.row(),LabelDelegate.DISPLAY_NAME_COLUMN_INDEX)
        display_name = model.data(display_name_index)
        if display_name:
            if len(display_name) > 8:
                display_name = "%s..."%display_name[0:8]
            painter.drawText(txt_x,txt_y, "%s"%display_name)
        #最後一條消息接收時間
        last_msg_received_time_index = model.index(index.row(),LabelDelegate.LAST_MSG_TIME_COLUMN_INDEX)
        last_message_received_time = model.data(last_msg_received_time_index)
        if last_message_received_time:
            last_message_received_time_str = self.format_last_message_received_time(last_message_received_time)
            painter.drawText(txt_x+115,txt_y, "%(s1)+10s"%{"s1":last_message_received_time_str})
        #最後一條消息
        last_msg_index = model.index(index.row(),LabelDelegate.LAST_MSG_BODY_COLUMN_INDEX)
        last_message = model.data(last_msg_index)
        if last_message:
            painter.drawText(txt_x,rect_y+LabelDelegate.HEAD_IMG_HEIGHT+3, "%s"%last_message)
        
        user_name_index = model.index(index.row(),LabelDelegate.USER_NAME_COLUMN)
        user_name = model.data(user_name_index)
        #如果是聊天室，则还是显示是否屏弊消息
        if user_name.startswith("@@"):
            pass
        painter.restore()
        
    def format_last_message_received_time(self,last_message_received_time):
        #如果last_message_received_time是今天，只显示时间
        #如果是昨天，则显示为昨天
        #如果是本周内的日期，则显示为星期几
        #否则就显示对应的日期
        #0（星期一）到6（星期日）
        last_message_datetime = datetime.datetime.strptime(last_message_received_time, "%Y-%m-%d %H:%M:%S")  

        today = datetime.date.today()
        diff_days = (today - last_message_datetime.date()).days
        if diff_days == 0:
            return last_message_datetime.strftime("%H:%M:%S")
        elif diff_days == 1:
            return "昨天"
        elif diff_days > 1 and diff_days <= 6:
            weekday = last_message_datetime.weekday()
            weekdays = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"]
            return weekdays[weekday]
        else:
            return last_message_datetime.strftime("%Y-%m-%d")
    
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
            #计算头像的坐标(head_image_x,head_image_y)
            rect_x = option.rect.x()
            rect_y = option.rect.y()
            head_image_x_offset = 5
            head_image_y_offset = 10
            head_image_x = rect_x + head_image_x_offset
            head_image_y = rect_y + head_image_y_offset
            image = ("%s%s%s.jpg")%(LabelDelegate.CUSTOM_FACE,os.sep,userName)
            if not os.path.exists(image):
                image = LabelDelegate.DEFAULT_IMAGE
            painter.drawPixmap(head_image_x,head_image_y,LabelDelegate.HEAD_IMG_WIDTH,LabelDelegate.HEAD_IMG_HEIGHT, QPixmap(image))
            if msgCount and int(msgCount) > 0:
                
                msgCount = int(msgCount)
                white = QColor(255, 0, 0)
                painter.setPen(white)
                painter.setBrush(white)
                #圈的半徑
                ellipse_r = 15
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
            #####
            painter.restore()
            self.paint_last_message(painter, option, index)
        else:
            super(LabelDelegate, self).paint(painter, option, index)
            
