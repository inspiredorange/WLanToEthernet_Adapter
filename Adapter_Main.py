"""
WiFi to Ethernet Adapter for Philips Hue Bridge
For Raspberry Pico 2 with MicroPython

Dieses Skript erstellt einen Adapter, der WLAN mit Ethernet verbindet,
speziell für die Kommunikation mit einer Philips Hue Bridge.

WICHTIGER HINWEIS:
Der Raspberry Pi Pico 2 benötigt einen Ethernet-Controller, um mit Ethernet zu kommunizieren.
Eine direkte Verbindung eines Ethernet-Kabels mit dem Pico 2 ist ohne einen solchen Controller
nicht möglich. Alternativen zum W5500-Modul könnten sein:
- ENC28J60 Ethernet-Modul (benötigt andere Bibliothek)
- LAN8720 Ethernet-Modul (benötigt andere Bibliothek)
- USB-zu-Ethernet-Adapter (benötigt USB-Host-Funktionalität)

Fehlerbehebungen:
- Konfigurierbare Hue Bridge IP-Adresse hinzugefügt
- Verbesserte Fehlerbehandlung für Netzwerkkommunikation
- Timeouts für Socket-Verbindungen hinzugefügt
- Ordnungsgemäße Ressourcenbereinigung sichergestellt
- Ethernet-Initialisierung in eine Funktion verschoben
- Detailliertere Statusmeldungen hinzugefügt
"""

import network
import socket
import time
import machine
from machine import Pin

# Configuration - Replace with your network details
WIFI_SSID = "Feel Good Lounge"
WIFI_PASSWORD = "freieenergie"

# Hue Bridge configuration
HUE_BRIDGE_IP = "192.168.1.61"  # Replace with your Hue Bridge IP address on the Ethernet network

# Status LEDs
led_wifi = Pin(28, Pin.OUT)  # LED to indicate WiFi status
led_eth = Pin(27, Pin.OUT)   # LED to indicate Ethernet status
led_data = Pin(26, Pin.OUT)  # LED to indicate data transfer

# SPI pins for W5500 Ethernet module
spi_id = 0
sck = Pin(1)
mosi = Pin(3)
miso = Pin(4)
cs = Pin(2)
rst = Pin(5)

# Function to initialize Ethernet
def initialize_ethernet():
    # Reset the Ethernet module
    rst.value(0)
    time.sleep(0.1)
    rst.value(1)
    time.sleep(0.1)

    # Initialize SPI for Ethernet
    spi = machine.SPI(spi_id, baudrate=10000000, polarity=0, phase=0, sck=sck, mosi=mosi, miso=miso)

    # Initialize Ethernet using wiznet5k library
    try:
        import wiznet5k
        eth = wiznet5k.WIZNET5K(spi, cs, rst)
        # Use DHCP for Ethernet
        eth.dhcp_start()
        print("Ethernet initialized with IP:", eth.ifconfig()[0])
        led_eth.value(1)  # Turn on Ethernet LED
        return eth
    except ImportError:
        print("wiznet5k library not found. Please install it for Ethernet support.")
        led_eth.value(0)
        return None
    except Exception as e:
        print("Error initializing Ethernet:", e)
        led_eth.value(0)
        return None

# Connect to WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting to WiFi...")
        led_wifi.value(0)  # WiFi LED off while connecting
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        # Wait for connection with timeout
        max_wait = 10
        while max_wait > 0:
            if wlan.isconnected():
                break
            max_wait -= 1
            print("Waiting for connection...")
            time.sleep(1)

        if wlan.isconnected():
            print("WiFi connected. IP:", wlan.ifconfig()[0])
            led_wifi.value(1)  # WiFi LED on when connected
            return wlan
        else:
            print("WiFi connection failed")
            led_wifi.value(0)
            return None
    else:
        print("Already connected to WiFi. IP:", wlan.ifconfig()[0])
        led_wifi.value(1)
        return wlan

# Packet forwarding function
def forward_packets(wlan, eth):
    # Create UDP socket for Hue Bridge discovery (SSDP)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('0.0.0.0', 1900))  # SSDP uses port 1900

    # Create TCP socket for Hue Bridge communication
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(('0.0.0.0', 80))  # HTTP uses port 80
    tcp_socket.listen(5)

    # Set non-blocking mode
    udp_socket.setblocking(False)
    tcp_socket.setblocking(False)

    print("Starting packet forwarding between WiFi and Ethernet")

    while True:
        # Check for UDP packets (SSDP discovery)
        try:
            data, addr = udp_socket.recvfrom(1024)
            led_data.value(1)  # Blink data LED

            # Forward from WiFi to Ethernet
            if addr[0] == wlan.ifconfig()[0]:
                eth_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    eth_socket.settimeout(2)  # Set a 2-second timeout
                    eth_socket.sendto(data, ('239.255.255.250', 1900))  # SSDP multicast address
                except (socket.timeout, OSError) as e:
                    print("Error forwarding to Ethernet:", e)
                finally:
                    eth_socket.close()

            # Forward from Ethernet to WiFi
            else:
                wifi_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    wifi_socket.settimeout(2)  # Set a 2-second timeout
                    wifi_socket.sendto(data, ('239.255.255.250', 1900))
                except (socket.timeout, OSError) as e:
                    print("Error forwarding to WiFi:", e)
                finally:
                    wifi_socket.close()

            led_data.value(0)  # Turn off data LED
        except (BlockingIOError, OSError) as e:
            # BlockingIOError is expected in non-blocking mode when no data is available
            if not isinstance(e, BlockingIOError):
                print("UDP socket error:", e)

        # Check for TCP connections (HTTP API)
        try:
            client, addr = tcp_socket.accept()
            client.setblocking(True)
            led_data.value(1)  # Blink data LED

            try:
                # Receive data from client with timeout
                client.settimeout(3)
                request = client.recv(1024)

                if request:
                    # Forward to Hue Bridge using the configured IP address
                    hue_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    hue_socket.settimeout(5)  # Set a 5-second timeout
                    try:
                        hue_socket.connect((HUE_BRIDGE_IP, 80))
                        hue_socket.send(request)

                        # Get response from Hue Bridge
                        response = hue_socket.recv(4096)

                        # Send response back to client
                        client.send(response)
                    except (socket.timeout, OSError) as e:
                        print("Error communicating with Hue Bridge:", e)
                        # Send a simple error response to the client
                        client.send(b"HTTP/1.1 503 Service Unavailable\r\nContent-Type: text/plain\r\n\r\nCannot connect to Hue Bridge")
                    finally:
                        hue_socket.close()
                else:
                    print("Received empty request from client")
            except (socket.timeout, OSError) as e:
                print("Error receiving data from client:", e)
            finally:
                client.close()
                led_data.value(0)  # Turn off data LED
        except (BlockingIOError, OSError) as e:
            # BlockingIOError is expected in non-blocking mode when no connection is available
            if not isinstance(e, BlockingIOError):
                print("TCP socket error:", e)

        # Brief pause to prevent CPU overload
        time.sleep(0.01)

# Main function
def main():
    print("Starting WiFi to Ethernet Adapter for Philips Hue Bridge")

    # Connect to WiFi
    wlan = connect_wifi()
    if not wlan:
        print("Cannot proceed without WiFi connection")
        return

    # Initialize Ethernet
    eth = initialize_ethernet()
    if not eth:
        print("Cannot proceed without Ethernet connection")
        return

    # Check if Ethernet is connected
    if not eth.isconnected():
        print("Ethernet not connected")
        led_eth.value(0)
        return

    print("Both WiFi and Ethernet are connected and ready")
    print("WiFi IP:", wlan.ifconfig()[0])
    print("Ethernet IP:", eth.ifconfig()[0])
    print("Hue Bridge IP (configured):", HUE_BRIDGE_IP)

    # Start packet forwarding
    try:
        forward_packets(wlan, eth)
    except Exception as e:
        print("Error in packet forwarding:", e)
        # Blink both LEDs to indicate error
        for _ in range(5):
            led_wifi.value(1)
            led_eth.value(1)
            time.sleep(0.2)
            led_wifi.value(0)
            led_eth.value(0)
            time.sleep(0.2)

# Run the main function
if __name__ == "__main__":
    main()
