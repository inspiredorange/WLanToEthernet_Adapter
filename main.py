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

UMGEBUNGSHINWEIS:
Dieses Skript ist ausschließlich für die Ausführung auf einem Raspberry Pi Pico 2 mit 
MicroPython-Firmware konzipiert. Es kann nicht in einer Standard-Python-Umgebung auf einem
Computer ausgeführt werden. Bitte folgen Sie den Anweisungen in der Datei 
'MicroPython_Installation.md', um die erforderliche Umgebung einzurichten.

Fehlerbehebungen:
- Konfigurierbare Hue Bridge IP-Adresse hinzugefügt
- Verbesserte Fehlerbehandlung für Netzwerkkommunikation
- Timeouts für Socket-Verbindungen hinzugefügt
- Ordnungsgemäße Ressourcenbereinigung sichergestellt
- Ethernet-Initialisierung in eine Funktion verschoben
- Detailliertere Statusmeldungen hinzugefügt
- Optionale Ethernet-Verbindung hinzugefügt (REQUIRE_ETHERNET_LINK = False)
- Automatische Erkennung von Änderungen des Ethernet-Link-Status
- Fortsetzen der Ausführung auch ohne Ethernet-Verbindung
"""

# Überprüfen, ob das Skript in der richtigen Umgebung ausgeführt wird
import sys
if 'micropython' not in sys.implementation.name.lower():
    print("FEHLER: Dieses Skript kann nur auf einem Raspberry Pi Pico 2 mit MicroPython ausgeführt werden.")
    print("Bitte folgen Sie den Anweisungen in der Datei 'MicroPython_Installation.md', um die")
    print("erforderliche Umgebung einzurichten und das Skript auf den Pico zu übertragen.")
    sys.exit(1)

# MicroPython-spezifische Importe
try:
    import network
except ImportError:
    print("FEHLER: Das 'network' Modul wurde nicht gefunden.")
    print("Bitte stellen Sie sicher, dass Sie die MicroPython-Firmware mit WLAN-Unterstützung installiert haben.")
    print("Folgen Sie den Anweisungen in der Datei 'MicroPython_Installation.md', Abschnitt 1.2:")
    print("Wählen Sie die Version mit WLAN-Unterstützung für Ihren Raspberry Pi Pico.")
    import sys
    sys.exit(1)

import socket
import time
import machine
from machine import Pin
import network
import machine
import time

# Define BlockingIOError if it's not available in MicroPython
try:
    BlockingIOError
except NameError:
    class BlockingIOError(OSError):
        pass

try:
    import wiznet5k
except ImportError:
    print("wiznet5k-Bibliothek nicht gefunden!")
    print("Installiere wiznet5k-Bibliothek...")
    import mip
    mip.install("wiznet5k")
    import wiznet5k

# Configuration - Replace with your network details
WIFI_SSID = "Feel Good Lounge"
WIFI_PASSWORD = "freieenergie"

# Hue Bridge configuration
HUE_BRIDGE_IP = "192.168.1.61"  # Replace with your Hue Bridge IP address on the Ethernet network

# Ethernet configuration
REQUIRE_ETHERNET_LINK = False  # Set to True to require Ethernet link to be connected

# Status LEDs
WIFI_LED_PIN = 28
ETH_LED_PIN = 27
DATA_LED_PIN = 26
led_wifi = Pin(WIFI_LED_PIN, Pin.OUT)  # LED to indicate WiFi status
led_eth = Pin(ETH_LED_PIN, Pin.OUT)   # LED to indicate Ethernet status
led_data = Pin(DATA_LED_PIN, Pin.OUT)  # LED to indicate data transfer

# SPI pins for W5500 Ethernet module
spi_id = 0     
SCK_PIN = 2    # GP2 als SCK
MOSI_PIN = 3   # GP3 als MOSI
MISO_PIN = 4   # GP4 als MISO
CS_PIN = 5     # GP5 als CS
RST_PIN = 6    # GP6 als RST
sck = Pin(SCK_PIN)
mosi = Pin(MOSI_PIN)
miso = Pin(MISO_PIN)
cs = Pin(CS_PIN)
rst = Pin(RST_PIN)

# Function to initialize Ethernet
def initialize_ethernet():
    print("\nInitialisiere Ethernet...")
    print("Hardware Reset...")

    # Hardware Reset nach W5500 Datenblatt-Empfehlungen mit optimierten Wartezeiten
    rst.value(1)  # Ensure RST is high initially
    time.sleep(0.1)  # Optimized initial delay
    rst.value(0)  # Pull RST low for reset
    time.sleep(0.1)  # Optimized reset time (datasheet requires at least 2ms)
    rst.value(1)  # Release reset
    time.sleep(0.2)  # Optimized stabilization time

    print("Konfiguriere SPI...")
    # SPI mit höherer Geschwindigkeit, da der int und reset Pin nicht mehr vertauscht sind
    spi = machine.SPI(spi_id,
                      baudrate=1000000,  # Erhöht auf 1 MHz für bessere Leistung
                      polarity=0,
                      phase=0,
                      bits=8,
                      firstbit=machine.SPI.MSB,
                      sck=sck,
                      mosi=mosi,
                      miso=miso)

    # Kürzere Pause nach SPI-Initialisierung für optimierte Leistung
    time.sleep(0.1)

    try:
        print("\nInitialisiere Netzwerk-Interface...")
        # Disable DHCP and use static IP configuration
        # Enable debug mode to see more information during initialization
        nic = wiznet5k.WIZNET5K(spi, cs, rst, is_dhcp=False, debug=True)

        print("W5500 Chip erfolgreich initialisiert!")

        # Set static IP configuration
        # Use a different subnet than WiFi to avoid conflicts
        # Assuming WiFi is on 192.168.188.x, we'll use 192.168.1.x for Ethernet
        ip_address = ('192.168.1.111', '255.255.255.0', '192.168.1.1', '8.8.8.8')
        nic.set_ifconfig(ip_address)

        # Check if IP is all zeros and provide a more meaningful message
        ip_bytes = nic.ifconfig[0]
        if all(b == 0 for b in ip_bytes):
            print("Ethernet-Interface aktiviert, aber IP-Adresse konnte nicht gesetzt werden (0.0.0.0)")
            print("Dies könnte auf ein Problem mit der Ethernet-Hardware oder -Verbindung hinweisen.")
        else:
            print("Ethernet-Interface aktiviert mit statischer IP:", nic.pretty_ip(ip_bytes))
        print("Link Status:", "Verbunden" if nic.link_status else "Nicht verbunden")

        return nic

    except Exception as e:
        print("Fehler bei der Ethernet-Initialisierung:", e)
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
        print("Already connected to WiFi Roli. IP:", wlan.ifconfig()[0])
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

    # Check Ethernet link status
    ethernet_connected = eth.link_status
    if ethernet_connected:
        print("Starting packet forwarding between WiFi and Ethernet")
    else:
        print("Starting packet forwarding in limited mode (Ethernet link not detected)")
        print("Only WiFi to WiFi forwarding will be available")

    # Variables for periodic link status check
    last_link_check_time = time.time()
    link_check_interval = 5  # Check link status every 5 seconds

    while True:
        # Check for UDP packets (SSDP discovery)
        try:
            data, addr = udp_socket.recvfrom(1024)
            led_data.value(1)  # Blink data LED

            # Forward from WiFi to Ethernet (only if Ethernet is connected)
            if addr[0] == wlan.ifconfig()[0]:
                if ethernet_connected:
                    eth_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    try:
                        eth_socket.settimeout(2)  # Set a 2-second timeout
                        eth_socket.sendto(data, ('239.255.255.250', 1900))  # SSDP multicast address
                    except (socket.timeout, OSError) as e:
                        print("Error forwarding to Ethernet:", e)
                    finally:
                        eth_socket.close()
                else:
                    # Skip forwarding to Ethernet if not connected
                    if REQUIRE_ETHERNET_LINK:
                        print("Cannot forward to Ethernet: link not connected")
                    # In non-required mode, silently skip forwarding to Ethernet

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
            # BlockingIOError and EAGAIN (errno 11) are expected in non-blocking mode when no data is available
            if not isinstance(e, BlockingIOError) and not (isinstance(e, OSError) and e.errno == 11):
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
                    if ethernet_connected:
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
                        # Ethernet link not connected, send error response
                        print("Cannot forward to Hue Bridge: Ethernet link not connected")
                        client.send(b"HTTP/1.1 503 Service Unavailable\r\nContent-Type: text/plain\r\n\r\nEthernet link not connected. Cannot reach Hue Bridge.")
                else:
                    print("Received empty request from client")
            except (socket.timeout, OSError) as e:
                print("Error receiving data from client:", e)
            finally:
                client.close()
                led_data.value(0)  # Turn off data LED
        except (BlockingIOError, OSError) as e:
            # BlockingIOError and EAGAIN (errno 11) are expected in non-blocking mode when no connection is available
            if not isinstance(e, BlockingIOError) and not (isinstance(e, OSError) and e.errno == 11):
                print("TCP socket error:", e)

        # Periodically check if Ethernet link status has changed
        current_time = time.time()
        if current_time - last_link_check_time > link_check_interval:
            last_link_check_time = current_time
            current_link_status = eth.link_status

            # If link status has changed, update the ethernet_connected variable
            if current_link_status != ethernet_connected:
                ethernet_connected = current_link_status
                if ethernet_connected:
                    print("Ethernet link connected! Full functionality restored.")
                    led_eth.value(1)  # Turn on Ethernet LED
                else:
                    print("Ethernet link disconnected! Operating in limited mode.")
                    led_eth.value(0)  # Turn off Ethernet LED

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
    if not eth.link_status:
        print("Ethernet not connected")
        led_eth.value(0)
        if REQUIRE_ETHERNET_LINK:
            print("Cannot proceed without Ethernet link. Check cable connection.")
            return
        else:
            print("WARNING: Continuing without Ethernet link. Some features may not work correctly.")
            print("Connect an Ethernet cable to enable full functionality.")

    if eth.link_status:
        print("Both WiFi and Ethernet are connected and ready")
        led_eth.value(1)  # Turn on Ethernet LED
    else:
        print("WiFi is connected and ready (Ethernet link not detected)")
        # Ethernet LED is already off from the previous check

    print("WiFi IP:", wlan.ifconfig()[0])
    # Check if IP is all zeros and provide a more meaningful message
    ip_bytes = eth.ifconfig[0]
    if all(b == 0 for b in ip_bytes):
        print("Ethernet IP: 0.0.0.0 (IP-Adresse konnte nicht gesetzt werden)")
    else:
        print("Ethernet IP:", eth.pretty_ip(ip_bytes))
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
main()
