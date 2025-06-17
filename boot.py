"""
Boot script for Raspberry Pi Pico W
This script runs automatically when the Pico starts up.
It flashes the LEDs in a specific sequence as requested.
"""

from machine import Pin
import time

# Define the LEDs
WIFI_LED_PIN = 28
DATA_LED_PIN = 26
ETH_LED_PIN = 27
BUILTIN_LED_PIN = 25  # Builtin LED on Raspberry Pi Pico

# Initialize the LEDs
led_wifi = Pin(WIFI_LED_PIN, Pin.OUT)
led_data = Pin(DATA_LED_PIN, Pin.OUT)
led_eth = Pin(ETH_LED_PIN, Pin.OUT)
led_builtin = Pin(BUILTIN_LED_PIN, Pin.OUT)

# Turn off all LEDs initially
led_wifi.value(0)
led_data.value(0)
led_eth.value(0)
led_builtin.value(0)

# Flash duration and gap between flashes (in seconds)
FLASH_DURATION = 0.033  # 2.22 ms
FLASH_GAP = 0.111  # 1.11 ms

# Function to flash a single LED
def flash_led(led):
    led.value(1)
    time.sleep(FLASH_DURATION)
    led.value(0)
    #time.sleep(FLASH_GAP)

# Sequence of LEDs in forward order
forward_sequence = [led_wifi, led_data, led_eth, led_builtin]
# Sequence of LEDs in reverse order
reverse_sequence = [led_builtin, led_eth, led_data, led_wifi]

# Flash the LEDs in the specified sequence 3 times
for _ in range(3):
    # Forward sequence
    for led in forward_sequence:
        flash_led(led)
    
    # Reverse sequence
    for led in reverse_sequence:
        flash_led(led)

print("Boot sequence completed")