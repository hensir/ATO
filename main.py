"""
大华提供了抓图功能 然后windows自带的画图功能 可问题依然是时间调整 成功了 这个视频是个video 或者 dav的一秒视频 切帧 360的ie内核有点问题 卡
换成ie 大华的抓图命名是时间 到时候控制文件夹 文件名称对比单号右边第二列时间数据就能确认了 当然这是精确到秒的 webkit 不能抓图   不能截取视频
抓图还好 视频就太大了 所以全部都用trident 不一定 老ie没currenttime 没法跳时间 chrome改改还能用
webkit中video怎么跳时间那个canvas倒是一直在动 只有ie9+才支持video标签
"""
import sys
import os
from PyQt5.QtCore import QDir, pyqtSlot, Qt, QPoint
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem, QAbstractItemView
from UI_MainWindow import Ui_MainWindow
from function import handle_excel, export_excel
# from PyQt5.Qt import Itemis


# TODO 安全措施
# TODO IP是否输入 账号 密码  初始化列表 导入现在这个表 然后做修改代理 视频通道全取默认通道 截屏方式默认 秒数直接

class QmyMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)  # 调用父类构造函数，创建窗体

        self.ui = Ui_MainWindow()  # 创建UI对象
        self.ui.setupUi(self)  # 构造UI界面
        # 信号绑定 内建信号手动绑定内建槽函数
        self.ui.pB1.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(0))  # 按钮跳转层叠界面
        # self.ui.pB2.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex())
        self.ui.pB2.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(1))
        # self.ui.pB4.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(3))
        # 声明实例变量
        self._excelFileAddress = ""  # TODO 这里也可以把FL给添加到selfinit里
        # 优化改动UI
        self.ui.excelTW.setAlternatingRowColors(True)  # 交替行颜色
        self.ui.channelListTW.setAlternatingRowColors(True)  # 交替行颜色
        self.ui.shipHandleTW.setAlternatingRowColors(True)
        self.ui.excelTW.horizontalHeader().setVisible(True)  # 列头可见
        self.ui.excelTW.verticalHeader().setVisible(True)  # 行头可见
        self.ui.excelTW.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 默认不允许编辑

    # 类方法 内部要用的方法
    def GetExcelTWValue(self):
        # 获取并返回ExcelTW表格组件的所有数据
        rowcount = self.ui.excelTW.rowCount()
        columncount = self.ui.excelTW.columnCount()  # 总行数 总列数
        tablewidgetvalue = [[] for i in range(rowcount)]  # 创建二维列表空间
        for row in range(rowcount):
            for column in range(columncount):  # 循环坐标取值
                tablewidgetvalue[row].append(self.ui.excelTW.item(row, column).text())
        print(tablewidgetvalue)
        return tablewidgetvalue

    def GetShipHandleTWValue(self):
        # 获取并返回shiphandleTW表格组件的所有数据
        # TODO 范围调整一下
        rowcount = self.ui.shipHandleTW.rowCount()
        columncount = self.ui.shipHandleTW.columnCount()  # 总行数 总列数
        tablewidgetvalue = [[] for i in range(rowcount)]  # 创建二维列表空间
        for row in range(rowcount):
            for column in range(columncount):  # 循环坐标取值
                tablewidgetvalue[row].append(self.ui.shipHandleTW.item(row, column).text())
        print(tablewidgetvalue)
        return tablewidgetvalue

    # 通过内建信号自动连接信号的槽函数
    @pyqtSlot()
    def on_getfilePB_clicked(self):
        """选择文件按钮"""
        # ------获取文件名---------
        curPath = os.path.join(os.path.expanduser("~"), 'Desktop')
        dlgTitle = "请选择要处理的Excel"
        filt = "文档(*.xlsx);;所有(*.*)"
        filelist, filtUsed = QFileDialog.getOpenFileNames(self, dlgTitle, curPath, filt)
        # ------检测用户有没有选---------
        if filelist:
            if len(filelist) >= 2:
                QMessageBox.warning(self, "警告", "请选择单个文件进行处理")
                return
            self._excelFileAddress = filelist[0]
        self.ui.EFLineEdit.setText(self._excelFileAddress)

    @pyqtSlot()
    def on_handlePB_clicked(self):
        if self._excelFileAddress:  # 地址不为空
            FL = handle_excel(self._excelFileAddress)  # 调用函数 返回列表
            if FL == -1:  # 函数返回错误代码
                QMessageBox.warning(self, "警告", "处理返回数据为空，请检查数据是否为空或格式错误")
            elif FL == -2:
                QMessageBox.warning(self, "警告", "文件打开错误,支持文件格式为:xlsx,xlsm,xltx,xltm")
                # please check you can open it with Excel first. Supported formats are: .xlsx,.xlsm,.xltx,.xltm
            elif FL:
                print(FL)  # 处理成功 放到table上
                self.ui.excelTW.setRowCount(len(FL))  # 设置数据区行数
                for ODIndex, ODL in enumerate(FL):  # one-dimensional list
                    for TDIndex, TDL in enumerate(ODL):
                        item = QTableWidgetItem(str(TDL))  # 转换类型 实例表格项目类
                        item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 垂直水平居中
                        self.ui.excelTW.setItem(ODIndex, TDIndex, item)  # 向坐标 设置项目
                self.ui.excelTW.resizeColumnsToContents()  # 调整列宽
            else:
                QMessageBox.warning(self, "错误", FL)
        else:  # 弹窗出函数返回的自定义Exception
            QMessageBox.warning(self, "警告", "文件地址为空")
        self.ui.statusbar.showMessage("处理成功", 3000)

    @pyqtSlot()
    def on_exportExcelPB_clicked(self):
        # 导出  调用类方法取出excel表格组件中的数组 传给导出为excel函数
        excelTWValue = self.GetExcelTWValue()
        export_excel(excelTWValue, self._excelFileAddress)  # 列表传给导出函数
        self.ui.statusbar.showMessage("导出成功", 3000)

    @pyqtSlot()
    def on_excelTableEditablePB_clicked(self):  # 表格可编辑
        # 取当前状态然后做反选
        status = self.ui.excelTableEditablePB.text()
        if status == "表格可编辑":
            trig = QAbstractItemView.NoEditTriggers
            self.ui.excelTW.setEditTriggers(trig)  # 不允许编辑
            self.ui.excelTableEditablePB.setText("表格不可编辑")
        elif status == "表格不可编辑":
            trig = QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked
            self.ui.excelTW.setEditTriggers(trig)  # 允许编辑
            self.ui.excelTableEditablePB.setText("表格可编辑")

    @pyqtSlot()
    def on_ListIniPB_clicked(self):  # 初始化单号按钮
        excelTWValue = []
        try:
            excelTWValue = self.GetExcelTWValue()
        except AttributeError:
            QMessageBox.warning(self, "警告", "Excel处理表为空")
            return
        except Exception as e:
            print(e)
            return
        excelTWValue = self.GetExcelTWValue()
        print(excelTWValue)  # 处理成功 放到table上
        self.ui.shipHandleTW.setRowCount(len(excelTWValue))  # 设置数据区行数
        for ODIndex, ODL in enumerate(excelTWValue):  # one-dimensional list
            for TDIndex, TDL in enumerate(ODL):
                item = QTableWidgetItem(str(TDL))  # 转换类型 实例表格项目类
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 垂直水平居中
                if TDIndex == 0:
                    item.setCheckState(Qt.Checked)  # TODO 设置选择状态为 选中
                    # item.setSelected(True)
                self.ui.shipHandleTW.setItem(ODIndex, TDIndex, item)  # 向坐标 设置项目
                # 设置默认通道
                item = QTableWidgetItem(str(self.ui.defaultChannelLE.text()))
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 垂直水平居中
                self.ui.shipHandleTW.setItem(ODIndex, TDIndex + 1, item)  # 列加一 默认通道项目

                # 设置默认视频码流
                item = QTableWidgetItem(str(self.ui.defaultStreamCB.currentText()))
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 垂直水平居中
                # item.setFlags(Qt.ItemIsEditable)
                self.ui.shipHandleTW.setItem(ODIndex, TDIndex + 2, item)  # 列加一 默认视频码流

                # 设置默认提取方式
                item = QTableWidgetItem(str(self.ui.defaultEttractionMethodCB.currentText()))
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 垂直水平居中
                # item.setFlags(Qt.ItemIsEditable)
                self.ui.shipHandleTW.setItem(ODIndex, TDIndex + 3, item)
        self.ui.shipHandleTW.resizeColumnsToContents()  # 调整列宽

    @pyqtSlot()
    def on_ListSelHandlePB_clicked(self):  # 开始下载选中单号
        # 登录参数
        IP = self.ui.iPLineEdit.text()
        PORT = self.ui.portLE.text()
        USERNAME = self.ui.usernmLE.text()
        PASSWORD = self.ui.passwdLE.text()
        # 下载参数
        CHANNEL = self.ui.defaultChannelLE.text()
        STREAM = self.ui.defaultStreamCB.currentIndex()
        EttractionMethod = self.ui.defaultEttractionMethodCB.currentIndex()
        # 打包时间 打包参数 这样就没用遮遮掩掩了 可是要发起多少次啊
        pass


if __name__ == "__main__":  # 用于当前窗体测试
    app = QApplication(sys.argv)  # 创建GUI应用程序
    form = QmyMainWindow()  # 创建窗体
    form.show()
    sys.exit(app.exec_())
