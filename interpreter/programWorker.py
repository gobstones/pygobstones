class ProgramWorker(object):
    class RunMode:
        FULL = 'full'
        ONLY_CHECK = 'only_check'
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
        filename, program_text, initial_board_string, run_mode = message.body
        self.start(filename, program_text, initial_board_string, run_mode)
      