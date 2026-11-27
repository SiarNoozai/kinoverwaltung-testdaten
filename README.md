# kinoverwaltung-testdaten

Testdaten für die Kinoverwaltung aus dem Modul WK_2607 „Entwicklung komplexer betrieblicher Anwendungssysteme" (THM, 2026), gebaut mit SAP RAP und SAP Fiori Elements.
Team: Ramazan Gündüz (Matrikelnr. 5316317), Siar Noorzai (Matrikelnr. 5321690).

Die acht CSV-Dateien in diesem Repository werden im SAP-System von der Klasse `ZSS26_677_CL_IMPORT` direkt von hier geladen. Erzeugt werden sie mit dem Python-Skript `generate_testdaten.py`, das ebenfalls hier liegt. Diese Anleitung beschreibt, wie man die Daten selbst erzeugt, in ein eigenes Repository stellt und in SAP einliest.

## Was die Daten enthalten

Ein Kino mit 3 Sälen von September bis Dezember 2026:

| Datei | Zeilen | Inhalt |
|---|---|---|
| `werte.csv` | 33 | Auswahlwerte für Wertehilfen (Filmstatus, Genre, FSK, Buchungsstatus, Zahlungsart usw.) |
| `saal.csv` | 3 | Säle mit Plätzen, 2D oder 3D und Reinigungszeit |
| `film.csv` | 20 | Filme mit Dauer, FSK, Plakat und Status |
| `vorst.csv` | 224 | Vorstellungen mit Datum, Uhrzeit, Saal und Grundpreis |
| `buch.csv` | 1.029 | Buchungen mit Anzahl Erwachsene, Ermäßigte und Kinder (davon 50 storniert) |
| `prod.csv` | 14 | Snack-Produkte mit Preis, Liefermenge und Mindestbestand |
| `snack.csv` | 632 | Snackverkäufe an der Kasse und am Automaten |
| `snpos.csv` | 1.446 | Positionen der Snackverkäufe |

Eingebaute Muster, damit die Auswertungen etwas zeigen: Kinderfilme laufen um 11:00 und 14:30, Familienfilme um 14:30 und 17:30, Filme für Erwachsene um 17:30 und 20:15. Abends laufen die Filme in größeren Sälen, und es werden mehr Snacks gekauft. Dienstag ist Kinotag mit Rabatt. Ab und zu wird storniert, eine Vorstellung ist abgesagt. Am Automaten gibt es auch Käufe ohne Kinobesuch.

Die Daten halten dieselben Regeln ein wie die Anwendung: keine Überbuchung, keine Minuswerte, keine Kindertickets bei FSK 16 und 18, keine zwei Vorstellungen gleichzeitig im selben Saal.

Die Preise und Mengen sind ausgedacht, aber in einer für ein Kino plausiblen Größenordnung gewählt. Sie stammen nicht aus einem echten Kino.

## Aufbau der Dateien

Alle Dateien: UTF-8, Trennzeichen Semikolon, erste Zeile ist die Kopfzeile. Datum als `JJJJMMTT`, Uhrzeit als `HHMMSS`, Beträge mit Punkt als Dezimalzeichen.

| Datei | Spalten | Hinweise |
|---|---|---|
| `werte.csv` | feld; wert; text | `feld` ist die Gruppe (z. B. `FILMSTATUS`), `wert` der gespeicherte Wert, `text` die Anzeige |
| `saal.csv` | saal; kapazitaet; typ; reinigung_min | `typ` ist `2D` oder `3D`. Die Reinigungszeit gilt zwischen zwei Vorstellungen |
| `film.csv` | film_id; titel; genre; dauer_min; fsk; plakat_url; status | `status`: `AKTUELL` (läuft), `BALD` (noch nicht angelaufen), `ARCHIV` (abgelaufen). `plakat_url` zeigt auf Bilder in der Fiori-App |
| `vorst.csv` | vorst_id; film_id; datum; uhrzeit; saal; sitzplaetze; preis; waehrung; ende; status | `preis` ist der Grundpreis. `status`: `GEPLANT` oder `ABGESAGT` |
| `buch.csv` | buch_id; vorst_id; kundenname; email; anz_erw; anz_erm; anz_kind; status; zahlungsart | **Ohne Preis:** Den Gesamtpreis rechnet SAP beim Import mit `ZSS26_677_CL_PREISRECHNER`. Die E-Mail ist freiwillig. `status`: `RESERVIERT`, `BEZAHLT` oder `STORNIERT` |
| `prod.csv` | prod_id; name; kategorie; groesse; preis; waehrung; lieferbestand; mindestbestand | Der verfügbare Bestand ist immer Lieferbestand minus verkaufte Menge, er wird nicht gespeichert |
| `snack.csv` | verk_id; datum; uhrzeit; verkaufsstelle; zahlungsart; vorst_id; waehrung | `verkaufsstelle`: `KASSE` oder `AUTOMAT`. `vorst_id` ist leer, wenn der Kauf zu keiner Vorstellung gehört |
| `snpos.csv` | pos_id; verk_id; prod_id; menge; einzelpreis; summe; waehrung | Eine Zeile je Produkt in einem Verkauf |

## Nachbau in sechs Schritten

### 1. Python bereitstellen
Python 3 installieren (python.org). Getestet mit Python 3.12.10. Das Skript nutzt nur die Standardbibliothek, es muss nichts nachinstalliert werden.

### 2. Daten erzeugen
`generate_testdaten.py` in einen leeren Ordner legen, dort eine Eingabeaufforderung öffnen und ausführen:

```
python generate_testdaten.py
```

Ergebnis: Unterordner `csv` mit den acht Dateien und daneben `erwartung.md` mit den Sollwerten (Zeilenzahlen, Umsatz je Monat). Das Skript hat den festen Startwert 2607, deshalb erzeugt jeder Lauf genau dieselben Daten wie in diesem Repository (am 27.11.2026 geprüft: alle acht Dateien byte-gleich).

Zeitraum und Stichtag stehen oben im Skript (`START`, `ENDE`, `STICHTAG`). Alles bis zum Stichtag gilt als Vergangenheit, danach als Vorverkauf. Für einen anderen Zeitraum die drei Werte ändern und neu erzeugen.

### 3. Eigenes Repository anlegen
Auf github.com anmelden, oben rechts **+** und dann **New repository**. Einen Namen eingeben, z. B. `kinoverwaltung-testdaten`, **Public** wählen (SAP liest die Dateien ohne Anmeldung) und **Create repository** klicken.

### 4. Dateien hochladen
Im neuen Repository **Add file** und dann **Upload files** wählen. Die acht CSV-Dateien aus dem Ordner `csv` hineinziehen und **Commit changes** klicken. Die Dateien müssen direkt im Hauptverzeichnis liegen, nicht in einem Unterordner.

Zur Kontrolle im Browser aufrufen (Benutzer und Repository ersetzen):

```
https://raw.githubusercontent.com/<Benutzer>/<Repository>/main/film.csv
```

Es muss der reine Text der Datei erscheinen.

### 5. In SAP einlesen
Klasse `ZSS26_677_CL_IMPORT` anlegen (Code in der ABAP-Dokumentation, Schritt 26.1). Oben in der Klasse die Konstante `c_url` auf die eigene Adresse setzen, mit Schrägstrich am Ende:

```
CONSTANTS c_url TYPE string VALUE 'https://raw.githubusercontent.com/<Benutzer>/<Repository>/main/'.
```

Aktivieren und mit F9 ausführen. Die Klasse lädt zuerst alle acht Dateien. Fehlt eine, bricht sie ab und ändert nichts. Sonst löscht sie die alten Daten, schreibt die neuen und rechnet die Buchungspreise.

Voraussetzung: Das SAP-System darf Dateien über HTTPS von GitHub laden. Auf dem System A07 der THM wurde das am 20.11.2026 vorab geprüft (ABAP-Dokumentation, Schritt 23).

### 6. Ergebnis prüfen
Am Ende prüft die Klasse selbst, ob es Überbuchungen oder Minuswerte gibt (Meldung „T21 OK"), und gibt den Ticketumsatz je Monat aus. Er muss auf den Cent mit `erwartung.md` übereinstimmen:

| Monat | Ticketumsatz EUR |
|---|---|
| 2026-09 | 10.089,66 |
| 2026-10 | 9.807,98 |
| 2026-11 | 10.207,88 |
| 2026-12 | 1.904,34 |

## Weiterführend

Die vollständige Anleitung zur Kinoverwaltung (Datenmodell, Verhalten, Rollen, Fiori-App, Dashboard) steht in der ABAP-Dokumentation der Abgabe, die Testdaten in Teil D, Schritt 26.
