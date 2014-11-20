# -*- coding: utf-8 -*-
import os
import sys
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtGui import QMessageBox
import PyQt4
import views.resources
sys.path.append('..')
from commons.i18n import *
from commons.utils import root_path, user_path, clothing_for_file_exists, clothing_dir_for_file


def gobstones_folder():
    return os.path.join(user_path(), "gobstones")

class FileOption(object):

    def __init__(self, mainWindow):        
        self.mainW = mainWindow
        self.moduleFile = None
        self.libraryFile = None
        self.initGobstonesFolder()

    def initGobstonesFolder(self):
        if not os.path.exists(gobstones_folder()):
            os.makedirs(gobstones_folder())

    def getFileName(self):
        return self.moduleFile

    def setTabsNamesAndLabelButtonNameAndSetCurrentPathDirectory(self,
         qStringFName):
        (filepath, filename) = os.path.split(str(qStringFName))
        if self.isEqualDisk(filepath, self.mainW.rootDirectory) and self.is_subdir(filepath, self.mainW.rootDirectory):
            self.mainW.updateFilePath(
                '.' + filepath[filepath.find('PyGobstones'):][11:])
            print filepath
        else:
            self.mainW.updateFilePath(filepath)
        self.setCurrentPathDirectory(filepath)
        self.setTabsNames(filename, 'Biblioteca.gbs')

    def isEqualDisk(self, pathFile, rootDir):
        return pathFile[:1] == rootDir[:1]

    def is_subdir(self, path, directory):
        path = os.path.realpath(path)
        directory = os.path.realpath(directory)

        relative = os.path.relpath(path, directory)
        if relative.startswith(os.pardir + os.sep):
            return False
        else:
            return True

    def setCurrentPathDirectory(self, filepath):
        os.chdir(filepath)

    def setTabsNames(self, moduleFileName, libraryFileName):
        self.mainW.ui.tabWidgetEditors.setTabText(0, moduleFileName)
        self.mainW.ui.tabWidgetEditors.setTabText(1, libraryFileName)

    def wantOpenLibrary(self, qStringFName):
        (filepath, filename) = os.path.split(str(qStringFName))
        return filename == "Biblioteca.gbs"

    def loadLibrary(self):
        '''Purpose: Load library file of a current directory.
            If not exist the Biblioteca.gbs , then create a new file library
        '''
        if not os.path.exists('Biblioteca.gbs'):
            fileLibrary = open('Biblioteca.gbs', 'w')
            fileLibrary.write(i18n('-- New Library'))
            fileLibrary.close()
        fileLibrary = open('Biblioteca.gbs')
        self.libraryFile = os.path.abspath(str('Biblioteca.gbs'))
        data = fileLibrary.read()
        string = QtCore.QString()
        data = string.fromUtf8(data)
        self.mainW.ui.textEditLibrary.setPlainText(data)
        fileLibrary.close()

    def openFiles(self):

        if self.mainW.ui.textEditFile.document().isModified() or self.mainW.ui.textEditLibrary.document().isModified():
            val = QMessageBox.question(self.mainW, i18n('Warning!'),
             i18n('There are unsaved files, to load a new module changes will be lost, continue?'),
            QMessageBox.Yes, QMessageBox.Cancel)
            if val == QMessageBox.Cancel:
                return

        filename = QtGui.QFileDialog.getOpenFileName(self.mainW, i18n('Open File'),
        gobstones_folder(), '*.gbs')
        if not filename == PyQt4.QtCore.QString(''):
            if not self.wantOpenLibrary(filename):
                self.moduleFile = filename
                fname = open(filename)
                data = fname.read()
                string = QtCore.QString()
                data = string.fromUtf8(data)
                self.mainW.ui.textEditFile.setPlainText(data)
                self.setTabsNamesAndLabelButtonNameAndSetCurrentPathDirectory(filename)
                self.loadLibrary()
                fname.close()
            else:
                QMessageBox.question(self.mainW, i18n('Error loading the file'),
                     i18n('Must load a file different to library') + '\n'
                           + i18n('If you want edit the library, use the corresponding tab'),
                            QMessageBox.Ok)
        self.createInitialsFoldersAndFiles()
        self.updateClothingOptions()

    def updateClothingOptions(self):
        if clothing_for_file_exists(str(self.moduleFile)):
            path = clothing_dir_for_file(str(self.moduleFile))
            files = os.listdir(path)
        else:
            files = []
        self.mainW.ui.menuSelectResultView.clear()
        self.filesNames = []
        for f in files:
            fileName, fileExtension = os.path.splitext(os.path.join(path,f))
            if fileExtension == '.xml':
                self.filesNames.append(os.path.join(path, fileName))

        self.mapper = QtCore.QSignalMapper(self.mainW)
        self.actions = {}
        for fn in self.filesNames:
            (filepath, filename) = os.path.split(fn)            
            self.addClothing(fn, filename)
        
        self.addClothing('Gobstones', i18n('Gobstones Standard'))        
        self.addClothing('PixelBoard', i18n('Pixel Board'))
        self.mapper.mapped['QString'].connect(self.handleButton)

    def addClothing(self, clothing_filename, clothing_text):
        action = QtGui.QAction(clothing_text, self.mainW)
        self.actions[clothing_filename] = action        
        self.mapper.setMapping(action, clothing_filename)
        action.triggered.connect(self.mapper.map)
        self.mainW.ui.menuSelectResultView.addAction(action)

    def handleButton(self, identifier):
        self.updateIconClothing()
        for fn in self.filesNames:
            if fn == identifier:
                self.mainW.setClothing(fn + '.xml')
                self.actions[str(identifier)].setIcon(QtGui.QIcon(':/board-select.png'))

    def updateIconClothing(self):
        for file_name in self.filesNames:
            self.actions[str(file_name)].setIcon(QtGui.QIcon(":/empty.png"))


    def newFile(self):

        if self.mainW.ui.textEditFile.document().isModified():
            val = QMessageBox.question(self.mainW, i18n('Save changes?'),
             i18n('The file %s was changed, Do you save changes?') % (self.mainW.ui.tabWidgetEditors.tabText(0)[3:]),
            QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel)
            if val == QMessageBox.Yes:
                self.saveFile()
            elif val == QMessageBox.Cancel:
                return
        self.moduleFile = None
        self.clearCurrentModule()
        if clothing_dir_for_file(str(self.moduleFile)):
            self.updateClothingOptions()
            self.mainW.setClothing('Gobstones.xml')

    def closeApp(self, event):

        if self.mainW.ui.textEditFile.document().isModified() or self.mainW.ui.textEditLibrary.document().isModified():
                val = QMessageBox.question(self.mainW, i18n('Save changes?')
                    , i18n('There are unsaved files, you want to close the application?'),
                    QMessageBox.Yes, QMessageBox.No)
                if val == QMessageBox.Yes:
                    event.accept()
                else:
                    event.ignore()

    def clearCurrentModule(self):
        self.mainW.ui.textEditFile.clear()
        self.mainW.ui.tabWidgetEditors.setTabText(0, i18n('Empty'))

    def clearLibraryModule(self):
        self.mainW.ui.textEditLibrary.clear()
        self.mainW.ui.tabWidgetEditors.setTabText(1, i18n('Empty'))

    def closeFiles(self):        
        if (self.checkWasChangesInFiles() != QMessageBox.Cancel):
            self.clearCurrentModule()
            self.clearLibraryModule()
            if os.path.exists('Vestimentas'):
                self.updateClothingOptions()
                self.mainW.setClothing('Gobstones.xml')
            self.mainW.initWindowTitle()
            self.moduleFile = None

    def checkWasChangesInFiles(self):
        if self.mainW.ui.textEditFile.document().isModified():
            val = QMessageBox.question(self.mainW, i18n('Save changes?'),
             i18n('The file %s was changed, Do you save changes?') % (self.mainW.ui.tabWidgetEditors.tabText(0)[3:]),
            QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel)
            if val == QMessageBox.Yes:
                if not self.saveFile():
                    return QMessageBox.Cancel          
        if self.mainW.ui.textEditLibrary.document().isModified():
            val = QMessageBox.question(self.mainW, i18n('Save changes?'),
             i18n('The file %s was changed, Do you save changes?') % (self.mainW.ui.tabWidgetEditors.tabText(1)[3:]),
            QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel)
            if val == QMessageBox.Yes:
                if not self.saveFile():
                    return QMessageBox.Cancel                
        return val
            

    def saveFile(self):
        indexFile = self.mainW.ui.tabWidgetEditors.currentIndex()
        if indexFile == 0:
            if self.moduleFile is None:
                return self.saveAsFileDialog()
            else:
                modFile = open(self.moduleFile, 'w')
                modFile.write(self.mainW.ui.textEditFile.toPlainText().toUtf8())
                modFile.close()
                self.mainW.ui.textEditFile.document().setModified(False)
                return True
        else:
            if self.libraryFile is None:
                return self.saveAsFileDialog()
            else:
                modLibrary = open(self.libraryFile, 'w')
                modLibrary.write(self.mainW.ui.textEditLibrary.toPlainText().toUtf8())
                modLibrary.close()
                self.mainW.ui.textEditLibrary.document().setModified(False)
                return True

    def saveAsFileDialog(self):
        indexFile = self.mainW.ui.tabWidgetEditors.currentIndex()
        filename = QtGui.QFileDialog.getSaveFileName(self.mainW,
            i18n('Save as ...'), gobstones_folder(), '*.gbs')
        if filename == PyQt4.QtCore.QString(''):
            return False
        if indexFile == 0:
            (filep, filen) = os.path.split(str(filename))
            if filen == "Biblioteca.gbs" or filen == "Biblioteca":
                QMessageBox.question(self.mainW, i18n('Error saving the file'),
                    i18n('The file name dont be equals to library') + '\n'
                        + i18n(''),
                        QMessageBox.Ok)
                return False
            else:
                filename = self.addExtension(filename)
                self.moduleFile = filename
                myFile = open(filename, 'w')
                myFile.write(self.mainW.ui.textEditFile.toPlainText().toUtf8())
                self.setCurrentPathDirectory(os.path.dirname(filename))
                myFile.close()
                self.mainW.ui.textEditFile.document().setModified(False)
                self.setTabsNamesAndLabelButtonNameAndSetCurrentPathDirectory(filename)
                self.loadLibrary()
            
        if indexFile == 1:
            (filep, filen) = os.path.split(str(filename))
            if not filen.startswith('Biblioteca'):
                QMessageBox.question(self.mainW, i18n('Error saving the file'),
                    i18n('The file must be named "Library"') + '\n'
                        + i18n(''),
                        QMessageBox.Ok)
                return False
            elif not os.path.exists('Biblioteca.gbs'):
                filename = self.addExtension(filename)
                self.libraryFile = filename
                fileLibrary = open(filename, 'w')
                fileLibrary.write(self.mainW.ui.textEditLibrary.toPlainText().toUtf8())
                self.setCurrentPathDirectory(os.path.dirname(filename))
                fileLibrary.close()
                self.mainW.ui.textEditLibrary.document().setModified(False)
                self.mainW.ui.tabWidgetEditors.setTabText(1, self.addExtension(filen))
            else:
                self.saveLibrary()
                
        self.createInitialsFoldersAndFiles()
        self.updateClothingOptions()
        
        return True


    def createInitialsFoldersAndFiles(self):
        if not os.path.exists('Vestimentas'):
            path = os.path.join(gobstones_folder(), 'Vestimentas')
            os.makedirs(path)
            os.makedirs(os.path.join(path, 'Imagenes'))


    def saveLibrary(self):
        libFile = open(self.libraryFile, 'w')
        libFile.write(self.mainW.ui.textEditLibrary.toPlainText().toUtf8())
        libFile.close()
        self.mainW.ui.textEditLibrary.document().setModified(False)

    def addExtension(self, filename):
        filename = str(filename)
        if not filename.endswith('.gbs'):
            filename = filename + '.gbs'
        return filename

