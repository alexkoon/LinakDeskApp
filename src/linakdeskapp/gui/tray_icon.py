# MIT License
# 
# Copyright (c) 2017 Arkadiusz Netczuk <dev.arnet@gmail.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#


import logging
import functools
from enum import Enum, unique

from .qt import qApp, QSystemTrayIcon, QMenu, QAction



_LOGGER = logging.getLogger(__name__)



@unique
class TrayIconTheme(Enum):
    WHITE           = ('office-chair-white.png', 'office-chair-red.png')
    BLACK           = ('office-chair-black.png', 'office-chair-red.png')
    BLACK_ON_GRAY   = ('office-chair-gray.png', 'office-chair-red-gray.png')

    @classmethod
    def findByName(cls, name):
        for item in cls:
            if item.name == name:
                return item
        return None
    
    @classmethod
    def indexOf(cls, key):
        index = 0
        for item in cls:
            if item == key:
                return index
            if item.name == key:
                return index
            index = index + 1
        return -1
    
    
class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent):
        super().__init__(parent)

        self.device = None
        self.neutralIcon = None
        self.indicatorIcon = None
        self.currIconState = 1          ## 0 - unknown, 1 - neutral, 2 - indicator

        self.activated.connect( self._icon_activated )

        '''
            Define and add steps to work with the system tray icon
            show - show window
            hide - hide window
            exit - exit from application
        '''
        self.toggle_window_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        self.toggle_window_action.triggered.connect( self._toggleParent )
        quit_action.triggered.connect( qApp.quit )
        
        self.fav_menu = QMenu("Favs")
        
        tray_menu = QMenu()
        tray_menu.addAction( self.toggle_window_action )
        tray_menu.addMenu( self.fav_menu )
        tray_menu.addAction( quit_action )
        self.setContextMenu( tray_menu )
    
    def attachConnector(self, connector):
        if self.device != None:
            ## disconnect old object
            self.device.connectionStateChanged.disconnect( self.updateFavMenu )
            self.device.favoritiesChanged.disconnect( self.updateFavMenu )
             
        self.device = connector
        
        self.updateFavMenu()

        ## connect new object
        if self.device != None:
            self.device.connectionStateChanged.connect( self.updateFavMenu )
            self.device.favoritiesChanged.connect( self.updateFavMenu )         
    
    def setIconNeutral(self, icon):
        self.neutralIcon = icon
        if self.currIconState == 1:
            self.setNeutral()
    
    def setIconIndicator(self, icon):
        self.indicatorIcon = icon
        if self.currIconState == 2:
            self.setIndicator()
    
    def setNeutral(self):
        if self.neutralIcon != None:
            self.setIcon( self.neutralIcon )
            self.currIconState = 1
            
    def setIndicator(self):
        if self.indicatorIcon != None:
            self.setIcon( self.indicatorIcon )
            self.currIconState = 2
    
    def displayMessage(self, message):
        timeout = 10000
        ## under xfce4 there is problem with balloon icon -- it changes tray icon, so
        ## it cannot be changed back to proper one. Workaround is to use NoIcon parameter
        self.showMessage("Desk", message, QSystemTrayIcon.NoIcon, timeout)
        ##self.showMessage("Desk", message, QSystemTrayIcon.Information, timeout)
        ##QtCore.QTimer.singleShot(timeout, self._refreshIcon)
        
    def setInfo(self, message):
        self.setToolTip("Desk: " + message)
    
    def changeIcon(self, state):
        if state == True:
            self.setIndicator()
        else:
            self.setNeutral()
            
    def _refreshIcon(self):
        _LOGGER.warn("refreshing icon state: %s", self.currIconState)
        if self.currIconState == 1:
            self.setNeutral()
        elif self.currIconState == 2:
            self.setIndicator()
        else:
            _LOGGER.warn("unsupported state: %s", self.currIconState)
    
    def _icon_activated(self, reason):
#         print("tray clicked, reason:", reason)
        if reason == 3:
            ## clicked
            self._toggleParent()
    
    def _toggleParent(self):
        parent = self.parent()
        if parent.isHidden():
            parent.show()
        else:
            parent.hide()
        self.updateLabel()
    
    def updateFavMenu(self):
        self.fav_menu.clear()
        if self.device == None:
            return
        if self.device.isConnected() == False:
            return
        positions = self.device.favPositions()
        for i in range( len(positions) ):
            fav = positions[i]
            if fav == None:
                continue
            favAction = QAction( str(fav), self)
            favHandler = functools.partial(self.device.moveToFav, i)
            favAction.triggered.connect( favHandler )
            self.fav_menu.addAction( favAction )
        
    def updateLabel(self):
        parent = self.parent()
        if parent.isHidden():
            self.toggle_window_action.setText("Show")
        else:
            self.toggle_window_action.setText("Hide")
    