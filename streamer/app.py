from flask import Flask, render_template, Response

from camera import VideoCamera

flask_app = Flask(__name__)


@flask_app.route('/')
def index():
    return render_template('index.html')


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@flask_app.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def run():
    flask_app.run(host='0.0.0.0', debug=False)


if __name__ == "__main__":
    run()
