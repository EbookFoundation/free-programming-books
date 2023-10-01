import cv2
import numpy as np

# Initialize the camera
cap = cv2.VideoCapture(0)

# Create a background subtractor
fgbg = cv2.createBackgroundSubtractorMOG2()

while True:
    # Read a frame from the camera
    ret, frame = cap.read()

    # Apply background subtraction to detect motion
    fgmask = fgbg.apply(frame)

    # Threshold the foreground mask to create a binary image
    threshold = 50
    fgmask[fgmask < threshold] = 0
    fgmask[fgmask >= threshold] = 255

    # Find contours in the binary image
    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Draw rectangles around detected motion areas
    for contour in contours:
        if cv2.contourArea(contour) > 1000:  # Adjust this threshold as needed
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Display the frame with motion detection
    cv2.imshow('Motion Detection', frame)

    # Exit the loop when 'q' is pressed
    if cv2.waitKey(20) & 0xFF == ord('q'):
        break

# Release the camera and close all windows
cap.release()
cv2.destroyAllWindows()
