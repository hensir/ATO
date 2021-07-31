import sys
import os
from PyQt5.QtCore import pyqtSlot, Qt, QDate, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem, QAbstractItemView
from UI_MainWindow import Ui_MainWindow
from function import handle_excel, export_excel
from ctypes import *
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Enum import EM_USEDEV_MODE, EM_QUERY_RECORD_TYPE, EM_LOGIN_SPAC_CAP_TYPE
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect
from NetSDK.SDK_Struct import NET_TIME, NET_RECORDFILE_INFO, NET_IN_PLAY_BACK_BY_TIME_INFO, \
    NET_OUT_PLAY_BACK_BY_TIME_INFO, \
    C_LLONG, C_DWORD, C_LDWORD, NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY, NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY, \
    CB_FUNCTYPE, sys_platform


# TODO 安全措施
# TODO IP是否输入 账号 密码  初始化列表 导入现在这个表 然后做修改代理 视频通道全取默认通道 截屏方式默认 秒数直接
# TODO 现在编辑时间

# 继承QThread
class Mythread(QThread):
    # 定义信号,定义参数为int, int类型
    breakSignal = pyqtSignal(int, int)

    def __init__(self, parent=None, dwTotalSize=1, dwDownLoadSize=0):
        super().__init__(parent)
        self.dwTotalSize = dwTotalSize
        self.dwDownLoadSize = dwDownLoadSize

    def run(self):
        self.breakSignal.emit(self.dwTotalSize, self.dwDownLoadSize)

    def update_data(self, total_size, download_size):
        self.breakSignal.emit(total_size, download_size)


global wnd


@CB_FUNCTYPE(None, C_LLONG, C_DWORD, C_DWORD, C_LDWORD)
def DownLoadPosCallBack(lLoginID, pchDVRIP, nDVRPort, dwUser):
    pass


@CB_FUNCTYPE(c_int, C_LLONG, C_DWORD, POINTER(c_ubyte), C_DWORD, C_LDWORD)
def DownLoadDataCallBack(lPlayHandle, dwDataType, pBuffer, dwBufSize, dwUser):
    # buf_data = cast(pBuffer, POINTER(c_ubyte * dwBufSize)).contents
    # with open('./buffer.dav', 'ab+') as buf_file:
    #     buf_file.write(buf_data)
    return 1


@CB_FUNCTYPE(None, C_LLONG, C_DWORD, C_DWORD, c_int, NET_RECORDFILE_INFO,
             C_LDWORD)
def TimeDownLoadPosCallBack(lPlayHandle, dwTotalSize, dwDownLoadSize, index,
                            recordfileinfo, dwUser):
    try:
        wnd.update_download_progress_thread(dwTotalSize, dwDownLoadSize)
    except Exception as e:
        print(e)


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
        # 大华sdk

        # NetSDK用到的相关变量和回调
        self.loginID = C_LLONG()
        self.downloadID = C_LLONG()
        self.m_DisConnectCallBack = fDisConnect(self.DisConnectCallBack)
        self.m_ReConnectCallBack = fHaveReConnect(self.ReConnectCallBack)

        self.thread = Mythread()
        self.thread.breakSignal.connect(self.update_download_progress)  # 连接刷新进度条的方法
        self.thread.start()

        # 获取NetSDK对象并初始化
        self.sdk = NetClient()
        self.sdk.InitEx(self.m_DisConnectCallBack)
        self.sdk.SetAutoReconnect(self.m_ReConnectCallBack)

        # 测试预填充数据
        self._excelFileAddress = "C:\\Users\\Hast\\Desktop\\07.19\\表2\\广东中山分拨中心.xlsx"
        self.ui.handlePB.click()
        self.ui.ListIniPB.click()

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
        return tablewidgetvalue  # 打印并返回获取到的数值

    def GetShipHandleTWValue(self):
        # 获取并返回shiphandleTW表格组件的所有数据
        rowcount = self.ui.shipHandleTW.rowCount()
        columncount = self.ui.shipHandleTW.columnCount() - 1  # 总行数 总列数 因为最后一列的下载状态是不需要的数据所以减一
        tablewidgetvalue = [[] for i in range(rowcount)]  # 创建二维列表空间
        for row in range(rowcount):
            for column in range(columncount):  # 循环坐标取值
                tablewidgetvalue[row].append(str(self.ui.shipHandleTW.item(row, column).text()))
        print(tablewidgetvalue)
        return tablewidgetvalue  # 打印并返回获取到的数值

    def GetShipHandleTWFCCS(self):  # getshiphandletablewidgetfristcolumncheckedState
        """ 遍历shiphandleTW的第一列 获取checked的状态 这个一般用不到了"""

        rowcount = self.ui.shipHandleTW.rowCount()
        column = 1  # 因为是第一列所以总行和column——1

        def GetItemChecked(x, y):  # 将要用于处理所有列单元格的函数
            return self.ui.shipHandleTW.item(x, y).checkState()

        checkedList = self.HandleShipCR(rowcount, column, GetItemChecked)
        print(checkedList)
        # self.ui.shipHandleTW.
        return checkedList  # 打印并返回列表数据

    # 向下开发  指定列，指定行，指定函数并遍历用于索引内的单元格,返回处理后的cell项目
    def HandleShipCR(self, row, column, function):  # handle ship ColumnRow
        ProedList = []
        for r in range(row):
            for c in range(column):
                item = function(r, c)  # 内建方法 item(x,y)
                ProedList.append(item)  # 追加函数返回的数值
                if item is None:  # 如果自定义遍历处理函数返回None 则说明用户想要退出
                    return ProedList  # 目前是这样的 不确定这个判断以后还能不能用
        return ProedList

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
        self.ui.statusbar.showMessage("导出成功", 3000)  # 状态栏显示3秒

    @pyqtSlot()
    def on_excelTableEditablePB_clicked(self):  # 表格是否可以编辑
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
        # excelTWValue = []
        try:
            excelTWValue = self.GetExcelTWValue()  # 获取excelTW的数据
        except AttributeError:
            QMessageBox.warning(self, "警告", "Excel处理表为空")
            return
        except Exception as e:  # 捕捉所有错误
            print(e)
            return

        # 这里检测有没有登录 如果没有登录 就报个弹窗    # 或者没登录 初始化也没用 就直接setenable
        if self.loginID is None:  # 这个数值登录成功是登录句柄 失败则为0   如果loginid不为空
            pass
        else:
            dlgTitle = "Question"
            strInfo = "检测未登录,是否继续初始化单号?"
            defaultBtn = QMessageBox.NoButton  # 缺省按钮
            result = QMessageBox.question(self, dlgTitle, strInfo,
                                          QMessageBox.Yes | QMessageBox.No,
                                          defaultBtn)
            if result == QMessageBox.Yes:
                pass
            elif result == QMessageBox.No:
                return
            else:
                return

        # excelTWValue = self.GetExcelTWValue()
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
                item = QTableWidgetItem(str(self.ui.defaultChannelCB.currentText()))
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 垂直水平居中
                self.ui.shipHandleTW.setItem(ODIndex, TDIndex + 1, item)  # 列加一 默认通道项目

                # 设置默认视频码流
                item = QTableWidgetItem(str(self.ui.defaultStreamCB.currentText()))
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 垂直水平居中
                # item.setFlags(Qt.ItemIsEditable)
                self.ui.shipHandleTW.setItem(ODIndex, TDIndex + 2, item)  # 列加二 默认视频码流

                # 设置默认提取方式
                item = QTableWidgetItem(str(self.ui.defaultEttractionMethodCB.currentText()))
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 垂直水平居中
                # item.setFlags(Qt.ItemIsEditable)
                self.ui.shipHandleTW.setItem(ODIndex, TDIndex + 3, item)  # 列加三 默认提取方式
        self.ui.shipHandleTW.resizeColumnsToContents()  # 调整列宽

    @pyqtSlot()
    def on_ListClearPB_clicked(self):  # 清空所有单号按钮
        self.ui.shipHandleTW.clearContents()

    @pyqtSlot()
    def on_ListSelDeletePB_clicked(self):  # 删除选中单号按钮
        #  循环执行 已选单元格次数的遍历处理单元格自定义函数
        #
        rowcount = self.ui.shipHandleTW.rowCount()
        column = 1

        # 获取已选单元格总数   TODO 这个东西我写过类方法 记得替换一下 当然是完全可以替换的 下面那个判断的判断值也改为Checked才更符合思路
        def getshipHandleTWFCCC(x, y):  # getShipHandleTableWidgetFristColumnCheckedCount
            if self.ui.shipHandleTW.item(x, y).checkState() == Qt.Checked:
                return True
            else:
                return -1  # 如果为已选状态返回True 否则None

        # TODO 问题出现了 这个-1的判断替代None 如果是None的话就只能删除一个选项了 是因为None的判读
        # TODO 再做一个完美的返回值 不过这个明显不急

        CheckedCountList = self.HandleShipCR(rowcount, column, getshipHandleTWFCCC)
        print(CheckedCountList)
        CheckedCount = 0
        for i in CheckedCountList:  # 因为HandleShipCR比较底层 所以用循环来处理 已选总数
            if i is True:
                CheckedCount += 1

        print(CheckedCount)

        def deleteshipHandleTWFC(x, y):  # setshipHandleTWFirstColumnCheckToInverse
            """定义删除行遍历处理函数"""
            # print(self.ui.shipHandleTW.item(x, y).text())
            if self.ui.shipHandleTW.item(x, y).checkState() == Qt.Checked:
                self.ui.shipHandleTW.removeRow(x)
                return

        # 因为一旦删除一行之后 TW组件的索引会立即更新 而原处理方式的for循环的索引还是不变 举个例子，第一行已经删除了 第二行索引变为0
        # 而现在的for的i索引是1 这样就会索引到原本意义列表的第三行数据 所以我做了一个处理 在删除一行之后 立刻退出 然后重新开始遍历
        # 遍历总次数就是上面获取的 已选状态总数
        for i in range(CheckedCount):
            self.HandleShipCR(rowcount, column, deleteshipHandleTWFC)

    @pyqtSlot()
    def on_ListSelAllPB_clicked(self):  # 选择所有单号按钮
        rowcount = self.ui.shipHandleTW.rowCount()
        column = 1

        # 遍历shiphandleTW的第一列数据并设置所有的item的checkstate都为Checked
        def setshipHandleTWFCCTT(x, y):  # setshipHandleTWFirstCoulumnCheckstateToTrue
            self.ui.shipHandleTW.item(x, y).setCheckState(Qt.Checked)
            return self.ui.shipHandleTW.item(x, y).checkState()

        checkedstateList = self.HandleShipCR(rowcount, column, setshipHandleTWFCCTT)
        print(checkedstateList)

    @pyqtSlot()
    def on_ListSelNonePB_clicked(self):  # 取消选择所有单号按钮
        rowcount = self.ui.shipHandleTW.rowCount()
        column = 1

        # 遍历shiphandleTW的第一列数据并设置所有的item的checkstate都为Unchecked
        def setshipHandleTWFCCTF(x, y):  # setshipHandleTWFirstCoulumnCheckstateToFalse
            self.ui.shipHandleTW.item(x, y).setCheckState(Qt.Unchecked)
            return self.ui.shipHandleTW.item(x, y).checkState()

        checkedstateList = self.HandleShipCR(rowcount, column, setshipHandleTWFCCTF)
        print(checkedstateList)

    @pyqtSlot()
    def on_ListSelInversePB_clicked(self):  # 反向选择单号按钮
        rowcount = self.ui.shipHandleTW.rowCount()
        column = 1

        # 遍历shiphandleTW的第一列数据并检测当前item的选中状态做反转操作
        def setshipHandleTWFCCTI(x, y):  # setshipHandleTWFirstColumnCheckToInverse
            if self.ui.shipHandleTW.item(x, y).checkState() != Qt.Checked:
                self.ui.shipHandleTW.item(x, y).setCheckState(Qt.Checked)
            else:
                self.ui.shipHandleTW.item(x, y).setCheckState(Qt.Unchecked)
            return self.ui.shipHandleTW.item(x, y).checkState()

        checkedstateList = self.HandleShipCR(rowcount, column, setshipHandleTWFCCTI)
        print(checkedstateList)

    # @pyqtSlot()
    # def on_ListSelHandlePB_clicked(self):  # 开始下载选中单号
    #     # 登录参数
    #     IP = self.ui.iPLineEdit.text()
    #     PORT = self.ui.portLE.text()
    #     USERNAME = self.ui.usernmLE.text()
    #     PASSWORD = self.ui.passwdLE.text()
    #     # 下载参数
    #     # CHANNEL = self.ui.defaultChannelLE.text()
    #     # STREAM = self.ui.defaultStreamCB.currentIndex()
    #     # EttractionMethod = self.ui.defaultEttractionMethodCB.currentIndex()
    #     TWV = self.GetShipHandleTWValue()  # TableWidgetValue
    #     LPL = [IP, PORT, USERNAME, PASSWORD]  # login parameter list
    #     # GetDaHuaVideo(LPL, TWV)

    @pyqtSlot()
    def on_LoginPB_clicked(self):
        if not self.loginID:
            ip = self.ui.iPLineEdit.text()
            port = int(self.ui.portLE.text())
            username = self.ui.usernmLE.text()
            password = self.ui.passwdLE.text()
            stuInParam = NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY()
            stuInParam.dwSize = sizeof(NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY)
            stuInParam.szIP = ip.encode()
            stuInParam.nPort = port
            stuInParam.szUserName = username.encode()
            stuInParam.szPassword = password.encode()
            stuInParam.emSpecCap = EM_LOGIN_SPAC_CAP_TYPE.TCP
            stuInParam.pCapParam = None

            stuOutParam = NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY()
            stuOutParam.dwSize = sizeof(NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY)

            self.loginID, device_info, error_msg = self.sdk.LoginWithHighLevelSecurity(
                stuInParam, stuOutParam)
            if self.loginID != 0:
                title = self.windowTitle()
                self.setWindowTitle(title + ' 在线(OnLine)')
                # self.Login_pushButton.setText('登出')
                self.ui.LoginPB.setText('登出')
                self.ui.ListSelHandlePB.setEnabled(True)
                self.ui.defaultChannelCB.setEnabled(True)
                self.ui.defaultStreamCB.setEnabled(True)

                self.set_stream_type(0)
                for i in range(int(device_info.nChanNum)):
                    self.defaultChannelCB.addItem(str(i))
            else:
                QMessageBox.about(self, '提示(prompt)', error_msg)
        else:
            if self.downloadID:
                self.sdk.StopDownload(self.downloadID)
                self.downloadID = 0
            result = self.sdk.Logout(self.loginID)
            if result:
                title = self.windowTitle()
                self.setWindowTitle(title + " 离线(OffLine)")
                # self.Login_pushButton.setText("登录(Login)")
                self.ui.LoginPB.setText("登录")
                self.loginID = 0
                self.ui.defaultStreamCB.setEnabled(True)
                self.ui.ListSelHandlePB.setEnabled(True)
                self.ui.defaultChannelCB.setEnabled(True)
                self.ui.ListSelHandlePB.setText("开始下载选中单号")
                self.defaultChannelCB.clear()
                self.ui.downloadBar.setValue(0)
                self.thread.update_data(1, 0)

    def on_ListSelHandlePB_clicked(self):
        if not self.downloadID:
            TWVList = self.GetShipHandleTWValue()  # TableWidgetValueList
            # 这上面有 shipid  扫描时间 视频通道 视频码流
            for TWV in TWVList:
                print(TWV)
                front = os.path.dirname(__file__)
                behind = "/%s.dav" % TWV[0]
                save_file_name = front + behind

                if TWV[3] != "":        # TODO 看到这里 就确定 登陆之前初始化单号不能运行 我现在是做测试 所有的测试代码
                    nchannel = int(TWV[3])  # 视频通道      # 像这种庇护的都要删除掉
                else:
                    nchannel = ""
                if TWV[4] == "主码流":
                    stream_type = 0
                    # self.set_stream_type(stream_type)
                else:
                    stream_type = 0
                    self.set_stream_type(stream_type)

                time = TWV[1].strftime("%Y-%m-%d %H:%M:%S")

                startDateTime = NET_TIME()
                startDateTime.dwYear = 2021
                startDateTime.dwMonth = 7
                startDateTime.dwDay = 19
                startDateTime.dwHour = 5
                startDateTime.dwMinute = 30
                startDateTime.dwSecond = 30

                enddateTime = NET_TIME()
                enddateTime.dwYear = 2021
                enddateTime.dwMonth = 7
                enddateTime.dwDay = 19
                enddateTime.dwHour = 5
                enddateTime.dwMinute = 30
                enddateTime.dwSecond = 35

                self.downloadID = self.sdk.DownloadByTimeEx(
                    self.loginID, nchannel, int(EM_QUERY_RECORD_TYPE.ALL),
                    startDateTime, enddateTime, save_file_name,
                    TimeDownLoadPosCallBack, 0, DownLoadDataCallBack, 0)
                if self.downloadID:
                    # self.Download_pushButton.setText("停止(Stop)")
                    self.ui.ListSelHandlePB.setText("停止下载")
                else:
                    QMessageBox.about(self, '提示(prompt)',
                                      self.sdk.GetLastErrorMessage())
        else:
            result = self.sdk.StopDownload(self.downloadID)
            if result:
                self.downloadID = 0
                self.ui.ListSelHandlePB.setText("开始下载选中单号")
                self.ui.downloadBar.setValue(0)
                self.thread.update_data(1, 0)
            else:
                QMessageBox.about(self, '提示(prompt)',
                                  self.sdk.GetLastErrorMessage())

    def set_stream_type(self, stream_type):
        # set stream type;设置码流类型
        stream_type = c_int(stream_type)
        result = self.sdk.SetDeviceMode(self.loginID,
                                        int(EM_USEDEV_MODE.RECORD_STREAM_TYPE),
                                        stream_type)
        if not result:
            QMessageBox.about(self, '提示(prompt)',
                              self.sdk.GetLastErrorMessage())
            return 0, 0, None

    def update_download_progress_thread(self, totalsize, downloadsize):
        try:
            self.thread.update_data(totalsize, downloadsize)
        except Exception as e:
            print(e)

    # 实现断线回调函数功能
    def DisConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        title = self.windowTitle()
        self.setWindowTitle(title + " 离线(OffLine)")

    # 实现断线重连回调函数功能
    def ReConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        title = self.windowTitle()
        self.setWindowTitle(title + ' 在线(OnLine)')

    # 关闭主窗口时清理资源
    def closeEvent(self, event):
        event.accept()
        if self.loginID:
            self.sdk.Logout(self.loginID)
        self.sdk.Cleanup()

    def update_download_progress(self, total_size, download_size):
        try:
            if download_size == -1:
                self.downloadID = 0
                # self.Download_progressBar.setValue(0)
                self.ui.downloadBar.setValue(0)
                self.sdk.StopDownload(self.downloadID)
                self.ui.ListSelHandlePB.setText("开始下载选中单号")
                QMessageBox.about(self, '提示(prompt)', "Download End(下载结束)!")
            elif download_size == -2:
                self.downloadID = 0
                # self.Download_progressBar.setValue(0)
                self.ui.downloadBar.setValue(0)
                # self.Download_pushButton.setText("下载(download)")
                self.ui.ListSelHandlePB.setText("开始下载选中单号")
                QMessageBox.about(self, '提示(prompt)', "Download Failed(下载失败)!")
            else:
                if download_size >= total_size:
                    # self.Download_progressBar.setValue(100)
                    self.ui.downloadBar.setValue(0)
                else:
                    percentage = int(download_size * 100 / total_size)
                    # self.Download_progressBar.setValue(percentage)
                    self.ui.downloadBar.setValue(percentage)
        except Exception as e:
            print(e)


if __name__ == "__main__":  # 用于当前窗体测试
    app = QApplication(sys.argv)  # 创建GUI应用程序
    form = QmyMainWindow()  # 创建窗体
    wnd = form
    form.show()
    sys.exit(app.exec_())
