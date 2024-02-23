# uncompyle6 version 3.4.0
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.15+ (default, Jul  9 2019, 16:51:35) 
# [GCC 7.4.0]
# Embedded file name: /home/user/zeus/Display.py
# Compiled at: 2018-05-25 13:32:18
import sys, os, time, subprocess, threading, Queue
from display_wrapper import DisplayWrapper
from DebugImport import debug_message
display_wrapper = DisplayWrapper()

class DisplayData:

    def __init__(self, command, message):
        self.command = command
        self.message = message


class Display(threading.Thread):

    def __init__(self, app_path, display):
        threading.Thread.__init__(self)
        self.app_path = app_path
        self.display = display
        self.queue_display = Queue.Queue()
        self.online = True
        self.pipeout = None
        return

    def open_pipe(self):
        if self.pipeout is not None:
            try:
                os.close(self.pipeout)
            except:
                pass

        self.pipeout = os.open('/mnt/ramdisk/server', os.O_WRONLY)
        return

    def run(self):
        debug_message.print_message('------Display run----------')
        self.open_pipe()
        self.hide_debug_layer()
        self.set_message('')
        while self.online:
            try:
                if not self.queue_display.empty():
                    data = self.queue_display.get(block=True)
                    if isinstance(data, DisplayData):
                        self.run_cmd(data.command, data.message)
                    self.queue_display.task_done()
            except:
                pass
            else:
                time.sleep(0.05)

    def initialize(self):
        debug_message.print_message('Initialize display')
        cmd = 'echo -en "\\033[9;0]" > /dev/tty0'
        self.run_cmd_thread(_cmd=cmd)

    def exit(self):
        if self.online:
            self.online = False
        self.join(10)
        debug_message.print_message('Display stopped')

    def show_wait(self):
        self.show('wait', 'Display show wait')

    def show_passport(self):
        self.show('card', 'Display show passport')

    def show_addition(self):
        self.show('addition', 'Display show addition')

    def show_ticket(self):
        self.show('ticket', 'Display show ticket')

    def show_addition_ticket(self):
        self.show('ticket_m', 'Display show ticket')

    def show_stop(self, prefix=''):
        self.show('stop' + prefix, 'Display show stop with prefix: ' + prefix)

    def show_go(self, prefix=''):
        self.show('go' + prefix, 'Display show go')

    def show(self, command, message):
        self.queue_display.put(DisplayData(command, message))

    def show_temp(self, value):
        self.show_text(value)

    def show_text(self, value):
        cmd = 'echo -en "' + str(value) + ' | " > /dev/tty0'
        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.communicate('mq')
        p.stdout.close()
        sys.stdout.flush()

    def run_cmd_pipe(self, _cmd=''):
        os.system(_cmd)

    def run_cmd_thread(self, _cmd=''):
        p = subprocess.Popen(_cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.communicate('q')
        p.stdout.close()
        sys.stdout.flush()

    def wrapper_open_display(self):
        _thread_dl = threading.Thread(target=display_wrapper.open_image(_image))
        _thread_dl.start()
        _thread_dl.join(0.4)
        if _thread_dl.isAlive():
            debug_message.print_message('\t\t-Display command make killall')
            cmd = 'killall -9 fbv'
            os.system(cmd % os.getpid())

    def run_cmd(self, image='', message=''):
        open_time_start = time.time()
        self.send_to_pipe(image)
        debug_message.print_message(message)
        debug_message.print_message('Display --- %s seconds ---' % (time.time() - open_time_start))

    def send_to_pipe(self, image=''):
        try:
            os.write(self.pipeout, '%s' % image)
        except IOError as e:
            self.resend_to_pipe(image)
            debug_message.print_message(e)

    def resend_to_pipe(self, image=''):
        try:
            self.open_pipe()
            os.write(self.pipeout, '%s' % image)
        except IOError as e:
            debug_message.print_message(e)

    def set_message(self, message):
        debug_message.print_message('write message: ' + message)
        with open('/mnt/ramdisk/dmsg.txt', 'wb') as (_file):
            _file.write(message)

    def show_debug_layer(self):
        self.show('dtext', 'Display debug layer')

    def set_debug_layer(self, message):
        self.set_message(message)
        self.show_debug_layer()

    def hide_debug_layer(self):
        self.show('dtexthide', 'Display hide debug layer')

    def show_addition_layer(self):
        self.show('utext', 'Display show addition layer')

    def set_addition_layer(self, message):
        self.set_message(message)
        self.show('text', 'Display set and show addition layer')

    def hide_addition_layer(self):
        self.show('utexthide', 'Display hide addition layer')

    def show_debug_mode(self):
        self.show('debug', 'Display debug mode')

    def reload_config(self):
        self.show('reload', 'Display reload config')

    def close_app(self):
        self.show('reload', 'Display clode app')
# okay decompiling /home/a/Desktop/app/Display.pyc
