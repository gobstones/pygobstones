# -*- coding: utf-8 -*-

from views.gobstonesMain import *
from PyQt4 import QtGui
from PyQt4 import QtCore
import datetime
from views.qDesigner.interactive import *
sys.path.append('..')
from .fileOption import FileOption
from .preferencesWindow import PreferencesWindow
from .editOption import EditOption
from .boardOption import *
from .helpOption import HelpOption
from language.programRun import *
from views.boardPrint.board import *
from views.boardPrint.boardViewer import *
from resultsMainWindow import *
from commons.i18n import *
from commons.paths import root_path
from views.boardPrint.parseBoard import *
import time
import views.resources

GOBSTONES = 'Gobstones 3.0.0'
XGOBSTONES = 'XGobstones 1.0.0'

class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.initOptions()
        self.initMenuBarActions()
        self.initSignalsAndSlots()
        self.ui.actionStop.setEnabled(False)
        self.clothing = 'Gobstones.xml'
        self.lang = GOBSTONES
        self.initWindowTitle()
        self.initPreferencesDictionary()
        self.initLoggerSize()
        self.initialBoardGenerator = InitialBoardGenerator()
        self.guiInterpreterHandler = GUIInterpreterHandler(self)
        self.programRun = ProgramRun(self.getLang(),
                                    self.guiInterpreterHandler)
        self.rootDirectory = root_path()
        self.runButton = RunButton(self, self.ui.actionRun,
             self.ui.actionStop)
        self.setStyleSheet( "QMainWindow{background-image:url(':/backgroundWidget.png')}")

    def initWindowTitle(self):
        self.filePath = i18n('Without working directory')
        self.updateWindowTitle()

    def initMenuBarActions(self):
        self.ui.actionNewFile.triggered.connect(self.openNewFileDialog)
        self.ui.actionCloseFile.triggered.connect(self.closeFiles)
        self.ui.actionOpenFile.triggered.connect(self.openFileDialog)
        self.ui.actionSaveAs.triggered.connect(self.saveAsFileDialog)
        self.ui.actionSave.triggered.connect(self.saveFile)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionRun.triggered.connect(self.run)
        self.ui.actionStop.triggered.connect(self.stop)
        self.ui.actionBoardOptions.triggered.connect(self.openBoardOptions)
        self.ui.actionLoadBoard.triggered.connect(self.loadBoard)
        self.ui.actionChangeLang.triggered.connect(self.changeLang)
        self.ui.actionFind.triggered.connect(self.search)
        self.ui.actionReplace.triggered.connect(self.replace)
        self.ui.actionFonts.triggered.connect(self.fonts)
        self.ui.actionPreferences.triggered.connect(self.openPreferences)
        self.ui.actionOpenBoardEditor.triggered.connect(self.openBoardEditor)
        self.ui.actionUndo.triggered.connect(self.undo)
        self.ui.actionRedo.triggered.connect(self.redo)
        self.ui.actionCut.triggered.connect(self.cut)
        self.ui.actionCopy.triggered.connect(self.copy)
        self.ui.actionPaste.triggered.connect(self.paste)
        self.ui.actionSelectAll.triggered.connect(self.selectAll)
        self.ui.actionManual.triggered.connect(self.openManual)
        self.ui.actionLicense.triggered.connect(self.viewLicense)
        self.ui.actionAbout.triggered.connect(self.viewAbout)
        self.ui.actionCheck.triggered.connect(self.check)

    def initPreferencesDictionary(self):
        global preferencesDictionary
        preferencesDictionary = {'logger': False,
                                 'roseOfWinds': True,
                                 'cellNumbers': True,
                                 'lineNumbers': True,
                                 'autoIndentation': False,
                                }

    def initLoggerSize(self):
        if MainWindow.getPreference('logger'):
            self.ui.splitter.setSizes([800, 80])
        else:
            self.ui.splitter.setSizes([800, 0])

    @staticmethod
    def getPreference(keyPreference):
        return preferencesDictionary[keyPreference]

    def setPreference(self, keyPreference, valuePreference):
        preferencesDictionary[keyPreference] = valuePreference

    def getInitialBoard(self):
        return self.initialBoardGenerator.getInitialBoard()

    def setInitialBoard(self, board):
        self.initialBoardGenerator.setInitialBoard(board)

    def setAtNothingBoardOptions(self):
        self.initialBoardGenerator.set_nothing_options()

    def openBoardOptions(self):
        self.boardOption.openBoardOptionWindow(self.initialBoardGenerator)

    def openBoardEditor(self):
        self.boardOption.openBoardEditor(self.initialBoardGenerator)

    def undo(self):
        self.editOption.undo()

    def redo(self):
        self.editOption.redo()

    def cut(self):
        self.editOption.cut()

    def copy(self):
        self.editOption.copy()

    def paste(self):
        self.editOption.paste()

    def selectAll(self):
        self.editOption.selectAll()

    def search(self):
        self.editOption.openSearch()

    def replace(self):
        self.editOption.openReplace()

    def fonts(self):
        self.editOption.openFontDialog()

    def openPreferences(self):
        PreferencesWindow(self)

    def openManual(self):
        self.helpOption.openManual()

    def viewLicense(self):
        self.helpOption.viewLicense()

    def viewAbout(self):
        self.helpOption.viewAbout()

    def setClothing(self, clothing):
        self.clothing = clothing

    def getClothing(self):
        return self.clothing

    def initSignalsAndSlots(self):
        self.ui.textEditFile.document().modificationChanged.connect(self.updateTextEditFileUI)
        self.ui.textEditLibrary.document().modificationChanged.connect(self.updateTextEditLibraryUI)

    def closeFiles(self):
        self.fileOption.closeFiles()

    def openFileDialog(self):
        '''
        Purpose: Open a dialog for open a file. Then open the file that
        was selected and load it in the first text editor. Additionally
        load library.
        '''
        if self.fileOption.openFiles():
            self.fileOpened()

    def openNewFileDialog(self):
        self.fileOption.newFile()
        self.fileOpened()

    def closeEvent(self, event):
        self.fileOption.closeApp(event)

    def loadBoard(self):
        self.boardOption.loadBoard()

    def saveFile(self):
        if self.fileOption.saveFile():
            self.fileSaved()

    def saveAsFileDialog(self):
        if self.fileOption.saveAsFileDialog():
            self.fileSaved()

    def fileSaved(self):
        self.updateCompleters()
        
    def fileOpened(self):
        self.updateCompleters()
        
    def updateCompleters(self):
        filename, text = str(self.fileOption.getFileName()), str(self.ui.textEditFile.toPlainText().toUtf8())
        self.ui.textEditFile.updateCompleter(filename, text)
        self.ui.textEditLibrary.setCompleter(self.ui.textEditFile.getCompleter())

    def initOptions(self):
        self.fileOption = FileOption(self)
        self.editOption = EditOption(self)
        self.editOption.initEditorBehavior()
        self.boardOption = BoardOption(self)
        self.helpOption = HelpOption(self)

    def updateTextEditFileUI(self):
        self.editOption.updateEditUI(self.ui.textEditFile, 0)

    def updateTextEditLibraryUI(self):
        self.editOption.updateEditUI(self.ui.textEditLibrary, 1)

    def run(self):
        self.ui.logger.clear()
        if MainWindow.getPreference('logger') == False:
            self.setPreference('logger', True)
            self.initLoggerSize()
        self.guiInterpreterHandler.wasStoped = False
        self.guiInterpreterHandler.showInLog(i18n(
                                'Start execution || Languaje: ') + self.lang)
        self.guiInterpreterHandler.log('----------------' +
               str(datetime.datetime.now())[:19] +
              '-----------------')
        self.ui.logger.show()
        self.ui.actionStop.setEnabled(True)
        self.ui.actionCheck.setEnabled(False)
        self.ui.statusbar.showMessage(QtCore.QString(i18n('Processing...')))
        self.programRun.handler = self.guiInterpreterHandler
        self.runButton.start(self.programRun)

    def stop(self):
        self.guiInterpreterHandler.initialStatus()
        self.runButton.stopInterpreter()
        self.resetButtonsRunAndStop()
        self.ui.statusbar.showMessage(QtCore.QString
            (i18n('Execution interrupted by the user')))
        self.guiInterpreterHandler.showInLog(i18n(
                                'Execution interrupted by the user'))
        self.guiInterpreterHandler.log('----------------' +
               str(datetime.datetime.now())[:19] +
              '-----------------')

    def resetButtonsRunAndStop(self):
        self.ui.actionStop.setEnabled(False)
        self.ui.actionRun.setEnabled(True)
        self.ui.actionCheck.setEnabled(True)

    def updateFilePath(self, path):
        self.filePath = path
        self.updateWindowTitle()

    def updateWindowTitle(self):
        self.setWindowTitle(self.lang + ' -- ' + self.filePath)

    def check(self):
        self.ui.actionStop.setEnabled(True)
        self.ui.actionCheck.setEnabled(False)
        self.ui.actionRun.setEnabled(False)
        self.guiInterpreterHandler.showInLog(i18n(
                        'Start check || Languaje: ') + self.lang)
        self.guiInterpreterHandler.log('----------------' +
               str(datetime.datetime.now())[:19] +
              '-----------------')
        self.ui.statusbar.showMessage(QtCore.QString(i18n('Checking...')))
        self.checkButton = CheckButton(self)
        self.checkButton.start()

    def changeLang(self):
        if self.lang == GOBSTONES:
            self.lang = XGOBSTONES
            self.ui.actionChangeLang.setText("XGobstones")
            icon = QtGui.QIcon(":/logoXGobstones.png")
            self.ui.actionChangeLang.setIcon(icon)
            self.ui.set_highlighter(XGobstonesHighlighter)
        else:
            self.lang = GOBSTONES
            self.ui.actionChangeLang.setText("Gobstones")
            icon = QtGui.QIcon(":/logoGobstones.png")
            self.ui.actionChangeLang.setIcon(icon)
            self.ui.set_highlighter(GobstonesHighlighter)
        self.guiInterpreterHandler.showInLog(i18n
                            ("The languaje was changed to ") + self.lang)
        self.updateWindowTitle()
        self.programRun = ProgramRun(self.getLang(),
            self.guiInterpreterHandler)

    def getLang(self):
        if self.lang == GOBSTONES:
            return 'gobstones'
        else:
            return 'xgobstones'

# RUN BUTTON .....................

class GUIInterpreterHandler(EjecutionFailureHandler, EjecutionHandler):

    def __init__(self, mainW):
        self.mainW = mainW
        self.wasStoped = False
        self.isOpenInteractiveW = False
        self.interactiveW = InteractiveWindow(self.mainW)
        self.interactiveRunning = False
        self.failure_dict = {
            EjecutionFailureHandler.DEFAULT: self.interpreter_log_default_exception,
            EjecutionFailureHandler.PARSER_FAILURE: self.interpreter_log_failure,
            EjecutionFailureHandler.STATIC_FAILURE: self.interpreter_log_failure,
            EjecutionFailureHandler.DYNAMIC_FAILURE: self.interpreter_boom_failure,
        }
        super(GUIInterpreterHandler, self).__init__(self.failure_dict)


    def initialStatus(self):
        self.wasStoped = False
        self.isOpenInteractiveW = False
        self.interactiveW = InteractiveWindow(self.mainW)
        self.interactiveRunning = False


    def success(self, board_string, result):
        if not self.interactiveRunning:
            if not self.wasStoped:
                self.mainW.ui.statusbar.showMessage(QtCore.QString
                (i18n('Execution completed')))
                self.results = Results(self.mainW)
                board = self.prepareString(board_string)
                self.results.setInitialBoard(BoardViewer(self,
                self.mainW.initialBoardGenerator.board, self.mainW.getClothing()))
                self.results.setFinalBoard(BoardViewer(self,
                parseABoardString(board), self.mainW.getClothing()))
                self.results.setRetVars(result)
                self.setCodeInResults()
                self.results.ui.tabWidgetResults.setCurrentIndex(2)
                self.results.show()
                self.mainW.resetButtonsRunAndStop()
                self.showInLog(i18n('Execution completed'))
                self.log('----------------'+
                str(datetime.datetime.now())[:19] +
                '-----------------\n')
        else:
            self.mainW.ui.statusbar.showMessage(QtCore.QString
                (i18n('Execution completed')))
            self.showInLog(i18n('Execution completed'))
            self.log('----------------'+
                str(datetime.datetime.now())[:19] +
                '-----------------\n')
            self.interactiveW.setStatusMessage('    ' + i18n('Execution completed'))
            self.mainW.resetButtonsRunAndStop()
            self.wasStoped = False
            self.isOpenInteractiveW = False
            self.interactiveRunning = False

    def read_request(self):
        self.interactiveRunning = True
        if (not self.isOpenInteractiveW):
            self.isOpenInteractiveW = True
            self.partialBoard = self.mainW.initialBoardGenerator.getStringBoard()
            self.interactiveW.initialStatus(self.partialBoard)
            self.interactiveW.show()


    def partial(self, board_str):
        self.interactiveW.setPressAKeyState()
        self.interactiveW.setBoard(board_str)
        self.interactiveRunning = False

    def log(self, msg):
        if not self.wasStoped:
            loggermsg = self.mainW.ui.logger.document().toPlainText()
            self.mainW.ui.logger.setText(loggermsg + '\n -> ' + msg.decode('utf8'))
            self.mainW.ui.logger.moveCursor(QtGui.QTextCursor.End)

    def showInLog(self, msgDecode):
        # This method not required that the state is not stopped
            loggermsg = self.mainW.ui.logger.document().toPlainText()
            self.mainW.ui.logger.setText(loggermsg + '\n -> ' + msgDecode)
            self.mainW.ui.logger.moveCursor(QtGui.QTextCursor.End)

    def prepareString(self, board):
        myPrettyBoard = ''
        for s in board:
            if not (ord(s) is 13 or ord(s) is 10):
                myPrettyBoard += s
            if ord(s) is 10:
                myPrettyBoard += '\n'
        return myPrettyBoard

    def interpreter_log_default_exception(self, exception):
        if not self.wasStoped:
            self.mainW.ui.statusbar.showMessage(QtCore.QString
                (i18n('Was occurred an error')))
            self.showInLog(i18n('Was occurred an error'))            
            self.log(exception.msg)
            self.mainW.resetButtonsRunAndStop()

    def interpreter_log_failure(self, exception):
        if not self.wasStoped:
            self.mainW.ui.statusbar.showMessage(QtCore.QString
                (i18n('Was occurred an error')))
            self.showInLog(i18n('Was occurred an error'))
            self.showRowAndColError(exception)
            self.log(exception.msg)
            self.mainW.resetButtonsRunAndStop()

    def showRowAndColError(self, exception):
        self.showInLog(i18n('In row: ') +
        str(exception.area.interval()[0].row) + ' // ' +
        i18n('column: ') + str(exception.area.interval()[0].col))

    def interpreter_boom_failure(self, exception):
        if not self.wasStoped:
            self.mainW.ui.statusbar.showMessage(QtCore.QString('Boom !!!'))
            self.showInLog('Boom !!!')
            self.log(exception.msg)
            self.log('----------------'+
            str(datetime.datetime.now())[:19] +
                '-----------------\n')
            if not self.interactiveRunning:
                self.results = Results(self.mainW)
                self.results.setInitialBoard(BoardViewer(self,
                self.mainW.initialBoardGenerator.board, self.mainW.getClothing()))
                self.results.setFinalBoard(BoardViewerError())
                self.results.setRetVars(None)                
                self.results.ui.tabWidgetResults.setCurrentIndex(2)
                self.setCodeInResults()
                self.results.show()
            else:
                self.interactiveW.boom()
        self.mainW.resetButtonsRunAndStop()
        self.wasStoped = False
        self.isOpenInteractiveW = False
        self.interactiveRunning = False

    def setCodeInResults(self):
        fileCode = QtGui.QTextDocument(
            i18n('### FILE CODE ###\n\n') + self.mainW.ui.textEditFile.document().toPlainText())
        libraryCode =  QtGui.QTextDocument(
            i18n('### LIBRARY CODE ###\n\n') + self.mainW.ui.textEditLibrary.document().toPlainText())
        self.results.setSourceCode(fileCode, libraryCode)

class RunButton(QtGui.QWidget):

    def __init__(self, mainW, actionRun, actionStop):
        super(RunButton, self).__init__()
        self.mainW = mainW
        self.actionRun = actionRun
        self.actionStop = actionStop

    def start(self, interpreter):
        self.actionRun.setEnabled(False)
        interpreter.run(str(self.mainW.fileOption.getFileName()),
             str(self.mainW.ui.textEditFile.toPlainText().toUtf8()),
            self.mainW.getInitialBoard())

    def stopInterpreter(self):
        self.mainW.guiInterpreterHandler.wasStoped = True



# CHECK BUTTON .....................

class CheckButton(QtGui.QWidget):

    def __init__(self, mainW):
        super(CheckButton, self).__init__()
        self.mainW = mainW

    def start(self):
        self.gui = GUIInterpreterHandler_CheckMode(self.mainW)
        self.mainW.programRun.handler = self.gui
        self.mainW.programRun.run(str(self.mainW.fileOption.getFileName()),
                             str(self.mainW.ui.textEditFile.toPlainText().toUtf8()),
                             self.mainW.initialBoardGenerator.getStringBoard(),
                             ProgramRun.RunMode.ONLY_CHECK)


class GUIInterpreterHandler_CheckMode(GUIInterpreterHandler):

    def success(self, board_string, result):
        self.mainW.ui.statusbar.showMessage(QtCore.QString(i18n('Check completed')))
        self.showInLog(i18n('Check completed, program is OK'))
        self.log('----------------' +
                 str(datetime.datetime.now())[:19] +
                 '-----------------\n')
        self.mainW.resetButtonsRunAndStop()

    def initialize_failure_handler(self):
        def fail_handler(exception):
            self.mainW.ui.statusbar.showMessage(QtCore.QString(i18n('Check failed')))
            self.showInLog(i18n('Check failed:'))
            self.showRowAndColError(exception)
            self.log(exception.msg)
            self.log('----------------' +
                     str(datetime.datetime.now())[:19] +
                     '-----------------\n')
        self.failure = EjecutionFailureHandler(fail_handler).failure


class InteractiveWindow(QtGui.QDialog):
    def __init__(self, mainW):
        super(InteractiveWindow, self).__init__()
        self.setWindowTitle(i18n('Interactive Mode'))
        self.setGeometry(200, 200, 600, 600)
        self.ui = Ui_Interactive()
        self.ui.setupUi(self)
        self.ui.combo.activated[str].connect(self.onActivated)
        self.mainW = mainW
        self.current_clothing = 'Gobstones.xml'
        self.pressAKey = True
        self.setModal(True)
        self.ui.pushButton.clicked.connect(self.switch_view)
        self.currentImage = ':/ballGreen.png'
        self.setStyleSheet( "InteractiveWindow{background-image:url(':/backgroundWidget.png');}")
        self.load_views = None

    def init_switcher(self):
        if len(self.filesNames) == 1:
            self.next_clothing = None
            self.switcher = Switcher(i18n('Without clothing'), i18n('Without clothing'), self.ui.pushButton)
        else:
            self.current_clothing = self.boardV.getClothing()
            if self.current_clothing == 'Gobstones.xml':
                self.next_clothing = self.filesNames[1]
                self.switcher = Switcher(i18n('Enable clothing'), i18n('Disable clothing'), self.ui.pushButton)
            else:
                self.next_clothing = 'Gobstones.xml'
                self.switcher = Switcher(i18n('Disable clothing'), i18n('Enable clothing'), self.ui.pushButton)

    def onActivated(self, text):        
        if not text == 'Gobstones':
            if clothing_for_file_exists(self.mainW.fileOption.moduleFile):
                fn = str(text) + ".xml"
                path = os.path.join(clothing_dir_for_file(self.mainW.fileOption.moduleFile), fn)
                self.next_clothing = self.current_clothing
                self.current_clothing = path
                self.boardV.setClothing(path)
                self.boardV.update()
        elif self.current_clothing != 'Gobstones.xml':
                self.switch_view()
        self.switcher.change_state(text)

    def loadViewAlternatives(self):
        self.filesNames = ['Gobstones', 'PixelBoard']
        if clothing_for_file_exists(self.mainW.fileOption.moduleFile):
            path = clothing_dir_for_file(self.mainW.fileOption.moduleFile)
            files = os.listdir(path)
            for f in files:
                fileName, fileExtension = os.path.splitext(os.path.join(path,f))
                if fileExtension == '.xml':
                    self.filesNames.append(os.path.join(path, fileName))
        for fn in self.filesNames:
            (filepath, filename) = os.path.split(fn)
            self.ui.combo.addItem(filename)


    def switch_view(self):
        self.switcher.switch()
        self.ui.pushButton.setText(self.switcher.get_text())
        if self.current_clothing != "Gobstones.xml":
            self.boardV.setClothing('Gobstones.xml')
            self.boardV.update()
            self.next_clothing = self.current_clothing
            self.current_clothing = 'Gobstones.xml'

        else:
            if self.next_clothing is not None:
                self.boardV.setClothing(self.add_extension(self.next_clothing))
                self.boardV.update()
                self.current_clothing = self.next_clothing
                self.next_clothing = 'Gobstones.xml'
            else:
                return

    def setPressAKeyState(self):
        self.pressAKey = True
        self.ui.label.setText( '    ' + i18n("Press a key to continue"))
        self.currentImage = ':/ballGreen.png'
        self.update()

    def setProcessingAKeyState(self):
        self.pressAKey = False
        self.ui.label.setText( '    ' + i18n("Processing a key, wait"))
        self.currentImage = ':/ballRed.png'
        self.update()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            super(InteractiveWindow, self).keyPressEvent(e)
            self.close()
        elif self.pressAKey:
            try:
                a = str(e.text())
                ordinalValue = ord(a)
            except:
                if e.key() == QtCore.Qt.Key_Left:
                    self.setProcessingAKeyState()
                    self.mainW.programRun.send_input(1004)
                elif e.key() == QtCore.Qt.Key_Up:
                    self.setProcessingAKeyState()
                    self.mainW.programRun.send_input(1001)
                elif e.key() == QtCore.Qt.Key_Right:
                    self.setProcessingAKeyState()
                    self.mainW.programRun.send_input(1003)
                elif e.key() == QtCore.Qt.Key_Down:
                    self.setProcessingAKeyState()
                    self.mainW.programRun.send_input(1002)
                return
            self.setProcessingAKeyState()
            self.mainW.programRun.send_input(ordinalValue)

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.Antialiasing
        painter.begin(self)
        rect = QtCore.QRect(self.width()-285, self.height() - 32 , 20, 20)
        img = QtGui.QImage(self.currentImage)
        painter.drawImage(rect, img)
        painter.end()

    def setBoard(self, board):
        self.boardV = BoardViewer(self, parseABoardString(board), self.add_extension(self.current_clothing))
        self.boardV.setParent(self.ui.boardViewer)
        self.ui.boardViewer.removeTab(0)
        self.ui.boardViewer.insertTab(0, self.boardV, i18n('Board'))

    def add_extension(self, path):
        if not path.endswith('xml'):
            return path + '.xml'
        else:
            return path

    def boom(self):
        self.setStatusMessage('    BOOM !!!')
        boom = BoardViewerError()
        self.ui.boardViewer.removeTab(0)
        self.ui.boardViewer.insertTab(0, boom, i18n('Interactive'))

    def setStatusMessage(self, message):
        self.pressAKey = False
        self.ui.label.setText(i18n(message))

    def reset_clothing(self):
        self.ui.combo.clear()

    def initialStatus(self, partialBoard):
        if (self.load_views is None) or (self.load_views != root_path()):
            self.reset_clothing()
            self.loadViewAlternatives()
            self.load_views = root_path()
        self.boardV = BoardViewer(self, parseABoardString(partialBoard), self.mainW.getClothing())
        self.boardV.setParent(self.ui.boardViewer)
        self.ui.boardViewer.removeTab(0)
        self.ui.boardViewer.insertTab(0, self.boardV, i18n('Board'))
        self.setPressAKeyState()
        self.init_switcher()

    def closeEvent(self, e):
        self.mainW.ui.actionStop.setEnabled(False)
        self.mainW.programRun.send_input(4)
        e.accept()
