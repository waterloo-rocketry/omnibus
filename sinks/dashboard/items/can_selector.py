
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import os


from .parsley_instance import PARSLEY_INSTANCE
 
class CanSelectorWindow(object):
    def __init__(self, streamList):
        self.streamList = streamList
        self.PARSLEY_INSTANCE = PARSLEY_INSTANCE
        self.index = 0
        
        
    def render_buttons(self):
        _translate = QtCore.QCoreApplication.translate
        for i in range(len(self.streamList)):
            # rendering itterating through buttons
            self.index = i
            self.radioButton = QtWidgets.QRadioButton(self.centralwidget)
            self.radioButton.setGeometry(QtCore.QRect(80, 120 + (i*30), 380, 20))
            # adding signal and slot
            self.radioButton.clicked.connect(lambda checked, name=self.streamList[i]: self.radioselected(checked, name))

            self.radioButton.setText(_translate("MainWindow", f'{self.streamList[i]}'))
            
            if i == len(self.streamList) -1:
                self.noneButton = QtWidgets.QRadioButton(self.centralwidget)
                self.noneButton.setGeometry(QtCore.QRect(80, 120 + ((i+1)*30), 380, 20))
                self.noneButton.clicked.connect(lambda checked, name='None': self.radioselected(checked, name))
                self.noneButton.setText(_translate("MainWindow", 'None'))
        
            
        
        
        
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(466, 299)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
      
        self.render_buttons()
         
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(70, 90, 325, 20))
        MainWindow.setCentralWidget(self.centralwidget)
 
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
     
    def radioselected(self, selected, name):
        if selected:
            self.label.setText("Select an instance of parsley to communicate to:")
            PARSLEY_INSTANCE = name
            print(PARSLEY_INSTANCE)
            
            
             
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
 
        MainWindow.setWindowTitle(_translate("MainWindow", "Instance of Parsley"))
      
        #self.render_button_names()
        self.label.setText(_translate("MainWindow", "Select an instance of parsley to communicate to:"))
        
 
# Driver Code
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
   
    MainWindow = QtWidgets.QMainWindow()
    ui = CanSelectorWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())