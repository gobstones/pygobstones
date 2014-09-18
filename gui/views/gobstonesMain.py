# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gobstonesMain.ui'
#
# Created by: PyQt4 UI code generator 4.9.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
import sys
import resources
sys.path.append('..')
from commons.i18n import *
from gui.textEditor import *

 


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8('MainWindow'))
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8('centralwidget'))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(_fromUtf8('verticalLayout'))

        self.tabWidgetEditors = QtGui.QTabWidget(self.centralwidget)
        self.tabWidgetEditors.setObjectName(_fromUtf8('tabWidgetEditors'))
        self.tabWidgetEditors.setStyleSheet("border:2px solid #4682b4; border-color:'#4682b4';")
        self.tabWidgetEditors.tabBar().setStyleSheet("background-color:'white'; color:'#4682b4'; border:2px solid #4682b4; font-size:15px")
        self.tabWidgetEditors.tabBar().setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.tabFile = QtGui.QWidget()
        self.tabFile.setStyleSheet("border-color:white")
        self.tabFile.setObjectName(_fromUtf8('tabFile'))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.tabFile)
        self.verticalLayout_3.setObjectName(_fromUtf8('verticalLayout_3'))
        self.textEditFile = GobstonesTextEditor(self.tabFile)
        
        self.textEditFile.setObjectName(_fromUtf8('textEditFile'))
        self.textEditFile.setStyleSheet("selection-color: white; selection-background-color:#008080")
        self.verticalLayout_3.addWidget(self.textEditFile)
        self.tabWidgetEditors.addTab(self.tabFile, _fromUtf8(''))
        self.tabLibrary = QtGui.QWidget()
        self.tabLibrary.setStyleSheet("border-color:white")
        self.tabLibrary.setObjectName(_fromUtf8('tabLibrary'))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.tabLibrary)
        self.verticalLayout_2.setObjectName(_fromUtf8('verticalLayout_2'))
        self.textEditLibrary = GobstonesTextEditor(self.tabLibrary)
        self.textEditLibrary.setObjectName(_fromUtf8('textEditLibrary'))
        self.textEditLibrary.setStyleSheet("selection-color: white; selection-background-color:#008080")
        self.verticalLayout_2.addWidget(self.textEditLibrary)
        self.tabWidgetEditors.addTab(self.tabLibrary, _fromUtf8(''))
        
        self.set_highlighter(GobstonesHighlighter)
        

        self.logger = QtGui.QTextEdit()
        self.logger.setObjectName(_fromUtf8('logger'))
        self.logger.setReadOnly(True)
        self.logger.setStyleSheet("font-family: Monospace, Consolas, 'Courier New'; font-weight: 100; font-size: 10pt")
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(1)
        self.verticalLayout.addLayout(self.grid)
        self.splitter = QtGui.QSplitter(QtCore.Qt.Vertical, self.centralwidget)
        self.splitter.addWidget(self.tabWidgetEditors)
        self.splitter.addWidget(self.logger)
        self.verticalLayout.addWidget(self.splitter)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8('statusbar'))
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(MainWindow)
        self.toolBar.setObjectName(_fromUtf8('toolBar'))
        self.toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.menuBar = QtGui.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 703, 20))
        self.menuBar.setObjectName(_fromUtf8('menuBar'))
        self.menuFile = QtGui.QMenu(self.menuBar)
        self.menuFile.setObjectName(_fromUtf8('menuFile'))
        self.menuEdit = QtGui.QMenu(self.menuBar)
        self.menuEdit.setObjectName(_fromUtf8('menuEdit'))
        self.menuGobstones = QtGui.QMenu(self.menuBar)
        self.menuGobstones.setObjectName(_fromUtf8('menuGobstones'))
        self.menuBoard = QtGui.QMenu(self.menuBar)
        self.menuBoard.setObjectName(_fromUtf8('menuBoard'))
        self.menuSelectResultView = QtGui.QMenu(self.menuBoard)
        self.menuSelectResultView.setObjectName(_fromUtf8
                                                ('menuSelectResultView'))
        self.menuHelp = QtGui.QMenu(self.menuBar)
        self.menuHelp.setObjectName(_fromUtf8('menuHelp'))
        MainWindow.setMenuBar(self.menuBar)
        self.actionChangeLang = QtGui.QAction(MainWindow)
        icon = QtGui.QIcon(":/logoGobstones.png")
        self.actionChangeLang.setIcon(icon)
        self.actionChangeLang.setObjectName(_fromUtf8('actionChangeLang'))
        self.actionNewFile = QtGui.QAction(MainWindow)
        icon = QtGui.QIcon(":/new.png")
        self.actionNewFile.setIcon(icon)
        self.actionNewFile.setObjectName(_fromUtf8('actionNewFile'))
        self.actionCloseFile = QtGui.QAction(MainWindow)
        icon = QtGui.QIcon(":/close.png")
        self.actionCloseFile.setIcon(icon)
        self.actionCloseFile.setObjectName(_fromUtf8('actionCloseFile'))
        self.actionOpenFile = QtGui.QAction(MainWindow)
        icon1 = QtGui.QIcon(":/open.png")
        self.actionOpenFile.setIcon(icon1)
        self.actionOpenFile.setObjectName(_fromUtf8('actionOpenFile'))
        self.actionSave = QtGui.QAction(MainWindow)
        icon2 = QtGui.QIcon(":/save.png")
        self.actionSave.setIcon(icon2)
        self.actionSave.setObjectName(_fromUtf8('actionSave'))
        self.actionSaveAs = QtGui.QAction(MainWindow)
        icon3 = QtGui.QIcon(":/save-as.png")
        self.actionSaveAs.setIcon(icon3)
        self.actionSaveAs.setObjectName(_fromUtf8('actionSaveAs'))
        self.actionUndo = QtGui.QAction(MainWindow)
        icon5 = QtGui.QIcon(":/undo.png")
        self.actionUndo.setIcon(icon5)
        self.actionUndo.setObjectName(_fromUtf8('actionUndo'))
        self.actionRedo = QtGui.QAction(MainWindow)
        icon6 = QtGui.QIcon(":/redo.png")
        self.actionRedo.setIcon(icon6)
        self.actionRedo.setObjectName(_fromUtf8('actionRedo'))
        self.actionCut = QtGui.QAction(MainWindow)
        icon7 = QtGui.QIcon(":/cut.png")
        self.actionCut.setIcon(icon7)
        self.actionCut.setObjectName(_fromUtf8('actionCut'))
        self.actionCopy = QtGui.QAction(MainWindow)
        icon8 = QtGui.QIcon(":/copy.png")
        self.actionCopy.setIcon(icon8)
        self.actionCopy.setObjectName(_fromUtf8('actionCopy'))
        self.actionPaste = QtGui.QAction(MainWindow)
        icon9 = QtGui.QIcon(":/paste.png")
        self.actionPaste.setIcon(icon9)
        self.actionPaste.setObjectName(_fromUtf8('actionPaste'))
        self.actionSelectAll = QtGui.QAction(MainWindow)
        icon10 = QtGui.QIcon(":/select-all.png")
        self.actionSelectAll.setIcon(icon10)
        self.actionSelectAll.setObjectName(_fromUtf8('actionSelectAll'))
        self.actionFind = QtGui.QAction(MainWindow)
        icon11 = QtGui.QIcon(":/find.png")
        self.actionFind.setIcon(icon11)
        self.actionFind.setObjectName(_fromUtf8('actionFind'))
        self.actionReplace = QtGui.QAction(MainWindow)
        icon20 = QtGui.QIcon(":/find.png")
        self.actionReplace.setIcon(icon20)
        self.actionReplace.setObjectName(_fromUtf8('actionReplace'))
        self.actionFonts = QtGui.QAction(MainWindow)
        icon21 = QtGui.QIcon(":/select-font.png")
        self.actionFonts.setIcon(icon21)
        self.actionFonts.setObjectName(_fromUtf8('actionFonts'))
        self.actionPreferences = QtGui.QAction(MainWindow)
        self.actionPreferences.setObjectName(_fromUtf8('actionFonts'))
        self.actionCheck = QtGui.QAction(MainWindow)
        icon14 = QtGui.QIcon(":/check.png")
        self.actionCheck.setIcon(icon14)
        self.actionCheck.setObjectName(_fromUtf8('actionCheck'))
        self.actionRun = QtGui.QAction(MainWindow)
        icon12 = QtGui.QIcon(":/start.png")
        self.actionRun.setIcon(icon12)
        self.actionRun.setObjectName(_fromUtf8('actionRun'))
        self.actionStop = QtGui.QAction(MainWindow)
        icon13 = QtGui.QIcon(":/stop.png")
        self.actionStop.setIcon(icon13)
        self.actionStop.setObjectName(_fromUtf8('actionStop'))
        self.actionManual = QtGui.QAction(MainWindow)
        icon15 = QtGui.QIcon(":/help.png")
        self.actionManual.setIcon(icon15)
        self.actionManual.setObjectName(_fromUtf8('actionManual'))
        self.actionLicense = QtGui.QAction(MainWindow)
        icon16 = QtGui.QIcon(":/manual.png")
        self.actionLicense.setIcon(icon16)
        self.actionLicense.setObjectName(_fromUtf8('actionLicense'))
        self.actionAbout = QtGui.QAction(MainWindow)
        icon17 = QtGui.QIcon(":/about.png")
        self.actionAbout.setIcon(icon17)
        self.actionAbout.setObjectName(_fromUtf8('actionAbout'))
        self.actionExit = QtGui.QAction(MainWindow)
        icon18 = QtGui.QIcon(":/exit.png")
        self.actionExit.setIcon(icon18)
        self.actionExit.setObjectName(_fromUtf8('actionExit'))
        self.actionOpenBoardEditor = QtGui.QAction(MainWindow)
        icon19 = QtGui.QIcon(":/board-random.png")
        self.actionOpenBoardEditor.setIcon(icon19)
        self.actionOpenBoardEditor.setObjectName(_fromUtf8
                                            ('actionOpenBoardEditor'))
        self.actionBoardOptions = QtGui.QAction(MainWindow)
        icon20 = QtGui.QIcon(":/board-size.png")
        self.actionBoardOptions.setIcon(icon20)
        self.actionBoardOptions.setObjectName(_fromUtf8
                                            ('actionBoardOptions'))
        self.actionLoadBoard = QtGui.QAction(MainWindow)
        icon20 = QtGui.QIcon(":/board-new.png")
        self.actionLoadBoard.setIcon(icon20)
        self.actionLoadBoard.setObjectName(_fromUtf8
                                            ('actionLoadBoard'))
        self.toolBar.addAction(self.actionChangeLang)
        self.toolBar.addAction(self.actionNewFile)
        self.toolBar.addAction(self.actionOpenFile)
        self.toolBar.addAction(self.actionSave)
        self.toolBar.addAction(self.actionCloseFile)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionUndo)
        self.toolBar.addAction(self.actionRedo)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionOpenBoardEditor)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionCheck)
        self.toolBar.addAction(self.actionRun)
        self.toolBar.addAction(self.actionStop)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionManual)
        self.toolBar.addAction(self.actionAbout)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionChangeLang)
        self.menuFile.addAction(self.actionNewFile)
        self.menuFile.addAction(self.actionOpenFile)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSaveAs)
        self.menuFile.addAction(self.actionCloseFile)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionUndo)
        self.menuEdit.addAction(self.actionRedo)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionCut)
        self.menuEdit.addAction(self.actionCopy)
        self.menuEdit.addAction(self.actionPaste)
        self.menuEdit.addAction(self.actionSelectAll)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionFind)
        self.menuEdit.addAction(self.actionReplace)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionFonts)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionPreferences)
        self.menuGobstones.addSeparator()
        self.menuGobstones.addAction(self.actionRun)
        self.menuGobstones.addAction(self.actionStop)
        self.menuGobstones.addAction(self.actionCheck)
        self.menuBoard.addSeparator()
        self.menuBoard.addAction(self.actionLoadBoard)
        self.menuBoard.addAction(self.actionBoardOptions)
        self.menuBoard.addAction(self.actionOpenBoardEditor)
        self.menuBoard.addSeparator()
        self.menuBoard.addAction(self.menuSelectResultView.menuAction())
        self.menuHelp.addSeparator()
        self.menuHelp.addAction(self.actionManual)
        self.menuHelp.addAction(self.actionLicense)
        self.menuHelp.addAction(self.actionAbout)
        self.menuBar.addAction(self.menuFile.menuAction())
        self.menuBar.addAction(self.menuEdit.menuAction())
        self.menuBar.addAction(self.menuGobstones.menuAction())
        self.menuBar.addAction(self.menuBoard.menuAction())
        self.menuBar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        self.tabWidgetEditors.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def set_highlighter(self, highlighter_class):
        if hasattr(self, "highlighter"):
            self.highlighter["main"].setDocument(None)
            self.highlighter["library"].setDocument(None)
        else:
            self.highlighter = {}
        self.highlighter["main"] = highlighter_class(self.textEditFile.edit.document())
        self.highlighter["library"] = highlighter_class(self.textEditLibrary.edit.document())

    def retranslateUi(self, MainWindow):
        self.tabWidgetEditors.setTabText(
            self.tabWidgetEditors.indexOf(self.tabFile),
                 _translate('MainWindow', i18n('Untitled'), None))
        self.tabWidgetEditors.setTabText(
            self.tabWidgetEditors.indexOf(self.tabLibrary),
                 _translate('MainWindow', i18n('Untitled'), None))
        self.toolBar.setWindowTitle(_translate('MainWindow', 'toolBar', None))
        self.menuFile.setTitle(_translate('MainWindow', i18n('File'), None))
        self.menuEdit.setTitle(_translate('MainWindow', i18n('Edit'), None))
        self.menuGobstones.setTitle(_translate('MainWindow', 'Gobstones',
                                                             None))
        self.menuBoard.setTitle(_translate('MainWindow', i18n('Board'), None))
        self.menuSelectResultView.setTitle(_translate('MainWindow',
                                     i18n('Select view results'), None))
        self.menuHelp.setTitle(_translate('MainWindow', i18n('Help'), None))
        self.actionChangeLang.setText(_translate('MainWindow',
                                                        'Gobstones ', None))
        self.actionChangeLang.setToolTip(_translate('MainWindow',
                                i18n('Change the Gobstones Language'), None))
        self.actionChangeLang.setShortcut(_translate('MainWindow', 'F11', None))
        self.actionNewFile.setText(_translate('MainWindow', i18n('New'), None))
        self.actionNewFile.setToolTip(_translate('MainWindow',
                                         i18n('Create new file'), None))
        self.actionNewFile.setShortcut(_translate('MainWindow', 'Ctrl+N',
                                                                     None))
        self.actionCloseFile.setText(_translate('MainWindow', i18n('Close'), None))
        self.actionCloseFile.setToolTip(_translate('MainWindow',
                                         i18n('Close the current file and the library'), None))
        self.actionCloseFile.setShortcut(_translate('MainWindow', 'Ctrl+R',
                                                                     None))
        self.actionOpenFile.setText(_translate('MainWindow', i18n('Open'), None))
        self.actionOpenFile.setToolTip(_translate('MainWindow',
                                     i18n('Open an existent file'), None))
        self.actionOpenFile.setShortcut(_translate('MainWindow', 'Ctrl+O',
                                             None))
        self.actionSave.setText(_translate('MainWindow', i18n('Save'), None))
        self.actionSave.setToolTip(_translate('MainWindow',
                                     i18n('Save the current file'), None))
        self.actionSave.setShortcut(_translate('MainWindow', 'Ctrl+S', None))
        self.actionSaveAs.setText(_translate('MainWindow', i18n('Save as...'),
                                             None))
        self.actionSaveAs.setToolTip(_translate('MainWindow',
        i18n('Save the current file and allows put a name and choose the location'),
                                             None))
        self.actionUndo.setText(_translate('MainWindow', i18n('Undo'), None))
        self.actionUndo.setShortcut(_translate('MainWindow', 'Ctrl+Z', None))
        self.actionRedo.setText(_translate('MainWindow', i18n('Redo'), None))
        self.actionRedo.setShortcut(_translate('MainWindow', 'Ctrl+Shift+Z',
                                             None))
        self.actionCut.setText(_translate('MainWindow', i18n('Cut'), None))
        self.actionCut.setShortcut(_translate('MainWindow', 'Ctrl+X', None))
        self.actionCopy.setText(_translate('MainWindow', i18n('Copy'), None))
        self.actionCopy.setShortcut(_translate('MainWindow', 'Ctrl+C', None))
        self.actionPaste.setText(_translate('MainWindow', i18n('Paste'), None))
        self.actionPaste.setShortcut(_translate('MainWindow', 'Ctrl+V', None))
        self.actionSelectAll.setText(_translate('MainWindow',
                                         i18n('Select all'), None))
        self.actionSelectAll.setShortcut(_translate('MainWindow', 'Ctrl+A',
                                             None))
        self.actionFind.setText(_translate('MainWindow', i18n('Search'), None))
        self.actionFind.setShortcut(_translate('MainWindow', 'Ctrl+F', None))
        self.actionReplace.setText(_translate('MainWindow', i18n('Search and replace'), None))
        self.actionReplace.setShortcut(_translate('MainWindow', 'Ctrl+H', None))
        self.actionFonts.setText(_translate('MainWindow', i18n('Select fonts'), None))
        self.actionFonts.setShortcut(_translate('MainWindow', 'Ctrl+T', None))
        self.actionPreferences.setText(_translate('MainWindow', i18n('Preferences'), None))
        self.actionPreferences.setShortcut(_translate('MainWindow', 'Ctrl+P', None))
        self.actionRun.setText(_translate('MainWindow', i18n('Run'), None))
        self.actionRun.setToolTip(_translate('MainWindow',
                                 i18n('Executes the current program'), None))
        self.actionRun.setShortcut(_translate('MainWindow', 'F5', None))
        self.actionStop.setText(_translate('MainWindow', i18n('Stop'), None))
        self.actionStop.setToolTip(_translate('MainWindow',
                         i18n('Stops execution of the current program'), None))
        self.actionStop.setShortcut(_translate('MainWindow', 'F6', None))
        self.actionCheck.setText(_translate('MainWindow', i18n('Check'), None))
        self.actionCheck.setToolTip(_translate('MainWindow',
                         i18n('Checks if the program is well-formed'), None))
        self.actionCheck.setShortcut(_translate('MainWindow', 'F10', None))
        self.actionManual.setText(_translate('MainWindow', i18n('Manual'), None))
        self.actionManual.setToolTip(_translate('MainWindow',
                                i18n('Open the Gobstones\'s manual'), None))
        self.actionLicense.setText(_translate('MainWindow', i18n('Licence'), None))
        self.actionAbout.setText(_translate('MainWindow', i18n('About...'),
                                                                     None))
        self.actionExit.setText(_translate('MainWindow', i18n('Exit'), None))
        self.actionExit.setToolTip(_translate('MainWindow',
                                    i18n('Closes the application'), None))
        self.actionExit.setShortcut(_translate('MainWindow', 'Ctrl+Q', None))
        self.actionOpenBoardEditor.setText(_translate('MainWindow',
                                         i18n('Board editor'), None))
        self.actionOpenBoardEditor.setToolTip(_translate('MainWindow',
                                         i18n('Open board editor'), None))
        self.actionBoardOptions.setText(_translate('MainWindow',
                                         i18n('Options Board'), None))
        self.actionBoardOptions.setToolTip(_translate('MainWindow',
                                         i18n('Select board options'), None))
        self.actionLoadBoard.setText(_translate('MainWindow',
                                         i18n('Load board'), None))
        self.actionLoadBoard.setToolTip(_translate('MainWindow',
                                         i18n('Open a board from existing .gbb file'), None))

