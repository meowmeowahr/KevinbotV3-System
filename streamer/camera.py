import cv2


class VideoCamera(object):
    def __init__(self):
        # self.video = cv2.VideoCapture(r"libcamerasrc ! video/x-raw, width=640, height=480, framerate=24/1 !
        # videoconvert ! videoscale ! appsink", cv2.CAP_GSTREAMER)
        self.video = cv2.VideoCapture(0)

    def __del__(self):
        self.video.release()

    def get_frame(self):
        success, image = self.video.read()
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()
