# Konfigurationstest für den WiFi zu Ethernet Adapter

Dieses Dokument erklärt, wie Sie überprüfen können, ob Ihre persönlichen Konfigurationen (WLAN-Zugangsdaten, Hue Bridge IP und Pin-Belegungen) korrekt beibehalten wurden.

## Über den Konfigurationstest

Die Datei `config_test.py` ist ein einfaches Testskript, das alle Ihre benutzerdefinierten Konfigurationen überprüft und sicherstellt, dass sie korrekt in der Adapter-Software beibehalten wurden. Das Skript:

1. Lädt die aktuellen Konfigurationen aus der `Adapter_Main.py`
2. Vergleicht sie mit den erwarteten Werten:
   - WLAN-SSID: "Feel Good Lounge"
   - WLAN-Passwort: "freieenergie"
   - Hue Bridge IP: "192.168.1.61"
   - Pin-Belegungen für das W5500 Ethernet-Modul und die Status-LEDs
3. Gibt einen detaillierten Bericht aus
4. Blinkt alle LEDs, wenn alle Konfigurationen korrekt sind

## Verwendung des Konfigurationstests

### Methode 1: Ausführen auf dem Raspberry Pi Pico 2 W

1. Übertragen Sie sowohl `Adapter_Main.py` als auch `config_test.py` auf Ihren Raspberry Pi Pico 2 W
2. Verbinden Sie den Pico mit Ihrem Computer
3. Öffnen Sie Thonny IDE oder ein anderes MicroPython-Terminal
4. Führen Sie den Test aus:
   ```python
   import config_test
   ```
5. Überprüfen Sie die Ausgabe im Terminal
6. Wenn der Test erfolgreich ist, werden alle drei Status-LEDs dreimal blinken

### Methode 2: Überprüfen vor der Übertragung

Sie können die Konfigurationen auch überprüfen, bevor Sie die Dateien auf den Pico übertragen:

1. Öffnen Sie die Datei `Adapter_Main.py` in einem Texteditor
2. Überprüfen Sie die folgenden Zeilen:
   - Zeile 15-16: WLAN-Konfiguration
   - Zeile 19: Hue Bridge IP
   - Zeile 22-26: W5500 Pin-Konfiguration
   - Zeile 29-31: Status-LED Pin-Konfiguration
3. Stellen Sie sicher, dass alle Werte mit Ihren gewünschten Einstellungen übereinstimmen

## Fehlerbehebung

Falls der Test fehlschlägt:

1. Notieren Sie die Konfigurationen, die nicht mit den erwarteten Werten übereinstimmen
2. Öffnen Sie `Adapter_Main.py` und korrigieren Sie die entsprechenden Werte
3. Führen Sie den Test erneut aus, um sicherzustellen, dass alle Konfigurationen nun korrekt sind

## Hinweis

Die Konfigurationen wurden bereits während der Anpassung für MicroPython beibehalten. Dieser Test dient lediglich zur Bestätigung und zusätzlichen Sicherheit.

## Umgebungsanforderungen

Sowohl `Adapter_Main.py` als auch `config_test.py` sind ausschließlich für die Ausführung auf einem Raspberry Pi Pico 2 mit MicroPython-Firmware konzipiert. Sie können nicht in einer Standard-Python-Umgebung auf einem Computer ausgeführt werden.

Die `Adapter_Main.py` enthält nun eine Umgebungsprüfung, die sicherstellt, dass das Skript nur in der korrekten MicroPython-Umgebung ausgeführt wird. Wenn Sie versuchen, das Skript in einer Standard-Python-Umgebung auszuführen, erhalten Sie eine entsprechende Fehlermeldung mit Hinweisen zur Einrichtung der erforderlichen Umgebung.

Bitte folgen Sie den Anweisungen in der Datei `MicroPython_Installation.md`, um die erforderliche Umgebung einzurichten und die Skripte auf den Pico zu übertragen.
