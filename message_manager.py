#!/usr/bin/python2.7
# -*- coding:UTF-8 -*-
'''
Created on 2018年3月25日

@author: zhaohongxing
'''
import sqlite3
import time
import logging
from config import WechatConfig

class MessageManager(object):
    
    def __init__(self):
        self.config = WechatConfig()
        self.connection = sqlite3.connect("%s\\wechat.db"%self.config.getAppHome())
        #接收到的新消息，还没有点开看过。
        #因为可能会有多位联系人发来消息，同时为了存储和获取方便，用一个对像来存储
        self.message_pools = {}
        #没有來得及處理的新消息,主要用於存放UI未初始化完時收到消息，然後等初始結束處理.
        #因为这些消息处理不用区分是哪个联系人发起的，所以用数组存储
        self.block_message_pools = []
    
    def get_messages(self,user_name):
        return self.message_pools.get(user_name) or []
    
    def put_message(self,user_name,message):
        messages = []
        if user_name in self.message_pools:
            messages = self.message_pools[user_name]
        messages.append(message)
        self.message_pools[user_name] = messages
        
    def get_block_messages(self):
        #返回所有的未来得乃处理的消息
        return self.block_message_pools;
    
    def put_block_message(self,message):
        self.block_message_pools.append(message)
    
    def insert_message(self,message,local_user_id,local_to_user_id):
        cursor = self.connection.cursor()
        #FACE_ID圖片名稱
        #FACE_ID_HASH 圖片HASH值
        sql = "INSERT INTO MESSAGE(\
        MESSAGE_ID,\
        USER_ID,\
        TO_USER_ID,\
        BODY,\
        RECEIVED_TIME) VALUES(%d,%d,'%s','%s','%s')"%(\
        message["NewMsgId"],local_user_id,local_to_user_id,message["Content"],
        time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(message["CreateTime"] or "0"))
        )
        logging.debug(sql)
        cursor.execute(sql)
        self.connection.commit()
        
    def get_last_message_by_user(self,user_id):
        cursor = self.connection.cursor()
        #FACE_ID圖片名稱
        #FACE_ID_HASH 圖片HASH值
        sql = "SELECT body, received_time FROM message WHERE user_id=%s order by received_time desc limit 1"%(user_id)
        logging.debug(sql)
        result = cursor.execute(sql)
        row = result.fetchone()
        if row:
            message = {}
            message["Body"] = row[0]
            message["ReceivedTime"] = row[1]
            return message
        else:
            return None
    
    def delete_message(self,message_id):
        pass
    
    def delete_messages(self,message_ids):
        for message_id in message_ids:
            self.delete_message(message_id)
    
    def get_messages_by_user_id(self,user_id,filters,start=0,offset=15):
        '''
        :user_id 要查詢的人
        :filter 過滤條件
        :start 起始行
        :offset 查詢的條數
        '''
        #獲取某人的聊天記錄。估計得分頁
        return None
    
if __name__ == '__main__':
    import json
    message = '{"MsgId": "2345161802731017517", "FromUserName": "@d66c5bf137a8c3c962822c4774e641e2", "ToUserName": "@d66c5bf137a8c3c962822c4774e641e2", "MsgType": 1, "Content": "卜", "Status": 3, "ImgStatus": 1, "CreateTime": 1541656715, "VoiceLength": 0, "PlayLength": 0, "FileName": "", "FileSize": "", "MediaId": "", "Url": "", "AppMsgType": 0, "StatusNotifyCode": 0, "StatusNotifyUserName": "", "RecommendInfo": {"UserName": "", "NickName": "", "QQNum": 0, "Province": "", "City": "", "Content": "", "Signature": "", "Alias": "", "Scene": 0, "VerifyFlag": 0, "AttrStatus": 0, "Sex": 0, "Ticket": "", "OpCode": 0}, "ForwardFlag": 0, "AppInfo": {"AppID": "", "Type": 0}, "HasProductId": 0, "Ticket": "", "ImgHeight": 0, "ImgWidth": 0, "SubMsgType": 0, "NewMsgId": 2345161802731017517, "OriContent": "", "EncryFileName": ""}';
    message = '{"MsgId": "6104986236860269695", "FromUserName": "@01380a1dcf26ed1e54a337fdffbeca0c", "ToUserName": "@01380a1dcf26ed1e54a337fdffbeca0c", "MsgType": 1, "Content": "但", "Status": 3, "ImgStatus": 1, "CreateTime": 1541858155, "VoiceLength": 0, "PlayLength": 0, "FileName": "", "FileSize": "", "MediaId": "", "Url": "", "AppMsgType": 0, "StatusNotifyCode": 0, "StatusNotifyUserName": "", "RecommendInfo": {"UserName": "", "NickName": "", "QQNum": 0, "Province": "", "City": "", "Content": "", "Signature": "", "Alias": "", "Scene": 0, "VerifyFlag": 0, "AttrStatus": 0, "Sex": 0, "Ticket": "", "OpCode": 0}, "ForwardFlag": 0, "AppInfo": {"AppID": "", "Type": 0}, "HasProductId": 0, "Ticket": "", "ImgHeight": 0, "ImgWidth": 0, "SubMsgType": 0, "NewMsgId": 6104986236860269695, "OriContent": "", "EncryFileName": ""}';
    message = json.loads(message)
    
    print(time.strftime('%Y',time.localtime()))
    print(message)
    print((type(message)))
    print(message["NewMsgId"])
    print(message["FromUserName"])
    print(message["ToUserName"])
    print(message["Content"])
    print(message["CreateTime"] or "ddd")
    print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(message["CreateTime"])))
    message_manager = MessageManager()
    message_manager.insert_message(message)
    message_manager.put_message("dd", message)
    