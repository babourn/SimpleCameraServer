
import cv2
import time
from datetime import datetime
import os
import argparse
import threading
from imutils.video.videostream import  VideoStream
from utils import server

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", type=str,
                    help="path to optional output video file")
    ap.add_argument("-i", "--input", type=str,
                    help="path to optional output video file")
    ap.add_argument("-u", "--use-pi-camera",
                    help="use an rpi camera")
    ap.add_argument("-b", "--bottle-server", action="store_true",
                    help="enable a local bottle server to stream images")
    ap.add_argument("-r", "--resolution", type=tuple, default=(320, 480),
                    help="Set stream resolution")
    args = vars(ap.parse_args())

    if args["bottle_server"] is not None:
        t = threading.Thread(target=server.serve, args=())
        t.daemon = True
        t.start()

    writer = None
    vs = None

    if args["input"] is None:
        print("[INFO] starting video stream...")
        # vs = VideoStream(src=0).start()
        vs = VideoStream(usePiCamera=args["use_pi_camera"],
                         resolution=args["resolution"])
        vs.start()
        time.sleep(2.0)

    # otherwise, grab a reference to the video file
    else:
        print("[INFO] opening video file...")
        vs = cv2.VideoCapture(args["input"])

    while True:
        frame = vs.read()
        frame = frame[1] if args["input"] is not None else frame

        # if we are viewing a video and we did not grab a frame then we
        # have reached the end of the video
        if args["input"] is not None and frame is None:
            break

        if writer is None and args["output"] is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H:%M:%S")
            filename = "{}_vanilla.avi".format(timestamp)
            output_path = os.path.join(args["output"], filename)

            (H, W) = frame.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
            writer = cv2.VideoWriter(output_path, fourcc, 30, (W, H), True)

        if writer is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            writer.write(rgb)

        if args["bottle_server"] is not None:
            with server.lock:
                server.outputFrame = frame

    print("Shutting Down")
    vs.close()
    if writer is not None:
        writer.release()
