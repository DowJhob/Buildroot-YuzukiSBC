# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Oct  7 2019, 17:39:04) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/lib.py
# Compiled at: 2017-06-11 22:33:24
from urllib2 import Request, urlopen, URLError, HTTPError
from urllib import urlencode
from socket import timeout
HTTP_LAST_STATUS = 0

def singleton(cls):
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return getinstance


def requests(urls='', params='', timeouts=1):
    global HTTP_LAST_STATUS
    data = None
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'}
        if params:
            urls += '?' + urlencode(params)
        request = Request(urls, headers=headers)
        handler = urlopen(request, timeout=timeouts)
        data = handler.read()
        if HTTP_LAST_STATUS != 0:
            HTTP_LAST_STATUS = 0
    except HTTPError as e:
        if HTTP_LAST_STATUS != 1:
            print '=======================HTTP request error====================='
            print urls
            print e
            print '=======================!HTTP request error===================='
            HTTP_LAST_STATUS = 1
    except URLError as e:
        if HTTP_LAST_STATUS != 2:
            print '=======================HTTPUrl request error====================='
            print urls
            print e
            print '=======================!HTTPUrl request error===================='
            HTTP_LAST_STATUS = 2
    except timeout as e:
        if HTTP_LAST_STATUS != 3:
            print '=======================HTTP request timeout====================='
            print urls
            print e
            print '=======================!HTTP request timeout====================='
            HTTP_LAST_STATUS = 3

    return data


def float_eq(a, b, epsilon=1e-08):
    return abs(a - b) < epsilon