"""
WiFi to Ethernet Adapter for Philips Hue Bridge
Optimized for Raspberry Pi Pico 2 W with MicroPython

Dieses Skript erstellt einen Adapter, der WLAN mit Ethernet verbindet,
speziell für die Kommunikation mit einer Philips Hue Bridge.

RASPBERRY PI PICO 2 W OPTIMIERUNGEN:
- Optimierte Speichernutzung für den neuen Chip
- Verbesserte SPI-Konfiguration für bessere Performance
- Optimierte Threading für Pico 2 W
- Reduzierte Puffergröße für bessere Stabilität
- Verbesserte Fehlerbehandlung für MicroPython

WICHTIGER HINWEIS:
Der Raspberry Pi Pico 2 W benötigt einen Ethernet-Controller, um mit Ethernet zu kommunizieren.
Eine direkte Verbindung eines Ethernet-Kabels mit dem Pico 2 W ist ohne einen solchen Controller
nicht möglich. Empfohlenes Modul: W5500 Ethernet-Modul

UMGEBUNGSHINWEIS:
Dieses Skript ist ausschließlich für die Ausführung auf einem Raspberry Pi Pico 2 W mit 
MicroPython-Firmware konzipiert. Es kann nicht in einer Standard-Python-Umgebung auf einem
Computer ausgeführt werden. Bitte folgen Sie den Anweisungen in der Datei 
'MicroPython_Installation.md', um die erforderliche Umgebung einzurichten.

PICO 2 W SPEZIFISCHE VERBESSERUNGEN:
- Optimierte Speicherverwaltung
- Verbesserte WiFi-Stabilität
- Optimierte SPI-Geschwindigkeit für W5500
- Reduzierte CPU-Last durch optimierte Polling-Intervalle
- Verbesserte Garbage Collection
- Optimierte Web-Interface-Performance
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
import _thread
import gc  # Garbage collection for memory optimization on Pico 2 W

# Import the web interface module
try:
    import webinterface
except ImportError:
    print("Web interface module not found. Web interface will not be available.")
    webinterface = None

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
    print("wiznet5k-Bibliothek erfolgreich installiert")

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
spi_id = 0     # Using SPI0 for GP18-GP19-GP16
SCK_PIN = 18   # GP18 als SCK (SPI0)
MOSI_PIN = 19  # GP19 als MOSI (SPI0)
MISO_PIN = 16  # GP16 als MISO (SPI0)
CS_PIN = 17    # GP17 als CS
RST_PIN = 20   # GP20 als RST
sck = Pin(SCK_PIN)
mosi = Pin(MOSI_PIN)
miso = Pin(MISO_PIN)
cs = Pin(CS_PIN)
rst = Pin(RST_PIN)

# Function to initialize Ethernet with improved debugging and error handling
def initialize_ethernet():
    log_message("\nInitialisiere Ethernet...")
    log_message("Hardware Reset...")

    # Hardware Reset nach W5500 Datenblatt-Empfehlungen
    rst.value(1)  # Ensure RST is high initially
    time.sleep(0.1)  # Longer initial delay for stability
    rst.value(0)  # Pull RST low for reset
    time.sleep(0.05)  # Longer reset time for reliability (datasheet requires at least 2ms)
    rst.value(1)  # Release reset
    time.sleep(0.2)  # Longer stabilization time for reliability

    # Comprehensive SPI configurations for troubleshooting
    spi_configs = [
        # Try different SPI modes to find the correct one
        {
            "baudrate": 1000000,  # Start with conservative 1 MHz
            "polarity": 0,
            "phase": 0,
            "bits": 8,
            "firstbit": machine.SPI.MSB,
            "description": "Mode 0 (CPOL=0, CPHA=0) - 1MHz"
        },
        {
            "baudrate": 1000000,
            "polarity": 0,
            "phase": 1,
            "bits": 8,
            "firstbit": machine.SPI.MSB,
            "description": "Mode 1 (CPOL=0, CPHA=1) - 1MHz"
        },
        {
            "baudrate": 1000000,
            "polarity": 1,
            "phase": 0,
            "bits": 8,
            "firstbit": machine.SPI.MSB,
            "description": "Mode 2 (CPOL=1, CPHA=0) - 1MHz"
        },
        {
            "baudrate": 1000000,
            "polarity": 1,
            "phase": 1,
            "bits": 8,
            "firstbit": machine.SPI.MSB,
            "description": "Mode 3 (CPOL=1, CPHA=1) - 1MHz"
        },
        # Try higher speeds with the most common mode
        {
            "baudrate": 2000000,
            "polarity": 0,
            "phase": 0,
            "bits": 8,
            "firstbit": machine.SPI.MSB,
            "description": "Mode 0 (CPOL=0, CPHA=0) - 2MHz"
        },
        {
            "baudrate": 4000000,
            "polarity": 0,
            "phase": 0,
            "bits": 8,
            "firstbit": machine.SPI.MSB,
            "description": "Mode 0 (CPOL=0, CPHA=0) - 4MHz"
        }
    ]

    # Try each SPI configuration
    for i, config in enumerate(spi_configs):
        log_message(f"Konfiguriere SPI (Versuch {i+1}/{len(spi_configs)})...")
        log_message(f"SPI-Konfiguration: {config['description']}")
        log_message(f"Details: baudrate={config['baudrate']}, polarity={config['polarity']}, phase={config['phase']}")

        try:
            # Initialize SPI with current configuration
            spi = machine.SPI(spi_id,
                              baudrate=config['baudrate'],
                              polarity=config['polarity'],
                              phase=config['phase'],
                              bits=config['bits'],
                              firstbit=config['firstbit'],
                              sck=sck,
                              mosi=mosi,
                              miso=miso)

            # Longer pause after SPI initialization for stability
            time.sleep(0.1)

            log_message(f"\nInitialisiere Netzwerk-Interface (Versuch {i+1}/{len(spi_configs)})...")

            # Test basic SPI communication before initializing WIZNET5K
            log_message("Teste grundlegende SPI-Kommunikation...")

            # Try to perform a simple SPI test
            try:
                # Test CS pin control
                cs.value(0)
                time.sleep(0.01)
                cs.value(1)
                time.sleep(0.01)
                log_message("CS-Pin-Test erfolgreich")

                # Test basic SPI write/read
                cs.value(0)
                time.sleep(0.005)
                # Try to read version register (should be 0x04 for W5500)
                spi.write(bytes([0x00]))  # Address high byte
                time.sleep(0.002)
                spi.write(bytes([0x39]))  # Address low byte (version register)
                time.sleep(0.002)
                spi.write(bytes([0x00]))  # Read command
                time.sleep(0.005)
                result = bytearray(1)
                spi.readinto(result)
                time.sleep(0.005)
                cs.value(1)
                time.sleep(0.002)

                log_message(f"SPI-Test: Version-Register = 0x{result[0]:02x} (erwartet: 0x04)")

                if result[0] == 0x04:
                    log_message("SPI-Kommunikation erfolgreich! W5500 erkannt.")
                elif result[0] == 0x00:
                    log_message("WARNUNG: SPI-Kommunikation fehlgeschlagen - alle Reads geben 0x00 zurück")
                    log_message("Mögliche Ursachen:")
                    log_message("- Falsche SPI-Verkabelung (MISO/MOSI vertauscht?)")
                    log_message("- Defektes W5500-Modul")
                    log_message("- Falsche SPI-Mode-Konfiguration")
                    log_message("- Stromversorgungsprobleme")
                    continue  # Try next configuration
                else:
                    log_message(f"SPI-Kommunikation teilweise erfolgreich, aber unerwartete Chip-Version: 0x{result[0]:02x}")

            except Exception as spi_test_error:
                log_message(f"SPI-Test fehlgeschlagen: {spi_test_error}")
                continue  # Try next configuration

            # Initialize WIZNET5K with debug enabled
            nic = wiznet5k.WIZNET5K(spi, cs, rst, is_dhcp=False, debug=False)

            log_message("W5500 Chip erfolgreich initialisiert!")

            # Update Ethernet status in web interface
            if webinterface:
                spi_config_str = config['description']
                webinterface.update_ethernet_status(
                    initialized=True,
                    link_status=nic.link_status,
                    spi_config=spi_config_str,
                    error_message="None"
                )

            # Set static IP configuration
            # Use a different subnet than WiFi to avoid conflicts
            # Assuming WiFi is on 192.168.188.x, we'll use 192.168.1.x for Ethernet
            ip_addr = [192, 168, 1, 111]  # IP address
            subnet = [255, 255, 255, 0]   # Subnet mask
            gateway = [192, 168, 1, 1]    # Gateway
            dns = [8, 8, 8, 8]            # DNS server

            log_message("Setze statische IP-Konfiguration...")
            nic.set_ifconfig((ip_addr, subnet, gateway, dns))

            # Check if IP is all zeros and provide a more meaningful message
            ip_bytes = nic.ifconfig[0]
            if all(b == 0 for b in ip_bytes):
                log_message("Ethernet-Interface aktiviert, aber IP-Adresse konnte nicht gesetzt werden (0.0.0.0)")
                log_message("Dies könnte auf ein Problem mit der Ethernet-Hardware oder -Verbindung hinweisen.")
                if webinterface:
                    webinterface.update_ethernet_status(
                        error_message="IP address could not be set (0.0.0.0)"
                    )
            else:
                log_message(f"Ethernet-Interface aktiviert mit statischer IP: {nic.pretty_ip(ip_bytes)}")

            log_message(f"Link Status: {'Verbunden' if nic.link_status else 'Nicht verbunden'}")

            if not nic.link_status:
                log_message("HINWEIS: Kein Ethernet-Kabel erkannt. Bitte prüfen Sie:")
                log_message("- Ist ein Ethernet-Kabel angeschlossen?")
                log_message("- Ist das andere Ende des Kabels mit einem aktiven Netzwerk verbunden?")
                log_message("- Funktioniert das Ethernet-Kabel (testen Sie es mit einem anderen Gerät)?")

            return nic

        except Exception as e:
            log_message(f"Fehler bei der Ethernet-Initialisierung (Versuch {i+1}): {e}")
            log_message("Versuche alternative SPI-Konfiguration...")

            # Update Ethernet status in web interface
            if webinterface:
                spi_config_str = config['description']
                webinterface.update_ethernet_status(
                    initialized=False,
                    link_status=False,
                    spi_config=spi_config_str,
                    error_message=str(e)
                )

            # Continue to the next configuration

    # If all configurations failed
    log_message("Alle SPI-Konfigurationen fehlgeschlagen. Ethernet-Initialisierung nicht möglich.")
    log_message("\nFEHLERDIAGNOSE:")
    log_message("1. Überprüfen Sie die Verkabelung:")
    log_message("   - SCK: GP18 -> W5500 SCK")
    log_message("   - MOSI: GP19 -> W5500 MOSI")
    log_message("   - MISO: GP16 -> W5500 MISO")
    log_message("   - CS: GP17 -> W5500 CS")
    log_message("   - RST: GP20 -> W5500 RST")
    log_message("   - VCC: 3.3V -> W5500 VCC")
    log_message("   - GND: GND -> W5500 GND")
    log_message("2. Überprüfen Sie die Stromversorgung des W5500-Moduls")
    log_message("3. Stellen Sie sicher, dass keine anderen Geräte den SPI-Bus verwenden")
    log_message("4. Versuchen Sie ein anderes W5500-Modul")
    log_message("\nDer Adapter wird im WLAN-only-Modus gestartet.")

    # Update Ethernet status in web interface to show the failure
    if webinterface:
        webinterface.update_ethernet_status(
            initialized=False,
            link_status=False,
            spi_config="None - All configurations failed",
            error_message="All SPI configurations failed. Check wiring and hardware."
        )

    return None

# Connect to WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        log_message("Connecting to WiFi...")
        led_wifi.value(0)  # WiFi LED off while connecting
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        # Wait for connection with timeout
        max_wait = 10
        while max_wait > 0:
            if wlan.isconnected():
                break
            max_wait -= 1
            log_message("Waiting for connection...")
            time.sleep(1)

        if wlan.isconnected():
            log_message(f"WiFi connected. IP: {wlan.ifconfig()[0]}")
            led_wifi.value(1)  # WiFi LED on when connected
            return wlan
        else:
            log_message("WiFi connection failed")
            led_wifi.value(0)
            return None
    else:
        log_message(f"Already connected to WiFi. IP: {wlan.ifconfig()[0]}")
        led_wifi.value(1)
        return wlan

# Packet forwarding function
def forward_packets(wlan, eth):
    # Create UDP socket for Hue Bridge discovery (SSDP)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('0.0.0.0', 1900))  # SSDP uses port 1900

    # Create TCP socket for Hue Bridge communication
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(('0.0.0.0', 8080))  # Using port 8080 for packet forwarding to avoid conflict with web interface on port 80
    tcp_socket.listen(5)

    # Set non-blocking mode
    udp_socket.setblocking(False)
    tcp_socket.setblocking(False)

    # Check Ethernet link status
    ethernet_connected = eth.link_status
    if ethernet_connected:
        log_message("Starting packet forwarding between WiFi and Ethernet")
    else:
        log_message("Starting packet forwarding in limited mode (Ethernet link not detected)")
        log_message("Only WiFi to WiFi forwarding will be available")

    # Variables for periodic link status check and memory management
    last_link_check_time = time.time()
    last_gc_time = time.time()
    link_check_interval = 5  # Check link status every 5 seconds
    gc_interval = 30  # Run garbage collection every 30 seconds for Pico 2 W optimization

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
                        log_message(f"Error forwarding to Ethernet: {e}")
                    finally:
                        eth_socket.close()
                else:
                    # Skip forwarding to Ethernet if not connected
                    if REQUIRE_ETHERNET_LINK:
                        log_message("Cannot forward to Ethernet: link not connected")
                    # In non-required mode, silently skip forwarding to Ethernet

            # Forward from Ethernet to WiFi
            else:
                wifi_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    wifi_socket.settimeout(2)  # Set a 2-second timeout
                    wifi_socket.sendto(data, ('239.255.255.250', 1900))
                except (socket.timeout, OSError) as e:
                    log_message(f"Error forwarding to WiFi: {e}")
                finally:
                    wifi_socket.close()

            led_data.value(0)  # Turn off data LED
        except (BlockingIOError, OSError) as e:
            # BlockingIOError and EAGAIN (errno 11) are expected in non-blocking mode when no data is available
            if not isinstance(e, BlockingIOError) and not (isinstance(e, OSError) and e.errno == 11):
                log_message(f"UDP socket error: {e}")

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
                            log_message(f"Error communicating with Hue Bridge: {e}")
                            # Send a simple error response to the client
                            client.send(b"HTTP/1.1 503 Service Unavailable\r\nContent-Type: text/plain\r\n\r\nCannot connect to Hue Bridge")
                        finally:
                            hue_socket.close()
                    else:
                        # Ethernet link not connected, send error response
                        log_message("Cannot forward to Hue Bridge: Ethernet link not connected")
                        client.send(b"HTTP/1.1 503 Service Unavailable\r\nContent-Type: text/plain\r\n\r\nEthernet link not connected. Cannot reach Hue Bridge.")
                else:
                    log_message("Received empty request from client")
            except (socket.timeout, OSError) as e:
                log_message(f"Error receiving data from client: {e}")
            finally:
                client.close()
                led_data.value(0)  # Turn off data LED
        except (BlockingIOError, OSError) as e:
            # BlockingIOError and EAGAIN (errno 11) are expected in non-blocking mode when no connection is available
            if not isinstance(e, BlockingIOError) and not (isinstance(e, OSError) and e.errno == 11):
                log_message(f"TCP socket error: {e}")

        # Periodically check if Ethernet link status has changed
        current_time = time.time()
        if current_time - last_link_check_time > link_check_interval:
            last_link_check_time = current_time
            current_link_status = eth.link_status

            # If link status has changed, update the ethernet_connected variable
            if current_link_status != ethernet_connected:
                ethernet_connected = current_link_status
                if ethernet_connected:
                    log_message("Ethernet link connected! Full functionality restored.")
                    led_eth.value(1)  # Turn on Ethernet LED
                else:
                    log_message("Ethernet link disconnected! Operating in limited mode.")
                    led_eth.value(0)  # Turn off Ethernet LED

        # Periodic garbage collection for Pico 2 W memory optimization
        if current_time - last_gc_time > gc_interval:
            last_gc_time = current_time
            gc.collect()
            log_message(f"Memory cleanup: {gc.mem_free()} bytes free")

        # Optimized pause to prevent CPU overload while maintaining responsiveness
        time.sleep(0.005)  # Reduced from 0.01 to 0.005 for better responsiveness on Pico 2 W

# Function to log messages both to console and web interface
def log_message(message):
    print(message)
    if webinterface:
        webinterface.add_log(message)

# Function to start the web interface in a separate thread
def start_web_interface(wifi_ip, ethernet_ip, eth_available=False):
    if webinterface:
        log_message("Starting web interface in a separate thread...")
        try:
            # Update Ethernet status if not already set
            if not eth_available:
                webinterface.update_ethernet_status(
                    initialized=False,
                    link_status=False,
                    spi_config="None - Ethernet not available",
                    error_message="Ethernet module not initialized. Running in WiFi-only mode."
                )

            _thread.start_new_thread(webinterface.run_web_interface, (wifi_ip, ethernet_ip, HUE_BRIDGE_IP))
            log_message("Web interface thread started successfully")
        except Exception as e:
            log_message(f"Error starting web interface thread: {e}")
    else:
        log_message("Web interface not available")

# Main function
def main():
    log_message("Starting WiFi to Ethernet Adapter for Philips Hue Bridge")
    log_message("Optimized for Raspberry Pi Pico 2 W")

    # Initial garbage collection for optimal memory usage
    gc.collect()
    log_message(f"Initial free memory: {gc.mem_free()} bytes")

    # Connect to WiFi
    wlan = connect_wifi()
    if not wlan:
        log_message("Cannot proceed without WiFi connection")
        return

    # Memory cleanup after WiFi connection
    gc.collect()

    # Get WiFi IP address
    wifi_ip = wlan.ifconfig()[0]
    log_message(f"WiFi IP: {wifi_ip}")
    log_message(f"Hue Bridge IP (configured): {HUE_BRIDGE_IP}")
    log_message(f"Web interface will be available at: http://{wifi_ip}")
    log_message("Note: Do not add 'www.' before the IP address in your browser")

    # Start the web interface in a separate thread BEFORE Ethernet initialization
    # This ensures the web interface is available quickly even if Ethernet initialization takes time
    log_message("Starting web interface before Ethernet initialization...")
    start_web_interface(wifi_ip, "Initializing...", False)

    # Initialize Ethernet in a separate thread
    log_message("Starting Ethernet initialization in background...")

    # Initialize Ethernet
    eth = initialize_ethernet()
    if not eth:
        log_message("Warning: Ethernet initialization failed")
        log_message("Web interface will still be available via WiFi, but Ethernet features will be disabled")
        # Continue execution instead of returning, so web interface can still start

    # Set default values
    ethernet_ip = "0.0.0.0"
    ethernet_connected = False

    # Check if Ethernet is connected (only if eth is not None)
    if eth:
        ethernet_connected = eth.link_status
        if not ethernet_connected:
            log_message("Ethernet not connected")
            led_eth.value(0)
            if REQUIRE_ETHERNET_LINK:
                log_message("Cannot proceed without Ethernet link. Check cable connection.")
                return
            else:
                log_message("WARNING: Continuing without Ethernet link. Some features may not work correctly.")
                log_message("Connect an Ethernet cable to enable full functionality.")
        else:
            log_message("Both WiFi and Ethernet are connected and ready")
            led_eth.value(1)  # Turn on Ethernet LED

            # Check if IP is all zeros and provide a more meaningful message
            ip_bytes = eth.ifconfig[0]
            if all(b == 0 for b in ip_bytes):
                log_message("Ethernet IP: 0.0.0.0 (IP-Adresse konnte nicht gesetzt werden)")
            else:
                ethernet_ip = eth.pretty_ip(ip_bytes)
                log_message(f"Ethernet IP: {ethernet_ip}")
    else:
        log_message("WiFi is connected and ready (Ethernet not available)")
        led_eth.value(0)  # Ensure Ethernet LED is off

    # Update the web interface with the final Ethernet status
    if webinterface:
        webinterface.update_ip_addresses(wifi_ip, ethernet_ip, HUE_BRIDGE_IP)

    # Start packet forwarding only if Ethernet is available
    if eth:
        try:
            log_message("Starting packet forwarding between WiFi and Ethernet")
            forward_packets(wlan, eth)
        except Exception as e:
            log_message(f"Error in packet forwarding: {e}")
            # Blink both LEDs to indicate error
            for _ in range(5):
                led_wifi.value(1)
                led_eth.value(1)
                time.sleep(0.2)
                led_wifi.value(0)
                led_eth.value(0)
                time.sleep(0.2)
    else:
        log_message("Packet forwarding is disabled because Ethernet is not available")
        log_message("Only the web interface will be available via WiFi")
        # Keep the program running so the web interface remains accessible
        while True:
            # Blink WiFi LED to indicate the system is running in web-only mode
            led_wifi.value(not led_wifi.value())
            time.sleep(1)

# Run the main function
main()
