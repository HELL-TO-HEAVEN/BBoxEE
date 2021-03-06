# -*- coding: utf-8 -*-
#
# Bounding Box Editor and Exporter (BBoxEE)
# Author: Peter Ersts (ersts@amnh.org)
#
# --------------------------------------------------------------------------
#
# This file is part of Animal Detection Network's (Andenet)
# Bounding Box Editor and Exporter (BBoxEE)
#
# BBoxEE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# BBoxEE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# --------------------------------------------------------------------------
from PyQt5 import QtWidgets

from bboxee.gui import ExportWidget
from bboxee.gui import AnnotationWidget
from bboxee import __version__


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, icon_size, parent=None):
        super(MainWindow, self).__init__(parent)
        template = 'Bounding Box Editor and Exporter [BBoxEE v{}]'
        self.setWindowTitle(template.format(__version__))
        self.annotation_widget = AnnotationWidget(icon_size)
        widget = QtWidgets.QTabWidget()
        widget.addTab(self.annotation_widget, 'Annotate')
        widget.addTab(ExportWidget(icon_size), 'Export')
        self.setCentralWidget(widget)

    def closeEvent(self, event):
        if self.annotation_widget.dirty_data_check():
            event.accept()
        else:
            event.ignore()
