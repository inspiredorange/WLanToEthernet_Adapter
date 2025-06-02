# Anleitung zum Anschluss des Raspberry Pi Pico 2 an eine Ethernet-Buchse

## Benötigte Komponenten
- Raspberry Pi Pico 2
- W5500 Ethernet-Modul mit RJ45-Buchse
- Jumper-Kabel (weiblich zu männlich)
- 3 LEDs (optional für Statusanzeige)
- 3 Widerstände (ca. 220-330 Ohm) für die LEDs

## Verkabelungsschema

### Verbindung zwischen Raspberry Pi Pico 2 und W5500 Ethernet-Modul

| Raspberry Pi Pico 2 Pin | W5500 Ethernet-Modul Pin |
|-------------------------|--------------------------|
| Pin 18 (GP18)           | SCK (Serial Clock)       |
| Pin 19 (GP19)           | MOSI (Master Out)        |
| Pin 16 (GP16)           | MISO (Master In)         |
| Pin 17 (GP17)           | CS (Chip Select)         |
| Pin 20 (GP20)           | RST (Reset)              |
| 3.3V                    | VCC                      |
| GND                     | GND                      |

### Status-LEDs (optional)

| Raspberry Pi Pico 2 Pin | LED-Funktion        |
|-------------------------|---------------------|
| Pin 15 (GP15)           | WLAN-Status         |
| Pin 14 (GP14)           | Ethernet-Status     |
| Pin 13 (GP13)           | Datenübertragung    |

## Schematische Darstellung

```
Raspberry Pi Pico 2                W5500 Ethernet-Modul
+---------------+                  +----------------+
|               |                  |                |
| GP18 (Pin 18) |------> SCK ----->| Ethernet      |
| GP19 (Pin 19) |------> MOSI ---->| Controller    |
| GP16 (Pin 16) |<------ MISO -----|                |
| GP17 (Pin 17) |------> CS ------>|                |
| GP20 (Pin 20) |------> RST ----->|                |
| 3.3V          |------> VCC ----->|                |
| GND           |------> GND ----->|                |
|               |                  |                |
+---------------+                  +----------------+
                                   |     RJ45      |
                                   |   Buchse      |
                                   +----------------+
```

## Lötanleitung

1. **Vorbereitung**: Stellen Sie sicher, dass der Raspberry Pi Pico 2 nicht mit Strom versorgt ist.

2. **W5500-Modul vorbereiten**: Das W5500-Modul hat in der Regel Pins für SPI-Kommunikation (SCK, MOSI, MISO, CS), Reset, Stromversorgung (VCC) und Masse (GND).

3. **Verbindungen herstellen**:
   - Löten Sie ein Kabel von Pin 18 (GP18) des Pico 2 zum SCK-Pin des W5500-Moduls
   - Löten Sie ein Kabel von Pin 19 (GP19) des Pico 2 zum MOSI-Pin des W5500-Moduls
   - Löten Sie ein Kabel von Pin 16 (GP16) des Pico 2 zum MISO-Pin des W5500-Moduls
   - Löten Sie ein Kabel von Pin 17 (GP17) des Pico 2 zum CS-Pin des W5500-Moduls
   - Löten Sie ein Kabel von Pin 20 (GP20) des Pico 2 zum RST-Pin des W5500-Moduls
   - Verbinden Sie den 3.3V-Pin des Pico 2 mit dem VCC-Pin des W5500-Moduls
   - Verbinden Sie einen GND-Pin des Pico 2 mit dem GND-Pin des W5500-Moduls

4. **Status-LEDs (optional)**:
   - Für jede LED: Verbinden Sie die Anode (längeres Bein) über einen Widerstand (220-330 Ohm) mit dem entsprechenden GPIO-Pin
   - Verbinden Sie die Kathode (kürzeres Bein) mit einem GND-Pin des Pico 2

## Hinweise

- Das W5500-Modul hat bereits eine integrierte RJ45-Buchse, sodass keine separate Ethernet-Buchse gelötet werden muss.
- Achten Sie darauf, dass alle Verbindungen sicher und korrekt sind, bevor Sie den Raspberry Pi Pico 2 mit Strom versorgen.
- Die Software (Adapter_Main.py) ist bereits für diese Pinbelegung konfiguriert.

## Fehlerbehebung

- Wenn die Ethernet-LED nicht leuchtet, überprüfen Sie die Verbindungen zum W5500-Modul.
- Stellen Sie sicher, dass die wiznet5k-Bibliothek in MicroPython installiert ist.
- Überprüfen Sie, ob die Stromversorgung ausreichend ist (das W5500-Modul benötigt zusätzlichen Strom).