from views.viewResults import *
from PyQt4 import QtGui
from PyQt4 import QtCore
from views.boardPrint.board import *
from views.boardPrint.boardViewer import *
from views.boardPrint.parseBoard import *
from commons.i18n import *
from commons.utils import clothing_for_file_exists, clothing_dir_for_file
import views.resources


class Results(QtGui.QWidget):

    def __init__(self, main_window):
        super(Results, self).__init__()
        self.main_window = main_window
        self.retVars = None  
        self.ui = Ui_results()
        self.ui.setupUi(self)
        self.nextView = None
        self.ui.pushButtonSwitchViews.clicked.connect(self.switchViews)
        self.ui.pushButtonSaveResults.clicked.connect(self.saveBoard)
        self.ui.combo.activated[str].connect(self.onActivated)
        self.loadViewAlternatives()
        icon = QtGui.QIcon(':/logoGobstones.png')
        self.setWindowIcon(icon)
        self.setStyleSheet( "Results{background-image:url(':/backgroundWidget.png');}")
        self.initializeRetVarsTabLogic()

    def initializeRetVarsTabLogic(self):
        self.ui.retVarsTable.cellClicked.connect(self.onRetVarsTableRowClick)

    def onRetVarsTableRowClick(self, cell):
        retVarsTable = self.ui.retVarsTable
        retVarsInspector = self.ui.retVarsInspector
        item = retVarsTable.currentItem()
        if not item is None:
            retVarStr = self.formatRetVarRepr(retVarsTable.item(item.row(),1).text())
            retVarsInspector.setPlainText(retVarStr)

    def formatRetVarRepr(self, text):
        return text

    def setRetVars(self, retVars):
        self.retVars = retVars
        self.ui.showRetVars(self.retVars)

    def setInitialBoard(self, boardV):
        boardV.setParent(self.ui.tabWidgetResults)
        self.ui.tabWidgetResults.insertTab(0,boardV,i18n('Initial Board'))
        self.setCurrentClothing(boardV.getClothing())

    def setCurrentClothing(self, clothingPath):
        self.current_clothing = clothingPath
        if clothingPath == "Gobstones.xml":
            self.ui.combo.setCurrentIndex(self.filesNames.index('Gobstones'))
        elif clothingPath == "PixelBoard.xml":
            self.ui.combo.setCurrentIndex(self.filesNames.index('PixelBoard'))
        else:
            fileName, fileExtension = os.path.splitext(clothingPath)
            self.ui.combo.setCurrentIndex(self.filesNames.index(fileName))
        self.init_switcher()

    def setFinalBoard(self, boardV):
        boardV.setParent(self.ui.tabWidgetResults)
        self.ui.tabWidgetResults.insertTab(2,boardV,i18n('Final Board'))
        if not boardV.is_board_error():
            self.finalBoard = boardV.getBoard()
        else:
            self.ui.pushButtonSaveResults.setVisible(False)

    def setSourceCode(self, fileCode, libraryCode):
        self.ui.tabFileCode.setDocument(fileCode)
        self.ui.tabFileCode.setReadOnly(True)
        self.ui.tabLibraryCode.setDocument(libraryCode)
        self.ui.tabLibraryCode.setReadOnly(True)

    def saveBoard(self):
        filename = QtGui.QFileDialog.getSaveFileName(self,
        i18n('Save as ...'), os.getcwd(), '*.gbb')
        if not filename == QtCore.QString(''):
            filename = filename + '.gbb'
            (filep, filen) = os.path.split(str(filename))
            myFile = open(filename, 'w')
            myFile.write(boardToString(self.finalBoard))
            myFile.close()
        else:
            pass

    def switchViews(self):
        # [TODO] Abstract the method with the swithcViews in Interactive
        self.switcher.switch()
        self.ui.pushButtonSwitchViews.setText(self.switcher.get_text())
        self.current_clothing = self.ui.tabWidgetResults.widget(0).getClothing()
        if self.current_clothing != "Gobstones.xml":
            self.ui.tabWidgetResults.widget(0).setClothing("Gobstones.xml")
            self.ui.tabWidgetResults.widget(0).update()
            if not self.ui.tabWidgetResults.widget(2).is_board_error():
                self.ui.tabWidgetResults.widget(2).setClothing("Gobstones.xml")
                self.ui.tabWidgetResults.widget(2).update()
            self.nextView = self.current_clothing
            self.current_clothing = 'Gobstones.xml'
        else:
            if self.nextView is not None:
                self.ui.tabWidgetResults.widget(0).setClothing(self.nextView)
                self.ui.tabWidgetResults.widget(0).update()
                if not self.ui.tabWidgetResults.widget(2).is_board_error():
                    self.ui.tabWidgetResults.widget(2).setClothing(self.nextView)
                    self.ui.tabWidgetResults.widget(2).update()
                self.current_clothing = self.nextView
                self.nextView = "Gobstones.xml"
            else:
                return

    def loadViewAlternatives(self):
        self.filesNames = ['Gobstones', 'PixelBoard']
        program_file = str(self.main_window.fileOption.moduleFile)
        if clothing_for_file_exists(program_file):
            path = clothing_dir_for_file(program_file)
            files = os.listdir(path)
            for f in files:
                fileName, fileExtension = os.path.splitext(os.path.join(path,f))
                if fileExtension == '.xml':
                    self.filesNames.append(os.path.join(path, fileName))
        for fn in self.filesNames:
            (filepath, filename) = os.path.split(fn)
            self.ui.combo.addItem(filename)

    def init_switcher(self):
        b = self.ui.pushButtonSwitchViews
        if len(self.filesNames) == 1:
            self.switcher = Switcher(i18n('Without clothing'), i18n('Without clothing'), b)
        elif self.current_clothing == "Gobstones.xml":
            self.switcher = Switcher(i18n('Enable clothing'), i18n('Disable clothing'), b)
            self.nextView = self.filesNames[1] + '.xml'
        else:
            self.switcher = Switcher(i18n('Disable clothing'), i18n('Enable clothing'), b)
            self.nextView = self.filesNames[1] + '.xml'

    def onActivated(self, text):
        # [TODO] Abstract the method with the onActivated in Interactive
        if not text == 'Gobstones':
            program_file = str(self.main_window.fileOption.moduleFile)
            if clothing_for_file_exists(program_file):
                fn = str(text) + ".xml"
                path = os.path.join(clothing_dir_for_file(program_file), fn)
                self.ui.tabWidgetResults.widget(0).setClothing(path)
                self.ui.tabWidgetResults.widget(0).update()
                if not self.ui.tabWidgetResults.widget(2).is_board_error():
                    self.ui.tabWidgetResults.widget(2).setClothing(path)
                    self.ui.tabWidgetResults.widget(2).update()
                self.current_clothing = path
                self.nextView = 'Gobstones.xml'
        elif self.current_clothing != 'Gobstones.xml':
                self.switchViews()
        self.switcher.change_state(text)

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.Antialiasing
        painter.begin(self)
        rect = QtCore.QRect(0, 0, 1920, 1080)
        img = QtGui.QImage(':/backgroundWidget.png')
        painter.drawImage(rect, img)
        painter.end()


class Switcher:

    def __init__(self, text1, text2, button):
        self.text1 = text1
        self.text2 = text2
        self.button = button
        self.set_current_text(text1)

    def switch(self):
        if self.current_text == self.text1:
            self.set_current_text(self.text2)
        else:
            self.set_current_text(self.text1)

    def get_text(self):
        return self.current_text

    def change_state(self, text):
        if not self.current_text == i18n('Without clothing'):
            if text == "Gobstones":
                self.set_current_text(i18n('Enable clothing'))
            else:
                self.set_current_text(i18n('Disable clothing'))

    def set_current_text(self, text):
        self.current_text = text
        self.button.setText(text)