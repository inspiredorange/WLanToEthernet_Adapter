# Kompatibilitätshinweis für W5500-Ethernet-Module

## Bewertung des verlinkten Moduls

Das in der Anfrage verlinkte Modul (Hailege W5500 Ethernet Network Module) ist **kompatibel** mit diesem Projekt. 

### Begründung:

1. **Chipsatz**: Das verlinkte Modul basiert auf dem W5500-Chip, der exakt dem Chip entspricht, für den dieses Projekt entwickelt wurde.

2. **Schnittstelle**: Das Modul verwendet eine SPI-Schnittstelle, die mit den in der Verkabelungsanleitung angegebenen Pins (SCK, MOSI, MISO, CS, RST) kompatibel ist.

3. **Spannungsversorgung**: Das Modul arbeitet mit 3,3V, was mit der Stromversorgung des Raspberry Pi Pico 2 kompatibel ist.

4. **Software-Unterstützung**: Die im Projekt verwendete wiznet5k-Bibliothek ist speziell für W5500-basierte Module entwickelt und wird mit dem verlinkten Modul funktionieren.

## Installation und Einrichtung

Bitte folgen Sie den Anweisungen in den folgenden Dokumenten, um das Modul einzurichten:

1. **Verkabelungsanleitung.md** - Für die korrekte Verbindung des Moduls mit dem Raspberry Pi Pico 2
2. **MicroPython_Installation.md** - Für die Installation der erforderlichen Software und Bibliotheken

## Hinweise

- Stellen Sie sicher, dass Sie die wiznet5k-Bibliothek wie in der MicroPython_Installation.md beschrieben installieren.
- Die Pinbelegung in der Adapter_Main.py ist bereits für das W5500-Modul konfiguriert und sollte ohne Änderungen funktionieren.
- Bei Problemen mit der Verbindung überprüfen Sie zunächst die Verkabelung und stellen Sie sicher, dass alle Pins korrekt angeschlossen sind.