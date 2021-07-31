# coding=utf-8









class MyMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.setupUi(self)

        # 界面初始化
        self._init_ui()








if __name__ == '__main__':
    app = QApplication(sys.argv)
    my_wnd = MyMainWindow()
    wnd = my_wnd
    my_wnd.show()
    sys.exit(app.exec_())
