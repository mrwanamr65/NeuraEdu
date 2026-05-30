import multiprocessing
import json


# متغيرات مشتركة لتتبع حالة النظام
manager = None
running_processes = None
system_running = None
stop_event = None


def initialize_multiprocessing():
    """Initialize multiprocessing variables."""
    global manager, running_processes, system_running, stop_event
    manager = multiprocessing.Manager()
    running_processes = manager.dict()  # لتخزين العمليات الجارية
    system_running = manager.Value('b', False)  # لتخزين حالة النظام (True إذا كان يعمل)
    stop_event = manager.Event()  # لإشعار العمليات بالتوقف


def load_config(config_file):
    pass

def start_camera_detection(config):
   pass


def start_attendance(config):
    pass

def start_system():
    pass
def stop_system():
    pass

def is_running():
    pass
