# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Jul  9 2019, 16:51:35) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/App.py
# Compiled at: 2018-06-14 14:16:48
from __future__ import print_function
import time
from common import access_point
from config import StatusTypes, PassTypes, EventTypes, DirectionTypes, AccessPointTypes, CardTypes
from Card import Cards
from lib import requests, singleton
import json, binascii, os, unittest
from DebugImport import debug_message
from arjo import ArjoLink
from frame import Pn532Frame
from constants import *
from M5e import M5e, M5ePoller

def get_pwd():
    params = {'uID': '043038ca4e5381'}
    data = requests(urls='http://11.11.0.51:8080/Home/GetPassword', params=params, timeouts=3)
    try:
        if data is not None:
            data = json.loads(data)
            if data is not None and 'OutPwdPack' in data:
                return data['OutPwdPack']
    except Exception as e:
        print(e)

    return ''


def get_ticket_decrypt():
    params = {'uID': '043038ca4e5381', 'crypto': '2130cd0e3565f07392711f9a011b2b98'}
    data = requests(urls='http://11.11.0.51:8080/Home/TicketDecrypt', params=params, timeouts=3)
    try:
        if data is not None:
            data = json.loads(data)
            if data is not None and 'DecryptedData' in data:
                return data['DecryptedData']
    except Exception as e:
        print(e)

    return ''


def get_match_keys():
    _math_id = 25
    print('===================Get match key======================')
    params = {'PointID': 306}
    _request = requests(urls='http://iis-pilot/GetMatches/', params=params, timeouts=10)
    try:
        if _request is not None and len(_request) > 10:
            data = json.loads(_request)
            if data is not None and isinstance(data, list) and len(data) > 0:
                for _rec in data:
                    if _rec is not None and isinstance(_rec, dict) and 'ExternEventID' in _rec:
                        if 'FIFA_SAC' in _rec and 'FIFA_SAM' in _rec:
                            if int(_rec['ExternEventID']) == _math_id:
                                _sac = _rec['FIFA_SAC']
                                _sam = _rec['FIFA_SAM']
                                _filename = '/usr/AWS_FIFA/Virtual_SAM1_M' + str(_math_id) + '.txt'
                                _currend_data = ''
                                if os.path.isfile(_filename):
                                    with open(_filename, 'rb') as (_fp):
                                        _currend_data = _fp.read().strip()
                                if _currend_data != _sam:
                                    print('New data')
                                    with open(_filename, 'wb') as (_fpw):
                                        _fpw.write(_sam)

    except Exception as e:
        print(e)

    return


def test_get_match_keys():
    get_match_keys()


def test_pwd_pack():
    pwd_hex = '85b9b9faa0'
    print(pwd_hex)
    pwd_data = bytearray.fromhex(pwd_hex)
    print('package: ' + binascii.hexlify(pwd_data))
    print(pwd_data)


def get_data(data):
    ant, ids, rssi = data
    epc = ids.encode('hex').upper()
    debug_message.print_message('Rfid read data: ' + epc)


def p1(M5e):
    M5e.ChangeAntennaPorts(1, 1)
    return 'Ant1'


class TestAccessPointMethods(unittest.TestCase):

    @unittest.skip('In short time only. Should be activated')
    def test_match_data(self):
        debug_message.set_mode('development')
        _options = {'osdb_server': '11.11.0.2', 'ip': '11.11.0.41', 'point_mode': 'test'}
        access_point.init_point('/home/user/zeus', _options, None, None)
        print('Venue enter id: ' + str(access_point.venue_enter_id) + ' venue enter name: ' + access_point.venue_enter_name)
        access_point.get_id()
        access_point.get_params()
        access_point.get_lists()
        print('Match id: ' + str(access_point.get_current_match_id()))
        print('Sac: ' + access_point.get_sac())
        ret = access_point.get_current_match_id() > 0 and len(access_point.get_sac()) > 0
        self.assertTrue(ret, 'All data match is correct')
        return

    @unittest.skip('In short time only. Should be activated')
    def test_match_date(self):
        debug_message.set_mode('development')
        _options = {'osdb_server': '11.11.0.2', 'ip': '11.11.0.41', 'point_mode': 'test'}
        access_point.init_point('/home/user/zeus', _options, None, None)
        print('Venue enter id: ' + str(access_point.venue_enter_id) + ' venue enter name: ' + access_point.venue_enter_name)
        access_point.get_id()
        access_point.get_params()
        date = bytearray()
        date.append(16)
        date.append(5)
        date.append(17)
        _date = access_point.get_match_date()
        print('Date1: ' + binascii.hexlify(date))
        print('Date2: ' + binascii.hexlify(_date))
        self.assertEqual(date, _date, 'Dates not much')
        return

    @unittest.skip('In short time only. Should be activated')
    def test_set_date(self):
        debug_message.set_mode('development')
        access_point.set_sys_time('2017-06-16T10:53:10.603')

    @unittest.skip('In short time only. Should be activated')
    def test_get_start_time(self):
        _datetime = access_point.get_start_time()
        print('Startup date: ' + _datetime)

    @unittest.skip('In short time only. Should be activated')
    def test_pn32_frame(self):
        hex1 = '0000ff00ff000000ff0ff1d54b0101004400070463f80a4f53810700'
        hex11 = '0000ff00ff000000ff0ff1d54b010100440007041f9b020052810000'
        hex2 = '0000ff00ff000000ff05fbd54300573baf00'
        hex2 = '0000ff00ff000000ff05fbd54300c772af00'
        _answer = bytearray.fromhex(hex1)
        _tmp_frame = Pn532Frame.from_response(_answer)
        _data = _tmp_frame.get_data()
        print('  data: ' + binascii.hexlify(_data))
        print(_tmp_frame.calc_checksum())

    def test_display_exit_mb(self):
        debug_message.set_mode('development')
        for i in range(1, 10):
            debug_message.print_message('Start iterate ' + str(i))
            data = requests(urls='http://11.11.0.112/LockCard/', timeouts=2)
            debug_message.print_message(data)
            can_lock = False
            try:
                if data is not None:
                    data = json.loads(data)
                    if data is not None and 'locked' in data:
                        can_lock = data['locked']
            except Exception as e:
                debug_message.print_message(e)
            else:
                if can_lock:
                    debug_message.print_message('Successfully locked testing exit mode...')
                    data = requests(urls='http://11.11.0.112/OpenMb/', timeouts=12)
                    debug_message.print_message(data)
                    try:
                        if data is not None:
                            data = json.loads(data)
                            if data is not None and 'passed' in data:
                                self.mb.passed_local = data['passed']
                    except Exception as e:
                        debug_message.print_message(e)

                    data = requests(urls='http://11.11.0.112/UnlockCard/', timeouts=2)
                    debug_message.print_message(data)
                    time.sleep(2)
                else:
                    debug_message.print_message('Locked false...')

        return


def check_card():
    options = {'osdb_server': '11.11.0.2', 'sde_server': 'iis_sde', 'point_ip': '11.11.0.41', 'point_mode': 'test', 'os_ip': '11.11.0.112', 'point_direction': DirectionTypes.ENTER, 'master_ip': '11.11.0.112', 'rfid_power': 1400, 
       'monitor_ip': '11.11.0.113', 'rfid866_enable': True, 'rfid1356_enable': True}
    access_point.init_point('/home/user/zeus', options, None, None)
    debug_message.print_message('Venue enter id: ' + str(access_point.venue_enter_id) + ' venue enter name: ' + access_point.venue_enter_name)
    access_point.set_option('groups', '4.32,5.0,4.13,4.22,4.31,4.35,1.9,2.1,2.3')
    groups = access_point.get_option('groups')
    if groups:
        for group in groups:
            debug_message.print_message('group id: ' + group)

    access_point.set_online(True)
    cards = Cards()
    debug_message.print_message('=================================================')
    cards.clear()
    cards.get_card('E28011002000355A6AD80010', '', access_point.point_direction, CardTypes.RFID, 'E28011002000355A6AD80010', False, False)
    cards.add_card()
    cards.get_card('E28011002000585B47A001F3', '', access_point.point_direction, CardTypes.RFID, 'E28011002000585B47A001F3', False, False)
    cards.add_card()
    cgo = cards.can_go()
    print('can go: ' + str(cgo))
    do = cards.has_double_ic()
    print('double: ' + str(do))
    de = cards.is_declined()
    print('declined: ' + str(de))
    cards.is_enter = True
    cards.write_log()
    debug_message.print_message('=================================================')
    cards.clear()
    cards.get_card('E28011002000355A6AD80010', '', access_point.point_direction, CardTypes.RFID, 'E28011002000355A6AD80010', False, False)
    cards.add_card()
    cards.get_card('E2801100200034DC6ADE0010', '', access_point.point_direction, CardTypes.RFID, 'E2801100200034DC6ADE0010', False, False)
    cards.add_card()
    cgo = cards.can_go()
    print('can go: ' + str(cgo))
    do = cards.has_double_ic()
    print('double: ' + str(do))
    de = cards.is_declined()
    print('declined: ' + str(de))
    cards.is_enter = True
    cards.write_log()
    return


if __name__ == '__main__':
    debug_message.set_mode('development')
    check_card()
# okay decompiling /home/a/Desktop/app/App.pyc
