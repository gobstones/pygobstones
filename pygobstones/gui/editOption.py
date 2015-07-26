 # -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
import sys
from commons.i18n import *
sys.path.append('..')
import views.resources

class EditOption(object):

    def __init__(self, mainWindow):
        self.mainW = mainWindow

    def updateEditUI(self, editor, n):
        fileName = self.getTabText(n)
        if editor.document().isModified():
            self.setTabText(n, '(*)' + fileName)
        else:
            self.setTabText(n, fileName[3:])

    def setTabText(self, n, filename):
        self.mainW.ui.tabWidgetEditors.setTabText(n, filename)

    def getTabText(self, n):
        return self.mainW.ui.tabWidgetEditors.tabText(n)

    def initEditorBehavior(self):
        font = QtGui.QFont()
        font.setFamily("Helvetica")
        self.setFont(font)
        self.setTabWidth(font)

    def setTabWidth(self, font, width = 4):
        metrics = QtGui.QFontMetrics(font)
        self.mainW.ui.textEditFile.setTabStopWidth(width * metrics.width(' '))
        self.mainW.ui.textEditLibrary.setTabStopWidth(width * metrics.width(' '))

    def openSearch(self):
        self.search = SearchWidget(self.mainW)
        self.search.show()

    def openReplace(self):
        self.replace = ReplaceWidget(self.mainW)
        self.replace.show()

    def openFontDialog(self):
        font = QtGui.QFontDialog.getFont(self.mainW.ui.textEditFile.font(), self.mainW)
        self.setFont(font[0])
        self.setTabWidth(font[0])

    def setFont(self, font):
        self.mainW.ui.textEditFile.setFont(font)
        self.mainW.ui.textEditLibrary.setFont(font)

    def undo(self):
        self.currentEditor().undo()

    def redo(self):
        self.currentEditor().redo()

    def cut(self):
        self.currentEditor().cut()

    def copy(self):
        self.currentEditor().copy()

    def paste(self):
        self.currentEditor().paste()

    def selectAll(self):
        self.currentEditor().selectAll()

    def currentEditor(self):
        if self.mainW.ui.tabWidgetEditors.currentIndex() == 0:
            return self.mainW.ui.textEditFile
        else:
            return self.mainW.ui.textEditLibrary

    def activateLineNumbers(self, boolean):
        self.mainW.ui.textEditFile.activateLineNumbers(boolean)
        self.mainW.ui.textEditLibrary.activateLineNumbers(boolean)
        
    def activateAutoIndentation(self, boolean):
        self.mainW.ui.textEditFile.activateAutoIndentation(boolean)
        self.mainW.ui.textEditLibrary.activateAutoIndentation(boolean)

class ReplaceWidget(QtGui.QDialog):
    def __init__(self, parent):
        super(ReplaceWidget, self).__init__(parent)
        self.setWindowTitle(i18n('Search and replace'))
        self.resize(QtCore.QSize(300, 120))
        self.setModal(False)

        
        self.textEditor = self.setEditor()
        self.textEditor.moveCursor(QtGui.QTextCursor.Start)
        labelSearch = QtGui.QLabel(i18n('Search'))
        self.textOld = QtGui.QLineEdit()
        labelReplace = QtGui.QLabel(i18n('Replace with'))
        self.textNew = QtGui.QLineEdit()
        searchButton = QtGui.QPushButton(i18n('Search'))
        replaceButton = QtGui.QPushButton(i18n('Replace'))
        replaceAllButton = QtGui.QPushButton(i18n('Replace all'))

        layout = QtGui.QVBoxLayout()
        layout2 = QtGui.QGridLayout()
        layout2.addWidget(labelSearch, 0, 0)
        layout2.addWidget(self.textOld, 0, 1)
        layout2.addWidget(labelReplace, 1, 0)
        layout2.addWidget(self.textNew, 1, 1)
        layout3 = QtGui.QHBoxLayout()
        layout3.addWidget(replaceButton)
        layout3.addWidget(replaceAllButton)
        layout3.addWidget(searchButton)
        layout.addLayout(layout2)
        layout.addLayout(layout3)
        self.setLayout(layout)
    
        self.setStyleSheet("QDialog {background-color:'white'; border:2px solid #4682b4; border-color:'#4682b4';}")

        searchButton.clicked.connect(self.search)
        replaceButton.clicked.connect(self.replace)
        replaceAllButton.clicked.connect(self.replaceAll)

    def search(self):
        result = self.textEditor.edit.find(self.textOld.text())
        if not result:
            self.textEditor.moveCursor(QtGui.QTextCursor.Start)
            self.textEditor.edit.find(self.textOld.text())

    def replace(self):
        if self.textEditor.textCursor().hasSelection():
            self.textEditor.textCursor().insertText(self.textNew.text())

    def replaceAll(self):
        self.textEditor.moveCursor(QtGui.QTextCursor.Start)

        old = self.textOld.text()
        new = self.textNew.text()

        cursor = self.textEditor.textCursor()
        cursor.beginEditBlock()

        while True:
            result = self.textEditor.edit.find(old)
            if result:
                tc = self.textEditor.textCursor()
                if tc.hasSelection():
                    tc.insertText(new)
            else:
                break

        cursor.endEditBlock()

        self.textEditor.moveCursor(QtGui.QTextCursor.Start)

    def setEditor(self):
        if self.parent().ui.tabWidgetEditors.currentIndex() == 0:
            return self.parent().ui.textEditFile
        else:
            return self.parent().ui.textEditLibrary

class SearchWidget(QtGui.QDialog):
    def __init__(self, parent):
        super(SearchWidget, self).__init__(parent)
        self.setWindowTitle(i18n('Search'))
        self.resize(QtCore.QSize(300, 80))
        self.setModal(False)
        self.textEditor = self.setEditor()
        labelSearch = QtGui.QLabel(i18n('Search'))
        self.text = QtGui.QLineEdit()
        self.text.textChanged.connect(self.search)
        prevButton = QtGui.QPushButton()
        prevButton.setIcon(QtGui.QIcon(':/prev.png'))
        nextButton = QtGui.QPushButton()
        nextButton.setIcon(QtGui.QIcon(':/next.png'))
        layout = QtGui.QHBoxLayout()
        layout.addWidget(labelSearch)
        layout.addWidget(self.text)
        layout.addWidget(prevButton)
        layout.addWidget(nextButton)
        self.setLayout(layout)
        nextButton.clicked.connect(self.next)
        prevButton.clicked.connect(self.prev)
        
        self.setStyleSheet("QDialog {background-color:'white'; border:2px solid #4682b4; border-color:'#4682b4';}")

    def search(self):
        self.textEditor.moveCursor(QtGui.QTextCursor.Start)
        self.textEditor.edit.find(self.text.text())

    def next(self):
        result = self.textEditor.edit.find(self.text.text())
        if not result:
            self.textEditor.moveCursor(QtGui.QTextCursor.Start)
            self.textEditor.edit.find(self.text.text())
            
    def prev(self):
        result = self.textEditor.edit.find(self.text.text(), QtGui.QTextDocument.FindBackward)
        if not result:
            self.textEditor.moveCursor(QtGui.QTextCursor.End)
            self.textEditor.edit.find(self.text.text(), QtGui.QTextDocument.FindBackward)

    def setEditor(self):
        if self.parent().ui.tabWidgetEditors.currentIndex() == 0:
            return self.parent().ui.textEditFile
        else:
            return self.parent().ui.textEditLibrary
