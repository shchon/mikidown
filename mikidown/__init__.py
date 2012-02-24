#!/usr/bin/env python

#from date import Date, Today
import datetime
import os
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import QWebView, QWebPage
from PyQt4.QtWebKit import QGraphicsWebView
from mikidown.config import *

import markdown

md = markdown.Markdown()
__version__ = "0.0.1"

settings = QSettings('mikidown', 'mikidown')

class RecentChanged(QListWidget):
	def __init__(self, parent=None):
		super(RecentChanged, self).__init__(parent)

class RecentViewed(QDialogButtonBox):
	def __init__(self, parent=None):
		super(RecentViewed, self).__init__(Qt.Horizontal, parent)
		sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
		sizePolicy.setVerticalPolicy(QSizePolicy.Fixed)
		self.setSizePolicy(sizePolicy)

		self.addButton('old', QDialogButtonBox.ActionRole)
		self.addButton('new', QDialogButtonBox.ActionRole)
	
	def sizeHint(self):
		return QSize(400, 8)

class MikiTree(QTreeWidget):
	def __init__(self, parent=None):
		super(MikiTree, self).__init__(parent)
		self.header().close()
		self.setAcceptDrops(True)
		self.setDragEnabled(True)
		#self.setDropIndicatorShown(True)
		self.setDragDropOverwriteMode(True)
		self.setDragDropMode(QAbstractItemView.InternalMove)
		#self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.setContextMenuPolicy(Qt.CustomContextMenu)
	
	def getPath(self, item):
		path = ''
		if not hasattr(item, 'text'):
			return path
		item = item.parent()
		while item is not None:
			path = item.text(0) + '/' + path
			item = item.parent()
		return path

	def dropEvent(self, event):
		#event.setDropAction(Qt.MoveAction)
		#event.accept()
		sourceItem = self.currentItem()
		sourcePath = self.getPath(sourceItem)
		targetItem = self.itemAt(event.pos())
		targetPath = self.getPath(targetItem)
		oldName = sourcePath + sourceItem.text(0) + '.markdown'
		newName = targetPath + targetItem.text(0) + '/' + sourceItem.text(0) + '.markdown'
		oldDir = sourcePath + sourceItem.text(0)
		newDir = targetPath + targetItem.text(0) + '/' + sourceItem.text(0)
		if not QDir(newName).exists():
			QDir.current().mkpath(targetPath+targetItem.text(0))
		QDir.current().rename(oldName, newName)
		if sourceItem.childCount() != 0: 
			#if not QDir(newDir).exists():
			#	QDir.current.mkpath(newDir)
			QDir.current().rename(oldDir, newDir)
		if sourceItem.parent() is not None:
			parentItem = sourceItem.parent()
			parentPath = self.getPath(parentItem)
			print(parentPath+parentItem.text(0))
			print(parentItem.childCount())
			if parentItem.childCount() == 1:
				QDir.current().rmdir(parentPath + parentItem.text(0))
		print(oldName)
		print(newName)
		QTreeWidget.dropEvent(self, event)

	#def mouseMoveEvent(self, event):
	#	self.startDrag()
	#	QWidget.mouseMoveEvent(self, event)

	#def mousePressEvent(self, event):
		#self.clearSelection()
	#	QWidget.mousePressEvent(self, event)

class ItemDialog(QDialog):
	def __init__(self, parent=None):

		super(ItemDialog, self).__init__(parent)
		self.editor = QLineEdit()
		editorLabel = QLabel("Page Name:")
		editorLabel.setBuddy(self.editor)
		self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|
										  QDialogButtonBox.Cancel)
		self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
		layout = QGridLayout()
		layout.addWidget(editorLabel, 0, 0)
		layout.addWidget(self.editor, 0, 1)
		layout.addWidget(self.buttonBox, 1, 1)
		self.setLayout(layout)
		self.connect(self.editor, SIGNAL("textEdited(QString)"),
					 self.updateUi)
		self.connect(self.buttonBox, SIGNAL("accepted()"), self.accept)
		self.connect(self.buttonBox, SIGNAL("rejected()"), self.reject)
	def updateUi(self):
		self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(
				self.editor.text()!="")

class MikiWindow(QMainWindow):
	def __init__(self, notebookPath=None, parent=None):
		super(MikiWindow, self).__init__(parent)
		self.resize(800,600)
		screen = QDesktopWidget().screenGeometry()
		size = self.geometry()
		self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)
		
		self.tabWidget = QTabWidget()
		#self.viewedList = RecentViewed()
		self.viewedList = QToolBar(self.tr('Recently Viewed'), self)
		self.notesEdit = QTextEdit()
		#self.notesView = QGraphicsWebView()
		self.notesView = QWebView()
		self.findBar = QToolBar(self.tr('Find'), self)
		self.noteSplitter = QSplitter(Qt.Horizontal)
		self.noteSplitter.addWidget(self.notesEdit)
		self.noteSplitter.addWidget(self.notesView)
		self.notesEdit.setVisible(False)
		self.notesView.settings().clearMemoryCaches()
		self.notesView.settings().setUserStyleSheetUrl(QUrl.fromLocalFile('notes.css'))
		#self.notesView.setReadOnly(True)
		self.rightSplitter = QSplitter(Qt.Vertical)
		self.rightSplitter.addWidget(self.viewedList)
		self.rightSplitter.addWidget(self.noteSplitter)
		self.rightSplitter.addWidget(self.findBar)
		self.mainSplitter = QSplitter(Qt.Horizontal)
		self.mainSplitter.addWidget(self.tabWidget)
		self.mainSplitter.addWidget(self.rightSplitter)
		self.setCentralWidget(self.mainSplitter)
		self.mainSplitter.setStretchFactor(0, 1)
		self.mainSplitter.setStretchFactor(1, 5)
		sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
		sizePolicy.setVerticalPolicy(QSizePolicy.Fixed)
		self.viewedList.setSizePolicy(sizePolicy)

		self.notesTree = MikiTree()
		self.changedList = RecentChanged()
		self.tabWidget.addTab(self.notesTree, 'Index')
		self.tabWidget.addTab(self.changedList, 'Recently Changed')
		print(self.mainSplitter.sizes())
		print(self.rightSplitter.sizes())
		#self.rightSplitter.setSizes([600,20,600,580])
		self.rightSplitter.setStretchFactor(0, 0)

		self.currentItem = lambda: self.notesTree.currentItem()
		self.currentItemPath = lambda: self.getPath(self.currentItem)
		
		self.actionImportPage = self.act(self.tr('Import Page...'), trig=self.importPage)
		#self.actionSave = self.act(self.tr('Save'), trig=lambda item=self.notesTree.currentItem(): self.saveNote(item, item))
		self.actionSave = self.act(self.tr('Save'), shct=QKeySequence.Save, trig=self.saveCurrentNote)
		self.actionSave.setEnabled(False)
		#self.actionSaveAs = self.act(self.tr('Save as'), shct=QKeySequence.SaveAs, trig=self.saveNoteAs)
		self.actionSaveAs = self.act(self.tr('Save As...'), trig=lambda item=self.notesEdit.isVisible(): self.saveNoteAs(item))
		self.actionQuit = self.act(self.tr('Quit'), shct=QKeySequence.Quit)
		#self.connect(self.actionQuit, SIGNAL('triggered()'), qApp, SLOT('close()'))
		self.connect(self.actionQuit, SIGNAL('triggered()'), self, SLOT('close()'))
		self.actionQuit.setMenuRole(QAction.QuitRole)
		self.actionUndo = self.act(self.tr('Undo'), trig=lambda: self.notesEdit.undo())
		self.actionUndo.setEnabled(False)
		self.notesEdit.undoAvailable.connect(self.actionUndo.setEnabled)
		self.menuActionFind = self.act(self.tr('Find Text'), shct=QKeySequence.Find)
		self.menuActionFind.setCheckable(True)
		self.menuActionFind.triggered.connect(self.findBar.setVisible)
		self.menuActionSearch = self.act(self.tr('Search Note...'), )
		self.findBar.visibilityChanged.connect(self.findBarVisibilityChanged)
		self.actionFind = self.act(self.tr('Next'), shct=QKeySequence.FindNext, trig=self.findText)
		self.actionFindPrev = self.act(self.tr('Previous'), shct=QKeySequence.FindPrevious, 
				trig=lambda:self.findText(back=True))
		self.actionSearch = self.act(self.tr('Search'))

		self.menuBar = QMenuBar(self)
		self.setMenuBar(self.menuBar)
		self.menuFile = self.menuBar.addMenu('File')
		self.menuEdit = self.menuBar.addMenu('Edit')
		self.menuSearch = self.menuBar.addMenu('Search')
		self.menuHelp = self.menuBar.addMenu('Help')
		self.menuFile.addAction(self.actionImportPage)
		self.menuFile.addSeparator()
		self.menuFile.addAction(self.actionSave)
		self.menuFile.addAction(self.actionSaveAs)
		self.menuFile.addSeparator()
		self.menuFile.addAction(self.actionQuit)
		self.menuEdit.addAction(self.actionUndo)
		self.menuSearch.addAction(self.menuActionFind)
		self.menuSearch.addAction(self.menuActionSearch)

		self.toolBar = QToolBar(self.tr('toolbar'), self)
		self.addToolBar(Qt.TopToolBarArea, self.toolBar)
		self.actionEdit = self.act('Edit', trigbool=self.edit)
		self.actionLiveView = self.act('Live Edit', trigbool=self.liveView)
		self.toolBar.addAction(self.actionEdit)
		self.toolBar.addAction(self.actionLiveView)
		self.findEdit = QLineEdit(self.findBar)
		#self.findEdit.returnPressed().connect(self.findText)
		self.connect(self.findEdit, SIGNAL('returnPressed()'), self.findText)
		self.checkBox = QCheckBox(self.tr('Match case'), self.findBar)
		self.findBar.addWidget(self.findEdit)
		self.findBar.addWidget(self.checkBox)
		self.findBar.addAction(self.actionFindPrev)
		self.findBar.addAction(self.actionFind)
		self.findBar.setVisible(False)
		
		self.statusBar = QStatusBar(self)
		self.setStatusBar(self.statusBar)		
		
		self.connect(self.notesTree, SIGNAL('customContextMenuRequested(QPoint)'),
				     self.treeMenu)
		'''
		self.connect(self.notesTree, SIGNAL('itemClicked(QTreeWidgetItem *,int)'),
				self.showNote)
		self.connect(self.notesTree, 
					 SIGNAL('currentItemChanged(QTreeWidgetItem*, QTreeWidgetItem*)'),
					 self.saveNote)
		'''
		self.notesTree.currentItemChanged.connect(self.currentItemChangedWrapper)
		self.connect(self.notesEdit,
					 SIGNAL('textChanged()'),
					 self.noteEditted)

		self.notesView.page().linkHovered.connect(self.linkHovered)
		QDir.setCurrent(notebookPath)
		self.initTree(notebookPath, self.notesTree)
		self.updateRecentViewedNotes()
		files = readListFromSettings(settings, 'recentViewedNoteList')
		self.notesTree.setCurrentItem(self.NameToItem(files[0]))
		#self.openNote(files[0])
	def closeEvent(self, event):
		reply = QMessageBox.question(self, 'Message',
				'Are you sure to quit?', 
				QMessageBox.Yes|QMessageBox.No,
				QMessageBox.No)
		if reply == QMessageBox.Yes:
			self.saveCurrentNote()
			event.accept()
		else:
			event.ignore()

	def initTree(self, notePath, parent):
		if not QDir(notePath).exists():
			return
		noteDir = QDir(notePath)
		self.notesList = noteDir.entryInfoList(["*.markdown"],
							   QDir.NoFilter,
							   QDir.Name|QDir.IgnoreCase)
		for note in self.notesList:
			item = QTreeWidgetItem(parent, [note.baseName()])
			path = self.tr(notePath + '/' + note.baseName())
			self.initTree(path, item)
		self.editted = 0

	def ItemToName(self, noteItem):
		pass
	def NameToItem(self, noteName):
		splitPath = noteName.split('/')
		depth = len(splitPath)
		itemList = self.notesTree.findItems(splitPath[depth-1], Qt.MatchExactly)
		if len(itemList) == 1:
			return itemList[0]

		for item in itemList:
			parent = item.parent()
			for i in range(depth):
				if parent == None:
					break
				if depth-i-2 < 0:
					break
				if parent.text(0) == splitPath[depth-i-2]:
					if depth-i-2 == 0:
						return item
					else:
						parent = parent.parent()

	def currentItemChangedWrapper(self, current, previous):
		self.saveNote(current, previous)
		self.showNote(current)

	def getPath(self, item):
		path = ''
		if not hasattr(item, 'text'):
			return path
		item = item.parent()
		while item is not None:
			path = item.text(0) + '/' + path
			item = item.parent()
		return path

	def saveCurrentNote(self):
		item = self.notesTree.currentItem()
		self.saveNote(None, item)
		path = self.getPath(item)
		if hasattr(item, 'text'):
			self.statusBar.showMessage(path + item.text(0))

	def saveNote(self, current, previous):
		if previous is None:
			return
		if self.editted == 0:
			return
		self.editted = 1
		self.filename = previous.text(0)+".markdown"
		self.path = self.getPath(previous)
		print(self.path)
		fh = QFile(self.path + self.filename)
		try:
			if not fh.open(QIODevice.WriteOnly):
				raise IOError(fh.errorString())
		except IOError as e:
			QMessageBox.warning(self, "Save Error",
						"Failed to save %s: %s" % (self.filename, e))
		finally:
			if fh is not None:
				savestream = QTextStream(fh)
				savestream << self.notesEdit.toPlainText()
				fh.close()
				self.actionSave.setEnabled(False)
				self.updateView()
	
	def saveNoteAs(self, test):
		filename = QFileDialog.getSaveFileName(self, self.tr('Save as'), '',
				'(*.markdown *.mkd *.md);;'+self.tr('All files(*)'))
		if filename == '':
			return
		fh = QFile(filename)
		fh.open(QIODevice.WriteOnly)
		savestream = QTextStream(fh)
		savestream << self.notesEdit.toPlainText()
		fh.close()

	def noteEditted(self):
		self.editted = 1
		self.updateLiveView()
		item = self.notesTree.currentItem()
		path = self.getPath(item)
		self.actionSave.setEnabled(True)
		self.statusBar.showMessage(path + item.text(0) + '*')

	def treeMenu(self):
		menu = QMenu()
		menu.addAction("New Page", self.newPage)
		self.subpageCallback = lambda item=self.notesTree.currentItem(): self.newSubpage(item)
		menu.addAction("New Subpage", self.subpageCallback)
		menu.addSeparator()
		menu.addAction("Collapse All", self.collapseAll)
		menu.addAction("Uncollapse All", self.uncollapseAll)
		menu.addSeparator()
		menu.addAction('Rename Page', lambda item=self.notesTree.currentItem(): self.renamePage(item))
		self.delCallback = lambda item=self.notesTree.currentItem(): self.delPage(item)
		menu.addAction("Delete Page", self.delCallback)
		menu.exec_(QCursor.pos())
	
	def newPage(self):
		parent = self.notesTree.currentItem().parent()
		#parent = self.currentItem.parent()
		if parent is not None:
			self.newSubpage(parent)
		else:
			self.newSubpage(self.notesTree)

	def newSubpage(self, item):
		dialog = ItemDialog(self)
		if dialog.exec_():
			self.filename = dialog.editor.text()
			self.newPageWrapper(item, self.filename)
			self.notesTree.sortItems(0, Qt.AscendingOrder)
			
		self.editted = 0
	def newPageWrapper(self, item, pageName):
		pagePath = self.getPath(item)
		if hasattr(item, 'text'):
			pagePath = pagePath + item.text(0) + '/'
		if not QDir(pagePath).exists():
			QDir.current().mkdir(pagePath)
		fh = QFile(pagePath+pageName+'.markdown')
		print(pagePath + pageName)
		fh.open(QIODevice.WriteOnly)
		savestream = QTextStream(fh)
		savestream << '# ' + pageName + '\n'
		savestream << 'Created ' + str(datetime.date.today()) + '\n\n'
		fh.close()
		QTreeWidgetItem(item, [pageName])
		if pagePath != '':
			self.notesTree.expandItem(item)

	def importPage(self):
		filename = QFileDialog.getOpenFileName(self, self.tr('Import file'), '',
				'(*.markdown *.mkd *.md *.txt);;'+self.tr('All files(*)'))
		if filename == '':
			return
		fh = QFile(filename)
		fh.open(QIODevice.ReadOnly)
		fileBody = QTextStream(fh).readAll()
		fh.close()
		note = QFileInfo(filename)
		fh = QFile(note.baseName()+'.markdown')
		fh.open(QIODevice.WriteOnly)
		savestream = QTextStream(fh)
		savestream << fileBody
		fh.close()
		QTreeWidgetItem(self.notesTree, [note.baseName()])

	def renamePage(self, item):
		dialog = ItemDialog(self)
		if dialog.exec_():
			pageName = dialog.editor.text()
			pagePath = self.getPath(item)
			oldName = pagePath + item.text(0) + '.markdown'
			newName = pagePath + pageName + '.markdown'
			QDir.current().rename(oldName, newName)
			if item.childCount() != 0:
				oldDir = pagePath + item.text(0)
				newDir = pagePath + pageName
				QDir.current().rename(oldDir, newDir)
			item.setText(0, pageName)
			self.notesTree.sortItems(0, Qt.AscendingOrder)


	def delPage(self, item):
		index = item.childCount()
		while index > 0:
			index = index -1
			self.dirname = item.child(index).text(0)
			self.delPage(item.child(index))

		path = self.getPath(item)
		QDir.current().remove(path + item.text(0) + '.markdown')
		parent = item.parent()
		if parent is not None:
			index = parent.indexOfChild(item)
			parent.takeChild(index)
			if parent.childCount() == 0:
				QDir.current().rmdir(path)
		else:
			index = self.notesTree.indexOfTopLevelItem(item)
			self.notesTree.takeTopLevelItem(index)	
		self.showNote(self.notesTree.currentItem())
		QDir.current().rmdir(path + item.text(0))

	def collapseAll(self):
		self.notesTree.collapseAll()

	def uncollapseAll(self):
		self.notesTree.expandAll()

	def showNote(self, noteItem):
		self.path = self.getPath(self.notesTree.currentItem())
		noteFullName = self.path + noteItem.text(0)

		self.openNote(noteFullName)
		self.setCurrentFile()
		self.updateRecentViewedNotes()
		'''
		self.filename = noteItem.text(0)+".markdown"
		fh = QFile(self.path + self.filename)
		try:
			if not fh.open(QIODevice.ReadWrite):
				raise IOError(fh.errorString())
		except IOError as e:
			QMessageBox.warning(self, "Read Error",
					"Failed to open %s: %s" % (self.filename, e))
		finally:
			if fh is not None:
				noteBody = QTextStream(fh).readAll()
				fh.close()
		self.notesEdit.setPlainText(noteBody)
		self.editted = 0
		self.updateView()
		self.statusBar.showMessage(self.path + noteItem.text(0))
		'''

	def act(self, name, icon=None, trig=None, trigbool=None, shct=None):
		if icon:
			action = QAction(self.actIcon(icon), name, self)
		else:
			action = QAction(name, self)
		if trig:
			self.connect(action, SIGNAL('triggered()'), trig)
		elif trigbool:
			action.setCheckable(True)
			self.connect(action, SIGNAL('triggered(bool)'), trigbool)
		if shct:
			action.setShortcut(shct)
		return action

	def edit(self, viewmode):
		if self.actionLiveView.isChecked():
			self.actionLiveView.setChecked(False)
		self.saveCurrentNote()
		self.notesView.setVisible(not viewmode)
		self.notesEdit.setVisible(viewmode)

	def liveView(self, viewmode):
		if self.actionEdit.isChecked():
			self.actionEdit.setChecked(False)
			self.notesView.setVisible(viewmode)
		else:
			self.notesEdit.setVisible(viewmode)
		self.updateView()

	def updateView(self):
		self.notesView.setHtml(self.parseText())

	def updateLiveView(self):
		if self.actionLiveView.isChecked():
			QTimer.singleShot(1000, self.updateView)

	def parseText(self):
		htmltext = self.notesEdit.toPlainText()
		return md.convert(htmltext)

	def getFullPath(self):
		item = self.notesTree.currentItem()
		path = self.getPath(item)
		return path + item.text(0)

	def linkHovered(self, link, title, textContent):
		if link == '':
			self.statusBar.showMessage(self.getFullPath())
		else:
			self.statusBar.showMessage(link)

	def findBarVisibilityChanged(self, visible):
		self.menuActionFind.setChecked(visible)
		if visible:
			self.findEdit.setFocus(Qt.ShortcutFocusReason)

	def findText(self, back=False):
		flags = 0
		if back:
			flags = QTextDocument.FindBackward
		if self.checkBox.isChecked():
			flags = flags | QTextDocument.FindCaseSensitively
		text = self.findEdit.text()
		if not self.findMain(text, flags):
			if text in self.notesEdit.toPlainText():
				cursor = self.notesEdit.textCursor()
				if back:
					cursor.movePosition(QTextCursor.End)
				else:
					cursor.movePosition(QTextCursor.Start)
				self.notesEdit.setTextCursor(cursor)
				self.findMain(text, flags)
		#self.notesView.findText(text, flags)

	def findMain(self, text, flags):
		viewFlags = QWebPage.FindFlags(flags) | QWebPage.FindWrapsAroundDocument
		if flags:
			self.notesView.findText(text, viewFlags)
			return self.notesEdit.find(text, flags)
		else:
			self.notesView.findText(text)			
			return self.notesEdit.find(text)
	
	def setCurrentFile(self):
		noteItem = self.notesTree.currentItem()
		notePath = self.getPath(noteItem)
		noteFullName = notePath + noteItem.text(0)
		files = readListFromSettings(settings, 'recentViewedNoteList')
		for f in files:
			if f == noteFullName:
				files.remove(f)
		files.insert(0, notePath+noteItem.text(0))
		if len(files) > 10:
			del files[10:]
		writeListToSettings(settings, 'recentViewedNoteList', files)
	
	def updateRecentViewedNotes(self):
		self.viewedList.clear()
		viewedListActions = []
		filesOld = readListFromSettings(settings, 'recentViewedNoteList')
		files = []
		for f in filesOld:
			if self.existsNote(f):
				files.append(f)
				viewedListActions.append(self.act(f, trig=self.openFunction(f)))
		writeListToSettings(settings, 'recentViewedNoteList', files)
		for action in viewedListActions:
			self.viewedList.addAction(action)
	
	def existsNote(self, noteFullname):
		filename = noteFullname + '.markdown'
		fh = QFile(filename)
		return fh.exists()

	def openFunction(self, noteFullName):
		return lambda: self.openNote(noteFullName)

	def openNote(self, noteFullName):
		filename = noteFullName + '.markdown'
		fh = QFile(filename)
		try:
			if not fh.open(QIODevice.ReadOnly):
				raise IOError(fh.errorString())
		except IOError as e:
			QMessageBox.warning(self, 'Read Error', 
					'Failed to open %s: %s' % (filename, e))
		finally:
			if fh is not None:
				noteBody = QTextStream(fh).readAll()
				fh.close()
				self.notesEdit.setPlainText(noteBody)
				self.editted = 0
				self.updateView()
				self.statusBar.showMessage(noteFullName)
				
def main():
	app = QApplication(sys.argv)
	XDG_CONFIG_HOME = os.environ['XDG_CONFIG_HOME']
	config_dir = XDG_CONFIG_HOME + '/mikidown/'
	config_file = config_dir + 'notebooks.list'
	print(config_file)
	if not os.path.isfile(config_file):
		NotebookList.create()
	fh = QFile(config_file)
	fh.open(QIODevice.ReadOnly)
	notebookInfo = QTextStream(fh).readAll()

	notebookDir = notebookInfo.split(' ')[1]
	print(notebookDir)
	#NotebookList.read()
	window = MikiWindow(notebookDir)
	window.show()
	#NotebookList.create()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
