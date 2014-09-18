 # -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from PyQt4.QtWebKit import QWebView, QWebPage
import commons.utils as utils  
import sys, os
sys.path.append('..')
import views.resources
from commons.i18n import *
from commons.utils import root_path

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class HelpOption(object):

    def __init__(self, mainWindow):
        self.mainW = mainWindow
        self.license = LicenseWidget()
        self.about = AboutWidget()
        self.desktopServices = QtGui.QDesktopServices()

    def openManual(self):
        self.desktopServices.openUrl(QtCore.QUrl("http://www.gobstones.org/bibliografia"))

    def viewLicense(self):
        self.license.show()

    def viewAbout(self):
        self.about.show()

class LicenseWidget(QtGui.QDialog):

    def __init__(self):
        super(LicenseWidget, self).__init__()
        self.setModal(True)
        self.browser = QWebView()
        self.browser.load(QtCore.QUrl('http://www.gnu.org/licenses/gpl-3.0.txt'))
        self.setWindowTitle(i18n("License Agreement - Gobstones"))
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.browser)
        self.setLayout(layout)

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.Antialiasing
        painter.begin(self)
        rect = QtCore.QRect(0, 0, 1920, 1080)
        img = QtGui.QImage(':/backgroundWidget.png')
        painter.drawImage(rect, img)
        painter.end()

class AboutWidget(QtGui.QDialog):

    def __init__(self):
        super(AboutWidget, self).__init__()
        self.version = QtCore.QString(utils.read_file(os.path.join(utils.root_path(), 'version')))
        self.setModal(True)
        icon = QtGui.QIcon(':/logoGobstones.png')
        self.setWindowIcon(icon)
        self.setWindowTitle(i18n("About"))
        logoHtml = ""
        logoHtml += (       "<div align = 'center'>"
                            '<img src=":/logoHelp.png">'
                            "</div>"
                             )
        versionHtml = ""
        versionHtml += (        '<div align = "center">'
                                "<h3>PyGobstones</h3>"
                                "<p>Versi&oacute;n " + self.version + "</p>".decode('utf8') +
                                "<p>" + i18n("Developed with Python and PyQt") + "</p>"
                                "</div>"
                             )
        logo = QtGui.QLabel(logoHtml)
        version = QtGui.QLabel(versionHtml)
        hLayout = QtGui.QHBoxLayout()
        hLayout.addWidget(logo)
        hLayout.addWidget(version)

        tabs = QtGui.QTabWidget(self)
        tabs.tabBar().setStyleSheet("background-color:'white'; color:'#4682b4'; border:2px solid #4682b4; font-size:15px")
        tabs.tabBar().setAttribute(QtCore.Qt.WA_TranslucentBackground)

        about = self.openAndReturnHelpFile(os.path.join(utils.root_path(), 'about_files','about.html'))
        authors = self.openAndReturnHelpFile(os.path.join(utils.root_path(), 'about_files','authors.html'))
        history = self.openAndReturnHelpFile(os.path.join(utils.root_path(), 'about_files','history.html'))

        tabs.addTab(about, _fromUtf8(""))
        tabs.addTab(authors, _fromUtf8(""))
        tabs.addTab(history, _fromUtf8(""))

        tabs.setTabText(0, i18n("About"))
        tabs.setTabText(1, i18n("Authors"))
        tabs.setTabText(2, i18n("History"))

        vLayout = QtGui.QVBoxLayout()
        vLayout.addLayout(hLayout)
        vLayout.addWidget(tabs)
        self.setLayout(vLayout)

    def openAndReturnHelpFile(self, path):
        theFile = open(path)
        string = QWebView_([line.strip() for line in theFile])
        theFile.close()
        return string

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.Antialiasing
        painter.begin(self)
        rect = QtCore.QRect(0, 0, 1920, 1080)
        img = QtGui.QImage(':/backgroundWidget.png')
        painter.drawImage(rect, img)
        painter.end()

class QWebView_(QWebView):

    def __init__(self, content):
        super(QWebView_, self).__init__()
        self.linkClicked.connect(self.handleLinkClicked)
        content = map(lambda x:x.decode('utf8'), content)
        self.setHtml(''.join(content))
        self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)

    def handleLinkClicked(self, url):
        QtGui.QDesktopServices().openUrl(url)


class CommandHelpWidget(QtGui.QDialog):

     def __init__(self):
        super(CommandHelpWidget, self).__init__()
        self.setModal(True)
        self.setWindowTitle(i18n('User guide editor board'))
        tabs = QtGui.QTabWidget(self)
        tabs.tabBar().setStyleSheet("background-color:'white'; color:'#4682b4'; border:2px solid #4682b4; font-size:15px")
        tabs.tabBar().setAttribute(QtCore.Qt.WA_TranslucentBackground)

        command = self.openAndReturnHelpFile(os.path.join(utils.root_path(), 'about_files','command_editor.html'))

        tabs.addTab(command, _fromUtf8(""))

        tabs.setTabText(0, i18n("commands enables"))

        vLayout = QtGui.QVBoxLayout()
        vLayout.addWidget(tabs)
        self.setLayout(vLayout)

     def openAndReturnHelpFile(self, path):
        theFile = open(path)
        string = QWebView_([line.strip() for line in theFile])
        theFile.close()
        return string


     def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.Antialiasing
        painter.begin(self)
        rect = QtCore.QRect(0, 0, 1920, 1080)
        img = QtGui.QImage(':/backgroundWidget.png')
        painter.drawImage(rect, img)
        painter.end()
