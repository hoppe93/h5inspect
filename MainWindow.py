from PyQt5 import QtGui, QtWidgets
from design import main_design
import sys
import os.path
import numpy as np
import scipy.io
import h5py
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
import pathlib
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PlotWindow import PlotWindow

try:
    import convertMat2H5
    CONVERT_AVAILABLE = True
except ModuleNotFoundError:
    CONVERT_AVAILABLE = False


class MainWindow(QtWidgets.QMainWindow):


    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = main_design.Ui_MainWindow()
        self.ui.setupUi(self)

        self.filename = ""
        self.h5file = None

        self.itemToPlot = None
        self.plotWindows = []

        self.treeViewModel = QtGui.QStandardItemModel()
        self.ui.treeView.setModel(self.treeViewModel)

        self.attributeIcon = QtGui.QIcon("{}/icons/attribute.png".format(pathlib.Path(__file__).parent.absolute()))
        self.dataIcon      = QtGui.QIcon("{}/icons/data.png".format(pathlib.Path(__file__).parent.absolute()))
        self.groupIcon     = QtGui.QIcon("{}/icons/group.png".format(pathlib.Path(__file__).parent.absolute()))

        # Bind to events
        self.bindEvents()

        if not CONVERT_AVAILABLE:
            self.ui.actionImportMAT.setEnabled(False)

        # Disable controls
        self.disable()

        if len(sys.argv) == 2:
            self.loadFile(sys.argv[1])


    def bindEvents(self):
        self.ui.actionExit.triggered.connect(self.exit)
        self.ui.actionOpen.triggered.connect(self.openFile)
        self.ui.actionImportMAT.triggered.connect(self.importMAT)
        self.ui.treeView.selectionModel().selectionChanged.connect(self.itemSelected)
        self.ui.treeView.customContextMenuRequested.connect(self.tvContextMenu)


    def disable(self, enable=False):
        """
        Disable most controls (i.e. all those which should be inaccessible
        when no file is loaded)
        """
        self.ui.treeView.setEnabled(enable)
        self.ui.gbInfo.setEnabled(enable)
        self.ui.gbData.setEnabled(enable)
        self.ui.tbPath.setEnabled(enable)


    def enable(self): self.disable(True)


    def closeEvent(self, event):
        self.exit()


    def exit(self):
        if self.h5file is not None:
            self.h5file.close()

        for pw in self.plotWindows:
            pw.close()

        self.close()

    
    def openFile(self):
        filename, _ = QFileDialog.getOpenFileName(parent=self, caption="Open HDF5 file", filter="HDF5 file (*.h5 *.hdf5 *.mat);;All files (*.*)")

        if filename:
            self.loadFile(filename)


    def importMAT(self):
        filename, _ = QFileDialog.getOpenFileName(parent=self, caption="Open Matlab MAT file (old version)", filter="MAT file (*.mat);;All files (*.*)")
        savename, _ = QFileDialog.getSaveFileName(parent=self, caption="Name of HDF5 file to save to", filter="HDF5 file (*.h5);;All files (*.*)")

        try:
            convertMat2H5.convert(filename, savename)
        except Exception as ex:
            QMessageBox.critical(self, "MAT import failed", f"Failed to import Matlab MAT file. Warnings may appear in the terminal.\n\n{ex}")
            return

        self.loadFile(savename)


    def loadFile(self, filename):
        """
        Load the named file.
        """
        self.filename = filename
        self.h5file = h5py.File(filename, 'r')

        # Clear tree view
        self.treeViewModel.clear()

        self._populateTree('/', self.treeViewModel.invisibleRootItem())
        
        self.enable()


    def _populateTree(self, path, parent):
        """
        Populate the tree view recursively.
        """
        keys = sorted(list(self.h5file[path].keys()), key=str.lower)
        for key in keys:
            itm = QtGui.QStandardItem(key)
            parent.appendRow(itm)

            p = path
            if p[-1] != '/': p += '/' + key
            else: p += key
            
            if type(self.h5file[p]) == h5py.Group:
                itm.setIcon(self.groupIcon)
                self._populateTree(p, itm)
            else:
                itm.setIcon(self.dataIcon)

            for a in self.h5file[p].attrs:
                itma = QtGui.QStandardItem(a)
                itma.setIcon(self.attributeIcon)
                itma.setData('attribute')
                itm.appendRow(itma)


    def getData(self, dset):
        """
        Get data from dataset.
        """
        if type(dset) == h5py.Dataset:
            if dset.dtype == 'S1' or str(dset.dtype).startswith('|S'):
                return dset[:].tostring().decode('utf-8')
            elif dset.dtype == 'object':
                return dset[:][0].decode()
            else:
                return str(dset[:])
        else:
            if type(dset) == np.bytes_ or type(dset) == bytes:
                return dset.decode('utf-8')
            else:
                return str(dset)


    def getDataFromItem(self, item):
        """
        Given a TreeView item, returns the raw data corresponding to
        that item.
        """
        if type(item) == str:
            path = item
        else:
            path = self.getItemPath(item)

        dset = self.h5file[path]

        return dset[:]


    def loadItemData(self, path, attribute=None):
        """
        Load data for the given dataset.
        """
        dset = None
        if attribute is None:
            dset = self.h5file[path]
            self.ui.lblName.setText(path)
        else:
            dset = self.h5file[path].attrs[attribute]
            self.ui.lblName.setText(path + '/attribute')

        self.ui.lblType.setText(str(dset.dtype))
        self.ui.lblShape.setText(str(dset.shape))

        size = dset.size
        sizeidx = 0
        units = ['bytes', 'kiB', 'MiB', 'GiB', 'TiB', 'PiB']
        while size > 1024:
            sizeidx += 1
            size /= 1024
            
        if sizeidx > 0:
            self.ui.lblSize.setText('{:.2f} {}'.format(size, units[sizeidx]))
        else:
            self.ui.lblSize.setText('{:d} {}'.format(size, units[sizeidx]))

        # Only show data that is in the < 1 MiB
        if sizeidx <= 1:
            self.ui.txtData.setPlainText(self.getData(dset[:]))
        else:
            self.ui.txtData.setPlainText('[DATA > 1 MiB]')


    def getItemPath(self, item):
        """
        Returns the HDF5 path for the given item.
        """
        if item == None:
            return ''
        else:
            return self.getItemPath(item.parent()) + '/' + item.text()


    def getSelectedItem(self):
        """
        Returns the currently selected treeview item.
        """
        return self.treeViewModel.itemFromIndex(self.ui.treeView.selectionModel().selectedIndexes()[0])


    def itemSelected(self, newIndex, oldIndex=None):
        """
        Emitted when an item is selected in the TreeView.
        """
        item = self.treeViewModel.itemFromIndex(newIndex.indexes()[0])

        if item.data() == 'attribute':
            path = self.getItemPath(item.parent())
            self.loadItemData(path, item.text())

            self.ui.tbPath.setText(path + '/' + item.text())
        else:
            path = self.getItemPath(item)

            if type(self.h5file[path]) == h5py.Dataset:
                self.loadItemData(path)

            self.ui.tbPath.setText(path)


    def plot(self, x=None, y=None, xname=None, yname=None):
        """
        Plot the given data.
        """
        pw = PlotWindow()
        self.plotWindows.append(pw)

        #print(f'x = {x}')
        #print(f'y = {y}')
        if x is None:
            print(type(y))
            pw.plot(y)
        else:
            pw.plot(x, y)

        if xname:
            pw.set_xlabel(xname)
        if yname:
            pw.set_ylabel(yname)

        pw.show()


    def tvContextMenu(self, position):
        """
        Triggered when a context menu is requested for a TreeView item.
        """
        item = self.getSelectedItem()

        # Only show context menu for datasets (i.e. not groups)
        if item.hasChildren():
            return

        menu = QtWidgets.QMenu()

        if self.itemToPlot is None:
            # Plot this
            actionPlot = menu.addAction("Plot")
            # Plot against other dataset
            actionPlotAgainst = menu.addAction("Plot against...")

            action = menu.exec_(self.ui.treeView.viewport().mapToGlobal(position))

            if action == actionPlot:
                y = self.getDataFromItem(item)
                self.plot(y=y, yname=item.text())
            elif action == actionPlotAgainst:
                self.itemToPlot = self.getItemPath(item)
        else:
            actionPlot = menu.addAction(f"Plot against '{self.itemToPlot.split('/')[-1]}'")
            actionReset = menu.addAction("Reset plotting")

            action = menu.exec_(self.ui.treeView.viewport().mapToGlobal(position))

            if action == actionPlot:
                # TODO
                x = self.getDataFromItem(item)
                y = self.getDataFromItem(self.itemToPlot)
                self.plot(x=x, y=y, xname=item.text(), yname=self.itemToPlot.split('/')[-1])

                self.itemToPlot = None
            elif action == actionReset:
                self.itemToPlot = None


