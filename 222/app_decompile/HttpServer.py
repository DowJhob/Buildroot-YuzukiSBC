# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Jul  9 2019, 16:51:35) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/HttpServer.py
# Compiled at: 2018-05-27 13:09:02
from __future__ import print_function
import datetime, json, os, re, socket, SocketServer, time, threading, base64
from urlparse import urlparse, parse_qs
from common import access_point
from include import cards_local
from config import DirectionTypes, cards_lock, common_lock
from binascii import hexlify
from DebugImport import debug_message

class MyRequestHandlerWithStreamRequestHandler(SocketServer.StreamRequestHandler):

    def handle(self):
        try:
            headers = {}
            self.request.settimeout(2)
            debug_message.print_message('Connection from: %s' % str(self.client_address))
            user_pass = base64.encodestring('adminto:' + access_point.get_os_ip()).lower()
            headers = self.read_headers()
            http_response = self.page_not_found()
            if headers.has_key('method') and headers.has_key('host'):
                get_data = headers['method'].split(' ')
                if get_data and len(get_data) == 3:
                    params = parse_qs(urlparse(get_data[1].encode('utf-8')).query, keep_blank_values=True)
                    _is_auth = True
                    if get_data[1].startswith(u'/test/') or get_data[1].startswith(u'/manage/') or get_data[1].startswith(u'/turnstile/') or get_data[1].startswith(u'/access_point/'):
                        _is_auth = False
                        if headers.has_key('authorization'):
                            _auth_data = headers['authorization'].split(' ')
                            if len(_auth_data) == 2 and _auth_data[0] == 'basic' and _auth_data[1].strip() == user_pass.strip():
                                _is_auth = True
                    if not _is_auth:
                        http_response = self.send_basic_auth()
                    elif re.search('\\.html$', get_data[1]) is not None:
                        file_name = '/mnt/ramdisk/htdocs' + get_data[1]
                        if os.path.isfile(file_name):
                            http_response = self.send_file(file_name)
                    elif re.search('\\.css$', get_data[1]) is not None:
                        file_name = '/mnt/ramdisk/htdocs' + get_data[1]
                        if os.path.isfile(file_name):
                            http_response = self.send_file(file_name, 'text/css')
                    elif re.search('\\.js$', get_data[1]) is not None:
                        file_name = '/mnt/ramdisk/htdocs' + get_data[1]
                        if os.path.isfile(file_name):
                            http_response = self.send_file(file_name, 'application/x-javascript')
                    elif get_data[1] == u'/':
                        file_name = '/mnt/ramdisk/htdocs/index.html'
                        debug_message.print_message('Get file: ' + file_name)
                        if os.path.isfile(file_name):
                            http_response = self.send_file(file_name)
                    elif get_data[1] == u'/test/' or get_data[1] == u'/test':
                        file_name = '/mnt/ramdisk/htdocs/test/index.html'
                        debug_message.print_message('Get file: ' + file_name)
                        if os.path.isfile(file_name):
                            http_response = self.send_file(file_name)
                    elif get_data[1] == u'/manage/' or get_data[1] == u'/manage':
                        file_name = '/mnt/ramdisk/htdocs/manage/index.html'
                        debug_message.print_message('Get file: ' + file_name)
                        if os.path.isfile(file_name):
                            http_response = self.send_file(file_name)
                    elif get_data[1] == u'/turnstile/' or get_data[1] == u'/turnstile':
                        file_name = '/mnt/ramdisk/htdocs/turnstile/index.html'
                        debug_message.print_message('Get file: ' + file_name)
                        if os.path.isfile(file_name):
                            http_response = self.send_file(file_name)
                    elif get_data[1] == u'/access_point/' or get_data[1] == u'/access_point':
                        file_name = '/mnt/ramdisk/htdocs/access_point/index.html'
                        debug_message.print_message('Get file: ' + file_name)
                        if os.path.isfile(file_name):
                            http_response = self.send_file(file_name)
                    elif get_data[1].startswith(u'/monitor/'):
                        if access_point.is_master():
                            http_response = self.point_monitor(params)
                        else:
                            http_response = self.point_monitor_slave(get_data[1])
                    elif get_data[1].startswith(u'/interface/'):
                        http_response = self.setup_interface(params)
                    elif get_data[1].startswith(u'/setoptions/'):
                        http_response = self.set_mb_options(params)
                    elif get_data[1].startswith(u'/setapoptions/'):
                        http_response = self.set_ap_options(params)
                    elif get_data[1].startswith(u'/lockcard/'):
                        http_response = self.lock_card()
                    elif get_data[1].startswith(u'/unlockcard/'):
                        http_response = self.unlock_card()
                    elif get_data[1].startswith(u'/checklock/'):
                        http_response = self.check_lock()
                    elif get_data[1].startswith(u'/openmb/'):
                        http_response = self.open_mb()
                    elif get_data[1].startswith(u'/openmbenter/'):
                        http_response = self.open_mb_enter()
                    elif get_data[1].startswith(u'/checkwarming/'):
                        http_response = self.check_warming()
                    elif get_data[1].startswith(u'/status/'):
                        http_response = self.check_status()
                    elif get_data[1].startswith(u'/mbstatus/'):
                        http_response = self.check_mb_status()
                    elif get_data[1].startswith(u'/apstatus/'):
                        http_response = self.get_ap_options()
                    elif get_data[1].startswith(u'/testmode/'):
                        http_response = self.test_mode()
                    elif get_data[1].startswith(u'/testmodeoff/'):
                        http_response = self.test_mode_off()
                    elif get_data[1].startswith(u'/resetopensensor/'):
                        http_response = self.reset_open_sensor()
                    elif get_data[1].startswith(u'/rebootpher/'):
                        http_response = self.reboot_pher()
                    elif get_data[1].startswith(u'/rebootdevice/'):
                        http_response = self.reboot_device()
                    elif get_data[1].startswith(u'/rebootmonitor/'):
                        http_response = self.reboot_monitor()
                    elif get_data[1].startswith(u'/pingslave/'):
                        http_response = self.ping_from_slave(self.client_address)
                    elif get_data[1].startswith(u'/freemode/'):
                        http_response = self.set_free_mode()
                    elif get_data[1].startswith(u'/normalmode/'):
                        http_response = self.set_normal_mode()
                    elif get_data[1].startswith(u'/setdatetime/'):
                        http_response = self.set_new_datetime(params)
                    elif get_data[1].startswith(u'/reloaddisplayconfig/'):
                        http_response = self.display_reload_config()
                    elif get_data[1].startswith(u'/closedisplay/'):
                        http_response = self.display_close()
                    elif get_data[1].startswith(u'/displaydebugmessageshow/'):
                        http_response = self.display_show_debug_message()
                    elif get_data[1].startswith(u'/displaydebugmessagehide/'):
                        http_response = self.display_hide_debug_message()
                    elif get_data[1].startswith(u'/displayresetimage/'):
                        http_response = self.display_reset_image()
                    elif get_data[1].startswith(u'/setlightbarcode/'):
                        http_response = self.barcode_light(params)
                    elif get_data[1].startswith(u'/setdebuglevel/'):
                        http_response = self.set_debug_level()
                    elif get_data[1].startswith(u'/getdebugmessages/'):
                        http_response = self.get_debug_messages()
                    elif get_data[1].startswith(u'/accesspointinit/'):
                        http_response = self.get_access_point_init()
                    elif get_data[1].startswith(u'/accesspointparams/'):
                        http_response = self.get_access_point_params()
                    elif get_data[1].startswith(u'/updateaccesspointid/'):
                        http_response = self.update_access_point_id()
                    elif get_data[1].startswith(u'/getlistcount/'):
                        http_response = self.get_list_count()
                    elif get_data[1].startswith(u'/setupdatemode/'):
                        http_response = self.set_update_mode()
            self.wfile.write(http_response)
            self.wfile.flush()
        except Exception as ex:
            debug_message.print_message('---------HTTP SERVER ERROR-------------')
            debug_message.print_message(ex)
            debug_message.print_message(headers)
            debug_message.print_message('---------!HTTP_SERVER_ERROR------------')

        return

    def read_headers(self):
        headers = {}
        for line in self.rfile:
            line = line.strip().lower()
            if not line:
                break
            parts = line.split(':', 2)
            if line.startswith('get'):
                headers['method'] = line
            elif line.startswith('host'):
                headers['host'] = line
            elif len(parts) == 2:
                headers[parts[0].strip()] = parts[1].strip()

        return headers

    def send_basic_auth(self):
        dt = datetime.datetime.now()
        http_response = 'HTTP/1.1 401 Unauthorized \r\n'
        http_response += 'Date: ' + dt.strftime('%a, %d %b %Y %H:%M:%S UTC+3') + '\r\n'
        http_response += 'WWW-Authenticate: Basic realm="Control Auth"\r\n'
        http_response += 'Connection: close\r\n'
        http_response += 'Content-Type: text/html; charset=UTF-8\r\n\r\n'
        return http_response

    def page_not_found(self):
        html_body = 'Page not found!!!'
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Expires: Thu, 19 Nov 1981 08:52:00 GMT\r\n'
        http_response += 'Cache-Control: no-store, no-cache, must-revalidate, post-check=0, pre-check=0\r\n'
        http_response += 'Pragma: no-cache\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n'
        http_response += 'Connection: close\r\n'
        http_response += 'Content-Type: text/html; charset=UTF-8\r\n\r\n'
        http_response += html_body
        return http_response

    def send_file(self, fname, ftype='text/html'):
        html_body = 'Page not found!!!'
        debug_message.print_message('Star send_file')
        with open(fname, 'rb') as (f):
            html_body = f.read()
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Expires: Thu, 19 Nov 1981 08:52:00 GMT\r\n'
        http_response += 'Cache-Control: no-store, no-cache, must-revalidate, post-check=0, pre-check=0\r\n'
        http_response += 'Pragma: no-cache\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n'
        http_response += 'Connection: close\r\n'
        if ftype == 'text/html':
            http_response += 'Content-Type: ' + ftype + ' charset=UTF-8\r\n\r\n'
        else:
            http_response += 'Content-Type: ' + ftype + '\r\n\r\n'
        http_response += html_body
        debug_message.print_message('End send_file')
        return http_response

    def lock_card(self):
        debug_message.print_message('---------LOCK RECEIVED-------------')
        data = {'locked': False}
        if cards_local.lock_cards():
            data = {'locked': True}
            debug_message.print_message('---------CARD IS LOCKED-------------')
        else:
            debug_message.print_message('---------CARD LOCKED FAILED-------------')
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def unlock_card(self):
        debug_message.print_message('---------UNLOCK RECEIVED-------------')
        data = {'unlocked': True}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        cards_local.unlock_cards()
        return http_response

    def check_lock(self):
        data = {'locked': False}
        if cards_lock.locked():
            data = {'locked': True}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def check_status(self):
        _version = access_point.get_version()
        _version_mb = access_point.get_mb_version()
        _temperature = access_point.get_temperature()
        _osbd = access_point.get_osbd_status()
        _slave = access_point.get_slave_status()
        _alarm = access_point.get_alarm()
        _turnstile = access_point.is_turnstile_monitor()
        _mb = access_point.is_online()
        _monitor = access_point.get_monitor_status()
        _reader1 = access_point.get_reader_866_state()
        _reader2 = access_point.get_reader_1356_state()
        _reader3 = access_point.get_reader_barcode_state()
        _cpu = access_point.get_cpu_usage()
        _memory = access_point.get_memory_usage()
        _pin_data = access_point.get_pin_data()
        _startup_time = access_point.get_start_time()
        _mode = True
        if access_point.is_development() or access_point.is_test_mode():
            _mode = False
        _access_mode = access_point.get_access_point_mode()
        _point_type = access_point.get_access_point_type()
        _tmp = access_point.get_match_date()
        _match_date = hexlify(_tmp)
        _param_status = access_point.get_param_status()
        _tmp = access_point.get_current_match_id()
        _reader_866_co = access_point.get_reader_866_reconnects()
        _reader_1356_co = access_point.get_reader_1356_reconnects()
        _reader_barcode_co = access_point.get_reader_barcode_reconnects()
        if _tmp == 0:
            _match_id = '-'
        else:
            _match_id = str(_tmp)
        _data = {'version': _version, 'version_mb': _version_mb, 'reader_1': _reader1, 'reader_2': _reader2, 'reader_3': _reader3, 'turnstile': _turnstile, 'osbd': _osbd, 'mb': _mb, 
           'display': True, 'monitor': _monitor, 'slave': _slave, 'temperature': _temperature, 'open_sensor': _alarm, 
           'point_mode': _mode, 'access_point_mode': _access_mode, 'access_point_type': _point_type, 
           'memory': _memory, 'cpu': _cpu, 'pin_data': _pin_data, 'startup_time': _startup_time, 
           'match_date': _match_date, 'match_id': _match_id, 'param_status': _param_status, 
           '866_reconnects': _reader_866_co, '1356_reconnects': _reader_1356_co, 'barcode_reconnects': _reader_barcode_co}
        _html_body = json.dumps(_data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Age: 0\r\n'
        http_response += 'Cache-Control: post-check=0, pre-check=0\r\n'
        http_response += 'Cache-Control: private, no-store, no-cache, must-revalidate\r\n'
        http_response += 'Content-Type: application/javascript;\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Pragma: no-cache\r\n'
        http_response += 'Expires: Mon, 26 Jul 1997 05:00:00 GMT\r\n'
        http_response += 'Content-Length: ' + str(len(_html_body)) + '\r\n\r\n'
        http_response += _html_body
        del _data
        del _html_body
        return http_response

    def check_mb_status(self):
        data = access_point.get_mb_options()
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Age: 0\r\n'
        http_response += 'Cache-Control: post-check=0, pre-check=0\r\n'
        http_response += 'Cache-Control: private, no-store, no-cache, must-revalidate\r\n'
        http_response += 'Content-Type: application/javascript;\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Pragma: no-cache\r\n'
        http_response += 'Expires: Mon, 26 Jul 1997 05:00:00 GMT\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def get_ap_options(self):
        data = access_point.get_options()
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Age: 0\r\n'
        http_response += 'Cache-Control: post-check=0, pre-check=0\r\n'
        http_response += 'Cache-Control: private, no-store, no-cache, must-revalidate\r\n'
        http_response += 'Content-Type: application/javascript;\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Pragma: no-cache\r\n'
        http_response += 'Expires: Mon, 26 Jul 1997 05:00:00 GMT\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def ping_from_slave(self, ip):
        access_point.set_slave_ping(ip)
        data = {'status': True}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def test_mode(self):
        access_point.set_test_mode()
        data = {'status': True}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def test_mode_off(self):
        access_point.set_test_mode_off()
        data = {'status': True}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def open_mb(self):
        debug_message.print_message('================================Open MB=============================')
        try:
            open_time_start = time.time()
            access_point.start_card_lock_time()
            __is_self_lock = False
            if not common_lock.acquire(False):
                pass
            else:
                __is_self_lock = True
            if access_point.point_direction == DirectionTypes.ENTER:
                access_point.exit_mb()
            else:
                access_point.enter_mb()
            data = {'passed': False}
            if access_point.is_passed_mb():
                data = {'passed': True}
            access_point.set_passed()
            html_body = json.dumps(data)
            http_response = 'HTTP/1.1 200 OK\r\n'
            http_response += 'Content-Type: application/json\r\n'
            http_response += 'Access-Control-Allow-Origin: *\r\n'
            http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
            http_response += html_body
            if __is_self_lock:
                common_lock.release()
            cards_local.unlock_cards()
            debug_message.print_message('--- %s seconds ---' % (time.time() - open_time_start))
            debug_message.print_message('!================================Open MB=============================')
        except Exception as he1:
            debug_message.print_message('==============Open MB Error===================')
            debug_message.print_message(he1)
            debug_message.print_message('==============!Open MB Error==================')

        return http_response

    def open_mb_enter(self):
        debug_message.print_message('================================Open MB Enter=============================')
        try:
            open_time_start = time.time()
            access_point.start_card_lock_time()
            __is_self_lock = False
            if not common_lock.acquire(False):
                pass
            else:
                __is_self_lock = True
            if access_point.point_direction == DirectionTypes.ENTER:
                access_point.enter_mb()
            else:
                access_point.exit_mb()
            data = {'passed': False}
            if access_point.is_passed_mb():
                data = {'passed': True}
            access_point.set_passed()
            html_body = json.dumps(data)
            http_response = 'HTTP/1.1 200 OK\r\n'
            http_response += 'Content-Type: application/json\r\n'
            http_response += 'Access-Control-Allow-Origin: *\r\n'
            http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
            http_response += html_body
            if __is_self_lock:
                common_lock.release()
            cards_local.unlock_cards()
            debug_message.print_message('--- %s seconds ---' % (time.time() - open_time_start))
            debug_message.print_message('!================================Open MB=============================')
        except Exception as he1:
            debug_message.print_message('==============Open MB Error===================')
            debug_message.print_message(he1)
            debug_message.print_message('==============!Open MB Error==================')

        return http_response

    def check_warming(self):
        debug_message.print_message('================================Warming=============================')
        try:
            open_time_start = time.time()
            __is_self_lock = False
            if not common_lock.acquire(False):
                pass
            else:
                __is_self_lock = True
            access_point.start_warming()
            time.sleep(10)
            access_point.stop_warming()
            data = {'passed': True}
            access_point.set_passed()
            html_body = json.dumps(data)
            http_response = 'HTTP/1.1 200 OK\r\n'
            http_response += 'Content-Type: application/json\r\n'
            http_response += 'Access-Control-Allow-Origin: *\r\n'
            http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
            http_response += html_body
            if __is_self_lock:
                common_lock.release()
            debug_message.print_message('--- %s seconds ---' % (time.time() - open_time_start))
            debug_message.print_message('!================================Warming=============================')
        except Exception as he1:
            debug_message.print_message('==============Warming Error===================')
            debug_message.print_message(he1)
            debug_message.print_message('==============!Warming Error==================')

        return http_response

    def point_monitor(self, params):
        client_crc = 0
        access_point.set_monitor_ping()
        if 'crc_time' in params:
            client_crc = params['crc_time'][0]
        js_message = ''
        js_name = ''
        js_has_ic = False
        js_has_tc = False
        js_has_uc = False
        js_can_go = False
        js_has_sp = False
        js_declined = False
        js_time = cards_local.get_latest_time()
        js_online = access_point.get_online()
        image_data = ''
        if client_crc != js_time:
            image_src = cards_local.get_image()
            js_message = cards_local.get_message()
            js_has_ic = cards_local.has_ic_latest()
            js_has_tc = cards_local.has_tc_latest()
            js_has_uc = cards_local.has_uc_latest()
            js_can_go = cards_local.get_latest_can_go()
            js_declined = cards_local.get_latest_is_declined()
            js_has_sp = cards_local.has_sp_latest()
            js_name = cards_local.get_fio()
            if image_src:
                image_data = 'data:image/jpeg;base64,' + image_src
        _data = {'image': image_data, 'message': js_message, 'has_ic': js_has_ic, 'has_uc': js_has_uc, 'has_tc': js_has_tc, 
           'can_go': js_can_go, 'declined': js_declined, 'js_time': js_time, 'js_online': js_online, 
           'js_name': js_name, 'has_sp': js_has_sp}
        _html_body = json.dumps(_data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(_html_body)) + '\r\n\r\n'
        http_response += _html_body
        del _data
        del _html_body
        return http_response

    def point_monitor_slave(self, params):
        data = access_point.proxy(params, timeouts=3)
        html_body = data
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def setup_interface(self, params):
        debug_message.print_message('---------INTERFACE CHANGE RECEIVED-------------')
        _ret = access_point.setup_interface(params)
        data = {'return': _ret}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def set_mb_options(self, params):
        debug_message.print_message('---------OPTIONS CHANGE RECEIVED-------------')
        _ret = access_point.set_mb_options(params)
        data = {'return': _ret}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def set_ap_options(self, params):
        debug_message.print_message('---------AP OPTIONS CHANGE RECEIVED-------------')
        _ret = access_point.save_options(params)
        data = {'return': _ret}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def reset_open_sensor(self):
        debug_message.print_message('---------RESET OPEN SENSOR-------------')
        _ret = access_point.reset_open_sensor()
        data = {'return': _ret}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def reboot_pher(self):
        debug_message.print_message('---------RESET TI-------------')
        _ret = access_point.reboot_pher()
        data = {'return': _ret}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def reboot_device(self):
        debug_message.print_message('---------RESET DEVICE-------------')
        _ret = access_point.reboot_device()
        data = {'return': _ret}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def reboot_monitor(self):
        debug_message.print_message('---------REBOOT MONITOR-------------')
        _ret = access_point.reboot_monitor()
        data = {'return': _ret}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def set_free_mode(self):
        debug_message.print_message('---------SET FREE MODE-------------')
        access_point.set_free_mode()
        data = {'return': True}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def set_normal_mode(self):
        debug_message.print_message('---------SET NORMAL MODE-------------')
        access_point.set_normal_mode()
        data = {'return': True}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def set_new_datetime(self, params):
        data = {'return': False}
        if 'datetime' in params:
            access_point.set_sys_time(params['datetime'][0])
            data = {'return': True}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Age: 0\r\n'
        http_response += 'Cache-Control: post-check=0, pre-check=0\r\n'
        http_response += 'Cache-Control: private, no-store, no-cache, must-revalidate\r\n'
        http_response += 'Content-Type: application/javascript;\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Pragma: no-cache\r\n'
        http_response += 'Expires: Mon, 26 Jul 1997 05:00:00 GMT\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def display_reload_config(self):
        debug_message.print_message('---------RELOAD DISPLAY CONFIG-------------')
        access_point.display_reload_config()
        data = {'return': True}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def display_close(self):
        debug_message.print_message('---------RELOAD DISPLAY CONFIG-------------')
        access_point.display_close()
        data = {'return': True}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def display_show_debug_message(self):
        debug_message.print_message('---------DISPLAY SHOW DEBUG MESSAGE-------------')
        access_point.show_debug_message()
        data = {'return': True}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def display_hide_debug_message(self):
        debug_message.print_message('---------DISPLAY HIDE DEBUG LAYER-------------')
        access_point.hide_debug_layer()
        data = {'return': True}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def display_reset_image(self):
        debug_message.print_message('---------DISPLAY HIDE DEBUG LAYER-------------')
        access_point.reset_display()
        data = {'return': True}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def barcode_light(self, params):
        debug_message.print_message('---------BARCODE LIGHT-------------')
        data = {'return': False}
        if 'command' in params:
            if params['command'][0] == 'LIGHT_ON':
                access_point.set_light_barcode_on()
                data = {'return': True}
            elif params['command'][0] == 'LIGHT_OFF':
                access_point.set_light_barcode_off()
                data = {'return': True}
            elif params['command'][0] == 'LIGHT_PWM_ON':
                access_point.set_light_barcode_blink_on()
                data = {'return': True}
            elif params['command'][0] == 'LIGHT_PWM_OFF':
                access_point.set_light_barcode_blink_off()
                data = {'return': True}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def set_debug_level(self):
        debug_message.print_message('---------SET DEBUG WEB-------------')
        _ret = debug_message.set_web_mode(True)
        data = {'return': _ret}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def get_debug_messages(self):
        debug_message.print_message('---------GET DEBUG MESSAGE-------------')
        _ret = debug_message.get_debug_messages()
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: text/plain; charset=utf-8\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(_ret)) + '\r\n\r\n'
        http_response += _ret
        return http_response

    def check_point_initial(self):
        debug_message.print_message('---------CEHCK POINT INITIAL-------------')
        _ret = debug_message.get_debug_messages()
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: text/plain; charset=utf-8\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(_ret)) + '\r\n\r\n'
        http_response += _ret
        return http_response

    def get_access_point_init(self):
        debug_message.print_message('---------GET ACCESS POINT INIT-------------')
        data = access_point.get_access_point_init()
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def get_access_point_params(self):
        debug_message.print_message('---------GET ACCESS POINT INIT-------------')
        data = access_point.get_access_point_params()
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def update_access_point_id(self):
        debug_message.print_message('---------UPDATE POINTID-------------')
        access_point.set_access_point_init()
        data = {'return': True}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def get_list_count(self):
        debug_message.print_message('---------GET LIST COUNT-------------')
        data = access_point.get_list_count()
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response

    def set_update_mode(self):
        debug_message.print_message('---------UPDATE MODE-------------')
        access_point.set_update_mode()
        data = {'return': True}
        html_body = json.dumps(data)
        http_response = 'HTTP/1.1 200 OK\r\n'
        http_response += 'Content-Type: application/json\r\n'
        http_response += 'Access-Control-Allow-Origin: *\r\n'
        http_response += 'Content-Length: ' + str(len(html_body)) + '\r\n\r\n'
        http_response += html_body
        return http_response


class ThreadedTCPServer(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.tcp_server = None
        return

    def run(self):
        debug_message.print_message('start server')
        self.tcp_server = SocketServer.ThreadingTCPServer(('0.0.0.0', 80), RequestHandlerClass=MyRequestHandlerWithStreamRequestHandler, bind_and_activate=False)
        self.tcp_server.allow_reuse_address = True
        self.tcp_server.server_bind()
        self.tcp_server.server_activate()
        self.tcp_server.serve_forever()

    def exit(self):
        self.tcp_server.shutdown()
        self.tcp_server.server_close()
        self.join(10)
        debug_message.print_message('TCP server exit')
# okay decompiling /home/a/Desktop/app/HttpServer.pyc
