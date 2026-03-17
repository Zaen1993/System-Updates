import time
import os

try:
    import cv2
    import numpy as np
    import requests
    HAS_LIB = True
    print(f"OpenCV version: {cv2.__version__}")
except ImportError as e:
    HAS_LIB = False
    LIB_ERROR = str(e)

def run_service():
    while True:
        if HAS_LIB:
            print(f"Service status: Active. OpenCV version: {cv2.__version__}")
        else:
            print(f"Service error: Libraries missing. {LIB_ERROR}")
        time.sleep(60)

if __name__ == '__main__':
    run_service()
