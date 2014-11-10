# coding:utf-8
#
# Copyright (C) 2011-2013 Pablo Barenbaum <foones@gmail.com>,
#                         Ary Pablo Batista <arypbatista@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import lang
import logging
import common.messaging
import lang.bnf_parser
from common.utils import SourceException
import common.i18n as i18n
from common.tools import tools

class GobstonesRunHandler(object):
    def __init__(self, success, failure, log, partial, read_input):
        self.success = success
        self.failure = failure
        self.log = log
        self.partial = partial
        self.read_input = read_input

class GobstonesRun(object):
    def __init__(self, handler):
        self.handler = handler
        self.running = False
        self.comm = common.messaging.MessageCommunicator()        
        self.worker = InterpreterWorker(self.comm.opposite())
        # worker's queue_in is app's queue_out and vice-versa:
        self.process = common.threads.Process(target=self.worker.run)
        self.process.start()
    def start(self, filename, current_text, board_repr):
        self.running = True
        self.comm.send('START', (filename,
            current_text,
            board_repr))
    def continue_run(self):
        while True:
            message = self.comm.receive_nowait()
            if message.header == 'OK':
                self.handler.success(message.body[0], message.body[1])                
            elif message.header == 'FAIL':
                reduced = message.body
                self.handler.failure(reduced[0](*reduced[1]))
            elif message.header == 'READ_REQUEST':
                reading = self.handler.read_input()
                self.comm.send('READ_DONE', reading)
            elif message.header == 'LOG':
                self.handler.log(message.body)
            elif message.header == 'PARTIAL':
                self.handler.partial(message.body)
            else:
                print(message)
                assert False
    def end(self):
        if self.running:
            common.threads.terminate_process(self.process)
        self.comm.send('EXIT')
    def abort(self):
        area = lang.bnf_parser.fake_bof()
        if self.running:
            common.threads.terminate_process(self.process)
        self.handler.failure(SourceException(i18n.i18n('Execution interrupted by the user'), area))

class GUIGobstonesApi(lang.GobstonesApi):
    def __init__(self, communicator):
        self.comm = communicator
    def read(self):
        self.comm.send('READ_REQUEST')
        message = self.comm.receive()
        if message.header != 'READ_DONE': assert False
        return message.body        
    def show(self, board):
        self.comm.send('PARTIAL', tools.board_format.to_string(board))
    def log(self, msg):
        self.comm.send('LOG', msg)

class InterpreterWorker(object):
    def __init__(self, communicator):
        self.communicator = communicator
    def run(self):
        api = GUIGobstonesApi(self.communicator)
        options = lang.GobstonesOptions()
        lang.setGrammar(options.lang_version)
        gobstones = lang.Gobstones(options, api)
        
        message = self.communicator.receive()
        assert message.header in ['START', 'EXIT']
        if message.header == 'EXIT': return
        filename, current_text, board_repr = message.body        
        try:
            self.success(gobstones.run(filename, current_text, tools.board_format.from_string(board_repr)))
        except SourceException as exception:
            self.failure(exception)
    def success(self, gbs_run):
        self.communicator.send('OK', (tools.board_format.to_string(gbs_run.final_board), gbs_run.result))
    def failure(self, exception):
        # Note: we cannot send an exception directly through a queue.Queue / multiprocessing.Queue
        # (it has to do with the requirement of the object being serializable)
        self.communicator.send('FAIL', (exception.__class__, (exception.msg, exception.area)))   