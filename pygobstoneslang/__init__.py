#!/usr/bin/python
import pygobstoneslang.common.utils as utils
import pygobstoneslang.common.i18n as i18n
from pygobstoneslang.common.tools import tools
import pygobstoneslang.lang as lang
from pygobstoneslang.lang.gbs_api import GobstonesRun


class GUIExecutionAPI(lang.ExecutionAPI):

    def __init__(self, communicator):
        self.comm = communicator

    def read(self):
        self.comm.send('READ_REQUEST')
        message = self.comm.receive()
        if message.header != 'READ_DONE':
            assert False
        return message.body

    def show(self, board):
        self.comm.send('PARTIAL', tools.board_format.to_string(board))

    def log(self, msg):
        self.comm.send('LOG', msg)


class ProgramWorker(object):

    class RunMode:
        FULL = 'full'
        ONLY_CHECK = 'only_check'
        NAMES = 'names'

    def __init__(self, communicator):
        self.communicator = communicator

    def prepare(self):
        pass

    def start(self, filename, program_text, initial_board_string):
        pass

    def exit(self):
        pass

    def run(self):
        self.prepare()
        message = self.communicator.receive()
        assert message.header in ['START', 'EXIT']
        if message.header == 'EXIT':
            self.exit()
            return
        filename, program_text, initial_board_string, run_mode, gobstones_version = message.body
        self.start(
            filename,
            program_text,
            initial_board_string,
            run_mode,
            gobstones_version
            )


class GobstonesWorker(ProgramWorker):

    def prepare(self):
        self.api = GUIExecutionAPI(self.communicator)

    def start(self, filename, program_text, initial_board_string,
              run_mode, gobstones_version="xgobstones"):

        if run_mode == GobstonesWorker.RunMode.ONLY_CHECK:
            options = lang.GobstonesOptions(
                lang_version=gobstones_version,
                check_liveness=True,
                lint_mode="strict"
                )
        else:
            options = lang.GobstonesOptions(lang_version=gobstones_version)
        self.gobstones = lang.Gobstones(options, self.api)

        try:
            if run_mode == GobstonesWorker.RunMode.FULL:
                board = tools.board_format.from_string(initial_board_string)
                self.success(self.gobstones.run(filename, program_text, board))
            elif run_mode == GobstonesWorker.RunMode.ONLY_CHECK:
                # Parse gobstones script
                self.gobstones.api.log(i18n.i18n('Parsing.'))
                gbs_run = self.gobstones.parse(filename, program_text)
                assert gbs_run.tree
                # Check semantics, liveness and types
                self.gobstones.check(gbs_run.tree)
                self.success()
            elif run_mode == GobstonesWorker.RunMode.NAMES:
                self.success(self.gobstones.parse_names(filename, program_text))
            else:
                raise Exception(
                    "There is no action associated " +
                    "with the given run mode."
                    )
        except Exception as exception:
            self.failure(exception)

    def success(self, result=None):
        if result is None:
            self.communicator.send('OK', (None, None))
        elif isinstance(result, GobstonesRun):
            self.communicator.send('OK', (
                tools.board_format.to_string(result.final_board),
                result.result
                ))
        elif isinstance(result, dict):
            self.communicator.send('OK', (result,))
        else:
            assert False

    def failure(self, exception):
        if hasattr(exception, 'area'):
            self.communicator.send(
                'FAIL',
                (exception.__class__,
                (exception.msg, exception.area))
                )
        elif hasattr(exception, 'msg'):
            self.communicator.send(
                'FAIL',
                (exception.__class__, (exception.msg, ))
                )
        else:
            self.communicator.send(
                'FAIL',
                (utils.GobstonesException, (unicode(exception),))
                )
