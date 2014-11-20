from views.viewEditor import *
from views.boardPrint.board import *
from views.boardPrint.boardEditor import *
import views.resources
import boardOption
from helpOption import *
from commons.i18n import *
from commons.utils import root_path

class Editor(QtGui.QWidget):

    def __init__(self, parent, generator):
        super(Editor, self).__init__()
        self.parent = parent
        self.ui = Ui_editor()
        self.ui.setupUi(self)
        icon = QtGui.QIcon(':/logoGobstones.png')
        self.setWindowIcon(icon)
        self.initcomboBoxLoad()
        self.init_combo_box_persist()
        self.init_combo_box_options()
        self.boardOption = boardOption.BoardOption(self)
        self.boardGenerator = generator
        self.getInitialBoardFromMainWindow()
        self.dictionary_load = {"Load Initial Board":'self.getInitialBoardFromMainWindow()',
                            "Load from disk":'self.loadBoardFromDisk()',
                            'Load from ...': 'self.nothing()'}
        self.dictionary_persist = {'Persist board': 'self.nothing()',
                                    'Set as initial board': 'self.setInitialBoardToMainWindow()',
                                    'Save board to disk': 'self.saveBoardFromDisk()',
                                    'Save board to image': 'self.saveBoardToImage()'}
        self.dictionary_options = {'Options': 'self.nothing()',
                                   'Options Board': 'self.openBoardOptionWindow()',
                                   'User Options': 'self.openUserOptionsWindow()'}

    def init_combo_box_options(self):
        self.connect(self.ui.combo_box_options, QtCore.SIGNAL('activated(QString)'), self.combo_box_options_chosen)
        self.ui.combo_box_options.addItem(i18n('Options'))
        self.ui.combo_box_options.addItem(i18n('Options Board'))
        self.ui.combo_box_options.addItem(i18n('User Options'))

    def initcomboBoxLoad(self):
        self.connect(self.ui.comboBoxLoad, QtCore.SIGNAL('activated(QString)'), self.comboBoxLoad_chosen)
        self.ui.comboBoxLoad.addItem(i18n('Load from ...'))
        self.ui.comboBoxLoad.addItem(i18n("Load Initial Board"))
        self.ui.comboBoxLoad.addItem(i18n("Load from disk"))

    def init_combo_box_persist(self):
        self.connect(self.ui.combo_box_persist, QtCore.SIGNAL('activated(QString)'), self.combo_box_persist_chosen)
        self.ui.combo_box_persist.addItem(i18n('Persist board'))
        self.ui.combo_box_persist.addItem(i18n('Set as initial board'))
        self.ui.combo_box_persist.addItem(i18n('Save board to disk'))
        self.ui.combo_box_persist.addItem(i18n('Save board to image'))

    def combo_box_persist_chosen(self, string):
        exec(self.dictionary_persist[getEnglishTraduction(string)])

    def comboBoxLoad_chosen(self, string):
        exec(self.dictionary_load[getEnglishTraduction(string)])

    def combo_box_options_chosen(self, string):
        exec(self.dictionary_options[getEnglishTraduction(string)])

    def nothing(self):
        pass

    def setInitialBoard(self, board):
        self.board = board
        self.boardGenerator.setInitialBoard(board)
        self.ui.boardEditor.setBoard(self.board)
        self.ui.boardEditor.populate()

    def setInitialBoardToMainWindow(self):
        self.board = boardToString(self.ui.boardEditor.getEditedBoard())
        self.parent.setInitialBoard(self.board)
        self.parent.setAtNothingBoardOptions()
        self.reset_combo_persist()
        self.reset_combo_options()

    def getInitialBoardFromMainWindow(self):
        board = self.boardGenerator.getStringBoard()
        self.setInitialBoard(board)
        self.reset_combo_load()

    def openUserOptionsWindow(self):
        self.command = CommandHelpWidget()
        self.command.show()
        self.reset_combo_options()

    def openBoardOptionWindow(self):
        self.boardOption.openBoardOptionWindow(self.parent.initialBoardGenerator)
        self.reset_combo_options()

    def update(self):
        board = self.boardGenerator.getInitialBoard()
        self.setInitialBoard(board)
        self.ui.boardEditor.populate()
        self.ui.boardEditor.update()

    def loadBoardFromDisk(self):
        self.boardOption.loadBoard()
        self.reset_combo_load()

    def saveBoardFromDisk(self):
        self.board = boardToString(self.ui.boardEditor.getEditedBoard())
        filename = QtGui.QFileDialog.getSaveFileName(self,
        i18n('Save as ...'), root_path(), '*.gbb')
        if not filename == QtCore.QString(''):
            (filep, filen) = os.path.split(str(filename))
            myFile = open(filename, 'w')
            myFile.write(self.board)
            myFile.close()
        self.reset_combo_persist()
        
    def saveBoardToImage(self):
        filename = QtGui.QFileDialog.getSaveFileName(self,
                                                     i18n('Save as ...'), 
                                                     root_path(), 
                                                     '*.png')
        if not filename == QtCore.QString(''):
            self.ui.boardEditor.save_to_image(filename)
        self.reset_combo_persist()

    def reset_combo_load(self):
        self.ui.comboBoxLoad.setCurrentIndex(0)

    def reset_combo_persist(self):
        self.ui.combo_box_persist.setCurrentIndex(0)

    def reset_combo_options(self):
        self.ui.combo_box_options.setCurrentIndex(0)

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.Antialiasing
        painter.begin(self)
        rect = QtCore.QRect(0, 0, 1920, 1080)
        img = QtGui.QImage(':/backgroundWidget.png')
        painter.drawImage(rect, img)
        painter.end()