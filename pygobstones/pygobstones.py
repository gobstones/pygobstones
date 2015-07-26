#!/usr/bin/python
from PyQt4 import QtGui, QtCore
from gui.mainWindow import *
from time import time, sleep
from PyQt4.QtGui import QApplication, QSplashScreen, QPixmap
from PyQt4.QtCore import QSize
from PyQt4.QtSvg import QSvgWidget
import sys
import os
import platform
from commons.paths import root_path, pygobstones_user_path
import logging
import traceback

def run_pygobstones():
    app = QtGui.QApplication(sys.argv)

    #Get the locale settings
    locale = unicode(QtCore.QLocale.system().name())

    # This is to make Qt use locale configuration; i.e. Standard Buttons
    # in your system's language.
    qtTranslator=QtCore.QTranslator()
    qtTranslator.load("qt_" + locale,
                        QtCore.QLibraryInfo.location(
                        QtCore.QLibraryInfo.TranslationsPath)
                        )
    app.installTranslator(qtTranslator)

    path = os.path.join(root_path(), 'commons')

    f = QtGui.QFontDatabase.addApplicationFont(os.path.join(path, 'ubuntu.ttf'))
    font = QtGui.QFont('Ubuntu Titling')
    font.setBold(True)
    font.setPixelSize(16)
    app.setFont(font)

    start = time()
    
    if 'huayra' in platform.uname():
        img = QPixmap(os.path.join(path, 'gobstones_huayra.png'))
    else:
        img = QPixmap(os.path.join(path, 'gobstones.png'))

    splash = QSplashScreen(img)
    splash.show()

    while time() - start < 1:
        app.processEvents()
    
    w = MainWindow()
    icon = QtGui.QIcon(os.path.join(path, 'logo.png'))
    w.setWindowIcon(icon)
    splash.finish(w)
    w.showMaximized()
    sys.exit(app.exec_())

def setup_logger():
    logger = logging.getLogger()    
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(name)s] %(message)s')

    if not os.path.exists(pygobstones_user_path()):
        os.mkdir(pygobstones_user_path())

    filehandler = logging.FileHandler(os.path.join(pygobstones_user_path(), "pygobstones.log"))
    filehandler.setFormatter(formatter)
    
    consolehandler = logging.StreamHandler()
    consolehandler.setFormatter(formatter)
    
    logger.addHandler(filehandler) 
    logger.addHandler(consolehandler)
    logger.setLevel(logging.WARNING)

def main():
    setup_logger()
    try:
        run_pygobstones()
    except Exception as e:
        logging.getLogger().critical(traceback.format_exc(e))

if __name__ == '__main__':
    main()
