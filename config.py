#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年3月25日

@author: zhaohongxing
'''
import os

class WechatConfig(object):

    def __init__(self):
        self.__user_home = os.path.expanduser('~')
        self.__app_home = self.__user_home + '\\.wechat'
        self.__default_head_icon = './resource/images/default.png'
        #new
        self.customFace = "%s\\customface"%(self.__app_home)
        self.imageRecive = "%s\\imageRec"%(self.__app_home)
        
    def getUserHome(self):
        return self.__user_home
    
    def getAppHome(self):
        return self.__app_home
    
    def getHeadHome(self):
        return self.__head_home
    
    def getCacheHome(self):
        return self.__cache_home
    
    def getCacheImageHome(self):
        return self.__cache_image_home
    
    def getContactHeadHome(self):
        return self.__contact_head_home
    
    def getContactHome(self):
        return self.getContactHeadHome()
    
    def getDefaultIcon(self):
        return self.__default_head_icon