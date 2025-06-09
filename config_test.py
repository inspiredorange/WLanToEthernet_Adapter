"""
Konfigurationstest für den WiFi zu Ethernet Adapter
Dieses Skript überprüft, ob die benutzerdefinierten Konfigurationen korrekt beibehalten wurden.
"""

import machine
from machine import Pin

# Lade die Konfigurationen aus der Hauptdatei
from main import (
    WIFI_SSID, WIFI_PASSWORD, HUE_BRIDGE_IP,
    SCK_PIN, MOSI_PIN, MISO_PIN, CS_PIN, RST_PIN,
    WIFI_LED_PIN, ETH_LED_PIN, DATA_LED_PIN
)

def test_configurations():
    """Überprüft, ob alle Konfigurationen korrekt sind"""
    print("\n=== Konfigurationstest ===\n")

    # WLAN-Konfiguration überprüfen
    print("WLAN-Konfiguration:")
    print(f"  SSID: {WIFI_SSID}")
    print(f"  Passwort: {WIFI_PASSWORD}")
    print(f"  Erwartet: SSID='Feel Good Lounge', Passwort='freieenergie'")

    # Hue Bridge IP überprüfen
    print("\nHue Bridge Konfiguration:")
    print(f"  IP-Adresse: {HUE_BRIDGE_IP}")
    print(f"  Erwartet: IP='192.168.1.61'")

    # W5500 Pin-Konfiguration überprüfen
    print("\nW5500 Ethernet Modul Pin-Konfiguration:")
    print(f"  SCK: Pin {SCK_PIN}")
    print(f"  MOSI: Pin {MOSI_PIN}")
    print(f"  MISO: Pin {MISO_PIN}")
    print(f"  CS: Pin {CS_PIN}")
    print(f"  RST: Pin {RST_PIN}")
    print(f"  Erwartet: SCK=1, MOSI=3, MISO=4, CS=2, RST=5")

    # Status-LED Pin-Konfiguration überprüfen
    print("\nStatus-LED Pin-Konfiguration:")
    print(f"  WLAN-LED: Pin {WIFI_LED_PIN}")
    print(f"  Ethernet-LED: Pin {ETH_LED_PIN}")
    print(f"  Daten-LED: Pin {DATA_LED_PIN}")
    print(f"  Erwartet: WLAN=28, Ethernet=27, Daten=26")

    # Überprüfen, ob alle Konfigurationen korrekt sind
    all_correct = (
        WIFI_SSID == "Feel Good Lounge" and
        WIFI_PASSWORD == "freieenergie" and
        HUE_BRIDGE_IP == "192.168.1.61" and
        SCK_PIN == 1 and
        MOSI_PIN == 3 and
        MISO_PIN == 4 and
        CS_PIN == 2 and
        RST_PIN == 5 and
        WIFI_LED_PIN == 28 and
        ETH_LED_PIN == 27 and
        DATA_LED_PIN == 26
    )

    print("\n=== Testergebnis ===")
    if all_correct:
        print("BESTANDEN: Alle Konfigurationen wurden korrekt beibehalten!")
    else:
        print("FEHLGESCHLAGEN: Einige Konfigurationen stimmen nicht mit den erwarteten Werten überein.")

    return all_correct

# Test ausführen
if __name__ == "__main__":
    test_configurations()

    # Blinke alle LEDs, wenn der Test erfolgreich war
    if test_configurations():
        print("\nBlinke LEDs zur Bestätigung...")
        wifi_led = Pin(WIFI_LED_PIN, Pin.OUT)
        eth_led = Pin(ETH_LED_PIN, Pin.OUT)
        data_led = Pin(DATA_LED_PIN, Pin.OUT)

        for _ in range(3):
            wifi_led.value(1)
            eth_led.value(1)
            data_led.value(1)
            machine.time.sleep(0.5)
            wifi_led.value(0)
            eth_led.value(0)
            data_led.value(0)
            machine.time.sleep(0.5)
