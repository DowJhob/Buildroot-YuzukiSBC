# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Oct  7 2019, 17:39:04) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/Card.py
# Compiled at: 2018-06-15 14:00:50
from lib import singleton, float_eq
from common import access_point
from config import StatusTypes, PassTypes, EventTypes, DirectionTypes, AccessPointTypes, CardTypes
from config import add_lock, waiting_lock, cards_lock, card_write_lock
import time, threading, copy
from DebugImport import debug_message

class Card:

    def __init__(self, rfid, barcode, direction):
        self.direction = direction
        self.rfid = rfid
        self.barcode = barcode
        self.pass_type = None
        self.pass_id = None
        self.name = ''
        self.photo = ''
        self.code = ''
        self.time = ''
        self.let_go = StatusTypes.NOACCESS
        self.flag = 0
        self.message = ''
        self.PassTypes = PassTypes
        self.card_type = CardTypes.RFID
        self.is_local = False
        self.local_code = ''
        return

    def pass_group(self):
        ret = self.pass_type
        if ret is not None and self.is_ic():
            ret = self.PassTypes.IC
        return ret

    def is_ic(self):
        ret = False
        if self.pass_type is None:
            return ret
        if self.pass_type == self.PassTypes.IC or self.pass_type == self.PassTypes.IAC or self.pass_type == self.PassTypes.DP or self.pass_type == self.PassTypes.GP or self.pass_type == self.PassTypes.SP or self.pass_type == self.PassTypes.SC or self.pass_type == self.PassTypes.SD or self.pass_type == self.PassTypes.MP or self.pass_type == self.PassTypes.RP or self.pass_type == self.PassTypes.NP or self.pass_type == self.PassTypes.T1 or self.pass_type == self.PassTypes.T2:
            ret = True
        return ret


@singleton
class Cards:

    def __init__(self):
        self.cards = {}
        self.cur_card = None
        self.latest_cards = {}
        self.latest_can_go = False
        self.latest_is_declined = False
        self.latest_is_pass = False
        self.pass_types = {'UD': -2, 'NA': -1, 'TC': 0, 'IC': 1, 'IAC': 2, 'UC': 3, 'DP': 4, 'GP': 5, 'SP': 6, 'SC': 7, 'SD': 8}
        self.is_enter = False
        self.time_action_wait = 10
        self.monitor_action_wait = 3
        self.start_time = 0
        self.current_time = 0
        self.thread_w = None
        self.thread_ww = None
        self.is_own = False
        self.barcode_status_changed = False
        return

    def is_busy(self):
        return add_lock.locked() or waiting_lock.locked()

    def lock_cards(self):
        if self.is_busy():
            return False
        else:
            if not cards_lock.acquire(False):
                return False
            access_point.start_card_lock_time()
            return True

    def unlock_cards(self):
        try:
            if cards_lock.locked():
                cards_lock.release()
        except Exception as e:
            debug_message.print_message('-------------Cards lock release error---------')
            debug_message.print_message(e)
            debug_message.print_message('-------------Cards lock release error---------')

        access_point.stop_card_lock_time()

    def get_card(self, rfid, barcode, direction, card_type, code, rf1356, pwdpack):
        card = access_point.check_card(direction, card_type=card_type, code=code, _rf1356=rf1356, _pwdpack=pwdpack)
        self.cur_card = Card(rfid, barcode, direction)
        self.cur_card.code = code
        self.cur_card.card_type = card_type
        self.cur_card.time = time.time()
        if card is not None:
            self.cur_card.pass_type = card['PassType']
            self.cur_card.pass_id = card['PassID']
            if card['NameOnPass'] is not None:
                self.cur_card.name = card['NameOnPass']
            if card['Photo'] is not None:
                self.cur_card.photo = card['Photo']
            self.cur_card.let_go = card['LetGo']
            self.cur_card.flag = card['Flag']
            self.cur_card.message = card['Message']
            if 'IsLocal' in card and card['IsLocal'] is not None and type(card['IsLocal']) is bool:
                self.cur_card.is_local = card['IsLocal']
            if 'LocalCode' in card and card['LocalCode'] is not None:
                self.cur_card.local_code = card['LocalCode']
        return

    def add_card(self):
        if not access_point.is_online():
            return
        else:
            if self.cur_card.pass_id is None:
                debug_message.print_message('Card pass_id is None')
            else:
                debug_message.print_message('Card pass_id: ' + str(self.cur_card.pass_id))
            try:
                if len(self.cards) == 0:
                    self.latest_cards.clear()
                    self.latest_can_go = False
                    self.latest_is_pass = False
                    self.latest_is_declined = False
            except Exception as e:
                pass

            self.cards[self.cur_card.code] = copy.deepcopy(self.cur_card)
            self.latest_cards[self.cur_card.code] = copy.deepcopy(self.cur_card)
            self.cur_card = None
            access_point.latest_time_index = time.time()
            return

    def add(self, rfid='', barcode='', direction=None, rf1356=False, pwdpack=False):
        debug_message.print_message('In Card adding a record......')
        if not access_point.is_turnstile_monitor():
            debug_message.print_message('Turnstile not ready')
            access_point.send_queue()
            return
        else:
            if not add_lock.acquire(False):
                debug_message.print_message('--------Card thread is locked-------------')
                access_point.send_queue()
            elif direction is None:
                direction = access_point.point_direction
            else:
                code = rfid
                card_type = CardTypes.RFID
                if barcode:
                    code = barcode
                    card_type = CardTypes.BARCODE
                elif rf1356 and access_point.type_id == AccessPointTypes.SP and len(rfid) > 0:
                    barcode = code
                    card_type = CardTypes.BARCODE
                    rfid = ''
                else:
                    if not code or code in self.cards:
                        debug_message.print_message('\t-Code already present')
                        add_lock.release()
                        return
                    if not self.can_check_card(rfid, barcode, direction):
                        add_lock.release()
                        return
                    if access_point.is_master() and cards_lock.locked():
                        debug_message.print_message('------------Cards is locked by slave-------------------')
                        access_point.show_stop()
                        time.sleep(1)
                        access_point.reset_display()
                        add_lock.release()
                        access_point.send_queue()
                        return

                if access_point.is_slave() and len(self.cards) == 0:
                    can_lock = access_point.lock_master()
                    if not can_lock:
                        access_point.show_stop()
                        time.sleep(1)
                        access_point.reset_display()
                        add_lock.release()
                        access_point.send_queue()
                        return
                debug_message.print_message('======================In Card add method======================')
                if code and code not in self.cards:
                    if card_write_lock.locked():
                        debug_message.print_message('==============Already in write log====================')
                        add_lock.release()
                        return
                    access_point.show_wait()
                    if card_write_lock.locked():
                        debug_message.print_message('==============Already in write log====================')
                        add_lock.release()
                        return
                    self.start_time = time.time()
                    debug_message.print_message('New card with ' + code)
                    self.get_card(rfid, barcode, direction, card_type, code, rf1356, pwdpack)
                    self.add_card()
                    self.display_info()
                    if self.can_go():
                        self.time_action_wait = access_point.get_time_wait_pass()
                        self.latest_can_go = True
                        access_point.latest_time_index = time.time()
                        if self.waiting_circle_lock():
                            self.thread_w = threading.Thread(target=self.waiting_circle)
                            self.thread_w.start()
                        if access_point.point_direction == DirectionTypes.ENTER:
                            self.thread_ww = threading.Thread(target=access_point.enter_mb)
                            self.thread_ww.start()
                        else:
                            self.thread_ww = threading.Thread(target=access_point.exit_mb)
                            self.thread_ww.start()
                        self.thread_w.join(self.time_action_wait)
                        _tmp_sleep = access_point.get_option('mb_timeout', 0.4)
                        if not float_eq(_tmp_sleep, 0):
                            time.sleep(_tmp_sleep)
                    elif self.is_declined():
                        self.latest_is_declined = True
                        access_point.latest_time_index = time.time()
                        self.time_action_wait = access_point.get_time_decline()
                        if self.waiting_circle_lock():
                            self.thread_w = threading.Thread(target=self.waiting_circle)
                            self.thread_w.start()
                        self.thread_w.join(self.time_action_wait)
                    elif access_point.type_id == AccessPointTypes.SP and self.has_ic() and access_point.check_pass:
                        debug_message.print_message('===Active barcode====')
                        self.time_action_wait = access_point.get_time_wait_card()
                        access_point.start_read_barcode()
                        if self.waiting_circle_lock():
                            self.thread_w = threading.Thread(target=self.waiting_circle)
                            self.thread_w.start()
                    else:
                        self.time_action_wait = access_point.get_time_wait_card()
                        if self.waiting_circle_lock():
                            self.thread_w = threading.Thread(target=self.waiting_circle)
                            self.thread_w.start()
                    access_point.latest_time_index = time.time()
                else:
                    debug_message.print_message('Card with ' + code + ' already added')
                debug_message.print_message('======================!In Card add method=====================')
                add_lock.release()

            return

    def waiting_circle_lock(self):
        if not waiting_lock.locked():
            if not waiting_lock.acquire(False):
                debug_message.print_message('------------Waiting circle already started-------------')
            else:
                return True
        return False

    def waiting_circle(self):
        debug_message.print_message('================in waiting circle====================')
        tmp_time = time.time()
        debug_message.print_message('\t\tStart time: ' + str(tmp_time))
        tick_var = 0
        tick_tl = 0
        debug_message.print_message('block waiting circle: ' + str(self.start_time))
        while self.start_time > 0 and time.time() - self.start_time < self.time_action_wait:
            cur_sub_time = time.time() - self.start_time
            if tick_var > 1:
                debug_message.print_message('-----in 10 time circle: ' + str(cur_sub_time))
                tick_var = 0
            time.sleep(0.1)
            tick_var += 0.1
            if self.get_ff_mode() and self.is_declined() and self.get_flag() == 16:
                if float_eq(tick_tl, 0.8):
                    tick_tl = 0
                if float_eq(tick_tl, 0):
                    access_point.show_red()
                elif float_eq(tick_tl, 0.4):
                    access_point.show_tl()
                tick_tl += 0.1
            if self.has_blink_led() and self.can_go():
                if float_eq(tick_tl, 0.6):
                    tick_tl = 0
                if float_eq(tick_tl, 0):
                    access_point.show_green()
                elif float_eq(tick_tl, 0.3):
                    access_point.show_tl()
                tick_tl += 0.1
            if access_point.is_passed_mb():
                debug_message.print_message('-------Cards: Person is enter-------')
                self.latest_is_pass = True
                self.is_enter = True
                access_point.latest_time_index = time.time()
                break

        card_write_lock.acquire()
        try:
            if self.thread_ww is not None and self.thread_ww.is_alive():
                self.thread_ww.join(4)
        except Exception as e:
            debug_message.print_message(e)

        access_point.set_passed()
        self.write_log()
        tmp_time = time.time()
        debug_message.print_message('\t\tStop time: ' + str(tmp_time))
        card_write_lock.release()
        waiting_lock.release()
        debug_message.print_message('=================!in waiting circle=================')
        return

    def can_check_card(self, rfid, barcode, direction):
        debug_message.print_message('==============Can check card=====================')
        debug_message.print_message('Point type: ' + str(access_point.type_id))
        if access_point.direction != DirectionTypes.ENTEREXIT:
            if access_point.direction != DirectionTypes.DEFAULT:
                if access_point.point_direction != access_point.direction:
                    debug_message.print_message('Direction not allowed')
                    access_point.send_queue()
                    return False
        if access_point.type_id not in [AccessPointTypes.SP, AccessPointTypes.AT]:
            debug_message.print_message('Wrong point type')
            access_point.send_queue()
            return False
        if self.is_declined():
            debug_message.print_message('Has declined card')
            return False
        debug_message.print_message('Access point direction: ' + str(access_point.direction))
        debug_message.print_message('Point direction: ' + str(access_point.point_direction))
        debug_message.print_message('Card direction: ' + str(direction))
        if access_point.direction != DirectionTypes.ENTEREXIT:
            if direction != access_point.point_direction:
                debug_message.print_message('Direction does not match')
                access_point.send_queue()
                return False
        if access_point.type_id == AccessPointTypes.SP:
            debug_message.print_message('Find Access point in SP mode')
            if rfid:
                if not access_point.check_pass:
                    debug_message.print_message('Rfid is disabled in SP mode')
                    access_point.send_queue()
                    return False
                if self.has_sp():
                    debug_message.print_message('SP card already added in SP mode')
                    return False
            if barcode:
                debug_message.print_message('Barcode found')
                if self.has_barcode():
                    debug_message.print_message('Barcode already added in SP mode')
                    return False
                if not self.has_ic() and access_point.check_pass:
                    debug_message.print_message('Rfid not yet added in SP mode')
                    access_point.send_queue()
                    return False
        else:
            debug_message.print_message('Find access point in AT mode')
            if barcode:
                debug_message.print_message('Barcode already added in AT mode')
                access_point.send_queue()
                return False
        if self.has_empty_card() and access_point.online:
            debug_message.print_message('Has empty cards')
            return False
        if self.can_write_log():
            debug_message.print_message('Cards is full')
            return False
        debug_message.print_message('==============!Can check card====================')
        return True

    def can_write_log(self):
        if len(self.cards) == 2:
            return True
        if self.can_go():
            return True
        return False

    def get(self):
        for k, v in self.cards.items():
            debug_message.print_message(v.code)

    def get_image(self):
        ret = ''
        if len(self.latest_cards) > 0:
            data = {k:v for k, v in self.latest_cards.items() if len(v.photo) > 0}
            if data:
                ret = data.values()[0].photo
        return ret

    def get_fio(self):
        ret = ''
        if len(self.latest_cards) > 0:
            data = {k:v for k, v in self.latest_cards.items() if len(v.name) > 0}
            if data:
                ret = data.values()[0].name
        return ret

    def has_ic_latest(self):
        ret = False
        if len(self.latest_cards) > 0:
            data = {k:v for k, v in self.latest_cards.items() if v.pass_group() == PassTypes.IC}
            if data:
                ret = True
        return ret

    def has_sp_latest(self):
        ret = False
        if len(self.latest_cards) > 0:
            data = {k:v for k, v in self.latest_cards.items() if v.pass_group() == PassTypes.SP}
            if data:
                ret = True
        return ret

    def has_uc_latest(self):
        ret = False
        if len(self.latest_cards) > 0:
            data = {k:v for k, v in self.latest_cards.items() if v.pass_group() == PassTypes.UC}
            if data:
                ret = True
        return ret

    def has_tc_latest(self):
        ret = False
        if len(self.latest_cards) > 0:
            data = {k:v for k, v in self.latest_cards.items() if v.pass_group() == PassTypes.TC}
            if data:
                ret = True
        return ret

    def get_latest_time(self):
        return str(access_point.latest_time_index)

    def get_latest_can_go(self):
        return self.latest_can_go

    def get_latest_is_declined(self):
        return self.latest_is_declined

    def get_latest_is_pass(self):
        return self.latest_is_pass

    def get_message(self):
        message = ''
        flag = -1
        if len(self.latest_cards) > 0:
            for k, v in self.latest_cards.items():
                if v.flag > flag:
                    message = v.message

        return message

    def has_ic(self):
        ret = False
        if len(self.cards) > 0:
            data = {k:v for k, v in self.cards.items() if v.pass_group() == PassTypes.IC}
            if data:
                ret = True
        return ret

    def has_double_ic(self):
        if self.cards:
            data = {k:v for k, v in self.cards.items() if v.pass_group() == PassTypes.IC}
            if data and len(data) == 2:
                debug_message.print_message('Double cards with IC group!!!')
                return True
        return False

    def has_uc(self):
        ret = False
        if len(self.cards) > 0:
            data = {k:v for k, v in self.cards.items() if v.pass_group() == PassTypes.UC}
            if data:
                ret = True
        return ret

    def has_empty_card(self):
        ret = False
        if len(self.cards) > 0:
            data = {k:v for k, v in self.cards.items() if v.pass_id is None}
            if data:
                ret = True
        return ret

    def has_tc(self):
        ret = False
        if len(self.cards) > 0:
            data = {k:v for k, v in self.cards.items() if v.pass_group() == PassTypes.TC}
            if data:
                ret = True
        return ret

    def has_sp(self):
        ret = False
        if len(self.cards) > 0:
            data = {k:v for k, v in self.cards.items() if v.pass_type == PassTypes.SP}
            if data:
                ret = True
        return ret

    def has_rfid(self):
        ret = False
        if len(self.cards) > 0:
            data = {k:v for k, v in self.cards.items() if v.card_type == CardTypes.RFID}
            if data:
                ret = True
        return ret

    def has_barcode(self):
        ret = False
        if len(self.cards) > 0:
            data = {k:v for k, v in self.cards.items() if v.card_type == CardTypes.BARCODE}
            if data:
                ret = True
        return ret

    def has_local_card(self):
        ret = False
        if len(self.cards) > 0:
            data = {k:v for k, v in self.cards.items() if v.is_local is True}
            if data:
                ret = True
        return ret

    def has_blink_led(self):
        ret = False
        if len(self.cards) > 0:
            data = {k:v for k, v in self.cards.items() if v.local_code == 'CH'}
            if data:
                ret = True
        return ret

    def can_go(self):
        ret = False
        if len(self.cards) > 0:
            if self.has_double_ic():
                return False
            if access_point.type_id == AccessPointTypes.SP and not access_point.check_pass:
                debug_message.print_message('=========In Cards GO checking access via ticket==========')
                data = {k:v for k, v in self.cards.items() if v.pass_group() == PassTypes.TC and v.let_go == StatusTypes.ALLOW}
                if not data:
                    debug_message.print_message('Access not allowed!!!')
                else:
                    debug_message.print_message('Allow access by ticket')
                    debug_message.print_message(data)
                debug_message.print_message('=========!In Cards GO checking access via ticket=========')
            elif self.is_spectator_has_not_ticket():
                return False
            else:
                debug_message.print_message('=========In Cards GO. Checking access by one card==============')
                data = {k:v for k, v in self.cards.items() if v.pass_group() == PassTypes.IC and v.let_go == StatusTypes.ALLOW}
                if not data:
                    debug_message.print_message('===========In Cards Go. Checking for access with UC or TC===========')
                    data = {k:v for k, v in self.cards.items() if v.pass_group() == PassTypes.IC and v.let_go == StatusTypes.NOACCESS} and ({k:v for k, v in self.cards.items() if v.pass_group() == PassTypes.UC and v.let_go == StatusTypes.ALLOW} or {k:v for k, v in self.cards.items() if v.pass_group() == PassTypes.TC and v.let_go == StatusTypes.ALLOW})
                    if not data:
                        debug_message.print_message('Access not allowed!!!')
                    else:
                        debug_message.print_message('Allow access by two card')
                        debug_message.print_message(data)
                    debug_message.print_message('===========!In Cards Go. Checking for access with UC or TC===========')
                else:
                    debug_message.print_message('Allow access by one card')
                    debug_message.print_message(data)
                debug_message.print_message('=========!In Cards GO. Checking access by one card=============')

            if len(data):
                ret = True
        return ret

    def is_spectator_has_ticket(self):
        _card_list = list(self.cards.keys())
        if access_point.type_id == AccessPointTypes.SP and len(_card_list) == 2 and self.has_sp() and self.has_tc():
            return True
        return False

    def is_spectator_has_not_ticket(self):
        _card_list = list(self.cards.keys())
        if access_point.type_id == AccessPointTypes.SP and len(_card_list) >= 2 and self.has_sp() and not self.has_tc():
            return True
        return False

    def is_declined(self):
        ret = False
        if len(self.cards) > 0:
            data = {k:v for k, v in self.cards.items() if v.let_go == StatusTypes.DECLINED}
            if len(data):
                ret = True
            else:
                if self.is_spectator_has_not_ticket():
                    ret = True
                if self.has_double_ic():
                    ret = True
        return ret

    def is_let_go(self):
        ret = False
        if len(self.cards) > 0:
            data = {k:v for k, v in self.cards.items() if v.let_go == StatusTypes.ALLOW}
            if len(data):
                ret = True
        return ret

    def get_flag(self):
        flag = EventTypes.UNA.value
        if len(self.cards) > 0:
            flag = max(v.flag for v in self.cards.values())
            if self.can_go():
                flag = EventTypes.REF.value
                if self.is_enter:
                    flag = EventTypes.ENT.value
            if self.is_declined() and flag == 10:
                flag = EventTypes.WRFID.value
            if self.has_double_ic():
                flag = EventTypes.WCT.value
            if self.is_spectator_has_not_ticket():
                flag = EventTypes.WCT.value
            if not self.can_go() and flag == EventTypes.ENT:
                flag = EventTypes.UNA.value
        return flag

    def write_log(self):
        debug_message.print_message('In cards write logs')
        if len(self.cards) > 0:
            llist = list(self.cards.keys())
            card1 = self.cards.get(llist[0])
            card2 = None
            if len(llist) == 2:
                card2 = self.cards.get(llist[1])
            is_log_online = True
            if card1.pass_id is None or card2 is not None and card2.pass_id is None:
                is_log_online = False
            if self.has_local_card():
                debug_message.print_message('\tCard is defined as local')
                is_log_online = False
            if is_log_online:
                access_point.write_log(access_point.point_direction, self.get_flag(), card1, card2)
            else:
                access_point.write_log_offline(access_point.point_direction, self.get_flag(), card1, card2)
            if access_point.is_slave():
                access_point.unlock_master()
        self.clear()
        return

    def clear(self):
        self.cards.clear()
        self.is_enter = False
        access_point.reset_display()
        access_point.send_queue()
        monitor_thread = threading.Thread(target=self.clear_monitor)
        monitor_thread.start()

    def clear_monitor(self):
        monitor_clear_time = time.time()
        while time.time() - monitor_clear_time < self.monitor_action_wait:
            time.sleep(0.01)

        if not self.is_busy() and len(self.cards) == 0:
            try:
                self.latest_cards.clear()
                self.latest_can_go = False
                self.latest_is_pass = False
                self.latest_is_declined = False
                access_point.latest_time_index = time.time()
            except Exception as e:
                pass

    def get_stop_prefix(self):
        _prefix = ''
        if self.get_ff_mode():
            if self.get_flag() == 16:
                _prefix = '_wn'
            else:
                _prefix = '_inv'
        elif self.has_tc():
            _prefix = '_tc'
        elif self.has_sp():
            _prefix = '_fs'
        elif self.has_ic():
            _prefix = '_ac'
        debug_message.print_message('--------Stop prefix is ' + _prefix)
        return _prefix

    def get_go_prefix(self):
        if not self.get_ff_mode():
            return ''
        _prefix = ''
        if access_point.point_direction == DirectionTypes.ENTER:
            _prefix = '_en'
        elif access_point.point_direction == DirectionTypes.EXIT:
            _prefix = '_ex'
        debug_message.print_message('--------Go prefix is ' + _prefix)
        return _prefix

    def display_info(self):
        if self.can_go():
            access_point.show_go(prefix=self.get_go_prefix())
        elif self.is_declined():
            access_point.show_stop(prefix=self.get_stop_prefix())
        elif self.has_empty_card():
            access_point.show_stop()
        elif len(self.cards) == 0:
            access_point.show_passport()
        elif len(self.cards) == 1:
            if access_point.type_id != AccessPointTypes.SP:
                access_point.show_addition()
            else:
                access_point.show_addition_ticket()
        elif len(self.cards) == 2:
            access_point.show_stop()

    def is_barcode_active(self):
        return access_point.is_barcode_active()

    def get_barcode_status(self):
        _tmp = access_point.is_barcode_active()
        if _tmp != self.barcode_status_changed:
            debug_message.print_message('------------Barcode status changed-------------')
            self.barcode_status_changed = _tmp
            return True
        return False

    def is_rfid_1356_active(self):
        return access_point.is_rfid_1356_active()

    def is_rfid_866_active(self):
        return access_point.is_rfid_866_active()

    def get_key_server_ip(self):
        return access_point.get_key_server_ip()

    def get_key_server_port(self):
        return access_point.get_key_server_port()

    def get_ff_mode(self):
        return access_point.get_option('ff_mode', False)

    def get_sac(self):
        return access_point.get_sac()

    def get_match_id(self):
        return access_point.get_current_match_id()

    def get_match_date(self):
        return access_point.get_match_date()

    def get_nfc_enable(self):
        return access_point.get_nfc_enable()

    def get_barcode_length(self, barcode_type=6):
        if barcode_type == 3:
            return access_point.barcode_length_128
        else:
            return access_point.barcode_length_2of5

    def get_barcode_type(self):
        if access_point.barcode_length_2of5 > 0:
            return 6
        else:
            if access_point.barcode_length_128 > 0:
                return 3
            else:
                return

            return