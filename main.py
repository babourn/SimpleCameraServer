
import cv2
import time
from datetime import datetime
import os
import argparse
import threading

from imutils.video.fps import FPS
from imutils.video.videostream import VideoStream

from utils import server
from utils.gracefulkiller import GracefulKiller

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", type=str,
                    help="path to optional output video file")
    ap.add_argument("-i", "--input", type=str,
                    help="path to optional output video file")
    ap.add_argument("-u", "--use-pi-camera", action="store_true",
                    help="use an rpi camera")
    ap.add_argument("-j", "--jetson", action="store_true",
                    help= "use for a jetson camera")
    ap.add_argument("-b", "--bottle-server", action="store_true",
                    help="enable a local bottle server to stream images")
    ap.add_argument("-w", "--width", type=int, default=3264,
                    help="Set stream resolution width")
    ap.add_argument("--height", type=int, default=2464,
                    help="Set stream resolution height")
    ap.add_argument("-f", "--framerate", type=int, default=21,
                    help="Set stream resolution")
    ap.add_argument("-d", "--display", action="store_true",
                    help="display video to a screen for monitor viewing stream")
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
        if args["jetson"]:
            src_string = "nvarguscamerasrc ! \
                        video/x-raw(memory:NVMM), width=(int){}, height=(int){}, format=(string)NV12, framerate=(fraction){}/1 ! \
                        nvvidconv ! video/x-raw, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink"
            src = src_string.format(args["width"], args["height"], args["framerate"])
            print("SRC_STRING: {}".format(src))
            vs = VideoStream(src=src,
                             resolution=(args["height"], args["width"]))
        elif args["use_pi_camera"]:
            vs = VideoStream(usePiCamera=False,
                             resolution=(args["height"], args["width"]))
        else:
            vs = VideoStream(usePiCamera=False,
                             resolution=(args["height"], args["width"]))
        vs.start()
        time.sleep(2.0)

    # otherwise, grab a reference to the video file
    else:
        print("[INFO] opening video file...")
        vs = cv2.VideoCapture(args["input"])

    killer = GracefulKiller()
    # fps = FPS().start()
    while not killer.kill_now:

        frame = vs.read()
        frame = frame[1] if args["input"] is not None else frame

        # if we are viewing a video and we did not grab a frame then we
        # have reached the end of the video
        if args["input"] is not None and frame is None:
            break

        if writer is None and args["output"] is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H\%M\%S")
            (H, W) = frame.shape[:2]

            if args["jetson"]:
                filename = "{}_vanilla.hevc".format(timestamp)
                output_path = os.path.join(args["output"], filename)
                output_pipeline = 'appsrc ! video/x-raw, format=BGR ! queue ! videoconvert ! video/x-raw,format=BGRx ! nvvidconv ! omxh265enc MeasureEncoderLatency=1 ! matroskamux ! filesink location={}'

                output_pipeline = output_pipeline.format(output_path)
                print("OUTPUT_PIPELINE: {}".format(output_pipeline))
                try:
                    fourcc = cv2.VideoWriter_fourcc(*"HEVC")
                    writer = cv2.VideoWriter(output_pipeline, cv2.CAP_GSTREAMER, fourcc, args["framerate"], (W, H), True)
                except Exception as e:
                    print(e)
                    break
            else:
                filename = "{}_vanilla.avi".format(timestamp)
                output_path = os.path.join(args["output"], filename)
                try:
                    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
                    writer = cv2.VideoWriter(output_path, fourcc, 30, (W, H),
                                             True)
                except Exception as e:
                    print(e)
                    break

            time.sleep(2)
            if not writer.isOpened():
                print("Failed to open writer")
                break

        if writer is not None:
            writer.write(frame)
            cv2.waitKey(1)

        if args["bottle_server"] is not None:
            with server.lock:
                server.outputFrame = frame
        # fps.update()
        #
        # if fps._numFrames % 100 is 0:
        #     fps.stop()
        #     print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
        #     print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
        #     fps = FPS().start()

        if args["display"]:
            cv2.imshow("Stream", frame)
            if cv2.waitKey(1) == 113:
                break

    # fps.stop()
    print("Shutting Down")
    vs.stop()
    if writer is not None:
        writer.release()
    cv2.destroyAllWindows()
