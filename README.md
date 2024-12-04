# Web-Based PC Remote Control

This application allows you to control your PC through a web browser when devices are on the same network.

## Features
- Real-time screen sharing
- Mouse control
- Keyboard input
- Works on most modern and older browsers
- Secure local network operation

## Requirements
- Python 3.7 or higher
- Web browser
- Devices must be on the same network

## Installation

1. Install the required Python packages:
```
pip install -r requirements.txt
```

2. Run the server:
```
python server.py
```

3. Access the control panel:
- Open your web browser
- Navigate to `http://[YOUR_PC_IP]:5000`
  (Replace [YOUR_PC_IP] with your computer's local IP address)

## Usage
- The webpage will show your computer screen
- Move your mouse on the webpage to control the PC's cursor
- Click to perform mouse actions
- Type on your keyboard to send keystrokes to the PC

## Security Note
This application is designed for local network use only. Do not expose it to the internet without proper security measures.
