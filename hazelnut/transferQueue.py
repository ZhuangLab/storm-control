#!/usr/bin/env python
#
# Handles the transfer queue GUI and also file transfer.
#
# Hazen 08/16
#

from PyQt5 import QtCore, QtGui, QtWidgets


class TransferQueueListViewDelegate(QtWidgets.QStyledItemDelegate):
    """
    A custom look for each item, mostly so that we include a progress bar.
    """
    def __init__(self, model, proxy_model):
        QtWidgets.QStyledItemDelegate.__init__(self)
        self.model = model
        self.proxy_model = proxy_model

    def itemFromProxyIndex(self, proxy_index):
        source_index = self.proxy_model.mapToSource(proxy_index)
        return self.model.itemFromIndex(source_index)
    

class TransferQueueSortFilterProxyModel(QtCore.QSortFilterProxyModel):
    """
    Sort items in the queue.
    """
    def lessThan(self, left, right):
        left_file_obj = self.sourceModel().itemFromIndex(left).getFileObject()
        right_file_obj = self.sourceModel().itemFromIndex(right).getFileObject()
        return (left_file_obj.mtime < right_file_obj.mtime)
    

class TransferQueueStandardItem(QtGui.QStandardItem):
    """
    A single file object to be transferred.
    """
    def __init__(self, file_object):
        QtGui.QStandardItem.__init__(self, file_object.__str__())
        self.file_object = file_object

    def getFileObject(self):
        return self.file_object
    
    
class TransferQueueStandardItemModel(QtGui.QStandardItemModel):
    """
    Transfer queue listview model.
    """

    
class TransferQueueMVC(QtWidgets.QListView):
    """
    Encapsulates a list view specialized for the transfer file queue and it's associated model.
    """
    def __init__(self, parent = None):
        QtWidgets.QListView.__init__(self, parent)

        # Transfer queue model.
        self.tq_model = TransferQueueStandardItemModel(self)
        self.tq_proxy_model = TransferQueueSortFilterProxyModel(self)
        self.tq_proxy_model.setSourceModel(self.tq_model)
        self.setModel(self.tq_proxy_model)

        # Rendering.
        self.setItemDelegate(TransferQueueListViewDelegate(self.tq_model, self.tq_proxy_model))

    def addFileObject(self, file_object):
        q_item = TransferQueueStandardItem(file_object)
        self.tq_model.appendRow(q_item)
        self.tq_proxy_model.sort(0)

    def removeFileObject(self, file_object):
        pass
    

