# Anleitung zum Aufspielen der aktuellen MicroPython-Firmware auf den Raspberry Pi Pico 2

## Benötigte Werkzeuge
- Computer mit Internetverbindung
- USB-Kabel (Micro-USB auf USB-A oder USB-C, je nach Computer)
- Raspberry Pi Pico 2

## Schritte zum Aufspielen der Firmware

### 1. Herunterladen der aktuellen MicroPython-Firmware

1. Besuchen Sie die offizielle MicroPython-Website: [https://micropython.org/download/rp2-pico/](https://micropython.org/download/rp2-pico/)
2. Laden Sie die neueste stabile Version der Firmware herunter (Datei mit der Endung `.uf2`)
   - Wählen Sie die Standard-Version für allgemeine Anwendungen
   - Alternativ können Sie auch die Version mit WLAN-Unterstützung wählen, wenn Ihr Pico W WLAN-Funktionalität hat

### 2. Vorbereiten des Raspberry Pi Pico 2

1. Trennen Sie den Raspberry Pi Pico 2 von allen Stromquellen
2. Halten Sie die BOOTSEL-Taste auf dem Pico gedrückt
3. Verbinden Sie den Pico über das USB-Kabel mit Ihrem Computer, während Sie die BOOTSEL-Taste gedrückt halten
4. Lassen Sie die BOOTSEL-Taste los, nachdem der Pico mit dem Computer verbunden ist
5. Der Pico sollte nun als USB-Massenspeichergerät auf Ihrem Computer erscheinen (wie ein USB-Stick)

### 3. Aufspielen der Firmware

1. Öffnen Sie den Datei-Explorer und navigieren Sie zum Raspberry Pi Pico, der als Laufwerk angezeigt wird
2. Kopieren Sie die heruntergeladene `.uf2`-Datei auf das Pico-Laufwerk
3. Der Pico wird die Firmware automatisch installieren und sich danach neu starten
4. Nach dem Neustart ist der Pico nicht mehr als Massenspeichergerät sichtbar, sondern als serieller USB-Port

### 4. Installation der benötigten Bibliotheken

Für die Verwendung mit dem W5500 Ethernet-Modul benötigen Sie die wiznet5k-Bibliothek:

1. Installieren Sie [Thonny IDE](https://thonny.org/) auf Ihrem Computer
2. Öffnen Sie Thonny und wählen Sie unter "Tools" > "Options" > "Interpreter" den MicroPython (Raspberry Pi Pico) aus
3. Verbinden Sie den Pico mit Ihrem Computer
4. Öffnen Sie die Shell in Thonny und führen Sie folgende Befehle aus:

```python
import mip
mip.install("wiznet5k")
```

5. Warten Sie, bis die Installation abgeschlossen ist

### 5. Überprüfen der Installation

1. Führen Sie in der Thonny-Shell folgenden Befehl aus, um die MicroPython-Version zu überprüfen:

```python
import sys
print(sys.version)
```

2. Um zu überprüfen, ob die wiznet5k-Bibliothek korrekt installiert wurde:

```python
import wiznet5k
print("wiznet5k erfolgreich installiert")
```

### 6. Übertragen des Adapter-Skripts

1. Öffnen Sie die Datei `Adapter_Main.py` in Thonny
2. Speichern Sie die Datei auf dem Pico als `main.py`, damit sie beim Start automatisch ausgeführt wird

## Fehlerbehebung

- **Problem**: Der Pico wird nicht als Massenspeichergerät erkannt
  **Lösung**: Stellen Sie sicher, dass Sie die BOOTSEL-Taste gedrückt halten, während Sie den Pico anschließen

- **Problem**: Die Firmware-Installation schlägt fehl
  **Lösung**: Versuchen Sie, eine andere Version der Firmware herunterzuladen oder einen anderen USB-Port zu verwenden

- **Problem**: Die wiznet5k-Bibliothek kann nicht installiert werden
  **Lösung**: Stellen Sie sicher, dass Ihr Pico mit dem Internet verbunden ist oder installieren Sie die Bibliothek manuell

## Hinweise

- Nach dem Aufspielen der Firmware und der Installation der wiznet5k-Bibliothek ist Ihr Raspberry Pi Pico 2 bereit für die Verwendung mit dem W5500 Ethernet-Modul gemäß der Verkabelungsanleitung.
- Stellen Sie sicher, dass alle Verbindungen korrekt hergestellt sind, bevor Sie den Adapter in Betrieb nehmen.
- Die Datei `main.py` wird automatisch beim Start des Pico ausgeführt.