import cv2


def correct_camera_orientation(frame):
    return frame

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Camera not opened")

while True:
    ok, frame = cap.read()
    if not ok:
        break

    frame = correct_camera_orientation(frame)

    cv2.imshow("Camera Test", frame)
    if (cv2.waitKey(1) & 0xFF) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()