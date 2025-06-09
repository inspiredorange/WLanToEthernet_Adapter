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
    
    # Hardware Reset mit längeren Wartezeiten
    rst.value(0)
    time.sleep(1.0)  # Längere Reset-Zeit
    rst.value(1)
    time.sleep(1.0)  # Längere Aufwachzeit
    
    print("Konfiguriere SPI...")
    # SPI mit niedrigerer Geschwindigkeit für die Diagnose
    spi = machine.SPI(spi_id,
                      baudrate=100000,  # Reduziert auf 100 kHz
                      polarity=0,
                      phase=0,
                      bits=8,
                      firstbit=machine.SPI.MSB,
                      sck=sck,
                      mosi=mosi,
                      miso=miso)
    
    def read_register(address):
        """Liest ein Register vom W5500"""
        cs.value(0)
        time.sleep(0.001)
        
        # Sende Adresse und Kontrollbyte
        spi.write(bytes([address >> 8]))    # Adresse High
        spi.write(bytes([address & 0xFF]))  # Adresse Low
        spi.write(bytes([0x00]))           # Kontrollbyte für Lesen
        
        # Lese Daten
        result = bytearray(1)
        spi.readinto(result)
        
        cs.value(1)
        time.sleep(0.001)
        return result[0]
    
    try:
        print("\nDiagnose-Test:")
        
        # Teste Chip-Version
        version = read_register(0x0039)
        print(f"Chip Version: 0x{version:02x} (erwartet: 0x04)")
        
        # Teste Mode Register
        mode = read_register(0x0000)
        print(f"Mode Register: 0x{mode:02x}")
        
        if version != 0x04:
            print("\nFehlerdiagnose:")
            print("1. Überprüfen Sie die Stromversorgung (3.3V)")
            print("2. Überprüfen Sie die Verkabelung:")
            print(f"   - SCK:  GPIO{sck.id()}")
            print(f"   - MOSI: GPIO{mosi.id()}")
            print(f"   - MISO: GPIO{miso.id()}")
            print(f"   - CS:   GPIO{cs.id()}")
            print(f"   - RST:  GPIO{rst.id()}")
            print("3. Messen Sie die Signale mit einem Oszilloskop")
            raise Exception("W5500 antwortet nicht korrekt")
        
        print("\nChip-Test erfolgreich, initialisiere Netzwerk-Interface...")
        nic = wiznet5k.WIZNET5K(spi, cs, rst)
        nic.active(True)
        print("Ethernet-Interface aktiviert")
        
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


def bit_banging_spi_test():
    print("\nStarte Bit-Banging SPI Test...")
    
    # Pins konfigurieren
    sck.init(mode=machine.Pin.OUT)
    mosi.init(mode=machine.Pin.OUT)
    miso.init(mode=machine.Pin.IN)
    cs.init(mode=machine.Pin.OUT)
    rst.init(mode=machine.Pin.OUT)
    
    # Initiale Pin-Zustände
    sck.value(0)
    mosi.value(0)
    cs.value(1)
    rst.value(1)
    
    def send_byte(byte_val):
        """Sendet ein Byte über Bit-Banging"""
        for i in range(8):
            # MSB first
            bit = (byte_val & 0x80) >> 7
            mosi.value(bit)
            time.sleep(0.001)  # 1ms Verzögerung
            
            # Clock pulse
            sck.value(1)
            time.sleep(0.001)
            sck.value(0)
            time.sleep(0.001)
            
            byte_val <<= 1
    
    def read_byte():
        """Liest ein Byte über Bit-Banging"""
        result = 0
        for i in range(8):
            sck.value(1)
            time.sleep(0.001)
            
            # Bit lesen
            bit = miso.value()
            result = (result << 1) | bit
            
            sck.value(0)
            time.sleep(0.001)
        return result
    
    try:
        print("Hardware Reset...")
        rst.value(0)
        time.sleep(0.5)
        rst.value(1)
        time.sleep(0.5)
        
        print("\nLese W5500 Version Register...")
        cs.value(0)  # CS aktiv
        time.sleep(0.01)
        
        # Sende Adresse und Kommando für Version Register (0x0039)
        send_byte(0x00)  # Adresse High
        send_byte(0x39)  # Adresse Low
        send_byte(0x00)  # Lese-Kommando
        
        # Lese Antwort
        version = read_byte()
        
        cs.value(1)  # CS inaktiv
        time.sleep(0.01)
        
        print(f"Gelesener Wert: {hex(version)}")
        if version == 0x04:
            print("W5500 erfolgreich erkannt!")
        else:
            print("Unerwartete Version oder keine Antwort")
            print("\nBitte überprüfen:")
            print("1. MISO-Signalpegel mit Oszilloskop während der Übertragung")
            print("2. CS-Signal (sollte während der Übertragung LOW sein)")
            print("3. Spannung am W5500 (3.3V)")
            
    except Exception as e:
        print("Fehler beim SPI-Test:", e)

# Test ausführen
#bit_banging_spi_test()