import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import glob

# Path to your YOLOv5 directory
YOLOV5_DIR = r'C:\IoT_SmartCar\Python\yolov5'
# Directory to watch for new images
WATCH_DIRECTORY = r'C:\IoT_SmartCar\Python\new_image'
# File to store results
RESULTS_FILE = r'C:\IoT_SmartCar\Python\result\detection_results.txt'

def read_and_write_detection_results(image_path, results_file):
    # Directory where YOLOv5 saves its text output
    labels_dir = os.path.join(YOLOV5_DIR, 'runs/detect/exp/labels')
    # Find the corresponding text file for the image
    base_name = os.path.basename(image_path)
    base_name_no_ext = os.path.splitext(base_name)[0]
    txt_file_path = os.path.join(labels_dir, f'{base_name_no_ext}.txt')

    # If the txt file exists, read it and append its contents to the results file
    if os.path.exists(txt_file_path):
        with open(txt_file_path, 'r') as file:
            contents = file.read()
        with open(results_file, 'a') as f:
            f.write(f'Detection Results for {image_path}:\n{contents}\n')
    else:
        # If no detection file is found, note that in the results
        with open(results_file, 'a') as f:
            f.write(f'No detections for {image_path}.\n')

class Watcher:
    def __init__(self, directory_to_watch):
        self.observer = Observer()
        self.directory_to_watch = directory_to_watch

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
    @staticmethod
    def on_created(event):
        if event.is_directory:
            return None

        elif event.src_path.endswith(".jpg"):
            print(f"Detected new image: {event.src_path}")
            # Run YOLOv5 detection
            subprocess.run([
                'python',
                os.path.join(YOLOV5_DIR, 'detect.py'),
                '--weights', 'yolov5s.pt',
                '--img', '640',
                '--conf', '0.25',
                '--source', event.src_path,
                '--save-txt',  # This saves results to a .txt file
                '--exist-ok'  # Overwrite existing files
            ], capture_output=True, text=True, encoding='utf-8')

            # Call the function to read and write detection results
            read_and_write_detection_results(event.src_path, RESULTS_FILE)

if __name__ == "__main__":
    w = Watcher(WATCH_DIRECTORY)
    w.run()
