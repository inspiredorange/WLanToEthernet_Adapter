from wiznet5k import WIZNET5K
from machine import Pin, SPI
import wiznet5k_socket as socket
import sma_esp32_w5500_requests as requests

# SPI pins for W5500 Ethernet module on Raspberry Pi Pico W
SCK_PIN = 2    # GP2 as SCK
MOSI_PIN = 3   # GP3 as MOSI
MISO_PIN = 4   # GP4 as MISO
CS_PIN = 5     # GP5 as CS
RST_PIN = 6    # GP6 as RST

# Initialize SPI with proper pins for Raspberry Pi Pico W
spi = SPI(0,
          baudrate=100000,  # Reduced to 100 kHz for stability
          polarity=0,
          phase=0,
          bits=8,
          firstbit=SPI.MSB,
          sck=Pin(SCK_PIN),
          mosi=Pin(MOSI_PIN),
          miso=Pin(MISO_PIN))

cs = Pin(CS_PIN, Pin.OUT)
rst = Pin(RST_PIN, Pin.OUT)
nic = WIZNET5K(spi, cs, rst)

# Initialize a requests object with a socket and ethernet interface
requests.set_socket(socket, nic)
