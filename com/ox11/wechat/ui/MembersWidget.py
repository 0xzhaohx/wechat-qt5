#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-

'''
Created on 2018年6月15日

@author: zhaohongxing
'''
import os

from PyQt5.Qt import QIcon,QStandardItemModel, QApplication, QLabel
from PyQt5 import QtGui
from PyQt5.QtCore import QSize, pyqtSlot, pyqtSignal,QEvent
from PyQt5.QtWidgets import QTableView,QVBoxLayout,QDialog,QPushButton,QSpacerItem,QSizePolicy,\
    QLineEdit, QCheckBox

from com.ox11.wechat.ui.ContactsWindow import ContactsWindow
import wechatutil

class MembersWidget(QDialog):
    WIDTH = 205
    membersChanged = pyqtSignal(str)
    
    def __init__(self,member_list,contacts,parent = None):
        super(MembersWidget,self).__init__(parent)
        self.setMinimumSize(MembersWidget.WIDTH, 600)
        self.setFixedWidth(MembersWidget.WIDTH)
        self.user_home = os.path.expanduser('~')
        #self.setAcceptDrops(True)
        self.app_home = self.user_home + '/.wechat/'
        self.head_home = ("%s/heads"%(self.app_home))
        self.cache_home = ("%s/cache/"%(self.app_home))
        self.cache_image_home = "%s/image/"%(self.cache_home)
        self.contact_head_home = ("%s/contact/"%(self.head_home))
        self.default_head_icon = './resource/images/default.png'
        self.default_member_icon = './resource/images/webwxgeticon.png'
        self.members = member_list
        self.contacts = contacts
        #self.setWindowFlags(Qt.FramelessWindowHint)#|Qt.Popup
        self.membersTable = QTableView()
        self.membersTable.verticalHeader().setDefaultSectionSize(45)
        self.membersTable.verticalHeader().setVisible(False)
        self.membersTable.horizontalHeader().setDefaultSectionSize(45)
        self.membersTable.horizontalHeader().setVisible(False)
        mainLayout=QVBoxLayout()
        #
        self.member_search = QLineEdit("")
        self.member_search.setPlaceholderText("搜索聯天室成員")
        mainLayout.addWidget(self.member_search)
        #More
        self.more_members = QPushButton(wechatutil.unicode('顯示更多'))
        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        
        self.membersTableModel = QStandardItemModel(0,4)
        self.init_members_widget(self.members)
        mainLayout.addWidget(self.membersTable)
        mainLayout.addWidget(self.more_members)
        self.chat_room_name = QLabel("聯天室名稱")
        mainLayout.addWidget(self.chat_room_name)
        #
        self.chat_room_name_edit = QLineEdit("")
        mainLayout.addWidget(self.chat_room_name_edit)
        #
        self.chat_room_notice = QLabel("群組公告")
        mainLayout.addWidget(self.chat_room_notice)
        
        self.chat_room_notic_content = QLabel("暫無公告")
        mainLayout.addWidget(self.chat_room_notic_content)
        #
        self.my_name = QLabel("我在聯天室中的名稱")
        mainLayout.addWidget(self.my_name)
        
        self.my_name_content = QLineEdit("0x11")
        mainLayout.addWidget(self.my_name_content)
        
        self.display_name = QLabel("顯示成員在聯天室的名稱")
        mainLayout.addWidget(self.display_name)
        self.display_name_cb = QCheckBox()
        mainLayout.addWidget(self.display_name_cb)
        #
        self.message_mute = QLabel("訊息免打擾")
        mainLayout.addWidget(self.message_mute)
        self.mute_cb = QCheckBox()
        mainLayout.addWidget(self.mute_cb)
        #
        self.top = QLabel("置頂聯天")
        mainLayout.addWidget(self.top)
        self.top_cb = QCheckBox()
        mainLayout.addWidget(self.top_cb)
        
        self.storage = QLabel("保存到通訊綠")
        mainLayout.addWidget(self.storage)
        self.storage_cb = QCheckBox()
        mainLayout.addWidget(self.storage_cb)
        
        self.exit = QPushButton(wechatutil.unicode("刪除并退出"))
        mainLayout.addWidget(self.exit)
        
        mainLayout.addItem(self.verticalSpacer)
        self.setLayout(mainLayout)
        
    def update_members(self,members):
        self.members = members
        self.membersTableModel.removeRows(0, self.membersTableModel.rowCount())
        self.append_row(self.members)
        
    def init_members_widget(self,member_list):
        #self.membersTableModel.setHorizontalHeaderItem(0,QStandardItem("0000"))
        self.append_row(member_list)
        self.membersTable.setModel(self.membersTableModel)
        self.membersTable.setIconSize(QSize(40,40))
        self.membersTable.clicked.connect(self.member_click)
        
    def member_click(self):
        self.memberListWindow = ContactsWindow(self.contacts,self)
        self.memberListWindow.resize(400,600)
        self.memberListWindow.membersConfirmed.connect(self.route)
        self.memberListWindow.show()
    
    @pyqtSlot(str)
    def route(self,_object):
        self.membersChanged.emit(_object)
        
    def event(self, event):#
        if event.type() == QEvent.ActivationChange:
            if QApplication.activeWindow() != self:
                self.close()
        return QDialog.event(self, event)
        
    def append_row(self,members):
        if len(members) <= 0:
            return
        ###############
        cells = []
        #添加第一行
        item = QtGui.QStandardItem("+")
        cells.append(item)
        for member in members[0:3]:
            user_head_icon = self.contact_head_home + member['UserName']+".jpg"
            if not os.path.exists(user_head_icon):
                user_head_icon = self.default_member_icon
            display_name = member['DisplayName'] or member['NickName']
            item = QtGui.QStandardItem(QIcon(user_head_icon),wechatutil.unicode(display_name))
            cells.append(item)
        self.membersTableModel.appendRow(cells)
        i = 3
        #添加其他的
        members_len = len(members)
        if members_len > 19:
            members_len = 19
        while i < members_len:
            cells = []
            for member in members[i:i+4]:
                user_head_icon = self.contact_head_home + member['UserName']+".jpg"
                if not os.path.exists(user_head_icon):
                    user_head_icon = self.default_member_icon
                dn = member['DisplayName'] or member['NickName']
                if not dn:
                    dn = member['NickName']
                item = QtGui.QStandardItem(QIcon(user_head_icon),wechatutil.unicode(dn))
                cells.append(item)
            i = i + 4
            self.membersTableModel.appendRow(cells)