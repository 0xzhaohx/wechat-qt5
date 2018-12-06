#!/usr/bin/python2.7
# -*- coding:UTF-8 -*-
'''
Created on 2018年11月6日

@author: zhaohongxing
'''
import sqlite3
from config import WechatConfig
'''
PYInitial和PYQuanPin的值和NickName有關
RemarkPYInitial和RemarkPYQuanPin的值和RemarkName有關
'''
class UserManager(object):
    
    def __init__(self):
        self.config = WechatConfig()
        #当前登陆的用户
        self.__user = []
        #會話联系人列表
        self.__chat_list = []
        #聯系人列表（包含會話列表）
        self.__contact_list = []
        self.connection = sqlite3.connect("%s\\wechat.db"%self.config.getAppHome())
        
    def set_user(self,user):
        self.__user = user
    
    def get_user(self):
        return self.__user
    
    def get_chat_list(self):
        #获取所有的历史聊天记录人员列表
        return self.__chat_list
    
    def set_chat_list(self,chat_list):
        self.__chat_list = chat_list
        
    def add_chat_contact(self,i,chat):
        self.__chat_list[i] = chat
    
    def append_chat_contact(self,chat):
        self.__chat_list.append(chat)
        
    def set_contacts(self,contacts):
        self.__contact_list = contacts
    
    def get_contacts(self):
        #获取联系人列表
        return self.__contact_list
    
    def get_locale_user_id_by_fresh_user_name(self,user_name):
        #根据最新user_name获取存儲在數据中联系人的user_id
        if not user_name:
            return "-1"
        fresh_from_contact = None
        for contact in self.__contact_list:
            if user_name == contact["UserName"]:
                fresh_from_contact = contact
                break
        
        storaged_users = self.get_storaged_contacts()
        for sto_user in storaged_users:
            if self.user_match(sto_user, fresh_from_contact):
                return sto_user["USER_ID"]
        return "-1"
        
    def user_match(self,storage_user,fresh_user):
        return storage_user["PY_QUANPIN"] == fresh_user["PYQuanPin"] 

    def match_deep_1(self,storage_user,fresh_user):
        pass
    
    def match_deep_2(self,storage_user,fresh_user):
        pass
    
    def match_deep_3(self,storage_user,fresh_user):
        pass
    
    def match_deep_4(self,storage_user,fresh_user):
        pass
    
    def append_contact(self,contact):
        self.__contact_list.append(contact)

    def update_chat_contact(self,i,contact):
        self.__chat_list[i] = contact
        
    @DeprecationWarning
    def update_friend(self,i,contact):
        self.__contact_list[i] = contact
    
    def find_diff_users(self,users):
        #找到和之前不相同的聯系人。
        #不同可能有3種情况：
        #1、新曾的；
        #2、修改了名稱的。如果不能確定，則需要用户手動進行匹配
        #3、刪除的
        #由于網頁版的聯系人的唯一標識是動態的，所有用'PYQuanPin'來作為唯一標識，
        #但對於同一個用户的'PYQuanPin'在以後有可能會改變，所以當發現有聯系人和之前
        #保存的不一致時，找出不一致的，由用户手動的把不一致的關連起來
        pass
    
    ''''''''''''''''''''''''''''''''''''
    #以下是关于数据库的操作
    ''''''''''''''''''''''''''''''''''''
    def insert_user(self,user):
        cursor = self.connection.cursor()
        #FACE_ID圖片名稱
        #FACE_ID_HASH 圖片HASH值
        sql = "INSERT INTO USER(\
        FACE_ID,\
        FACE_ID_HASH,\
        USER_NAME,\
        NICK_NAME,\
        REMARK_NAME,\
        PY_QUANPIN,\
        SEX) VALUES('%s','%s','%s','%s','%s','%s',%d)"%(\
        user["UserName"],
        user["UserName"],
        user["UserName"],
        user["NickName"],
        user["RemarkName"],
        user["PYQuanPin"],
        user["Sex"]
        )
        cursor.execute(sql)
        self.connection.commit()
    
    def delete_message(self,user_id):
        cursor = self.connection.cursor()
        delete = "DELETE FROM USER WHERE ID = %d"%user_id
        cursor.execute(delete)
        self.connection.commit()
    
    def get_user_by_id(self,user_id):
        cursor = self.connection.cursor()
        select = "SELECT * FROM USER WHERE PY_QUANPIN = '%s'"%(user_id)
        result = cursor.execute(select)
        row = result.fetchone()
        if row:
            user = {}
            user["user_id"] = row[0]
            return user
        else:
            return None
    
    def get_storaged_contacts(self):
        cursor = self.connection.cursor()
        select = "SELECT *  FROM USER"
        result = cursor.execute(select)
        stored_users = []
        for row in result:
            stored_user = {}
            stored_user["USER_ID"]= row[0]
            stored_user["NICK_NAME"]= row[5]
            stored_user["REMARK_NAME"]= row[6]
            stored_user["PY_QUANPIN"]= row[7]
            stored_user["USER_ID"]= row[0]
            stored_users.append(stored_user)
        return stored_users
        
    
    def update_user(self):
        pass
    
if __name__ =="__main__":
    userManager = UserManager()
    user = userManager.get_user_by_id("0x11")
    print(user)