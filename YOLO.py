import os
import time
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import yaml
import cv2
import matplotlib.pyplot as plt
import urllib.request
import numpy as np
import concurrent.futures

# Path to your YOLOv5 directory
YOLOV5_DIR = r'C:\IoT_SmartCar\Python\yolov5'
# Directory to watch for new images
WATCH_DIRECTORY = r'C:\IoT_SmartCar\Python\new_image'
# File to store results
RESULTS_FILE = r'C:\IoT_SmartCar\Python\result\detection_results.txt'
# Path to the class labels file
CLASS_NAMES_FILE = r'C:\IoT_SmartCar\Python\yolov5\data\coco.yaml'

IMAGE_URL = "http://192.168.1.105/cam-hi.jpg"

label_array = [
    "person", "bicycle", "car", "motorcycle", "airplane",
    "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter", "bench", "bird",
    "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat",
    "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle",
    "wine glass", "cup", "fork", "knife", "spoon",
    "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut",
    "cake", "chair", "couch", "potted plant", "bed",
    "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven",
    "toaster", "sink", "refrigerator", "book", "clock",
    "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
]

url = "http://192.168.1.105/cam-hi.jpg"

i = 0

# Function to clear the results file before starting the observer
def initialize_results_file():
    with open(RESULTS_FILE, 'w') as f:
        f.write("")

def download_image(image_url, save_dir):
    image_path = os.path.join(save_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
    try:
        urllib.request.urlretrieve(image_url, image_path)
        print(f"Downloaded image saved to {image_path}")
        return image_path
    except Exception as e:
        print(f"Failed to download image: {str(e)}")
        return None

def read_and_write_detection_results(image_path, results_file):
    global i
    if i==0:
        labels_dir = os.path.join(YOLOV5_DIR, 'runs/detect/exp/labels')
    else:
        labels_dir = os.path.join(YOLOV5_DIR, f'runs/detect/exp{i}/labels')
        
    i = i+1
    base_name = os.path.basename(image_path)
    base_name_no_ext = os.path.splitext(base_name)[0]
    txt_file_path = os.path.join(labels_dir, f'{base_name_no_ext}.txt')

    if os.path.exists(txt_file_path):
        with open(txt_file_path, 'r') as file:
            detections = file.readlines()
        with open(results_file, 'a') as f:
            for detection in detections:
                class_id, x_center, y_center, width, height = map(float, detection.split())
                class_name = label_array[int(class_id)]
                f.write(f'{class_name} detected at (x:{x_center},y: {y_center},width: {width},height: {height})\n')

class Watcher:
    def __init__(self, directory_to_watch):
        self.observer = Observer()
        self.directory_to_watch = directory_to_watch
        initialize_results_file()  # Initialize the results file when the observer is created

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.directory_to_watch, recursive=True)
        self.observer.start()
        try:
            while True:
                # Download image at regular intervals
                image_path = download_image(IMAGE_URL, self.directory_to_watch)
                if image_path:
                    event_handler.process_image(image_path)
        except:
            self.observer.stop()
            print("Observer Stopped")
        self.observer.join()

class Handler(FileSystemEventHandler):
    def __init__(self):
        self.processed_files = set()

    def on_created(self, event):
        if event.is_directory or event.src_path in self.processed_files:
            return None
        if event.src_path.endswith(".jpg"):
            self.processed_files.add(event.src_path)
            self.process_image(event.src_path)

    def process_image(self, image_path):
        print("Pulling the image from the website...")
        print(f"Detected new image: {image_path}")
        subprocess.run([
            'python',
            os.path.join(YOLOV5_DIR, 'detect.py'),
            '--weights', 'yolov5s.pt',
            '--img', '640',
            '--conf', '0.25',
            '--source', image_path,
            '--save-txt'
        ], capture_output=True, text=True, encoding='utf-8')

        read_and_write_detection_results(image_path, RESULTS_FILE)

if __name__ == "__main__":
    w = Watcher(WATCH_DIRECTORY)
    w.run()
