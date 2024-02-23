# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Jul  9 2019, 16:51:35) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/http_server.py
# Compiled at: 2018-05-16 17:40:38
import errno, os, socket, threading, json
from urlparse import urlparse, parse_qs
from common import access_point
from include import cards_local
from config import DirectionTypes, cards_lock, common_lock
import time, re
from binascii import hexlify
from DebugImport import debug_message
SERVER_ADDRESS = HOST, PORT = ('', 80)
REQUEST_QUEUE_SIZE = 30

def grim_reaper(signum, frame):
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
        except OSError:
            return
        else:
            if pid == 0:
                return


class HttpServer(threading.Thread):

    def __init__(self, app_path, unix_socket=''):
        threading.Thread.__init__(self)
        self.unix_socket = unix_socket
        self.port = None
        self.app_path = app_path
        self.client = None
        self.online = True
        self.is_connect = False
        self.thread_w = None
        self.listen_socket = None
        self.timeout = 3.0
        self.connection_timeout = 0.1
        self.threads = []
        self.cur_thread = None
        return

    def run(self):
        self.serve_forever()

    def exit(self):
        self.online = False
        self.join(10)
        if self.isAlive():
            debug_message.print_message("Can't stop Http Server thread")
        else:
            debug_message.print_message('Http Server stopped')

    def path_no(self):
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
        if _tmp == 0:
            _match_id = '-'
        else:
            _match_id = str(_tmp)
        _data = {'version': _version, 'version_mb': _version_mb, 'reader_1': _reader1, 'reader_2': _reader2, 'reader_3': _reader3, 'turnstile': _turnstile, 'osbd': _osbd, 'mb': _mb, 
           'display': True, 'monitor': _monitor, 'slave': _slave, 'temperature': _temperature, 'open_sensor': _alarm, 
           'point_mode': _mode, 'access_point_mode': _access_mode, 'access_point_type': _point_type, 
           'memory': _memory, 'cpu': _cpu, 'pin_data': _pin_data, 'startup_time': _startup_time, 
           'match_date': _match_date, 'match_id': _match_id, 'param_status': _param_status}
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

    def handle_request(self, client_connection, ip_addr):
        connection_closed = False
        try:
            client_connection.settimeout(self.timeout)
            request = client_connection.recv(1024)
            request_text = request.decode()
            http_response = self.path_no()
            request_lines = request_text.splitlines()
            if request_lines and len(request_lines) > 0:
                get_data = request_lines[0].split(' ')
                if get_data and len(get_data) == 3:
                    params = parse_qs(urlparse(get_data[1].encode('utf-8')).query, keep_blank_values=True)
                    if not get_data[1].startswith(u'/Monitor/') and not get_data[1].startswith(u'/Status/'):
                        debug_message.print_message('========================request========================')
                        debug_message.print_message(get_data[1])
                        debug_message.print_message(params)
                        debug_message.print_message('========================!request=======================')
                    if re.search('\\.html$', get_data[1]) is not None:
                        file_name = self.app_path + '/htdocs' + get_data[1]
                        debug_message.print_message('Get file: ' + file_name)
                        if os.path.isfile(file_name):
                            http_response = self.send_file(file_name)
                    elif re.search('\\.js$', get_data[1]) is not None:
                        file_name = self.app_path + '/htdocs' + get_data[1]
                        debug_message.print_message('Get file: ' + file_name)
                        if os.path.isfile(file_name):
                            http_response = self.send_file(file_name, 'application/x-javascript')
                    elif re.search('\\.css$', get_data[1]) is not None:
                        file_name = self.app_path + '/htdocs' + get_data[1]
                        debug_message.print_message('Get file: ' + file_name)
                        if os.path.isfile(file_name):
                            http_response = self.send_file(file_name, 'text/css')
                    elif get_data[1] == u'/':
                        file_name = self.app_path + '/htdocs/index.html'
                        debug_message.print_message('Get file: ' + file_name)
                        if os.path.isfile(file_name):
                            http_response = self.send_file(file_name)
                    elif get_data[1] == u'/test/' or get_data[1] == u'/test':
                        file_name = self.app_path + '/htdocs/test/index.html'
                        debug_message.print_message('Get file: ' + file_name)
                        if os.path.isfile(file_name):
                            http_response = self.send_file(file_name)
                    elif get_data[1] == u'/manage/' or get_data[1] == u'/manage':
                        file_name = self.app_path + '/htdocs/manage/index.html'
                        debug_message.print_message('Get file: ' + file_name)
                        if os.path.isfile(file_name):
                            http_response = self.send_file(file_name)
                    elif get_data[1] == u'/turnstile/' or get_data[1] == u'/turnstile':
                        file_name = self.app_path + '/htdocs/turnstile/index.html'
                        debug_message.print_message('Get file: ' + file_name)
                        if os.path.isfile(file_name):
                            http_response = self.send_file(file_name)
                    elif get_data[1] == u'/access_point/' or get_data[1] == u'/access_point':
                        file_name = self.app_path + '/htdocs/access_point/index.html'
                        debug_message.print_message('Get file: ' + file_name)
                        if os.path.isfile(file_name):
                            http_response = self.send_file(file_name)
                    elif get_data[1].startswith(u'/Monitor/'):
                        if access_point.is_master():
                            http_response = self.point_monitor(params)
                        else:
                            http_response = self.point_monitor_slave(get_data[1])
                    elif get_data[1].startswith(u'/Interface/'):
                        http_response = self.setup_interface(params)
                    elif get_data[1].startswith(u'/SetOptions/'):
                        http_response = self.set_mb_options(params)
                    elif get_data[1].startswith(u'/SetApOptions/'):
                        http_response = self.set_ap_options(params)
                    elif get_data[1].startswith(u'/LockCard/'):
                        http_response = self.lock_card()
                    elif get_data[1].startswith(u'/UnlockCard/'):
                        http_response = self.unlock_card()
                    elif get_data[1].startswith(u'/CheckLock/'):
                        http_response = self.check_lock()
                    elif get_data[1].startswith(u'/OpenMb/'):
                        http_response = self.open_mb()
                    elif get_data[1].startswith(u'/OpenMbEnter/'):
                        http_response = self.open_mb_enter()
                    elif get_data[1].startswith(u'/CheckWarming/'):
                        http_response = self.check_warming()
                    elif get_data[1].startswith(u'/Status/'):
                        http_response = self.check_status()
                    elif get_data[1].startswith(u'/MbStatus/'):
                        http_response = self.check_mb_status()
                    elif get_data[1].startswith(u'/ApStatus/'):
                        http_response = self.get_ap_options()
                    elif get_data[1].startswith(u'/TestMode/'):
                        http_response = self.test_mode()
                    elif get_data[1].startswith(u'/TestModeOff/'):
                        http_response = self.test_mode_off()
                    elif get_data[1].startswith(u'/ResetOpenSensor/'):
                        http_response = self.reset_open_sensor()
                    elif get_data[1].startswith(u'/RebootPher/'):
                        http_response = self.reboot_pher()
                    elif get_data[1].startswith(u'/RebootDevice/'):
                        http_response = self.reboot_device()
                    elif get_data[1].startswith(u'/RebootMonitor/'):
                        http_response = self.reboot_monitor()
                    elif get_data[1].startswith(u'/PingSlave/'):
                        http_response = self.ping_from_slave(ip_addr)
                    elif get_data[1].startswith(u'/FreeMode/'):
                        http_response = self.set_free_mode()
                    elif get_data[1].startswith(u'/NormalMode/'):
                        http_response = self.set_normal_mode()
                    elif get_data[1].startswith(u'/SetDatetime/'):
                        http_response = self.set_new_datetime(params)
                    elif get_data[1].startswith(u'/ReloadDisplayConfig/'):
                        http_response = self.display_reload_config()
                    elif get_data[1].startswith(u'/CloseDisplay/'):
                        http_response = self.display_close()
                    elif get_data[1].startswith(u'/DisplayDebugMessageShow/'):
                        http_response = self.display_show_debug_message()
                    elif get_data[1].startswith(u'/DisplayDebugMessageHide/'):
                        http_response = self.display_hide_debug_message()
                    elif get_data[1].startswith(u'/DisplayResetImage/'):
                        http_response = self.display_reset_image()
                    elif get_data[1].startswith(u'/SetLightBarcode/'):
                        http_response = self.barcode_light(params)
                    elif get_data[1].startswith(u'/SetDebugLevel/'):
                        http_response = self.set_debug_level()
                    elif get_data[1].startswith(u'/GetDebugMessages/'):
                        http_response = self.get_debug_messages()
            client_connection.sendall(http_response)
            client_connection.close()
            connection_closed = True
        except Exception as he:
            debug_message.print_message('============Handler stopped 1==============')
            debug_message.print_message(he)
            debug_message.print_message('============!Handler stopped 1=============')

        if not connection_closed:
            try:
                http_response = self.path_no()
                client_connection.sendall(http_response)
                client_connection.close()
            except Exception as he:
                debug_message.print_message('============Handler stopped 2==============')
                debug_message.print_message(he)
                debug_message.print_message('============!Handler stopped 2=============')

        return

    def serve_forever(self):
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_socket.settimeout(self.connection_timeout)
        self.listen_socket.bind(SERVER_ADDRESS)
        self.listen_socket.listen(REQUEST_QUEUE_SIZE)
        debug_message.print_message(('Serving HTTP on port {port} ...').format(port=PORT))
        while self.online:
            try:
                client_connection, client_address = self.listen_socket.accept()
            except socket.timeout:
                continue
            except IOError as e1:
                debug_message.print_message('Http Server accept error')
                debug_message.print_message(e1)
                code, msg = e1.args
                if code == errno.EINTR:
                    continue
                else:
                    continue
            else:
                try:
                    http_client_thread = threading.Thread(target=self.handle_request(client_connection, client_address[0]))
                    http_client_thread.start()
                    self.cur_thread = http_client_thread
                except Exception as e2:
                    debug_message.print_message('================Http Error==========================')
                    debug_message.print_message(e2)
                    debug_message.print_message('================!Http Error=========================')

        try:
            self.listen_socket.shutdown(socket.SHUT_RDWR)
            self.listen_socket.close()
            if self.cur_thread is not None:
                self.cur_thread.join()
        except Exception as e3:
            debug_message.print_message('==============Http Listen Error==========================')
            debug_message.print_message(e3)
            debug_message.print_message('==============!Http Listen Error=========================')

        debug_message.print_message('HTTP server stopped')
        return
# okay decompiling /home/a/Desktop/app/http_server.pyc
