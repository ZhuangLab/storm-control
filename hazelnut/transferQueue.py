#!/usr/bin/env python
#
# Handles the transfer queue GUI and also file transfer.
#
# Hazen 08/16
#

import time

from PyQt5 import QtCore, QtGui, QtWidgets


#
# Transfer Queue related.
#
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
    
    def paint(self, painter, option, index):
        tq_item = self.itemFromProxyIndex(index)
        fo_object = tq_item.getFileObject()

        item_rect = option.rect

        painter.setPen(QtGui.QColor(224, 224, 224))
        painter.setBrush(QtGui.QColor(255, 255, 255))
        painter.drawRect(item_rect)
        
        if (tq_item.getStatus() == "in_transfer"):

            # Draw background.
            #color = QtGui.QColor(100, 100, 255)
            #painter.setPen(color)
            #painter.setBrush(color)
            #painter.drawRect(item_rect)

            # Draw progress.
            painter.setPen(QtGui.QColor(224, 224, 224))
            painter.setBrush(QtGui.QColor(30, 144, 255))

            total_divisions = 20
            step = int((1.0/total_divisions) * item_rect.width())
            
            pr_height = item_rect.height()
            pr_left = item_rect.left() + 1
            pr_width = int((1.0/total_divisions) * item_rect.width() - 2)
            pr_top = item_rect.top()

            num_divisions = int(total_divisions * 0.01 * tq_item.getProgress())
            for i in range(num_divisions):
                progress_rect = QtCore.QRect(pr_left + step*i,
                                             pr_top,
                                             pr_width,
                                             pr_height)
            
                painter.drawRoundedRect(progress_rect, 2.0, 2.0)
                        
        #style = option.widget.style()
        #style.drawControl(QtGui.QStyle.CE_ItemViewItem, option, painter, option.widget)

        # Draw text.
        color = QtGui.QColor(0,0,0)
        painter.setPen(color)
        painter.setBrush(color)

        text_rect = QtCore.QRect(item_rect)
        text_rect.setTop(text_rect.top() + 2)
        painter.drawText(text_rect, QtCore.Qt.AlignLeft, " " + fo_object.getPartialPathName())
        painter.drawText(text_rect, QtCore.Qt.AlignRight, fo_object.getMTime().strftime("%c") + " ")

    def sizeHint(self, option, index):
        result = QtWidgets.QStyledItemDelegate.sizeHint(self, option, index)
        result.setHeight(1.4 * result.height())
        return result


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
        self.progress = 0
        self.status = "queued"

    def getFileObject(self):
        return self.file_object

    def getProgress(self):
        return self.progress
    
    def getStatus(self):
        return self.status

    def setProgress(self, progress):
        self.progress = progress
        self.emitDataChanged()
        
    def setStatus(self, status):
        self.status = status
        self.emitDataChanged()

    
class TransferQueueStandardItemModel(QtGui.QStandardItemModel):
    """
    Transfer queue listview model.
    """

    
class TransferQueueMVC(QtWidgets.QListView):
    transferStarted = QtCore.pyqtSignal()
    transferStopped = QtCore.pyqtSignal()
    
    """
    Encapsulates a list view specialized for the transfer file queue and it's associated model.
    """
    def __init__(self, parent = None):
        QtWidgets.QListView.__init__(self, parent)
        self.destination_dir_obj = None
        self.max_threads = 1
        self.running_threads = []
        self.tr_timer = QtCore.QTimer(self)

        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        # Configure transfer timer.
        self.tr_timer.setInterval(100)
        self.tr_timer.timeout.connect(self.handleTrTimer)
        
        # Transfer queue model.
        self.tq_model = TransferQueueStandardItemModel(self)
        self.tq_proxy_model = TransferQueueSortFilterProxyModel(self)
        self.tq_proxy_model.setSourceModel(self.tq_model)
        self.setModel(self.tq_proxy_model)

        # Rendering.
        self.setItemDelegate(TransferQueueListViewDelegate(self.tq_model, self.tq_proxy_model))

    def addDestination(self, dir_obj):
        self.destination_dir_obj = dir_obj
        
    def addFileObject(self, file_object):
        q_item = TransferQueueStandardItem(file_object)
        self.tq_model.appendRow(q_item)
        self.tq_proxy_model.sort(0)

    def amTransferring(self):
        return self.tr_timer.isActive()
    
    def clearFileObjects(self):
        self.tq_model.clear()

    def handleTrTimer(self):
        """
        Create threads for files that need to transferred.
        Files at the top of the queue go first.
        """
        tr_max = self.max_threads - len(self.running_threads)
        if (tr_max > self.tq_model.rowCount()):
            tr_max = self.tq_model.rowCount()
        for i in range(tr_max):
            proxy_index = self.tq_proxy_model.index(i, 0)
            source_index = self.tq_proxy_model.mapToSource(proxy_index)
            source_item = self.tq_model.itemFromIndex(source_index)
            source_item.setStatus("in_transfer")
            tr_thread = TransferThread(self.destination_dir_obj, source_item)
            tr_thread.transferComplete.connect(self.handleTransferComplete)
            tr_thread.transferProgress.connect(self.handleTransferProgress)
            tr_thread.start(QtCore.QThread.NormalPriority)
            self.running_threads.append(tr_thread)

    def handleTransferComplete(self, tr_thread):
        tq_item = tr_thread.getTQItem()
        
        # Remove this from the list of items in the transfer queue.
        source_index = self.tq_model.indexFromItem(tq_item)
        self.tq_model.removeRow(source_index.row())

        # Throw away this thread.
        tr_thread.transferComplete.disconnect()
        tr_thread.transferProgress.disconnect()
        self.running_threads.remove(tr_thread)

        # Check if the timer has stopped and no other threads are running.
        if not self.amTransferring():
            if (len(self.running_threads) == 0):
                self.transferStopped.emit()

    def handleTransferProgress(self, tq_item, progress):
        tq_item.setProgress(progress)
                               
    def setMaxThreads(self, new_max):
        self.max_threads = new_max
        
    def startTransfer(self):
        self.tr_timer.start()
        self.transferStarted.emit()

    def stopTransfer(self):
        self.tr_timer.stop()
        if (len(self.running_threads) == 0):
            self.transferStopped.emit()


#
# Thread class for file transfers.
#
class TransferThread(QtCore.QThread):
    transferComplete = QtCore.pyqtSignal(object)
    transferProgress = QtCore.pyqtSignal(object, int)

    def __init__(self, dir_object, tq_item):
        QtCore.QThread.__init__(self)
        self.dir_object = dir_object
        self.tq_item = tq_item

    def getTQItem(self):
        return self.tq_item
    
    def run(self):
        file_object = self.tq_item.getFileObject()
        if self.dir_object.shouldTransfer(file_object):
            callback = lambda x: self.transferProgress.emit(self.tq_item, x)
            self.dir_object.transferFile(file_object, callback)
        self.transferComplete.emit(self)

