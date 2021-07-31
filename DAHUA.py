# 取出回调 不要图形框架 独立类
# 所有的导入 最后再判断哪些是不需要的
import sys
import os

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal
from ctypes import *

from PlayBackUI import Ui_MainWindow
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Enum import EM_USEDEV_MODE, EM_QUERY_RECORD_TYPE, EM_LOGIN_SPAC_CAP_TYPE
from NetSDK.SDK_Struct import NET_TIME, NET_RECORDFILE_INFO, NET_IN_PLAY_BACK_BY_TIME_INFO, \
    NET_OUT_PLAY_BACK_BY_TIME_INFO, \
    C_LLONG, C_DWORD, C_LDWORD, NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY, NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY, \
    CB_FUNCTYPE, sys_platform
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect


class Dahua(object):
    def __init__(self, pardent=None):
        super().__init__()
        # NetSDK用到的相关变量
        self.loginID = C_LLONG()
        self.downloadID = C_LLONG()
        # 获取NetSDK对象并初始化
        self.sdk = NetClient()
        self.widget = QWidget()

    def login(self):
        if not self.loginID:
            ip = "10.30.15.216"
            port = 80
            username = "admin"
            password = "450000ydzz"

            # 标准输入参数
            stuInParam = NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY()
            stuInParam.dwSize = sizeof(NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY)
            stuInParam.szIP = ip.encode()
            stuInParam.nPort = port
            stuInParam.szUserName = username.encode()
            stuInParam.szPassword = password.encode()
            stuInParam.emSpecCap = EM_LOGIN_SPAC_CAP_TYPE.TCP
            stuInParam.pCapParam = None
            # 标准输出参数
            stuOutParam = NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY()
            stuOutParam.dwSize = sizeof(NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY)
            self.loginID, device_info, error_msg = self.sdk.LoginWithHighLevelSecurity(
                stuInParam, stuOutParam)
            if self.loginID != 0:
                # 如果ID不为零 就可以登出 那说明登录成功了
                # 可以下载 改变通道 视频码流 日期
                # 默认视频码流为主码流 0
                self.set_stream_type(0)
                # 从这里获取所有的通道索引 原文件139行
            else:
                QMessageBox.about(self.widget, '提示(prompt)', error_msg)
        else:
            if self.downloadID:
                self.sdk.StopDownload(self.downloadID)
                self.downloadID = 0
            result = self.sdk.Logout(self.loginID)
            if result:
                # 结果不为空 则设置标题离线
                # 可点击登录
                self.loginID = 0
                # 不可以 设置视频码流 回访 暂停下载 设置通道
                # 通道列表 日期 视频是否存在 重画playback的什么
                # 清除通道列表 设置下载进度为零

    def download(self):
        if not self.downloadID:
            save_file_name = os.path.dirname(__file__) + 'data.dav'
            stream_type = 0
            self.set_stream_type(stream_type)
            nchannel = 29
            # 视频保存地址 码流索引 日期时间
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
            # 5秒
            self.downloadID = self.sdk.DownloadByTimeEx(
                self.loginID, nchannel, int(EM_QUERY_RECORD_TYPE.ALL),
                startDateTime, enddateTime, save_file_name)
            if self.downloadID:
                # 改变按钮为 停止 现在不设置 也就是不能停止下载
                pass
            else:
                QMessageBox.about(self.widget, '提示(prompt)',
                                  self.sdk.GetLastErrorMessage())
        else:
            result = self.sdk.StopDownload(self.downloadID)
            if result:
                self.downloadID = 0
                # 设置下载按钮 为 可下载
            else:
                QMessageBox.about(self.widget, '提示(prompt)',
                                  self.sdk.GetLastErrorMessage())

    def set_stream_type(self, stream_type):
        # set stream type;设置码流类型
        stream_type = c_int(stream_type)
        result = self.sdk.SetDeviceMode(self.loginID,
                                        int(EM_USEDEV_MODE.RECORD_STREAM_TYPE),
                                        stream_type)
        if not result:
            QMessageBox.about(self.widget, '提示(prompt)',
                              self.sdk.GetLastErrorMessage())
            return 0, 0, None
