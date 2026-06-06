import cv2
import pyvirtualcam
import threading
import sys
import pythoncom  # 👈 IMPORTANTE
import ctypes

from pyvirtualcam import PixelFormat
from pygrabber.dshow_graph import FilterGraph
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
from threading import Event


WIDTH = 640
HEIGHT = 480
FPS = 30
KEYWORDS = ("ps3", "eye")

running = True
exit_event = Event()
cap = None


ctypes.windll.user32.ShowWindow(
    ctypes.windll.kernel32.GetConsoleWindow(), 0
)

def find_ps3_eye():
    graph = FilterGraph()
    devices = graph.get_input_devices()

    print("Dispositivos detectados:")
    for i, name in enumerate(devices):
        print(f"[{i}] {name}")
        if any(k in name.lower() for k in KEYWORDS):
            print(f"✔ PS3 Eye encontrada: {name}")
            return i

    raise RuntimeError("No se encontró la PS3 Eye")


def camera_loop():
    global cap

    pythoncom.CoInitialize()

    try:
        cam_index = find_ps3_eye()

        cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FPS, FPS)

        if not cap.isOpened():
            print("No se pudo abrir la PS3 Eye")
            return

        with pyvirtualcam.Camera(
            width=WIDTH,
            height=HEIGHT,
            fps=FPS,
            fmt=PixelFormat.BGR
        ) as cam:

            print(f"Cámara virtual activa: {cam.device}")

            while not exit_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    continue

                frame = cv2.resize(frame, (WIDTH, HEIGHT))
                cam.send(frame)
                cam.sleep_until_next_frame()

        cap.release()

    finally:
        pythoncom.CoUninitialize()

def create_image():
    image = Image.new("RGB", (64, 64), "black")
    dc = ImageDraw.Draw(image)
    dc.rectangle((16, 16, 48, 48), fill="white")
    return image


def on_exit(icon, item):
    exit_event.set()
    icon.stop()


def main():
    thread = threading.Thread(
        target=camera_loop,
        daemon=True
    )
    thread.start()

    icon = Icon(
        "PS3EyeVirtualCam",
        create_image(),
        "PS3 Eye → VirtualCam",
        menu=Menu(
            MenuItem("Salir", on_exit)
        )
    )

    icon.run()


if __name__ == "__main__":
    main()
