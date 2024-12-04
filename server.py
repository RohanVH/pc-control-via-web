from flask import Flask, render_template, Response, request, jsonify
import cv2
import numpy as np
import pyautogui
import base64
from PIL import ImageGrab, Image, ImageDraw
import threading
import time
import json
from io import BytesIO
import win32gui
import win32con
import win32api
import os
from flask_socketio import SocketIO
from engineio.async_drivers import threading as async_threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins='*', 
                   ping_timeout=10, ping_interval=5,
                   engineio_logger=True, logger=True)

# Configure PyAutoGUI
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

# Load cursor image
cursor_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
if not os.path.exists(cursor_dir):
    os.makedirs(cursor_dir)

def create_cursor_image():
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw white arrow with black border
    arrow_points = [(0, 0), (16, 16), (8, 16), (12, 24), (8, 24), (4, 16), (0, 16)]
    # Black border
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        border_points = [(x + dx, y + dy) for x, y in arrow_points]
        draw.polygon(border_points, fill='black')
    # White fill
    draw.polygon(arrow_points, fill='white')
    
    cursor_path = os.path.join(cursor_dir, 'cursor.png')
    img.save(cursor_path, 'PNG')
    return cursor_path

CURSOR_PATH = create_cursor_image()

def capture_screen():
    cursor_img = Image.open(CURSOR_PATH)
    while True:
        try:
            # Capture the screen
            screen = ImageGrab.grab()
            
            # Get cursor position
            cursor_x, cursor_y = win32gui.GetCursorPos()
            
            # Convert to RGBA to support transparency
            screen = screen.convert('RGBA')
            
            # Paste cursor at current position
            screen.paste(cursor_img, (cursor_x, cursor_y), cursor_img)
            
            # Convert back to RGB for JPEG
            screen = screen.convert('RGB')
            
            # Convert to bytes with lower quality for better performance
            img_byte_arr = BytesIO()
            screen.save(img_byte_arr, format='JPEG', quality=50)
            img_byte_arr = img_byte_arr.getvalue()
            
            # Convert to base64
            base64_frame = base64.b64encode(img_byte_arr).decode('utf-8')
            
            # Emit the frame
            try:
                socketio.emit('screen_update', {'image': base64_frame})
            except Exception as e:
                print(f"Error emitting screen: {e}")
            
            time.sleep(0.1)  # 10 FPS for better compatibility
            
        except Exception as e:
            print(f"Error in capture_screen: {e}")
            time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    screen_width, screen_height = pyautogui.size()
    socketio.emit('screen_size', {'width': screen_width, 'height': screen_height})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('mouse_move')
def handle_mouse_move(data):
    try:
        screen_width, screen_height = pyautogui.size()
        client_x = float(data['x'])
        client_y = float(data['y'])
        client_width = float(data['screenWidth'])
        client_height = float(data['screenHeight'])
        
        scale_x = screen_width / client_width
        scale_y = screen_height / client_height
        
        x = int(client_x * scale_x)
        y = int(client_y * scale_y)
        
        x = max(0, min(x, screen_width - 1))
        y = max(0, min(y, screen_height - 1))
        
        win32api.SetCursorPos((x, y))
    except Exception as e:
        print(f"Error in mouse_move: {e}")

@socketio.on('mouse_click')
def handle_mouse_click(data):
    try:
        button = data.get('button', 'left')
        clicks = data.get('clicks', 1)
        
        button_map = {
            'left': (win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_LEFTUP),
            'right': (win32con.MOUSEEVENTF_RIGHTDOWN, win32con.MOUSEEVENTF_RIGHTUP)
        }
        
        down_event, up_event = button_map.get(button, button_map['left'])
        
        for _ in range(clicks):
            win32api.mouse_event(down_event, 0, 0, 0, 0)
            time.sleep(0.05)
            win32api.mouse_event(up_event, 0, 0, 0, 0)
            time.sleep(0.05)
    except Exception as e:
        print(f"Error in mouse_click: {e}")

@socketio.on('mouse_down')
def handle_mouse_down(data):
    try:
        button = data.get('button', 'left')
        if button == 'left':
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        elif button == 'right':
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    except Exception as e:
        print(f"Error in mouse_down: {e}")

@socketio.on('mouse_up')
def handle_mouse_up(data):
    try:
        button = data.get('button', 'left')
        if button == 'left':
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        elif button == 'right':
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    except Exception as e:
        print(f"Error in mouse_up: {e}")

@socketio.on('key_press')
def handle_key_press(data):
    try:
        key = data['key']
        if key == 'enter':
            pyautogui.press('enter')
        elif key == 'backspace':
            pyautogui.press('backspace')
        elif key == 'space':
            pyautogui.press('space')
        elif len(key) == 1:
            pyautogui.write(key)
    except Exception as e:
        print(f"Error in key_press: {e}")

@socketio.on('special_key')
def handle_special_key(data):
    try:
        key = data['key']
        pyautogui.press(key)
    except Exception as e:
        print(f"Error in special_key: {e}")

if __name__ == '__main__':
    # Start screen capture in a separate thread
    threading.Thread(target=capture_screen, daemon=True).start()
    # Run the Flask app with debug mode off for better performance
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
