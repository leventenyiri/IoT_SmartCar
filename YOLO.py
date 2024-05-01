import os
import time
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import yaml

# Path to your YOLOv5 directory
YOLOV5_DIR = r'C:\IoT_SmartCar\Python\yolov5'
# Directory to watch for new images
WATCH_DIRECTORY = r'C:\IoT_SmartCar\Python\new_image'
# File to store results
RESULTS_FILE = r'C:\IoT_SmartCar\Python\result\detection_results.txt'
# Path to the class labels file
CLASS_NAMES_FILE = r'C:\IoT_SmartCar\Python\yolov5\data\coco.yaml'

def load_class_labels(names_file_path):
    with open(names_file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    return data['names']

class_labels = load_class_labels(CLASS_NAMES_FILE)

# Function to clear the results file before starting the observer
def initialize_results_file():
    with open(RESULTS_FILE, 'w') as f:
        f.write("")

def read_and_write_detection_results(image_path, results_file, class_labels):
    labels_dir = os.path.join(YOLOV5_DIR, 'runs/detect/exp/labels')
    base_name = os.path.basename(image_path)
    base_name_no_ext = os.path.splitext(base_name)[0]
    txt_file_path = os.path.join(labels_dir, f'{base_name_no_ext}.txt')

    if os.path.exists(txt_file_path):
        with open(txt_file_path, 'r') as file:
            detections = file.readlines()
        with open(results_file, 'w') as f:
            f.write(f'Detection Results for {image_path}:\n')
            for detection in detections:
                class_id, x_center, y_center, width, height = map(float, detection.split())
                class_name = class_labels[int(class_id)]
                f.write(f'{class_name} detected at ({x_center}, {y_center}, {width}, {height})\n')

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
                time.sleep(5)
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

        read_and_write_detection_results(image_path, RESULTS_FILE, class_labels)

if __name__ == "__main__":
    w = Watcher(WATCH_DIRECTORY)
    w.run()
