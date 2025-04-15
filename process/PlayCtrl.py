import sys
from ctypes import *

# 回调函数类型定义
if 'linux' in sys.platform:
    fun_ctype = CFUNCTYPE
else:
    fun_ctype = WINFUNCTYPE


# 定义预览参数结构体
class FRAME_INFO(Structure):
    pass


LPFRAME_INFO = POINTER(FRAME_INFO)
FRAME_INFO._fields_ = [
    ('nWidth', c_uint32),
    ('nHeight', c_uint32),
    ('nStamp', c_uint32),
    ('nType', c_uint32),
    ('nFrameRate', c_uint32),
    ('dwFrameNum', c_uint32)
]


class NET_DVR_INITIALPOSITIONCTRL(Structure):
    _fields_ = [
        ("dwSize", c_ulong),  # Use c_ulong for DWORD
        ("dwChan", c_ulong),  # Use c_ulong for DWORD
        ("byWorkMode", c_byte),
        ("byRes", c_byte * 127),
    ]


# 显示回调函数
DISPLAYCBFUN = fun_ctype(None, c_long, c_char_p, c_long, c_long, c_long, c_long, c_long, c_long)
# 解码回调函数
DECCBFUNWIN = fun_ctype(None, c_long, POINTER(c_char), c_long, POINTER(FRAME_INFO), c_void_p, c_void_p)
