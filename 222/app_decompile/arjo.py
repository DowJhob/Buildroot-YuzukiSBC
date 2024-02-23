# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Oct  7 2019, 17:39:04) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/arjo.py
# Compiled at: 2018-04-17 21:45:18
import os.path
from ctypes import *
me = os.path.abspath(os.path.dirname(__file__))
lib = CDLL(os.path.join('/usr/AWS_FIFA', 'libarjo_i.so'), mode=RTLD_GLOBAL)

class ArjoLink(object):

    def __init__(self):
        self.obj = lib.ArjoLink_new()

    def info(self):
        lib.ArjoLink_info(self.obj)

    def get_packpwd(self, sak, uid, date, match_id):
        lib.ArjoLink_GetPackPwd.restype = POINTER(c_ubyte * 6)
        return lib.ArjoLink_GetPackPwd(self.obj, sak, uid, date, match_id)

    def get_decrypt_data(self, sak, crypt, uid, match_id):
        lib.ArjoLink_GetDecryptData.restype = POINTER(c_ubyte * 16)
        return lib.ArjoLink_GetDecryptData(self.obj, sak, crypt, uid, match_id)