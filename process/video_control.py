import os
import cv2
import time
import numpy as np
from process.HCNetSDK import *
from process.PlayCtrl import *



class HKCam(object):
    def __init__(self, host, port, username, password, lib_dir="../../lib/win"):
        # 登录的设备信息
        self.DEV_IP = create_string_buffer(host.encode())
        self.DEV_PORT = port
        self.DEV_USER_NAME = create_string_buffer(username.encode())
        self.DEV_PASSWORD = create_string_buffer(password.encode())
        self.WINDOWS_FLAG = True
        self.funcRealDataCallBack_V30 = None
        self.recent_img = None  # 最新帧
        self.n_stamp = None  # 帧时间戳
        self.last_stamp = None  # 上次时间戳
        self.login_success = False

        os.chdir(lib_dir)  # 加载库,先加载依赖库
        self.Objdll = ctypes.CDLL(r'./HCNetSDK.dll')  # 加载网络库
        self.Playctrldll = ctypes.CDLL(r'./PlayCtrl.dll')  # 加载播放库
        # 设置组件库和SSL库加载路径                                                              # 2 设置组件库和SSL库加载路径
        self.SetSDKInitCfg()
        # 初始化DLL
        self.Objdll.NET_DVR_Init()  # 3 相机初始化
        # 启用SDK写日志
        self.Objdll.NET_DVR_SetLogToFile(3, bytes('./SdkLog_Python/', encoding="utf-8"), False)
        os.chdir(r'../../')  # 切换工作路径到../../
        # 登录
        (self.lUserId, self.device_info) = self.LoginDev()  # 4 登录相机
        self.Playctrldll.PlayM4_ResetBuffer(self.lUserId, 1)  # 清空指定缓冲区的剩余数据。这个地方传进来的是self.lUserId，为什么呢？
        # print(self.lUserId)
        if self.lUserId < 0:  # 登录失败
            print('登录设备失败, 错误编码: %d' % self.Objdll.NET_DVR_GetLastError())
            # 释放资源
            self.Objdll.NET_DVR_Cleanup()
            exit()
        else:
            print(f'[INFO] 摄像头[{camIP}]登录成功!!')
            self.login_success = True
        self.start_play()  # 5 开始播放
        time.sleep(0.1)

    def start_play(self, ):
        # global funcRealDataCallBack_V30
        self.PlayCtrl_Port = c_long(-1)  # 播放句柄
        # 获取一个播放句柄 #wuzh获取未使用的通道号
        if not self.Playctrldll.PlayM4_GetPort(byref(self.PlayCtrl_Port)):
            print(u'获取播放库句柄失败')
        # 定义码流回调函数
        self.funcRealDataCallBack_V30 = REALDATACALLBACK(self.RealDataCallBack_V30)
        # 开启预览
        self.preview_info = NET_DVR_PREVIEWINFO()
        self.preview_info.hPlayWnd = 0
        self.preview_info.lChannel = 1  # 通道号
        self.preview_info.dwStreamType = 0  # 0:主码流,1:子码流
        self.preview_info.dwLinkMode = 1  # 0：TCP方式,1：UDP方式
        self.preview_info.bBlocked = 1  # 阻塞取流
        # 开始预览并且设置回调函数回调获取实时流数据
        self.lRealPlayHandle = self.Objdll.NET_DVR_RealPlay_V40(self.lUserId, byref(self.preview_info),
                                                                self.funcRealDataCallBack_V30, None)
        if self.lRealPlayHandle < 0:
            print('Open preview fail, error code is: %d' % self.Objdll.NET_DVR_GetLastError())
            # 登出设备
            self.Objdll.NET_DVR_Logout(self.lUserId)
            # 释放资源
            self.Objdll.NET_DVR_Cleanup()
            exit()

    # 设置组件库和SSL库加载路径
    def SetSDKInitCfg(self, ):
        # 设置SDK初始化依赖库路径
        # 设置HCNetSDKCom组件库和SSL库加载路径
        # print(os.getcwd())
        if self.WINDOWS_FLAG:
            strPath = os.getcwd().encode('gbk')
            sdk_ComPath = NET_DVR_LOCAL_SDK_PATH()
            sdk_ComPath.sPath = strPath
            self.Objdll.NET_DVR_SetSDKInitCfg(2, byref(sdk_ComPath))
            self.Objdll.NET_DVR_SetSDKInitCfg(3, create_string_buffer(strPath + b'\libcrypto-1_1-x64.dll'))
            self.Objdll.NET_DVR_SetSDKInitCfg(4, create_string_buffer(strPath + b'\libssl-1_1-x64.dll'))
        else:
            strPath = os.getcwd().encode('utf-8')
            sdk_ComPath = NET_DVR_LOCAL_SDK_PATH()
            sdk_ComPath.sPath = strPath
            self.Objdll.NET_DVR_SetSDKInitCfg(2, byref(sdk_ComPath))
            self.Objdll.NET_DVR_SetSDKInitCfg(3, create_string_buffer(strPath + b'/libcrypto.so.1.1'))
            self.Objdll.NET_DVR_SetSDKInitCfg(4, create_string_buffer(strPath + b'/libssl.so.1.1'))

    # 登录注册设备
    def LoginDev(self, ):
        # 登录注册设备
        device_info = NET_DVR_DEVICEINFO_V30()
        lUserId = self.Objdll.NET_DVR_Login_V30(self.DEV_IP, self.DEV_PORT, self.DEV_USER_NAME, self.DEV_PASSWORD,
                                                byref(device_info))
        return (lUserId, device_info)

    # 读取摄像头数据
    def read(self, ):
        while self.n_stamp == self.last_stamp:
            continue
        self.last_stamp = self.n_stamp
        return self.n_stamp, self.recent_img

    # 解码回调函数
    def DecCBFun(self, nPort, pBuf, nSize, pFrameInfo, nUser, nReserved2):
        if pFrameInfo.contents.nType == 3:
            t0 = time.time()
            # 解码返回视频YUV数据，将YUV数据转成jpg图片保存到本地
            # 如果有耗时处理，需要将解码数据拷贝到回调函数外面的其他线程里面处理，避免阻塞回调导致解码丢帧
            nWidth = pFrameInfo.contents.nWidth
            nHeight = pFrameInfo.contents.nHeight
            # nType = pFrameInfo.contents.nType
            dwFrameNum = pFrameInfo.contents.dwFrameNum
            nStamp = pFrameInfo.contents.nStamp
            # print(nWidth, nHeight, nType, dwFrameNum, nStamp, sFileName)
            YUV = np.frombuffer(pBuf[:nSize], dtype=np.uint8)
            YUV = np.reshape(YUV, [nHeight + nHeight // 2, nWidth])
            img_rgb = cv2.cvtColor(YUV, cv2.COLOR_YUV2BGR_YV12)
            self.recent_img, self.n_stamp = img_rgb, nStamp

    # 码流回调
    def RealDataCallBack_V30(self, lPlayHandle, dwDataType, pBuffer, dwBufSize, pUser):
        # 码流回调函数
        if dwDataType == NET_DVR_SYSHEAD:
            # 设置流播放模式
            self.Playctrldll.PlayM4_SetStreamOpenMode(self.PlayCtrl_Port, 0)
            # 打开码流，送入40字节系统头数据
            if self.Playctrldll.PlayM4_OpenStream(self.PlayCtrl_Port, pBuffer, dwBufSize, 1024 * 1024):
                # 设置解码回调，可以返回解码后YUV视频数据
                # global FuncDecCB
                self.FuncDecCB = DECCBFUNWIN(self.DecCBFun)
                self.Playctrldll.PlayM4_SetDecCallBackExMend(self.PlayCtrl_Port, self.FuncDecCB, None, c_long(0), None)
                # 开始解码播放
                if not self.Playctrldll.PlayM4_Play(self.PlayCtrl_Port, None):
                    print(u'播放库播放失败')

            else:
                print(u'播放库打开流失败')
        elif dwDataType == NET_DVR_STREAMDATA:
            self.Playctrldll.PlayM4_InputData(self.PlayCtrl_Port, pBuffer, dwBufSize)
        else:
            print(u'其他数据,长度:', dwBufSize)

    # 释放资源
    def release(self):
        self.Objdll.NET_DVR_StopRealPlay(self.lRealPlayHandle)
        if self.PlayCtrl_Port.value > -1:
            self.Playctrldll.PlayM4_Stop(self.PlayCtrl_Port)
            self.Playctrldll.PlayM4_CloseStream(self.PlayCtrl_Port)
            self.Playctrldll.PlayM4_FreePort(self.PlayCtrl_Port)
            self.PlayCtrl_Port = c_long(-1)
        self.Objdll.NET_DVR_Logout(self.lUserId)
        self.Objdll.NET_DVR_Cleanup()
        print('释放资源结束')

    # 上下文管理
    def __enter__(self):
        return self

    # 释放资源
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def main():
    """
    主函数，负责创建 HKCam 对象并处理用户键盘输入。
    功能：w、s、a、d 键控制云台上下左右移动，
        e、r 键控制焦距，
        t、y 键控制焦点，
        u、i 键控制光圈。
    """
    # 创建 HKCam 对象
    cam = HKCam("192.168.10.134", "admin", "ryzh123456", 8000, "./lib/win")  #E:\work\project_local\HK\5- Python开发示例\1-预览取流解码Demo\lib\win
    # 移动至初始预置点
    # cam.move_to_preset(1)
    # 调用 initialposition_ctrl 方法，并设置 work_mode 为 1 (调用零方位):
    # cam.initialposition_ctrl(work_mode=1)
    # 键盘控制云台 + opencv视频播放
    if cam.login_success:
        num = 0
        while True:
            try:
                _, frame = cam.read()

                if frame is not None:
                    cv2.imshow("HKCam", frame)
                    cv2.imwrite("./picture/29/frame_" + str(num) + ".jpeg", frame)
                    num += 1
                    print(num)
                    key = cv2.waitKey(10) & 0xFF
                    if key == 27:  # Esc 键退出
                        break
            except Exception as e:
                print(f"发生playback异常: {e}")
                break
        cv2.destroyAllWindows()
    else:
        print("请先登录设备")
    # 释放资源
    cam.release()


