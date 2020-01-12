"""
This demo will fill the screen with white, draw a black box on top
and then print Hello World! in the center of the display

This example is for use on (Linux) computers that are using CPython with
Adafruit Blinka to support CircuitPython libraries. CircuitPython does
not support PIL/pillow (python imaging library)!
"""

import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import redis
import json
import time
import os

# Define the Reset Pin
oled_reset = digitalio.DigitalInOut(board.D4)

# Change these
# to the right size for your display!
WIDTH = 128
HEIGHT = 32     # Change to 64 if needed
BORDER = 5

# Use for I2C.
i2c = board.I2C()
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3c, reset=oled_reset)

# Clear display.
oled.fill(0)
oled.show()

# Subscribe to redis messages
r = redis.Redis(host = os.getenv('REDIS_HOST', localhost), port = os.getenv('REDIS_PORT', 6379), db = 0, socket_keepalive = True, health_check_interval = 0)
p = r.pubsub(ignore_subscribe_messages = True)
p.subscribe('mhz19b', 'dh22')

mhz_message = None
dht_message = None

while True:
    message = p.get_message()
    if not message:
        time.sleep(1)
        continue

    # Clear display.
    oled.fill(0)
    oled.show()

    print(message)

    if message['channel'].decode('utf-8') == 'dh22':
        dht_message = json.loads(message['data'].decode('utf-8'))
    elif message['channel'].decode('utf-8') == 'mhz19b':
        mhz_message = json.loads(message['data'].decode('utf-8'))

    # Create blank image for drawing.
    # Make sure to create image with mode '1' for 1-bit color.
    image = Image.new('1', (oled.width, oled.height))

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype('arial.ttf', size = 14, encoding = 'unic')

    if dht_message:
        text = "{} C; {}%".format(dht_message['dht22_temperature'], dht_message['dht22_humidity'])
        draw.text((0, 0), text, font = font, fill = 188)

    if mhz_message:
        text = "{} ppm C02".format(mhz_message['mhz19_co2'])
        draw.text((0, 16), text, font = font, fill = 188)

    # Display image
    oled.image(image)
    oled.show()
