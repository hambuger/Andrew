import cv2
from openai_util.function_call.openaifunc_decorator import openai_func


@openai_func
def get_picture_from_camera():
    """
    从摄像头获取一张图片,并返回图片的路径
    :return: 图片的路径
    """
    # 创建一个 VideoCapture 对象
    cap = cv2.VideoCapture(0)

    # 检查是否成功打开摄像头
    if not cap.isOpened():
        print("Cannot open camera")
        exit()

    # 读取一帧图像
    ret, frame = cap.read()

    # 如果帧读取正确，ret 应该是 True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        exit()

    # 将图像保存到文件
    cv2.imwrite('temp.jpg', frame)

    # 释放摄像头
    cap.release()
    return 'temp.jpg'

# get_picture_from_camera()
