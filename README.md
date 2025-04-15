# 简介
本库使你能够像OpenCV调用RTSP流一样调用海康相机的SDK，实现低延迟视频取流。

# 优点
1.SDK取流最大的优点：延时低，RTSP取流延时一般在1-2s左右（主码流），SDK取流延时约为200ms。

2.SDK的稳定性：官方出品SDK，稳定性高于RTSP等协议，断流、卡顿较少，同时本库进行了优化，通过多线程队列取帧，保证帧的实时性，抛弃旧帧。

3.使用OpenCV作为底层，降低学习成本。

# 快速开始
### 1.安装
```shell
pip install hksdk
```
### 2.运行
```python
import cv2
from hksdk import VideoCapture

if __name__ == '__main__':
    cap = VideoCapture('192.168.10.170', 'admin', 'ryzh123456')
    while True:
        frame = cap.read()
        cv2.imshow("frame", frame)
        if chr(cv2.waitKey(1) & 255) == 'q':
            break
   ```
