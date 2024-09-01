# import libraries
from vidgear.gears import VideoGear
from vidgear.gears import WriteGear
import cv2
import random

options = {"CAP_PROP_EXPOSURE": 25}
stream = VideoGear(source=0, stabilize=False, **options).start() # To open any valid video stream(for e.g device at 0 index)

frame_counter = 0
# infinite loop
rnd = random.randint(0, 100)
while True:

    frame = stream.read()
    frame_counter += 1
    # read stabilized frames

    # check if frame is None
    if frame is None:
        #if True break the infinite loop
        break

    # do something with stabilized frame here

    cv2.imshow("Stabilized Frame", frame)
    # Show output window

    key = cv2.waitKey(1) & 0xFF
    # check for 'q' key-press
    if key == ord("q"):
        #if 'q' key-pressed break out
        break
    elif key == ord("e"):
        cv2.imwrite(f"frame_{rnd}_{frame_counter}.png", frame)

cv2.destroyAllWindows()
# close output window

stream.stop()
# safely close video stream