#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年3月25日

@author: zhaohongxing
'''
import random

__date__='2018年3月25日'

'''
import sip
sip.setapi('QString', 1)
sip.setapi('QVariant', 1)
'''

import sys
import os
import threading
import re
from time import sleep
import time

import xml.dom.minidom
import json
import logging

from PyQt5.QtGui import QIcon, QCursor, QTextImageFormat,QStandardItemModel
from PyQt5.QtWidgets import QLabel,QDialog,QFileDialog,QMenu,QVBoxLayout,QAction,QMainWindow
from PyQt5 import QtGui, uic
from PyQt5.QtCore import QSize, pyqtSlot, pyqtSignal, QPoint
from PyQt5.Qt import Qt
    
import wechatutil
from message import Message
from config import WechatConfig
from com.ox11.wechat import property
from com.ox11.wechat.ui.emotion import Emotion
from com.ox11.wechat.ui.MembersWidget import MembersWidget
from com.ox11.wechat.ui.about import About
from com.ox11.wechat.ui.delegate.labeldelegate import LabelDelegate
from com.ox11.wechat.ui.ContactsWindow import ContactsWindow
from user_manager import UserManager
from message_manager import MessageManager
from wechatweb import WeChatWeb
from com.ox11.wechat.ui.notice import Notice
'''
reload(sys)

sys.setdefaultencoding('utf-8')
'''

qtCreatorFile = "resource/ui/wechatwin-0.6.1.ui"

WeChatWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class WeChatWin(QMainWindow, WeChatWindow):
    
    window_list = []

    I18N = "resource/i18n/resource.properties"
    
    EMOTION_DIR = "./resource/expression"
    
    MESSAGE_TEMPLATE = "./resource/messages.html"
    
    LOG_FORMAT = '%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s'
    '''
        webwx_init
        ->webwxstatusnotify()
        ->(webwx_geticon|webwx_batch_getheadimg)
        ->webwx_getcontact
        ->first call webwx_batch_getcontact
        ->(webwx_geticon|webwx_batch_getheadimg)
        ->second call webwx_batch_getcontact
    '''
    
    initialed = pyqtSignal()
    #收到消息信号
    messageReceived = pyqtSignal(str)
    #TODO NEVER USED
    membersChanged = pyqtSignal(str)
    
    membersConfirmed = pyqtSignal(str)
    
    customFaceDownloadSuccess = pyqtSignal(str)
    
    MESSAGE_COUNT_CELL_INDEX = 4
    
    def __init__(self):
        QMainWindow.__init__(self)
        WeChatWindow.__init__(self)
        self.setAcceptDrops(True)
        self.config = WechatConfig()
        logging.basicConfig(filename="./wechat.log",format="%(asctime)s %(message)s",filemode="w",level=logging.DEBUG)
        self.default_head_icon = './resource/images/default.png'
        self.current_chat_contact = None
        self.messages_pool = {}
        #没有來得及處理的新消息,主要用於存放UI未初始化完時收到消息，然後等初始結束處理
        self.blocked_messages_pool = []
        self.prepare4Environment()
        self.wechat_web = WeChatWeb()
        #self.qApp=qApp
        self.setupUi(self)
        self.setWindowIcon(QIcon("resource/icons/hicolor/32x32/apps/wechat.png"))
        #user manager
        #message manager
        self.user_manager = UserManager()
        self.message_manager = MessageManager()
        #initial messages
        #should initial before chat item click
        ap = os.path.abspath(WeChatWin.MESSAGE_TEMPLATE)
        #self.messages.load(QUrl.fromLocalFile(ap))
        #self.messages.loadFinished.connect(self.loadFinished)
        #after initial,do login
        self.wechat_web.login()
        #IMPORTANT
        #wxinitial()執行初始化工作，獲取部分的聊天會話記錄以及全部的通訊錄，并用返回的部分聊天會話數据第一次調用batch_get_contact()
        #當完成UI的初始化之後，synccheck會返回一個初始化的消息，以獲取全部的聊天會話記錄。
        #再次用會話記錄調用batch_get_contact(parameter)[現在len(parameter)的長度是50，不知是不是做了優化，分批次調用batch_get_contact(parameter)]
        self.wxinitial()
        #self.synct = WeChatSync(self.wechat_web)
        #self.synct.start()
        self.sync_timer = threading.Timer(5, self.synccheck)
        self.sync_timer.setDaemon(True)
        self.sync_timer.start()
        
        self.memberListWidget = None
        self.showImageDialog = None
        #self.membersConfirmed.connect(self.getSelectedUsers)
        #chatsModel共4列
        #列1:userName(隐藏)
        #列2：image
        #列3：displayName
        #列4:屏弊狀態
        #列5:未读的消息数
        #TODO
        #列6:最後收到消息的內容
        #列7:最後收到消息的時間
        #列8:如果是群，群是否屏弊了消息.Statues=1，没有屏弊；Statues=0，屏弊
        self.chatsModel = QStandardItemModel(0,7)
        #friendsModel共3列
        #列1:userName(隐藏)
        #列2：image
        #列3：displayName
        self.friendsModel = QStandardItemModel(0,3)
        self.publicModel = QStandardItemModel()
        self.friendsWidget.setVisible(False)
        self.publicWidget.setVisible(False)
        self.profileWidget.setVisible(False)
        self.init_chat_contacts()
        self.init_friends()
        self.init_public()
        self.init_emotion_code()
        self.initialed.connect(self.process_blocked_messages)
        self.initialed.connect(self.startDwonloadCustomFace)
        
        self.chatAreaWidget.setVisible(False)
        self.chatsWidget.setItemDelegate(LabelDelegate())
        self.chatsWidget.setIconSize(QSize(45,45))
        self.chatsWidget.setModel(self.chatsModel)
        self.chatsWidget.selectionModel().selectionChanged.connect(self.chat_item_clicked)
        self.chatsWidget.setColumnHidden(0,True)
        self.chatsWidget.setColumnHidden(2,True)
        self.chatsWidget.setColumnHidden(3,True)
        self.chatsWidget.setColumnHidden(4,True)
        self.chatsWidget.setColumnHidden(5,True)
        self.chatsWidget.setColumnHidden(6,True)
        self.chatsWidget.setColumnWidth(1, 220);
        self.chatsWidget.setColumnWidth(3, 30);
        #self.chatsWidget.horizontalHeader().setStretchLastSection(True)
        self.friendsWidget.setModel(self.friendsModel)
        self.friendsWidget.setIconSize(QSize(45,45))
        
        ##self.friendsWidget.selectionModel().selectionChanged.connect(self.member_item_clicked)
        self.friendsWidget.setColumnHidden(0,True)
        self.friendsWidget.setColumnWidth(1, 70);
        self.friendsWidget.setColumnWidth(3, 30);
        self.publicWidget.setModel(self.publicModel)

        self.chatButton.clicked.connect(self.switch_chat)
        self.friendButton.clicked.connect(self.switch_friend)

        self.sendButton.clicked.connect(self.send_message)
        
        self.pushButton.clicked.connect(self.to_chat)
        self.emotionButton.clicked.connect(self.select_emotion)
        self.selectImageFileButton.clicked.connect(self.select_document)
        #connect the slot before #wxinitial()
        self.messageReceived.connect(self.webwx_sync_process)
        #self.currentChatUser.clicked.connect(self.current_chat_user_click)
        #显示成员列表
        self.showMemberButton.clicked.connect(self.showMembers)
        self.addMenu4SendButton()
        self.addMenu4SettingButton()
        
        self.customFaceDownloadSuccess.connect(self.updateCustomFace)
        #
        self.initialed.emit()
    
    @pyqtSlot()
    def loadFinished(self):
        print('loadFinished')
        self.messages.page().mainFrame().addToJavaScriptWindowObject("Wechat", self)
        
    @pyqtSlot(str)
    def showImage(self,image):
        if self.showImageDialog:
            print(image)
            self.showImageDialog.show()
        else:
            self.showImageDialog = QDialog(self)
            #self.showImageDialog.setModal(True)
            mainLayout = QVBoxLayout()
            image_label = QLabel()
            s_image = QtGui.QImage()
            user_icon = self.config.get + self.user_manager.get_user()['UserName'] + ".jpg"
            if s_image.load(user_icon):
                image_label.setPixmap(QtGui.QPixmap.fromImage(s_image))
            mainLayout.addWidget(image_label)
            self.showImageDialog.setLayout(mainLayout)
            self.showImageDialog.show()
            
    @pyqtSlot(str)
    def getSelectedUsers(self,users):
        '''
        #建群
        '''
        if not users:
            return
        #dictt = json.loads(str(users))
        user_list = str(users).split(";")
        member_list = []
        for s_user in user_list:
            if len(s_user) > 1:
                user = {}
                user['UserName']=s_user
                member_list.append(user)
        user = {}
        user['UserName']=self.current_chat_contact["UserName"]
        member_list.append(user)
        
        response_data = self.wechat_web.webwx_create_chatroom(member_list)
        #print("webwx_create_chatroom response:%s"%response_data)
        if not response_data:
            logging.error("创建失败")
            return
        data_dict = json.loads(response_data)
        if data_dict["BaseResponse"]["Ret"] == 0:
            chat_room_name = data_dict["ChatRoomName"]
            data = {
                'Count': 1,
                'List': [{"UserName":chat_room_name,"ChatRoomId":""}]
            }
            batch_response = self.wechat_web.webwx_batch_get_contact(data)
            if batch_response['Count'] and batch_response['Count'] > 0:
                new_contact = batch_response['ContactList'][0]
                remark_name = ("%s,%s,%s")%(self.wechat_web.user_manager()["NickName"],self.current_chat_contact["NickName"],"")
                new_contact["RemarkName"]=remark_name
                self.user_manager.append_chat_contact(new_contact)
                self.wechat_web.webwx_get_head_img(new_contact["UserName"], new_contact["HeadImgUrl"])
                self.append_contact_row(new_contact,self.chatsModel,action="INSERT",row=0)
    
    @pyqtSlot(str)
    def get_select_emotion(self,emotion):
        cursor = self.draft.textCursor()
        imageFormat =QTextImageFormat();

        imageFormat.setName(os.path.join(Emotion.EMOTION_DIR,str(emotion)));
        cursor.insertImage(imageFormat)
        '''
        self.draft.moveCursor(QTextCursor.End)
        self.draft.append("<img src=%s>"%(os.path.join(Emotion.EMOTION_DIR,str(emotion))))
        '''
    @pyqtSlot(str)
    def webwx_sync_process(self, data):
        '''
        @param data
        MSTTYPE:
        MSGTYPE_TEXT: 1,文本消息
        MSGTYPE_IMAGE: 3,图片消息
        MSGTYPE_VOICE: 34,语音消息
        37,好友确认消息
        MSGTYPE_VIDEO: 43,
        MSGTYPE_MICROVIDEO: 62,
        MSGTYPE_EMOTICON: 47,
        MSGTYPE_APP: 49,
        MSGTYPE_VOIPMSG: 50,
        51,微信初始化消息
        MSGTYPE_VOIPNOTIFY: 52,
        MSGTYPE_VOIPINVITE: 53,
        MSGTYPE_LOCATION: 48,
        MSGTYPE_STATUSNOTIFY: 51,
        MSGTYPE_SYSNOTICE: 9999,
        MSGTYPE_POSSIBLEFRIEND_MSG: 40,
        MSGTYPE_VERIFYMSG: 37,
        MSGTYPE_SHARECARD: 42,
        MSGTYPE_SYS: 10000,
        MSGTYPE_RECALLED: 10002,  // 撤销消息
        ''' 
        if not data:
            return False
        data = json.loads(str(data), object_hook=wechatutil.decode_data)
        ret_code = data['BaseResponse']['Ret']

        if ret_code == 0:
            pass
        else:
            return False

        add_msg_count = data['AddMsgCount']
        if add_msg_count == 0:
            return True

        messages = data['AddMsgList']

        for message in messages:
            self.msg_handle(message)
               
    def process_blocked_messages(self):
        logging.debug('start process blocked_messages_pool')
        for message in self.message_manager.get_block_messages():#self.blocked_messages_pool:
            self.msg_handle(message)
    
    def wxinitial(self):
        """
        "登陆成功之后调用此方法，主要用于取得部分聊天用户，
        "如果返回用户中有群，则要用包含所有群的user_name的一个数组去调用batch_get_contact，以获取群成员列表数据
        "返回的仅仅是部分数据，用户不全，其他的数据要在界面显示之后再加载
        """
        wx_init_response = self.wechat_web.webwx_init()
        #初始化user_manger中的__user
        self.user_manager.set_user(wx_init_response["User"])
        logging.debug("当前登陆人是：%s"%self.user_manager.get_user())
        mini_chat_list = wx_init_response['ContactList']
        self.user_manager.set_chat_list(mini_chat_list)
        logging.debug("取得的部分会话联系人有%d个："%len(mini_chat_list))
        
        #self.wechat_web.webwxstatusnotify()
        self.setupwxuser()
        #获取所有的联系人
        contacts = self.wechat_web.webwx_get_contact()
        logging.debug("联系人%d:"%(len(contacts)))
        #logging.debug(contacts)
        self.user_manager.set_contacts(contacts)
        self.synccheck(loop=False)
        #fetch the icon or head image that weixin initial response
        groups = []
        for contact in self.user_manager.get_chat_list():
            user_name = contact['UserName']
            head_img_url = contact['HeadImgUrl']
            if not user_name or not head_img_url:
                continue
            if self.isChatRoom(user_name):
                #prepare arguments for batch_get_contact
                group = {}
                group['UserName'] = contact['UserName']
                group['ChatRoomId'] = ''
                groups.append(group)
                #doanload head image
                if os.path.exists("%s%s%s.jpg"%(self.config.customFace,os.sep,user_name)):
                    logging.debug("custom face of chatroom %s is exist"%user_name)
                else:
                    self.wechat_web.webwx_get_head_img(user_name,head_img_url)
            elif user_name.startswith('@'):
                if os.path.exists("%s%s%s.jpg"%(self.config.customFace,os.sep,user_name)):
                    logging.debug("custom face of %s is exist"%user_name)
                else:
                    self.wechat_web.webwx_get_icon(user_name,head_img_url)
                pass
            else:
                pass
        params = {
            'Count': len(groups),
            'List': groups
        }
        #IMPORT第一次调用
        self.batch_get_contact(data=params)
        
    def addMenu4SendButton(self):
        menu = QMenu()
        enterAction = QAction(wechatutil.unicode("按Enter發送消息"),self)
        menu.addAction(enterAction)
        self.sendSetButton.setMenu(menu)
        
    def addMenu4SettingButton(self):
        menu = QMenu()
        createChatRoorAction = QAction(wechatutil.unicode("開始聊天"),self)
        menu.addAction(createChatRoorAction)
        notifySwitchAction = QAction(wechatutil.unicode("關閉通知"),self)
        menu.addAction(notifySwitchAction)
        soundSwitchAction = QAction(wechatutil.unicode("關閉聲音"),self)
        menu.addAction(soundSwitchAction)
        contactManageAction = QAction(wechatutil.unicode("聯系人管理"),self)
        menu.addAction(contactManageAction)
        logoutAction = QAction(wechatutil.unicode("退出"),self)
        menu.addAction(logoutAction)
        aboutAction = QAction(wechatutil.unicode("關於"),self)
        menu.addAction(aboutAction)
        self.settingButton.setMenu(menu)
        
        aboutAction.triggered.connect(self.showAbout)
        logoutAction.triggered.connect(self.logout)
        
    def showAbout(self):
        about = About(self)
        about.show()
        
    def init_emotion_code(self):
        self.emotionscode = property.parse(WeChatWin.I18N).properties or {}
        
    def batch_get_contact(self,data=None):
        logging.debug("invoke batch_get_contact(....)")
        #获取群的祥细信息，如群成员，群名称等
        params = data
        logging.debug("parameter of invoke batch_get_contact() is %s"%params)
        response = self.wechat_web.webwx_batch_get_contact(params)
        #logging.debug("response of batch_get_contact %s"%str(response))
        '''
        session_response中的contact里面有群成员，所以更新chat_contact
        if response['Count'] and response['Count'] > 0:
            session_list = response['ContactList']
            for x in session_list:
                for i,ss in enumerate(self.wechat_web.getChatContacts()):
                    if ss["UserName"] == x["UserName"]:
                        self.wechat_web.update_chat_contact(i,x)
                        break
        '''
        for chat_room in response['ContactList']:
            if not chat_room['UserName']:
                continue
            
            #如果群没有名字，则取前2个成员名字的组合作为群名称
            if not chat_room["NickName"] and not chat_room["DisplayName"]:
                displayNames = []
                for _member in chat_room["MemberList"][:2]:
                    displayNames.append(_member['DisplayName'] or _member['NickName'])
                        
                chat_room["DisplayName"] = "、".join(displayNames)
            #遍历所有的通信錄，把聯天室加入聯系人列表
            for i,member in enumerate(self.user_manager.get_contacts()):
                exist = False
                if chat_room["UserName"] == member["UserName"]:
                    exist = True
                    self.user_manager.update_chat_contact(chat_room)
                    break
            if not exist:
                self.user_manager.append_contact(chat_room)
            #更新chat_contact,以使其群成员有数据
            for i,chat_contact in enumerate(self.user_manager.get_chat_list()):
                if chat_room["UserName"] == chat_contact["UserName"]:
                    self.user_manager.update_chat_contact(i,chat_room)
                    break
        return response
    
    def prepare4Environment(self):
        if os.path.exists(self.config.customFace):
            self.__remove()
        else:
            os.makedirs(self.config.customFace)
            
        if not os.path.exists(self.config.imageRecive):
            os.makedirs(self.config.imageRecive)
            
    def __remove(self):
        '''
        #删除下载的头像文件
        '''
        for i in os.listdir(self.config.customFace):
            head_icon = os.path.join(self.config.customFace,i)
            if os.path.isfile(head_icon):
                os.remove(head_icon)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        print("dragEnterEvent")

    def dragMoveEvent(self, event):
        print("dragMoveEvent")
    
    def isImage(self,path):
        if not path:
            return False
        if path.endswith("jpg") or path.endswith("jpeg") or path.endswith("png"):
            return True
    '''
    def mousePressEvent(self, event):
        #重写Event事件，用以处理成员列表隠藏
        print("event")
        sender = self.sender()
        print(sender)
        print(event.button())
        if event.button() == Qt.LeftButton or event.button() == Qt.RightButton:
            #遍历输出拖动进来的所有文件路径
            print("okkkkkkkkkkkkkkkkk")
            self.membersWidget.setVisible(False)
        else:
            #super(Button,self).dropEvent(event)
            pass
        #return QWidget.mousePressEvent(event)
    '''
    
    def dropEvent(self, event):
        #print("dropEvent")
        if event.mimeData().hasUrls():
            #遍历输出拖动进来的所有文件路径
            for url in event.mimeData().urls():
                file_name = str(url.toLocalFile())
                if self.isImage(file_name):
                    self.draft.append("<img src=%s width=80 height=80>"%(file_name))
            event.acceptProposedAction()
        else:
            #super(Button,self).dropEvent(event)
            pass
    
    def load_image(self, img_path,use_default=True):
        image = QtGui.QImage()
        if image.load(img_path):
            return image
        else:
            if use_default:
                image.load(self.config.getAppHome())

    def setupwxuser(self):
        user = self.user_manager.get_user()
        nickName = user['NickName']
        self.userNameLabel.setText(wechatutil.unicode(nickName))
        user_icon = "%s\\%s.jpg"%(self.config.customFace,user['UserName'] )
        user_head_image = QtGui.QImage()
        if user_head_image.load(user_icon):
            self.headImageLabel.setPixmap(QtGui.QPixmap.fromImage(user_head_image).scaled(40, 40))
        else:
            if user_head_image.load(self.config.getDefaultIcon()):
                self.headImageLabel.setPixmap(QtGui.QPixmap.fromImage(user_head_image).scaled(40, 40))

    def code_emotion(self,msg):
        """
        #把消息中的表情图片编码成表情格式。即：[xxx]
        """
        image_pattern=re.compile(r'src="([.*\S]*\.gif)"',re.I)
        paragraph_pattern = re.compile(r'<p style=".*\S">(.+?)</p>', re.I)
        pimages = []
        paragraphs = paragraph_pattern.findall(msg)
        for paragraph in paragraphs:
            pimage = {}
            pimage["p"]=paragraph
            images = image_pattern.findall(paragraph,re.I)
            for image in images:
                for key,emotioncode in self.emotionscode.items():
                    epath = os.path.join(WeChatWin.EMOTION_DIR,("%s.gif")%key)
                    imagemark = ('<img src="%s" />')%(epath)
                    if image ==epath:
                        pcode = paragraph.replace(imagemark,'[%s]'%(wechatutil.unicode(emotioncode)))
                        #print("p coded:%s"%pcode)
                        pimage["p"]=pcode
                        break
            pimage["images"]=images
            pimages.append(pimage)
        return pimages
    
    def decode_emotion(self,msg):
        pattern =re.compile(u"\[[\u4e00-\u9fa5]{1,3}\]")
        result=re.findall(pattern,msg)
        for emotion in result:
            #print emotion
            for key,val in self.emotionscode.items():
                if emotion ==("[%s]")%(val):
                    epath = os.path.join(WeChatWin.EMOTION_DIR,("%s.gif")%key)
                    msg = msg.replace(emotion,("<img src=%s>")%(epath))
                    break
        return msg
        
    def append_chat_contact(self,chat_contact,action="APPEND",row=None):
        '''
        :param action APPEND OR INSERT,APPEND value is default
        '''
        ###############
        cells = []
        #1 cell user name item
        user_name = chat_contact['UserName']
        user_name_cell = QtGui.QStandardItem(wechatutil.unicode(user_name))
        cells.append(user_name_cell)
        #2 cell
        user_head_icon = "%s\\%s.jpg"%(self.config.customFace,user_name)
        item = QtGui.QStandardItem(QIcon(user_head_icon),"")
        cells.append(item)
        #3 cell
        dn = chat_contact['DisplayName'] or chat_contact['RemarkName'] or chat_contact['NickName']
        #if not dn:
            #dn = contact['NickName']
        # user remark or nick name
        display_name_item = QtGui.QStandardItem(wechatutil.unicode(dn))
        cells.append(display_name_item)
        #4 cell[]
        statues_item = QtGui.QStandardItem(chat_contact["Statues"])
        cells.append(statues_item)
        #5 cell[message count]
        tips_count_item = QtGui.QStandardItem()
        cells.append(tips_count_item)
        #6 cell[last message body]
        last_message_item = QtGui.QStandardItem()
        cells.append(last_message_item)
        #7 cell[last message received time]
        timess = ["12:21","13:34","09:34","21:22","15:45","17:42","10:34"]
        last_message_recevied_time_item = QtGui.QStandardItem(timess[random.randint(0,len(timess)-1)])
        cells.append(last_message_recevied_time_item)
        #8 cell[chat room status]
        chat_room_status_item = QtGui.QStandardItem()
        cells.append(chat_room_status_item)
        
        if "APPEND" == action:
            self.chatsModel.appendRow(cells)
        elif "INSERT" == action and row >= 0:
            self.chatsModel.insertRow(row,cells)
        else:
            self.chatsModel.appendRow(cells)
            
    def append_friend(self,contact,action="APPEND",row=None):
        '''
        :param action APPEND OR INSERT,APPEND value is default
        '''
        ###############
        cells = []
        # user name item
        user_name = contact['UserName']
        user_name_item = QtGui.QStandardItem(wechatutil.unicode(user_name))
        cells.append(user_name_item)
        
        user_head_icon = "%s%s%s.jpg"%(self.config.customFace,os.sep, user_name)
        if not os.path.exists(user_head_icon):
            user_head_icon = "./resource/images/default.png"
        
        item = QtGui.QStandardItem(QIcon(user_head_icon),"")
        cells.append(item)
        
        _name = contact['DisplayName'] or contact['RemarkName'] or contact['NickName']
        #if not dn:
            #dn = contact['NickName']
        # user remark or nick name
        _name_item = QtGui.QStandardItem(wechatutil.unicode(_name))
        cells.append(_name_item)
        #
        if "APPEND" == action:
            self.friendsModel.appendRow(cells)
        elif "INSERT" == action and row >= 0:
            self.friendsModel.insertRow(row,cells)
        else:
            self.friendsModel.appendRow(cells)
        
    def messages_clear(self):
        #ap = os.path.abspath(WeChatWin.MESSAGE_TEMPLATE)
        #self.messages.load(QUrl.fromLocalFile(ap))
        #self.messages.page().mainFrame().evaluateJavaScript("clearr();")
        self.messages.setText("")
        pass
        
    def init_chat_contacts(self):
        '''
        contact table (5 columns)
        column 1:user name(will be hidden)
        column 2:head icon
        column 3:remark or nick name
        column 4:message count tips(will be hidden)
        :return:
        '''
        #self.chatsWidget.setColumnCount(4)
        ''''''
        #print("初始化init_chat_contacts()")
        for chat_contact in self.user_manager.get_chat_list():
            self.append_chat_contact(chat_contact)
            #print(":UserName:",chat_contact["UserName"],";NickName:",chat_contact["NickName"])
            
        '''
        for session in sorted([x for x in self.wechat_web.friend_list if x["AttrStatus"] and x["AttrStatus"] > 0],key=lambda ct: ct["AttrStatus"],reverse=True):
            exist = False
            for contact in self.wechat_web.chat_list:
                if contact["UserName"] == session["UserName"]:
                    exist = True
            if not exist:
                self.append_contact_row(session,self.chatsModel)
        '''
        #self.chatsWidget.clicked.connect(self.chat_item_clicked)

    def init_friends(self):
        ''''''
        #self.friendsModel.setColumnHidden(0,True)
        '''
        /***/
        /*去掉每行的行号*/ 
        QHeaderView *headerView = table->verticalHeader();  
        headerView->setHidden(true);  
        '''
        self.friendsWidget.setColumnHidden(1,True)
        group_contact_list = []
        for member in self.user_manager.get_contacts():
            group_contact_list.append(member)
        group_contact_list.sort(key=lambda mm: mm['RemarkPYInitial'] or mm['PYInitial'])
        #group_contact_list.sort(key=lambda mm: mm['RemarkPYQuanPin'] or mm['PYQuanPin'])
        for member in group_contact_list:#.sort(key=lambda m: m['PYInitial'])
            #print(member)
            py_quan_pin = member["PYQuanPin"]
            user = None
            if py_quan_pin:
                user = self.user_manager.get_user_by_id(py_quan_pin)
            #如果已存在
            if user:
                pass
            else:
                self.user_manager.insert_user(member)
            self.append_friend(member)
            
        self.friendsWidget.clicked.connect(self.member_item_clicked)

    def init_public(self):
        pass
        #self.readerListWidget.addItem("readers")
        #self.readerListWidget.clicked.connect(self.contact_cell_clicked)

    def switch_chat(self,show=False):
        '''
        :desc 切换到聊天记录列表.如果已经有选中的聊天对像，
        则要把聊天记历史记录、发送按钮等显示出来，同时把
        '''
        current_row =self.chatsWidget.currentIndex().row()
        if current_row > 0 or show:
            self.chatAreaWidget.setVisible(True)
            self.label.setVisible(False)
        else:
            self.chatAreaWidget.setVisible(False)
            self.label.setVisible(True)
            
        self.chatsWidget.setVisible(True)
        
        self.friendsWidget.setVisible(False)
        self.profileWidget.setVisible(False)

    def public_button_clicked(self):
        self.friendsWidget.setVisible(False)
        self.chatsWidget.setVisible(False)
        self.publicWidget.setVisible(True)

    def switch_friend(self):
        current_row =self.friendsWidget.currentIndex().row()
        if current_row > 0:
            self.label.setVisible(False)
            self.profileWidget.setVisible(True)
        else:
            self.label.setVisible(True)
            self.profileWidget.setVisible(False)
            
        self.friendsWidget.setVisible(True)
        self.chatsWidget.setVisible(False)
        self.chatAreaWidget.setVisible(False)

    def get_contact(self,user_name):
        return self.get_member(user_name)

    def get_member(self,user_name):
        for member in self.user_manager.get_chat_list():
            if user_name == member['UserName']:
                return member
            
        for member in self.user_manager.get_contacts():
            if user_name == member['UserName']:
                return member
            
    def chat_item_clicked(self):
        #
        #TODO clear message's pool
        #
        if self.chatAreaWidget.isHidden():
            self.chatAreaWidget.setVisible(True)
            self.label.setVisible(False)
            
        if self.current_chat_contact:
            self.messages_clear()
        current_row = self.chatsWidget.currentIndex().row()
        user_name_cell_index = self.chatsModel.index(current_row,0)
        user_name_cell = self.chatsModel.data(user_name_cell_index)

        tip_index = self.chatsModel.index(current_row,WeChatWin.MESSAGE_COUNT_CELL_INDEX)
        tips_item = self.chatsModel.data(tip_index)
        if tips_item:
            self.chatsModel.setData(tip_index, "")
        head_tips_index = self.chatsModel.index(current_row,0)
        tips_item = self.chatsModel.data(head_tips_index)
        #if message_count:
        #    count = int(message_count)
        #TODO 
        user_name = user_name_cell
        logging.debug("current click user is %s"%user_name)
        if self.isChatRoom(user_name):
            contact = self.get_member(user_name)
            display_name = contact['DisplayName'] or contact['RemarkName'] or contact['NickName']
            self.currentChatUser.setText(("%s (%d)")%(wechatutil.unicode(display_name),contact["MemberCount"]))
        else:
            contact = self.get_contact(user_name)
            display_name = contact['DisplayName'] or contact['RemarkName'] or contact['NickName']
            self.currentChatUser.setText(wechatutil.unicode(display_name))
        self.current_chat_contact = contact
        #self.messages_clear()
        #self.messages.setText('')
        self.draft.setText('')
        cached_messages = self.message_manager.get_messages(user_name)#self.messages_pool.get(user_name) or []
        #for (key,messages_list) in self.msg_cache.items():
        #for (key,messages_list) in msgss:
            #if user_name == key:
        for message in cached_messages:
            msg_type = message['MsgType']
            if msg_type:
                if msg_type == 2 or msg_type == 51 or msg_type == 52:
                    continue
                if msg_type == 1:
                    self.text_msg_handler(message)
                elif msg_type == 3:
                    self.image_msg_handler(message)
                elif msg_type == 34:
                    self.voice_msg_handler(message)
                elif msg_type == 49:
                    self.app_msg_handler(message)
                elif msg_type == 10002:
                    self.sys_msg_handler(message)
                elif msg_type == 10000:
                    self.default_msg_handler(message)
                else:
                    self.default_msg_handler(message)
                #break
    def showMembers(self):
        '''
        :desc 处厘显示成员列表方法
        '''
        self.current_chat_user_click()
        '''
        if self.membersWidget.isHidden():
            self.membersWidget.setVisible(True)
        else:
            self.membersWidget.setVisible(False)
        self.aaaa()
        '''
    '''
    def aaaa(self):
        memebers = [self.current_chat_contact]
        #如果是群，则要显示所有的群成员
        if self.current_chat_contact['UserName'].find('@@') >= 0:
            memebers = self.current_chat_contact["MemberList"]
        #更新
        self.updateMembers(memebers)
    '''
        
    def calculate_members_widget_size(self):
        #rect包含了窗口的整个的高度和宽度
        frame_geometry = self.frameGeometry()
        geometry = self.geometry()
        #member_x=主窗口的x()+䜃窗口的WIDTH
        member_x = self.x()+frame_geometry.width()
        member_y = self.y()
        member_width = MembersWidget.WIDTH
        member_height = geometry.height()
        print("self.x():%d,self.y():%d"%(self.x(),self.y()))
        print("member_x:%d,member_y:%d"%(member_x,member_y))
        print("member_width:%d,member_height:%d"%(member_width,member_height))
        return (member_x,member_y,member_width,member_height)
    
    def current_chat_user_click(self):
        '''
        :desc 显示成员列表方法
        '''
        memebers = [self.current_chat_contact]
        if self.current_chat_contact['UserName'].find('@@') >= 0:
            memebers = self.current_chat_contact["MemberList"]
        if self.memberListWidget:
            if self.memberListWidget.isHidden():
                (member_x, member_y,member_width,member_height) = self.calculate_members_widget_size()
                #update memberslist
                self.memberListWidget.update_members(memebers)
                
                self.memberListWidget.resize(member_width,member_height)
                self.memberListWidget.move(member_x, member_y)
                self.memberListWidget.show()
            else:
                self.memberListWidget.hide()
        else:
            self.memberListWidget = MembersWidget(memebers,self.user_manager.get_contacts(),self)
            (member_x, member_y,member_width,member_height) = self.calculate_members_widget_size()
            self.memberListWidget.resize(member_width,member_height)
            self.memberListWidget.move(member_x, member_y)
            #update memberslist
            self.memberListWidget.update_members(memebers)
            self.memberListWidget.membersChanged.connect(self.getSelectedUsers)
            self.memberListWidget.show()
            
    def member_item_clicked(self):
        self.profileWidget.setVisible(True)
        self.chatAreaWidget.setVisible(False)
        self.label.setVisible(False)
        current_row =self.friendsWidget.currentIndex().row()
        user_name_index = self.friendsModel.index(current_row,0)
        user_name_o = self.friendsModel.data(user_name_index)
        '''python2
        user_name = user_name_o.toString()
        '''
        user_name = user_name_o
        contact = self.get_member(user_name)
        self.user_name_label.setVisible(False)
        self.user_name_label.setText(user_name)
        if contact:
            #user_icon = self.config.getContactHeadHome() + contact['UserName'] + ".jpg"
            user_icon = "%s\\%s.jpg"%(self.config.customFace, contact['UserName'])
            user_head_image = QtGui.QImage()
            if user_head_image.load(user_icon):
                self.avater_label.setPixmap(QtGui.QPixmap.fromImage(user_head_image).scaled(132, 132))
            else:
                if user_head_image.load(self.config.getDefaultIcon()):
                    self.avater_label.setPixmap(QtGui.QPixmap.fromImage(user_head_image).scaled(132, 132))
            
            self.nickname_label.setText(wechatutil.unicode(contact['NickName']))
            self.signature_label.setText(wechatutil.unicode(contact['Signature']) if ('Signature' in contact)  else "")
            self.remark_label.setText(wechatutil.unicode(contact['RemarkName']))
            self.province_label.setText(wechatutil.unicode(contact['RemarkName']))
        '''
        self.current_chat_contact = contact
        dn = contact['RemarkName'] or contact['NickName']
        if not dn:
            dn = contact['NickName']
        self.currentChatUser.setText(wechatutil.unicode(dn))
        self.messages.setText('')
        if self.msg_cache.has_key(user_name):
            messages_list = self.msg_cache[user_name]
            for message in messages_list:
                self.messages.append((message))
        '''
    def make_message(self,user_name,msg_body):
        '''MSG TEMPLATE
        {
            id:'',
            user:{
                head_class='',
                head_img = '<img src=xx.jpg/>'
            },
            body:{
                content_class:'',
                content:''
            }
        }
        '''
        """
        _msg = 
           {
            id:'%s',
            user:{
               head_class='%s',
               head_img = '%s'
            },
            body:{
               content_class:'%s',
               content:'%s'
            }
        } %(
            '1',
            ("divMyHead" if self.wechat_web.user["UserName"] == user_name else "divotherhead"),
            "<img src=%s.jpg/>"%(self.config.getContactHeadHome() + user_name),
            ("triangle-right right" if self.wechat_web.user["UserName"] == user_name else "triangle-left left"),
            wechatutil.unicode(msg_body)
        )
        """
        user = self.user_manager.get_user()
        _msg = {}
        _msg['id'] = ""
        _user = {}
        _user['head_class']=("divMyHead" if user["UserName"] == user_name else "divotherhead")
        _user['head_img']="%s\\%s.jpg"%(self.config.customFace , user_name)
        _msg['user']=_user
        _body = {}
        _body['content_class']= ("triangle-right right" if user["UserName"] == user_name else "triangle-left left")
        _body['content'] = wechatutil.unicode(msg_body)
        _msg['body']=_body

        return _msg

    def send_message(self):
        '''
        #把消息發送出去
        '''
        html_message = self.draft.toHtml()
        rr = re.search(r'<img src="([.*\S]*\.gif)"',html_message,re.I)
        message_body = ""
        if rr:
            pimages = self.code_emotion(html_message)
            for pimage in pimages:
                p = pimage["p"]
                message_body+=p
        else:
            message_body = self.draft.toPlainText()
        #print("xxxx %s"%msgBody)
        #msg_text = str(self.draft.toPlainText())
        if not message_body or len(message_body) <= 0:
            return 
        message_body = wechatutil.unicode(message_body)
        message = Message(1, message_body, self.current_chat_contact['UserName'])
        response = self.wechat_web.webwx_send_msg(message)
        if not response or response is False:
            return False
        #if send success
        self.stick(select=True)
        #self.chatsWidget.selectRow(0)
        format_msg = self.msg_timestamp(self.user_manager.get_user()['NickName'])
        #self.messages.page().mainFrame().evaluateJavaScript("append('%s');"%msgBody)
        #TODO append message
        self.messages.append(format_msg)
        message_body = message_body.replace("'", "\'")
        message_body = message_body.replace('"', '\"')
        message_decode_body = self.decode_emotion(message_body) if rr else message_body
        text_message = self.decode_emotion(message_decode_body)
        self.messages.append(wechatutil.unicode(message_decode_body))
        _message = self.make_message(self.current_chat_contact['UserName'],message_decode_body)
        #script = "nappend('%s','%s','%s','%s','%s');"%(_message['id'],_message['user']['head_class'],_message['user']['head_img'],_message['body']['content_class'],_message['body']['content'])
        #print(script)
        #self.messages.page().mainFrame().evaluateJavaScript(script)
        self.draft.setText('')
        #TODO FIX BUG
        if False:
            row_count = self.chatsModel.rowCount()
            find = False
            for row_number in range(row_count):
                user_name_index = self.chatsModel.index(row_number,0)
                user_name_obj = self.chatsModel.data(user_name_index)
                user_name = user_name_obj.toString()
                if user_name and user_name == self.current_chat_contact['UserName']:
                    find = True
                    tip_index = self.chatsModel.index(row_number,WeChatWin.MESSAGE_COUNT_CELL_INDEX)
                    tips_count_obj = self.chatsModel.data(tip_index)
                    if tips_count_obj:
                        tips_count = tips_count_obj.toInt()
                        if tips_count:
                            count = tips_count[0]
                            self.chatsModel.setData(tip_index, "%d"%(count+1))
                        else:
                            self.chatsModel.setData(tip_index, "1")
                    else:
                        count_tips_item = QtGui.QStandardItem("1")
                        self.chatsModel.setItem(row_number, WeChatWin.MESSAGE_COUNT_CELL_INDEX, count_tips_item)
                    #提昇from_user_name在會話列表中的位置
                    #move this row to the top of the sessions
                    taked_row = self.chatsModel.takeRow(row_number)
                    self.chatsModel.insertRow(0 ,taked_row)
                    break;
            if find == False:
                cells = []
                # user name item
                user_name_item = QtGui.QStandardItem((user_name))
                cells.append(user_name_item)
                
                item = QtGui.QStandardItem(QIcon("resource/icons/hicolor/32x32/apps/wechat.png"),"")
                cells.append(item)
                
                dn = self.current_chat_contact['RemarkName'] or self.current_chat_contact['NickName']
                #if not dn:
                    #dn = self.current_chat_contact['NickName']
                # user remark or nick name
                remark_nick_name_item = QtGui.QStandardItem((dn))
                cells.append(remark_nick_name_item)
                
                count_tips_item = QtGui.QStandardItem("1")
                cells.append(count_tips_item)
                
                self.chatsModel.insertRow(0,cells)
    
    def upload_send_msg_image(self,contact,ffile):
        '''
        #把圖片發送出去
        '''
        upload_response = self.wechat_web.webwx_upload_media(contact,ffile)
        json_upload_response = json.loads(upload_response)
        media_id = json_upload_response['MediaId']
        if self.isImage(ffile):
            msg = Message(3, str(media_id), self.current_chat_contact['UserName'])
            send_response = self.wechat_web.webwx_send_msg_img(msg)
        else:
            #parameter: appid,title,type=6,totallen,attachid(mediaid),fileext
            fileext = os.path.splitext(ffile)[1]
            if fileext and len(fileext) > 1 and fileext.startswith("."):
                fileext = fileext[1:(len(fileext))]
            content = "<appmsg appid='wxeb7ec651dd0aefa9' sdkver=''><title>%s</title><des></des><action></action><type>6</type><content></content><url></url><lowurl></lowurl><appattach><totallen>%d</totallen><attachid>%s</attachid><fileext>%s</fileext></appattach><extinfo></extinfo></appmsg>"%(os.path.basename(ffile),os.path.getsize(ffile),media_id,fileext)
            msg = Message(6, content, self.current_chat_contact['UserName'])
            send_response = self.wechat_web.webwx_send_app_msg(msg)
        return send_response
        
    def stick(self,row=None,select=False):
        '''
        :param row the row which will be move to the top of the chat contact list
        :select 是否要選中row指定的行
        '''
        #提昇from_user_name在會話列表中的位置
        #move this row to the top of the session table
        #從chat_contact列表中找人
        if not row or row <= 0:
            row_count = self.chatsModel.rowCount()
            for _row in range(row_count):
                index = self.chatsModel.index(_row,0)
                user_name_o = self.chatsModel.data(index)
                ''' Python2
                user_name = user_name_o.toString()
                '''
                user_name = user_name_o
                if user_name and user_name == self.current_chat_contact["UserName"]:
                    row = _row
                    break;
        if row == 0:
            return True
        elif row >= 1:
            taked_row = self.chatsModel.takeRow(row)
            self.chatsModel.insertRow(0 ,taked_row)
            if select:
                self.chatsWidget.selectRow(0)
            return True
        else:
            return False
                
    def over_the_top(self):
        '''
        :see stick
        '''
        sticked = self.stick(select=True)
        if not sticked:
            user = self.get_contact(self.current_chat_contact["UserName"])
            self.append_chat_contact(user,action="INSERT",row=0)
            self.chatsWidget.selectRow(0)
    
    def isChatRoom(self,user):
        '''
        :parameter user.the id of user
        '''
        if user:
            return user.startswith('@@')
        else:
            return False
        
    def get_user_display_name(self,message):
        '''
        :获取用户的显示名称，如果是群，则显示成员的名称
        '''
        
        from_user_name = message['FromUserName']
        user = self.user_manager.get_user()
        #如果和當前登陸人是同一個人
        if from_user_name == user["UserName"]:
            from_user = user
        else:
            from_user = self.get_contact(from_user_name)
        from_user_display_name = from_member_name= None
        #如果為群，則消息來源顯示from_member_name
        #如果是群消息
        if self.isChatRoom(from_user_name):
            content = message['Content']
            contents = content.split(":<br/>")
            from_user_display_name = from_member_name = contents[0]
                
            members = from_user["MemberList"]
            for member in members:
                if from_member_name == member['UserName']:
                    from_user_display_name = member['NickName'] or member['DisplayName'] or from_member_name
                    break
        else:
            from_user_display_name = from_user['RemarkName'] or from_user['NickName']
                
        return from_user_display_name or from_user_name
    
    def format_msg(self,userName,createTime=None):
        return self.msg_timestamp(userName, createTime)
    
    def msg_timestamp(self,userName,createTime=None):
        st = time.strftime("%Y-%m-%d %H:%M", time.localtime(createTime) if createTime else time.localtime())
        msg_timestamp = ('%s %s') % (userName, st)
        return wechatutil.unicode(msg_timestamp)
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    #    MESSAGE PROCESS HANDLERS
    ''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    def default_msg_handler(self,msg):
        '''
        #默認的消息處理handler
        '''
        self.text_msg_handler(msg)
        
    def wxinitial_msg_handler(self,message):
        '''
        #msg_type =51
        #微信初化消息處理handler，
        #我認為主要是初始化會話列表
        #用返回的數据更新會話列表
        
        #important!
        #important!
        #important!
        #statusNotifyUserName的内容就是完整的会话列表
        '''
        statusNotifyUserName = message["StatusNotifyUserName"]
        if statusNotifyUserName:
            statusNotifyUserNames = statusNotifyUserName.split(",")
            lists = []
            logging.debug("StatusNotifyUserName:")
            for userName in statusNotifyUserNames:
                logging.debug(userName)
                exist = False
                for tl in self.user_manager.get_chat_list():
                    if userName == tl["UserName"]:
                        exist = True
                        break
                if exist:
                    continue
                
                if userName.startswith("@@"):
                    #prepare arguments for batch_get_contact api
                    group = {}
                    group['UserName'] = userName
                    group['ChatRoomId'] = ''
                    lists.append(group)
            params = {
                'Count': len(lists),
                'List': lists
            }
            #update member list and download head image
            #第一次调用
            #拉取聯天室成員列表
            self.batch_get_contact(data=params)
            #
            #StatusNotifyCode = 2,4,5
            #4:初始化時所有的會話列表人員信息
            #2應該是新增會話，就是要把此人加入或提升到會話列表头
            #5還不清楚
            #
            statusNotifyCode = message["StatusNotifyCode"]
            logging.debug('statusNotifyCode:%s'%statusNotifyCode)
            if 4 == statusNotifyCode:
                #update chat list
                tmp_list = self.user_manager.get_chat_list()[:]
                for userName in statusNotifyUserNames:
                    exist = False
                    for tl in tmp_list:
                        #说明已经存/显示在ui上了
                        if userName == tl["UserName"]:
                            exist = True
                            break
                    if exist:
                        continue
                    #如果没有显示在UI上，则从联系人列表中找出，加入到会话列表，并同时更新table中的数据
                    for contact in self.user_manager.get_contacts():
                        if userName == contact["UserName"]:
                            self.user_manager.append_chat_contact(contact)
                            self.append_chat_contact(contact)
                            break
            elif statusNotifyCode == 2:#
                logging.debug("加入或提升到会话列表首位")
            else:
                logging.warning('statusNotifyCode is %s not process'%statusNotifyCode)
                logging.warning('message is %s'%message)
    
    def voice_msg_handler(self,msg):
        '''
            #把語音消息加入到聊天記錄裏
        '''
        if not self.current_chat_contact:
            pass
        
        from_user_display_name = self.get_user_display_name(msg)
        format_msg = self.msg_timestamp(from_user_display_name,msg["CreateTime"])
        #
        #如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        #
        from_user_name = msg['FromUserName']
        if from_user_name == self.user_manager.get_user()['UserName']:
            from_user_name = msg['ToUserName']
        if self.current_chat_contact and from_user_name == self.current_chat_contact['UserName']:
            self.messages.append(format_msg)
            self.messages.append(wechatutil.unicode("請在手機端收聽語音"))
        else:
            pass
    def video_msg_handler(self,msg):
        '''
        #把語音消息加入到聊天記錄裏
        '''
        if not self.current_chat_contact:
            pass
        from_user_display_name = self.get_user_display_name(msg)
        format_msg = self.msg_timestamp(from_user_display_name,msg["CreateTime"])
        #
        #如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        #
        from_user_name = msg['FromUserName']
        if from_user_name == self.user_manager.get_user()['UserName']:
            from_user_name = msg['ToUserName']
        if self.current_chat_contact and from_user_name == self.current_chat_contact['UserName']:
            self.messages.append(format_msg)
            self.messages.append(wechatutil.unicode("請在手機端觀看視頻"))
        else:
            pass
        
    def text_msg_handler(self,message):
        '''
        #:把文本消息加入到聊天記錄裏
        '''
        if not self.current_chat_contact:
            pass
        
        from_user_display_name = self.get_user_display_name(message)
        
            
        format_msg = self.msg_timestamp(from_user_display_name,message["CreateTime"])
        #
        #:如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        #
        from_user_name = message['FromUserName']
        if from_user_name == self.user_manager.get_user()['UserName']:
            from_user_name = message['ToUserName']
        if self.current_chat_contact and from_user_name == self.current_chat_contact['UserName']:
            content = message['Content']
            if self.isChatRoom(from_user_name):
                if content.startswith("@"):
                    contents = content.split(":<br/>")
                    content = contents[1]
            msg_content = self.decode_emotion(content)
            self.messages.append(format_msg)
            self.messages.append(wechatutil.unicode(msg_content))
        else:
            pass
        
    def download_msg_img(self,msg_id):
        data = self.wechat_web.webwx_get_msg_img(msg_id)
        if not data:
            return False
        img_cache_folder = ('%s/cache/img/'%(self.config.getAppHome()))
        msg_img = img_cache_folder+msg_id+'.jpg'
        with open(msg_img, 'wb') as image:
            image.write(data)
        return True
        
    def image_msg_handler(self,message):
        '''
        #把文本消息加入到聊天記錄裏
        '''
        if not self.current_chat_contact:
            pass
        from_user_display_name = self.get_user_display_name(message)
        format_msg = self.msg_timestamp(from_user_display_name,message["CreateTime"])
        msg_id = message['MsgId']
        self.wechat_web.webwx_get_msg_img(msg_id)
        #
        #如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        #
        from_user_name = message['FromUserName']
        if from_user_name == self.user_manager.get_user()['UserName']:
            from_user_name = message['ToUserName']
            
        if self.current_chat_contact and from_user_name == self.current_chat_contact['UserName']:
            self.messages.append(format_msg)
            msg_img = ('<img src=%s/%s.jpg>'%(self.config.imageRecive,msg_id))
            self.messages.append(msg_img)
        else:
            pass
    
    def login_another_devide_hander(self):
        #当从其他设备登陆时给于提示并退出
        notice_dia = Notice(self)
        if notice_dia.exec_() == QDialog.Accepted:
            notice_dia.accept()
            self.logout()
        
    def sys_msg_handler(self,msg):
        '''
        #系統消息處理
        '''
        if not self.current_chat_contact:
            pass
        
        from_user_display_name = self.get_user_display_name(msg)
        format_msg = self.msg_timestamp(from_user_display_name,msg["CreateTime"])
        
        xml_content = msg['Content']
        if xml_content:
            xml_content = xml_content.replace("&gt;",">")
            xml_content = xml_content.replace("&lt;","<")
            xml_content = xml_content.replace("<br/>","")
        
        user_name = msg['FromUserName']
        if user_name == self.user_manager.get_user()['UserName']:
            user_name = msg['ToUserName']
            
        msg_type = msg['MsgType']
        if msg_type == 10002:
            user_name = msg["FromUserName"]
            
        if self.isChatRoom(user_name):
            xml_contents = xml_content.split(":<br/>")
            xml_content = xml_contents[1]
            
        doc = xml.dom.minidom.parseString(xml_content)
        replacemsg_nodes = doc.getElementsByTagName("replacemsg")
        #old_msgid
        #TODO 用old message id 從歷史中刪去
        if replacemsg_nodes:
            replacemsg = str(replacemsg_nodes[0].firstChild.data)
            
        # 如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        if self.current_chat_contact and user_name == self.current_chat_contact['UserName']:
            self.messages.append((("%s\r\n%s")%(format_msg,wechatutil.unicode(replacemsg))))
        else:
            pass
        
    def app_msg_handler(self,msg):
        '''把應用消息加入到聊天記錄裏，應該指的是由其他應用分享的消息
        '''
        if not self.current_chat_contact:
            pass
        xmlContent = msg['Content']
        if xmlContent:
            xmlContent = xmlContent.replace("&gt;",">")
            xmlContent = xmlContent.replace("&lt;","<")
            xmlContent = xmlContent.replace("<br/>","")
        print("xmlContent %s"%xmlContent)
        user_name = msg['FromUserName']
        if user_name == self.user_manager.get_user()['UserName']:
            user_name = msg['ToUserName']
        if self.isChatRoom(user_name):
            index = xmlContent.find(":")
            if index > 0:
                xmlContent = xmlContent[index+1:len(xmlContent)]
        
        #print("xml_content %s"%xmlContent)
        doc = xml.dom.minidom.parseString(xmlContent)
        title_nodes = doc.getElementsByTagName("title")
        desc_nodes = doc.getElementsByTagName("des")
        app_url_nodes = doc.getElementsByTagName("url")
        
        title = ""
        desc = ""
        app_url = ""
        if title_nodes and title_nodes[0] and title_nodes[0].firstChild:
            title = title_nodes[0].firstChild.data
        if desc_nodes and desc_nodes[0] and desc_nodes[0].firstChild:
            desc = desc_nodes[0].firstChild.data
        if app_url_nodes and app_url_nodes[0] and app_url_nodes[0].firstChild:
            app_url = app_url_nodes[0].firstChild.data
        
        from_user_display_name = self.get_user_display_name(msg)
        format_msg = self.msg_timestamp(from_user_display_name,msg["CreateTime"])
        
        #
        #如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        #
        if self.current_chat_contact and user_name == self.current_chat_contact['UserName']:
            self.messages.append(format_msg)
            self.messages.append(wechatutil.unicode(('%s %s %s')%(title,desc,app_url)))
        else:
            pass
        
    def put_message_cache(self,cache_key,message):
        '''
        #用FromUserName做Key把消息存起來，同時把此人置頂。
        #如果当前打开的联系人和新消息的FromUserName一致，则直接显示消息；否则把消息放入
        '''   
        msg_type = message['MsgType']
        '''
        if msg_type == 10002 or self.isChatRoom(cache_key):
            cache_key = cache_key
        else:
            cache_key = message['FromUserName']
        '''
        #查看联天历史列表中有没有数据，如果没有，则有可能是UI还没有初始化完成，所以把消息放入blocked_messages_pool中，
        #等初始化完成之后处理
        row_count = self.chatsModel.rowCount()
        if row_count <= 0:
            self.message_manager.put_block_message(message)#self.blocked_messages_pool.append(message)
            return False
        '''
        if cache_key in self.messages_pool:
            messages = self.messages_pool[cache_key]
        else:
            messages = []
        messages.append(message)
        self.messages_pool[cache_key] = messages
        '''
        self.message_manager.put_message(cache_key, message)
        #
        #增加消息數量提示（提昇此人在會話列表中的位置）
        #
        exist = False#此人是否在會話列表中
        for row in range(row_count):
            index = self.chatsModel.index(row,0)
            user_name_o = self.chatsModel.data(index)
            user_name = user_name_o
            #user_name = self.chatsModel.item(i,0).text()
            if user_name and user_name == cache_key:
                exist = True
                tip_index = self.chatsModel.index(row,WeChatWin.MESSAGE_COUNT_CELL_INDEX)
                tips_count_obj = self.chatsModel.data(tip_index)
                if tips_count_obj:
                    tips_count = tips_count_obj
                    if tips_count:
                        self.chatsModel.setData(tip_index, int(tips_count)+1)
                    else:
                        self.chatsModel.setData(tip_index, "1")
                else:
                    count_tips_item = QtGui.QStandardItem("1")
                    self.chatsModel.setItem(row, WeChatWin.MESSAGE_COUNT_CELL_INDEX, count_tips_item)
                #提昇from_user_name在會話列表中的位置
                #move this row to the top of the sessions
                taked_row = self.chatsModel.takeRow(row)
                self.chatsModel.insertRow(0 ,taked_row)
                break;
        #have not received a message before（如果此人没有在會話列表中，則加入之）
        if not exist:
            contact = {}
            for member in self.user_manager.get_contacts():
                if member['UserName'] == cache_key:
                    contact = member
                    break
            if not contact:
                logging.warn('the contact %s not found in friends'%cache_key)
                return False
            dn = contact['RemarkName'] or contact['NickName']
            #if not dn:
                #dn = contact['NickName']
            user_name = contact['UserName']
            cells = []
            # user name item
            user_name_item = QtGui.QStandardItem((user_name))
            cells.append(user_name_item)
            
            item = QtGui.QStandardItem(QIcon("resource/icons/hicolor/32x32/apps/wechat.png"),"")
            cells.append(item)
            
            # user remark or nick name
            remark_nick_name_item = QtGui.QStandardItem((dn))
            cells.append(remark_nick_name_item)
            
            count_tips_item = QtGui.QStandardItem("1")
            cells.append(count_tips_item)
            
            self.chatsModel.insertRow(0,cells)
    
    def msg_handle(self,message):
        msg_type = message['MsgType']
        if msg_type:
            if msg_type == 51:
                self.wxinitial_msg_handler(message)
                return
            if msg_type == 2 or msg_type == 52:
                logging.warn('message not process:')
                logging.warn('message type %d'%msg_type)
                logging.warn('message body %s'%message)
                return
            #
            #
            #
            from_user_name = message['FromUserName']
            print(message)
            if self.isChatRoom(from_user_name):
                #user_name = from_user_name
                #from_user_name = message['FromUserName']
                pass
            else:
                #如果消息的發送者和登陸人一致，那麼此消息有可能是通過其他設备發送，那麼有取ToUserName,才能顯示正确
                if from_user_name == self.user_manager.get_user()['UserName']:
                    from_user_name = message['ToUserName']
            
            #get local user id
            local_user_id = self.user_manager.get_locale_user_id_by_fresh_user_name(from_user_name)
            local_to_user_id = self.user_manager.get_locale_user_id_by_fresh_user_name(message['ToUserName'])
            #insert message to database
            self.message_manager.insert_message(message,local_user_id,local_to_user_id)
            #
            #没有選擇和誰對話或者此消息的發送人和當前的對話人不一致，則把消息存放在message_cache中;
            #如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在聊天窗口中
            if (not self.current_chat_contact) or from_user_name != self.current_chat_contact['UserName']:
                self.put_message_cache(from_user_name,message)
            else:
                if msg_type == 1:
                    self.text_msg_handler(message)
                elif msg_type == 3:
                    self.image_msg_handler(message) 
                elif msg_type == 34:
                    self.voice_msg_handler(message)
                elif msg_type == 47:
                    self.default_msg_handler(message)
                elif msg_type == 49:
                    self.app_msg_handler(message)
                elif msg_type == 10002:
                    self.sys_msg_handler(message)
                else:
                    self.default_msg_handler(message)

    def select_emotion(self):
        emotionWidget = Emotion(self)
        cursor_point = QCursor.pos()
        #emotionWidget.move(cursor_point)
        emotionWidget.move(QPoint(cursor_point.x(),cursor_point.y()-Emotion.HEIGHT))
        emotionWidget.selectChanged.connect(self.get_select_emotion)
        emotionWidget.show()
        '''
        if QDialog.Accepted == emotionWidget.accept():
            selected_emotion = emotionWidget.get_selected_emotion()
            print("selected_emotion %s"%selected_emotion)
        '''
        
    def select_document(self):
        fileDialog = QFileDialog(self)
        if fileDialog.exec_():
            selectedFiles = fileDialog.selectedFiles()
            for ffile in selectedFiles:
                ffile = str(ffile)
                send_response = self.upload_send_msg_image(self.current_chat_contact,ffile)
                send_response_dict = json.loads(send_response)
                
                msg_id = send_response_dict["MsgID"]
                #send success append the image to history;failed append to draft 
                if msg_id:
                    self.stick(select=True)
                    self.wechat_web.webwx_get_msg_img(msg_id)
                    #st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
                    #format_msg = ('(%s) %s:') % (st, self.wechat_web.user['NickName'])
                    format_msg = self.msg_timestamp(self.user_manager.get_user()['NickName'])
                    self.messages.append(format_msg)
                    if self.isImage(ffile):
                        msg_img = ('<img src=%s/%s.jpg>'%(self.config.getCacheImageHome(),msg_id))
                    else:
                        msg_img = ffile
                    self.messages.append(msg_img)
                    #_msg = self.make_message(self.wechat_web.getUser()['UserName'],wechatutil.unicode(msg_img))
                    #self.messages.page().mainFrame().evaluateJavaScript("append('%s');"%(json.dumps(_msg)))
                    #self.messages.page().mainFrame().evaluateJavaScript("append('%s');"%wechatutil.unicode(msg_img))
                else:
                    #fileName=QtCore.QString.fromUtf8(fileName)
                    if self.isImage(ffile):
                        self.draft.append("<img src=%s width=80 height=80>"%(ffile))
                    else:
                        print(ffile)
    def to_chat(self):
        '''
        #點擊傳消息按鈕
        #把此人加入Chat列表，同時顯示
        '''
        user_name = self.user_name_label.text()
        logging.debug("to_chat user_name %s"%(user_name))
        self.current_chat_contact = self.get_contact(user_name)
        if self.current_chat_contact:
            self.messages_clear()
        self.switch_chat(show=True)
        self.over_the_top()
            
    def keyPressEvent(self,event):
        print("keyPressEvent")
        
    def startDwonloadCustomFace(self):
        timer = threading.Timer(1, self.downloadCustomFace)
        timer.setDaemon(True)
        timer.start()
    
    def downloadCustomFace(self):
        #'''
        #當UI顯示出來之後异步下載所有的custom face,發送信號更新
        #'''
        logging.debug("do downloadCustomFace()")
        for contact in self.user_manager.get_contacts():
            user_name = contact['UserName']
            head_img_url = contact['HeadImgUrl']
            if not user_name or not head_img_url:
                continue
            image = '%s%s%s.jpg'%(self.config.customFace,os.sep,user_name)
            #下載聯天室圖像
            if not os.path.exists(image):
                logging.debug("Downloading %s"%image)
                self.wechat_web.webwx_get_head_img(user_name,head_img_url)
                self.customFaceDownloadSuccess.emit(user_name)
            else:
                logging.warning("%s is already exist"%image)
    
    def updateCustomFace(self,contact):
        #利用repaint事件直接強制paint就可以了
        logging.debug("updateCustomFace:%s"%contact)
        row_will_be_update = -1
        row_count = self.chatsModel.rowCount()
        custom_face = None
        for row in range(row_count):
            index = self.chatsModel.index(row,0)
            user_name_o = self.chatsModel.data(index)
            ''' Python2
            user_name = user_name_o.toString()
            '''
            user_name = user_name_o
            if user_name and user_name == contact:
                row_will_be_update = row
                break;
        
        if row_will_be_update >= 0:
            logging.debug("row %d will be updateCustomFace:"%row_will_be_update)
            custom_face = "%s\\%s.jpg"%(self.config.customFace,contact)
            index = self.chatsModel.index(row_will_be_update,1)
            custom_fact_item = self.chatsModel.itemFromIndex(index)
            if custom_fact_item:
                custom_fact_item.setIcon(QIcon(custom_face))
                self.chatsWidget.update()
        ######################
        row_will_be_update = -1
        row_count = self.friendsModel.rowCount()
        for row in range(row_count):
            index = self.friendsModel.index(row,0)
            user_name_o = self.friendsModel.data(index)
            ''' Python2
            user_name = user_name_o.toString()
            '''
            user_name = user_name_o
            if user_name and user_name == contact:
                row_will_be_update = row
                break;
        
        if row_will_be_update >= 0:
            logging.debug("row %d will be updateCustomFace:"%row_will_be_update)
            index = self.friendsModel.index(row_will_be_update,1)
            custom_fact_item = self.friendsModel.itemFromIndex(index)
            if custom_fact_item:
                custom_fact_item.setIcon(QIcon(custom_face))
                self.friendsWidget.update()
        
    def synccheck(self,loop=True):
        '''
        #同步消息主循環
        :see webwx_sync_process
        '''
        while (loop):
            st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
            logging.debug('[push]synccheck %s' %(st))
            try:
                (code, selector) = self.wechat_web.sync_check()
            except:
                loop = False
                logging.error("wechat_web.sync_check() exception")
                self.logout()
            if loop is False:
                break
            if code == -1 and selector == -1:
                loop = False
                logging.error("self.wechat_web.sync_check() error")
            else:
                if code != '0':
                    if code == '1101' and selector == '0':
                        loop = False
                        self.sync_timer.cancel()
                        logging.warning("session is timeout,will do relogin")
                        self.logout()
                else:
                    if selector != '0':
                        sync_response = self.wechat_web.webwx_sync()
                        #print("WeChatSync.run#webwx_sync:")
                        if sync_response:
                            self.messageReceived.emit(sync_response)
                        #self.webwx_sync_process(sync_response)
            if loop is False:
                break
            sleep(15)
            
    '''''''''''''''''''''''''''''''''''''''''''''''
    
    '''''''''''''''''''''''''''''''''''''''''''''''
    '''
    def updateMembers(self,members):
        #self.members = members
        self.membersTableModel.removeRows(0, self.membersTableModel.rowCount())
        self.appendRow(members)
    
    def init_member_list_widget(self,member_list):
        #self.membersTableModel.setHorizontalHeaderItem(0,QStandardItem("0000"))
        self.appendRow(member_list, self.membersTableModel)
        self.membersTable.setModel(self.membersTableModel)
        self.membersTable.setIconSize(QSize(40,40))
        self.membersTable.clicked.connect(self.member_click)
    '''
        
    def member_click(self):
        print("member_clicked in member_click()")
        self.memberListWindow = ContactsWindow(self.user_manager.get_contacts(),self)
        self.memberListWindow.resize(400,600)
        self.memberListWindow.membersConfirmed.connect(self.getSelectedUsers)
        self.memberListWindow.show()
    
    def appendRow(self,members):
        '''
        #向membersTableWidget中填充信息
        '''
        ###############
        cells = []
        item = QtGui.QStandardItem(("+"))
        cells.append(item)
        for member in members[0:3]:
            user_head_icon = "%s\\%s.jpg"%(self.config.customFace, member['UserName']+".jpg")
            if not os.path.exists(user_head_icon):
                user_head_icon = './resource/images/webwxgeticon.png'#self.default_member_icon
            dn = member['DisplayName'] or member['NickName']
            if not dn:
                dn = member['NickName']
            item = QtGui.QStandardItem(QIcon(user_head_icon),wechatutil.unicode(dn))
            cells.append(item)
        self.membersTableModel.appendRow(cells)
        i = 3
        members_len = len(members)
        if members_len > 19:
            members_len = 19
        while i < members_len:
            cells = []
            for member in members[i:i+4]:
                user_head_icon = "%s\\%s.jpg"%(self.config.customFace, member['UserName']+".jpg")
                if not os.path.exists(user_head_icon):
                    user_head_icon = './resource/images/webwxgeticon.png'#self.default_member_icon
                dn = member['DisplayName'] or member['NickName']
                if not dn:
                    dn = member['NickName']
                item = QtGui.QStandardItem(QIcon(user_head_icon),wechatutil.unicode(dn))
                cells.append(item)
            i = i + 4
            self.membersTableModel.appendRow(cells)
            
    ''''''''''''''''''''''''''''''''''''''''''''''''
    ##处理注销、重登陆
    ''''''''''''''''''''''''''''''''''''''''''''''''
    def relogin(self):
        self.close()
        from wechat2 import WeChatLauncher
        launcher = WeChatLauncher()
        if QDialog.Accepted == launcher.exec_():
            #不能传入wechat weba api实例，否则当扫完登陆后会再把登陆窗口在显示出来
            window = WeChatWin()
            self.window_list.append(window)#这句一定要写，不然无法重新登录
            window.show()
        
    def logout(self):
        self.relogin()
        
    def login_another_device_tip(self):
        tip_dia = Notice()
        if QDialog.Accepted == tip_dia.exec_():
            tip_dia.accept()
            self.close()
        
        
            