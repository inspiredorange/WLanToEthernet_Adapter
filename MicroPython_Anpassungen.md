# Anpassungen für MicroPython auf dem Raspberry Pi Pico 2 W

Dieses Dokument beschreibt die Änderungen, die am ursprünglichen `Adapter_Main.py` vorgenommen wurden, um es mit MicroPython auf dem Raspberry Pi Pico 2 W kompatibel zu machen.

## Hauptänderungen

1. **Bibliotheken und Importe**:
   - Ersetzung von Standard-Python-Bibliotheken durch MicroPython-spezifische Module
   - Hinzufügung von `network`, `machine`, `Pin`, `SPI` und `wiznet5k` Modulen
   - Ersetzung von `threading.Thread` durch `_thread.start_new_thread`

2. **Hardware-Initialisierung**:
   - Konfiguration der GPIO-Pins für das W5500 Ethernet-Modul gemäß der Verkabelungsanleitung
   - Initialisierung der SPI-Schnittstelle für die Kommunikation mit dem W5500
   - Einrichtung von Status-LEDs für WLAN, Ethernet und Datenübertragung

3. **Netzwerkverbindung**:
   - Implementierung einer echten WLAN-Verbindung mit dem eingebauten WLAN-Modul des Pico W
   - Initialisierung des W5500 Ethernet-Moduls über die wiznet5k-Bibliothek
   - Konfiguration von DHCP für die automatische IP-Adresszuweisung

4. **Fehlerbehandlung**:
   - Anpassung der Ausnahmebehandlung für MicroPython (OSError statt BlockingIOError)
   - Verbesserte Fehlerbehandlung und Statusmeldungen

## Verwendung

1. **Vorbereitung**:
   - Folgen Sie der Anleitung in `MicroPython_Installation.md`, um MicroPython auf Ihrem Raspberry Pi Pico 2 W zu installieren
   - Stellen Sie sicher, dass die wiznet5k-Bibliothek installiert ist (`import mip; mip.install("wiznet5k")`)
   - Verkabeln Sie das W5500 Ethernet-Modul gemäß der `Verkabelungsanleitung.md`

2. **Konfiguration**:
   - Ihre definierten WLAN-Zugangsdaten (WIFI_SSID: "Feel Good Lounge" und WIFI_PASSWORD: "freieenergie") wurden beibehalten
   - Ihre definierte IP-Adresse der Hue Bridge (HUE_BRIDGE_IP: "192.168.1.61") wurde beibehalten
   - Alle von Ihnen definierten Pin-Belegungen für das W5500 Ethernet-Modul und die Status-LEDs wurden unverändert übernommen

3. **Übertragung und Ausführung**:
   - Übertragen Sie die angepasste `Adapter_Main.py` auf Ihren Raspberry Pi Pico 2 W
   - Speichern Sie die Datei als `main.py`, damit sie beim Start automatisch ausgeführt wird

## Status-LEDs

Die angepasste Version verwendet drei LEDs zur Statusanzeige:

- **WLAN-LED (GP15)**: Leuchtet, wenn die WLAN-Verbindung hergestellt ist
- **Ethernet-LED (GP14)**: Leuchtet, wenn die Ethernet-Verbindung hergestellt ist
- **Daten-LED (GP13)**: Blinkt bei Datenübertragung

## Fehlerbehebung

- **Problem**: WLAN-Verbindung kann nicht hergestellt werden
  **Lösung**: Überprüfen Sie die WLAN-Zugangsdaten und stellen Sie sicher, dass der Pico W in Reichweite des WLAN-Netzwerks ist

- **Problem**: Ethernet-Verbindung kann nicht hergestellt werden
  **Lösung**: Überprüfen Sie die Verkabelung zum W5500-Modul und stellen Sie sicher, dass die wiznet5k-Bibliothek installiert ist

- **Problem**: Keine Kommunikation mit der Hue Bridge
  **Lösung**: Überprüfen Sie die IP-Adresse der Hue Bridge und stellen Sie sicher, dass sie im gleichen Netzwerk wie der Pico W ist

## Beibehaltene Konfigurationen

Wie gewünscht wurden alle Ihre persönlichen Konfigurationen beibehalten:

1. **WLAN-Konfiguration**:
   - SSID: "Feel Good Lounge"
   - Passwort: "freieenergie"

2. **Hue Bridge**:
   - IP-Adresse: "192.168.1.61"

3. **Pin-Belegungen für W5500 Ethernet-Modul**:
   - SCK: Pin 1 (GP1)
   - MOSI: Pin 3 (GP3)
   - MISO: Pin 4 (GP4)
   - CS: Pin 2 (GP2)
   - RST: Pin 5 (GP5)

4. **Pin-Belegungen für Status-LEDs**:
   - WLAN-LED: Pin 28 (GP28)
   - Ethernet-LED: Pin 27 (GP27)
   - Daten-LED: Pin 26 (GP26)

Diese Konfigurationen wurden unverändert aus Ihrer ursprünglichen Einrichtung übernommen.
