#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget, QLayout
try:
    import Queue as queue
except ImportError:
    import queue
from db import CommandSession

DELETE_COMMAND = {
    "code":""
}

session = CommandSession()

class Command(QWidget):

    def __init__(self, parent=None):
        super(Command, self).__init__(parent)
        self.setWindowIcon(QIcon('./images/icon.png'))
        self.setAutoFillBackground(True)

        # categoryLable = QLabel("Category:")
        # categoryLable.setAlignment(Qt.AlignRight)
        # self.categoryText = QComboBox()
        # self.categoryText.addItem("all")

        nameLabel = QLabel("Search:")
        nameLabel.setAlignment(Qt.AlignRight)
        self.nameLine = QLineEdit(self)
        self.nameLine.setPlaceholderText("开始搜索")
        self.nameLine.setFocus()

        commandLabel = QLabel("command:")
        commandLabel.setAlignment(Qt.AlignRight)
        self.commandText = QTextEdit()
        self.commandText.setStyleSheet("font-size: 12px")
        # self.commandText.setStyleSheet("background:transparent")
        self.commandText.setReadOnly(True)

        descriptionLabel = QLabel("description:")
        descriptionLabel.setAlignment(Qt.AlignRight)
        self.descriptionText = QTextEdit()
        self.descriptionText.setStyleSheet("font-size: 12px")
        self.descriptionText.setReadOnly(True)
        # self.descriptionText.setStyleSheet("background:transparent;border-width:0;border-style:outset")

        self.consoleText = QLineEdit()
        self.consoleText.setReadOnly(True)
        self.consoleText.setStyleSheet("background:transparent;border-width:0;border-style:outset; font-size:11px;")

        self.consoleState = 0

        self.findButton = QPushButton("&Find")
        self.findButton.setEnabled(True)
        # self.findButton.setStyleSheet("QPushButton{background-color:#333}")
        self.addButton = QPushButton("&Add")
        self.findButton.setEnabled(True)
        self.editButton = QPushButton("&Edit")
        self.editButton.setEnabled(False)
        self.removeButton = QPushButton("&Remove")
        self.removeButton.setEnabled(False)

        self.nextButton = QPushButton("&Next")
        self.nextButton.setEnabled(False)
        self.previousButton = QPushButton("&Previous")
        self.previousButton.setEnabled(False)

        buttonLayout1 = QVBoxLayout()
        buttonLayout1.addWidget(self.findButton)
        buttonLayout1.addWidget(self.addButton)
        buttonLayout1.addWidget(self.editButton)
        buttonLayout1.addWidget(self.removeButton)
        buttonLayout1.addStretch()

        buttonLayout2 = QHBoxLayout()
        buttonLayout2.addWidget(self.previousButton)
        buttonLayout2.addWidget(self.nextButton)

        gridLayout1 = QGridLayout()
        gridLayout1.addWidget(nameLabel, 0, 0, Qt.AlignVCenter)
        gridLayout1.addWidget(self.nameLine, 0, 1)
        gridLayout1.addWidget(commandLabel, 1, 0, Qt.AlignTop)
        gridLayout1.addWidget(self.commandText, 1, 1)
        gridLayout1.addWidget(descriptionLabel, 2, 0, Qt.AlignTop)
        gridLayout1.addWidget(self.descriptionText, 2, 1)
        gridLayout1.addLayout(buttonLayout2, 3, 1)

        gridLayout2 = QGridLayout()
        gridLayout2.addLayout(gridLayout1, 0, 0)
        gridLayout2.addLayout(buttonLayout1, 0, 1)

        gridLayout3 = QGridLayout()
        gridLayout3.addLayout(gridLayout2, 0, 0)
        gridLayout3.addWidget(self.consoleText, 1, 0)

        mainLayout = QGridLayout()
        mainLayout.addLayout(gridLayout3, 0, 0)

        self.setLayout(mainLayout)
        self.setWindowTitle("Command Search v1.0")
        self.resize(650, 550)

        self.worker = Worker()
        self.worker.start()
        self.worker.signal.connect(self.display)

        self.addDialog = AddDialog(self)
        self.addDialog.add_signal.connect(self.addDialogCallBack)

        self.editDialog = EditDialog(self)
        self.editDialog.edit_signal.connect(self.editDialogCallBack)

        self.nameLine.returnPressed.connect(self.findContact)
        self.addButton.clicked.connect(self.addContact)
        self.findButton.clicked.connect(self.findContact)
        self.editButton.clicked.connect(self.editContact)
        self.removeButton.clicked.connect(self.removeContact)
        self.nextButton.clicked.connect(lambda: self.next(1))
        self.previousButton.clicked.connect(lambda: self.previous(-1))

        self.prepare_command()

    def prepare_command(self):
        self.consoleText.setText("正在获取数据...")
        self.all_command = list(session.getAllCommand())
        self.current_command = {}
        self.consoleText.setText("总共 {} 条数据.".format(len(self.all_command)))

    def display(self, result, **kws):
        if isinstance(result, FindResult):
            self.result = result
            self.findButton.setEnabled(True)
            if result.is_success:
                if not result.empty():
                    self.showResult(self.all_command[result.first()])
                    self.editButton.setEnabled(True)
                    self.removeButton.setEnabled(True)
                    self.previousButton.setEnabled(True)
                    self.nextButton.setEnabled(True)
                self.consoleText.setText("搜索到 {} 条数据！".format(len(result.data)))
                self.showMessageBox(self, result.onSuccess())
            else:
                self.showMessageBox(self, result.onError())

        elif isinstance(result, InsertResult):
            if result.is_success:
                self.all_command.append(result.data)
                self.consoleText.setText("数据插入成功 ！")
                self.showMessageBox(self.addDialog, result.onSuccess())
            else:
                self.showMessageBox(self.addDialog, result.onError())

        elif isinstance(result, UpdateResult):
            if result.is_success:
                self.current_command.update(result.data)
                self.all_command[self.result.loc_in_all_command] = self.current_command
                self.showResult(self.current_command)
                self.consoleText.setText("数据更新成功 ！")
                self.showMessageBox(self.editDialog, result.onSuccess())
            else:
                self.showMessageBox(self.editDialog, result.onError())

        elif isinstance(result, DeleteResult):
            if result.is_success:
                self.all_command[self.result.loc_in_all_command] = DELETE_COMMAND
                if self.result.remove():
                    self.commandText.clear()
                    self.descriptionText.clear()
                    self.previousButton.setEnabled(False)
                    self.nextButton.setEnabled(False)
                    self.editButton.setEnabled(False)
                    self.removeButton.setEnabled(False)
                    self.nameLine.setFocus()
                else:
                    self.next(0)
                self.consoleText.setText("删除成功, 但仍在本地缓存中，作为占位符")
                self.showMessageBox(self, result.onSuccess())
            else:
                self.showMessageBox(self, result.onError())
        else:
            self.showMessageBox(self, self.onError())

    @staticmethod
    def showMessageBox(parent, msg, title="tip"):
        QMessageBox.information(parent, title, msg)

    def showResult(self, row):
        self.current_command = row
        self.commandText.setText(self.current_command["code"])
        self.descriptionText.setText(self.current_command["description"])

    def onError(self):
        return "something is wrong !"

    def next(self, offset=1):
        self.showResult(self.all_command[self.result.scroll(offset)])

    def previous(self, offset=-1):
        self.showResult(self.all_command[self.result.scroll(offset)])

    def findContact(self):
        self.searchText = self.nameLine.text()
        if not self.searchText:
            QMessageBox.information(self, "Empty",
                    "Please input something.")
            return
        self.consoleText.setText("正在搜索: {}".format(self.searchText))
        self.worker.putTask(WorkItem(parent=self, data=self.searchText, type="find"))
        self.findButton.setEnabled(False)
        self.removeButton.setEnabled(False)
        self.previousButton.setEnabled(False)
        self.nextButton.setEnabled(False)

    def addContact(self):
        self.addDialog.show()

    def editContact(self):
        self.editDialog.show()
        self.editDialog.commandEdit.setPlainText(self.current_command["code"])
        self.editDialog.descriptionEdit.setPlainText(self.current_command["description"])
        self.editDialog.authorLine.setText(self.current_command["author"])
        self.editDialog.categoryLine.setText(self.current_command["category"])

    def removeContact(self):
        ret = QMessageBox.warning(self,"delete","are you sure？", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.No:
            return
        self.worker.putTask(WorkItem(parent=self, data=self.current_command, type="delete"))

    def addDialogCallBack(self, kws):
        self.worker.putTask(WorkItem(parent=self, data=kws, type="insert"))

    def editDialogCallBack(self, kws):
        self.worker.putTask(WorkItem(parent=self, data=kws, type="update"))


class CustomDialog(QDialog):
    def __init__(self, parent=None):
        super(CustomDialog, self).__init__(parent)

        commandLabel = QLabel("Command")
        commandLabel.setAlignment(Qt.AlignRight)
        self.commandEdit = QTextEdit()
        self.commandEdit.setStyleSheet("font-size: 12px")

        descriptionLabel = QLabel("description")
        descriptionLabel.setAlignment(Qt.AlignRight)
        self.descriptionEdit = QTextEdit()
        self.descriptionEdit.setStyleSheet("font-size: 12px")

        authorLabel = QLabel("Author")
        authorLabel.setAlignment(Qt.AlignRight)
        self.authorLine = QLineEdit()
        self.authorLine.setText("admin")

        categoryLabel = QLabel("Category")
        categoryLabel.setAlignment(Qt.AlignRight)
        self.categoryLine = QLineEdit()

        self.submitButton = QPushButton("&Submit")

        gridLayout = QGridLayout()
        gridLayout.addWidget(commandLabel, 0, 0, Qt.AlignTop)
        gridLayout.addWidget(self.commandEdit, 0, 1)
        gridLayout.addWidget(descriptionLabel, 1, 0, Qt.AlignTop)
        gridLayout.addWidget(self.descriptionEdit, 1, 1)
        gridLayout.addWidget(authorLabel, 2, 0, Qt.AlignVCenter)
        gridLayout.addWidget(self.authorLine, 2, 1)
        gridLayout.addWidget(categoryLabel, 3, 0, Qt.AlignVCenter)
        gridLayout.addWidget(self.categoryLine, 3, 1)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.submitButton)

        mainLayout = QGridLayout()
        mainLayout.addLayout(gridLayout, 0, 0)
        mainLayout.addLayout(buttonLayout, 0, 1, Qt.AlignBottom)

        self.setLayout(mainLayout)
        self.resize(550, 380)

        self.submitButton.clicked.connect(self.submitContact)

    def submitContact(self):
        pass

    def reset(self):
        self.commandEdit.clear()
        self.descriptionEdit.clear()

    def check(self):
        if not self.command:
            QMessageBox.information(self, "Empty Field",
                    "Please input command.")
            return False

        if not self.description:
            QMessageBox.information(self, "Empty Field",
                    "Please input description.")
            return False

        if not self.author:
            QMessageBox.information(self, "Empty Field",
                    "Please input author.")
            return False

        if not self.category:
            QMessageBox.information(self, "Empty Field",
                    "Please input category.")
            return False
        return True

class AddDialog(CustomDialog):

    add_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(AddDialog, self).__init__(parent)
        self.setWindowTitle("Add Command")

    def submitContact(self):
        self.command = self.commandEdit.toPlainText()
        self.description = self.descriptionEdit.toPlainText()
        self.author = self.authorLine.text()
        self.category = self.categoryLine.text()
        if self.check():
            self.add_signal.emit(dict(code=self.command,description=self.description,author=self.author, category=self.category))

class EditDialog(CustomDialog):

    edit_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(EditDialog, self).__init__(parent)
        self.setWindowTitle("Edit Command")

    def submitContact(self):
        self.command = self.commandEdit.toPlainText()
        self.description = self.descriptionEdit.toPlainText()
        self.author = self.authorLine.text()
        self.category = self.categoryLine.text()
        if self.check():
            self.edit_signal.emit(dict(code=self.command,description=self.description,author=self.author, category=self.category))

class Result(object):

    def __init__(self, data=None, is_success=None):
        self.data = data
        self.is_success = is_success

    def onSuccess(self, msg="Sucess !"):
        return msg

    def onError(self):
        return self.data

class FindResult(Result):

    def __init__(self,data=None, is_success=None):
        self.count = 0
        self.rownumber = 0
        super().__init__(data=data, is_success=is_success)

    def first(self):
        return self.data[0]

    def scroll(self, offset):
        self.count += offset
        self.rownumber = self.data[self.count % (len(self.data))]
        return self.rownumber

    def remove(self):
        self.count = self.rownumber
        self.data.remove(self.rownumber)
        return self.empty()

    def empty(self):
        return len(self.data) == 0

    @property
    def loc_in_all_command(self):
        return self.rownumber

    def onSuccess(self):
        return "搜索到 {} 条数据！".format(len(self.data))

class InsertResult(Result):

    def __init__(self,data=None, is_success=None):
        super().__init__(data=data, is_success=is_success)


class UpdateResult(Result):

    def __init__(self,data=None, is_success=None):
        super().__init__(data=data, is_success=is_success)


class DeleteResult(Result):

    def __init__(self,data=None, is_success=None):
        super().__init__(data=data, is_success=is_success)


class WorkItem(object):

    def __init__(self, parent, data, type):
        self.parent = parent
        self.data = data
        self.type = type

    def run(self):
        if self.type == "find":
            ret = []
            for idx, item in enumerate(self.parent.all_command):
                try:
                    if item["code"] and self.data.lower() in item["code"].lower():
                        ret.append(idx)
                except Exception as e:
                    return FindResult(str(e), is_success=False)
            return FindResult(ret, is_success=True)

        elif self.type == "insert":
            try:
                lastrowid = session.insertCommand(**self.data)
            except Exception as e:
                return InsertResult(str(e), is_success=False)
            return InsertResult(session.select_by_id(id=lastrowid), is_success=True)

        elif self.type == "update":
            try:
                session.updateCommand(id=self.parent.current_command["id"], **self.data)
            except Exception as e:
                return UpdateResult(str(e), is_success=False)
            return UpdateResult(self.data, is_success=True)

        elif self.type == "delete":
            try:
                session.deleteCommand(id=self.parent.current_command["id"])
            except Exception as e:
                return DeleteResult(str(e), is_success=False)
            return DeleteResult(self.data, is_success=True)

class Worker(QThread):

    signal = pyqtSignal(object)

    def __init__(self, parent=None, max_workers=5):
        super().__init__(parent)
        self.work_queue = queue.Queue()
        self.is_running = 1

    def putTask(self, workItem):
        self.work_queue.put(workItem)

    def getTask(self):
        return self.work_queue.get()

    def work(self, workItem):
        try:
            ret = workItem.run()
            return ret
        except Exception as e:
            return e
        else:
            return "empty"

    def emit(self, result):
        self.signal.emit(result)

    def run(self):
        while self.is_running:
            try:
                workItem = self.getTask()
            except queue.Empty:
                continue
            result = self.work(workItem)
            self.emit(result)

        self.signal.emit("worker close !")
        self.quit()


    def __del__(self):
        self.wait()


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    mainWindow = Command()
    mainWindow.show()
    sys.exit(app.exec_())
