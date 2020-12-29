from bottle import template, static_file, response, Bottle
import threading
import imutils
import time
import cv2

outputFrame = None
lock = threading.Lock()
app = Bottle()

@app.route("/")
def index():
  return template('utils/views/index', feed=app.get_url('/feed'))

@app.route("/body.css")
def body():
  return static_file('body.css', root='./utils/views')

@app.route("/feed")
def feed():
  response.content_type = "multipart/x-mixed-replace; boundary=frame"
  return generate()

def generate():
  global outputFrame, lock

  while True:
    with lock:
      if outputFrame is None:
        continue
      (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
      if not flag:
        continue
    yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

def serve():
  app.run(host='0.0.0.0', port='1337', server='waitress')
