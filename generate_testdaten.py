"""Testdaten-Generator Kinoverwaltung (WK_2607, Erweiterung November 2026).

Erzeugt CSV-Dateien (Semikolon, UTF-8, Kopfzeile) fuer den Import in SAP
ueber GitHub (Repository SiarNoozai/kinoverwaltung-testdaten).

Fester Startwert: jeder Lauf erzeugt exakt dieselben Daten.
Preise der Buchungen stehen NICHT in der CSV, SAP rechnet sie beim Import
mit ZSS26_677_CL_PREISRECHNER. Dieses Skript rechnet sie nach denselben
Regeln nur fuer die Erwartungswerte (Testfall T19/T21) in erwartung.md.

Aufruf:  python generate_testdaten.py
"""
import csv
import math
import random
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

random.seed(2607)

OUT = Path(__file__).parent / "csv"
OUT.mkdir(exist_ok=True)

START = date(2026, 9, 1)
ENDE = date(2026, 12, 20)
STICHTAG = date(2026, 11, 26)   # alles davor ist Vergangenheit (Praesentation 27.11.)

# ---------------------------------------------------------------- Auswahlwerte
WERTE = [
    ("FILMSTATUS", "AKTUELL", "Läuft aktuell"), ("FILMSTATUS", "BALD", "Demnächst"),
    ("FILMSTATUS", "ARCHIV", "Abgelaufen"),
    ("GENRE", "Action", "Action"), ("GENRE", "Animation", "Animation"),
    ("GENRE", "Drama", "Drama"), ("GENRE", "Fantasy", "Fantasy"),
    ("GENRE", "Komödie", "Komödie"), ("GENRE", "Science-Fiction", "Science-Fiction"),
    ("GENRE", "Thriller", "Thriller"),
    # FSK zweistellig wie das Tabellenfeld fsk (NUMC 2), sonst passt die Wertehilfe nicht
    ("FSK", "00", "ohne Altersbeschränkung"), ("FSK", "06", "ab 6 Jahren"),
    ("FSK", "12", "ab 12 Jahren"), ("FSK", "16", "ab 16 Jahren"), ("FSK", "18", "ab 18 Jahren"),
    ("BUCHSTATUS", "RESERVIERT", "Reserviert"), ("BUCHSTATUS", "BEZAHLT", "Bezahlt"),
    ("BUCHSTATUS", "STORNIERT", "Storniert"),
    ("VORSTSTATUS", "GEPLANT", "Geplant"), ("VORSTSTATUS", "ABGESAGT", "Abgesagt"),
    ("ZAHLUNGSART", "BAR", "Bar"), ("ZAHLUNGSART", "KARTE", "Karte"),
    ("VERKSTELLE", "KASSE", "Kasse"), ("VERKSTELLE", "AUTOMAT", "Snackautomat"),
    ("KATEGORIE", "POPCORN", "Popcorn"), ("KATEGORIE", "GETRAENK", "Getränk"),
    ("KATEGORIE", "SNACK", "Snack"), ("KATEGORIE", "MENUE", "Menü"),
    ("SAALTYP", "2D", "2D"), ("SAALTYP", "3D", "3D"),
    ("GROESSE", "S", "Klein"), ("GROESSE", "M", "Mittel"), ("GROESSE", "L", "Groß"),
]

# ---------------------------------------------------------------- Saele
SAELE = [  # saal, kapazitaet, typ, reinigung_min
    ("Saal 1", 120, "3D", 20),
    ("Saal 2", 80, "2D", 15),
    ("Saal 3", 50, "2D", 15),
]
SAAL = {s[0]: s for s in SAELE}

# ---------------------------------------------------------------- Filme
# id, titel, genre, dauer, fsk, plakat, zielgruppe, beliebtheit, laeuft_ab, laeuft_bis
# Dauer (Kinofassung) und FSK am 20.11.2026 geprueft (de.wikipedia.org, filmstarts.de, FBW).
# Ausnahme Dune Teil 3: noch keine offizielle Laufzeit/FSK; 151 Min. laut IFCO-Bericht
# (slashfilm.com, 04.11.2026), FSK 12 ist eine Annahme fuer die Testdaten (Status BALD).
# zielgruppe: KIND (11:00/14:30), FAMILIE (14:30/17:30), ERW (17:30/20:15)
FILME = [
    (1, "Der Herr der Ringe: Die Gefährten", "Fantasy", 178, 12, "/images/film1.jpg", "ERW", 1.1, date(2026, 10, 1), ENDE),
    (2, "Inception", "Thriller", 148, 12, "/images/film2.jpg", "ERW", 1.0, START, date(2026, 11, 15)),
    (3, "Toy Story", "Animation", 81, 0, "/images/film3.jpg", "KIND", 0.9, START, ENDE),
    (4, "Dune Teil 3", "Science-Fiction", 151, 12, "/images/film4.jpg", "ERW", 1.4, None, None),  # BALD, keine Vorstellungen
    (5, "Titanic", "Drama", 194, 12, "/images/film5.jpg", "ERW", 0.8, START, date(2026, 10, 11)),
    (6, "Barbie", "Komödie", 114, 6, "/images/film6.jpg", "FAMILIE", 1.0, START, date(2026, 10, 31)),
    (7, "Oppenheimer", "Drama", 180, 12, "", "ERW", 1.0, date(2026, 9, 15), date(2026, 11, 30)),
    (8, "Der König der Löwen", "Animation", 88, 0, "", "KIND", 1.0, date(2026, 10, 1), ENDE),
    (9, "Findet Nemo", "Animation", 100, 0, "", "KIND", 0.9, START, date(2026, 10, 31)),
    (10, "Die Eiskönigin - Völlig unverfroren", "Animation", 101, 0, "", "KIND", 1.2, date(2026, 11, 1), ENDE),
    (11, "Interstellar", "Science-Fiction", 169, 12, "", "ERW", 1.2, START, ENDE),
    (12, "The Dark Knight", "Action", 152, 16, "", "ERW", 1.1, START, date(2026, 10, 31)),
    (13, "Joker", "Thriller", 122, 16, "", "ERW", 0.9, date(2026, 10, 1), date(2026, 11, 30)),
    (14, "Avatar: The Way of Water", "Science-Fiction", 193, 12, "", "ERW", 1.3, date(2026, 11, 1), ENDE),
    (15, "Alles steht Kopf 2", "Animation", 96, 0, "", "KIND", 1.1, START, date(2026, 11, 30)),
    (16, "Top Gun: Maverick", "Action", 130, 12, "", "ERW", 1.0, START, date(2026, 11, 15)),
    (17, "Gladiator", "Action", 155, 16, "", "ERW", 0.9, date(2026, 11, 1), ENDE),
    (18, "Vaiana", "Animation", 107, 0, "", "KIND", 1.0, date(2026, 10, 15), ENDE),
    (19, "Matrix", "Science-Fiction", 136, 16, "", "ERW", 0.8, date(2026, 10, 1), date(2026, 11, 30)),
    (20, "Zoomania", "Animation", 108, 0, "", "KIND", 1.0, date(2026, 9, 15), date(2026, 11, 15)),
]
FILM = {f[0]: f for f in FILME}


def film_status(f):
    if f[8] is None:
        return "BALD"
    return "AKTUELL" if f[9] >= STICHTAG else "ARCHIV"


# ---------------------------------------------------------------- Spielplan
# Wochentag (Mo=0): Liste von (Uhrzeit, Saal, erlaubte Zielgruppen, Grundpreis, Grundauslastung)
SLOT_KIND_VORMITTAG = ("110000", "Saal 3", ("KIND",), Decimal("8.50"), 0.30)
SLOT_NACHMITTAG = ("143000", "Saal 3", ("KIND", "FAMILIE"), Decimal("9.50"), 0.40)
SLOT_VORABEND = ("173000", "Saal 2", ("FAMILIE", "ERW"), Decimal("11.00"), 0.38)
SLOT_ABEND = ("201500", "Saal 1", ("ERW",), Decimal("12.50"), 0.52)
SPIELPLAN = {
    1: [SLOT_VORABEND, SLOT_ABEND],                                   # Dienstag (Kinotag)
    3: [SLOT_VORABEND, SLOT_ABEND],                                   # Donnerstag
    4: [SLOT_VORABEND, SLOT_ABEND],                                   # Freitag
    5: [SLOT_KIND_VORMITTAG, SLOT_NACHMITTAG, SLOT_VORABEND, SLOT_ABEND],  # Samstag
    6: [SLOT_KIND_VORMITTAG, SLOT_NACHMITTAG, SLOT_VORABEND, SLOT_ABEND],  # Sonntag
}
TAGESFAKTOR = {1: 1.20, 3: 0.85, 4: 1.15, 5: 1.30, 6: 1.15}
# Skaliert die Auslastung auf eine realistische Groessenordnung (rund 1000 Buchungen)
SKALA = 0.30

# ---------------------------------------------------------------- Produkte
# id, name, kategorie, groesse, preis, mindestbestand, nur_kasse
PRODUKTE = [
    (1, "Popcorn süß", "POPCORN", "S", Decimal("4.50"), 60, True),
    (2, "Popcorn süß", "POPCORN", "M", Decimal("5.50"), 60, True),
    (3, "Popcorn süß", "POPCORN", "L", Decimal("6.50"), 60, True),
    (4, "Popcorn salzig", "POPCORN", "M", Decimal("5.50"), 40, True),
    (5, "Nachos mit Käsedip", "SNACK", "M", Decimal("6.00"), 40, True),
    (6, "Cola 0,5 l", "GETRAENK", "M", Decimal("3.80"), 80, False),
    (7, "Cola 1,0 l", "GETRAENK", "L", Decimal("5.20"), 40, True),
    (8, "Wasser 0,5 l", "GETRAENK", "M", Decimal("2.90"), 60, False),
    (9, "Eistee 0,5 l", "GETRAENK", "M", Decimal("3.50"), 40, False),
    (10, "Apfelsaft 0,33 l", "GETRAENK", "S", Decimal("2.90"), 40, False),
    (11, "Schokoriegel", "SNACK", " ", Decimal("2.50"), 40, False),
    (12, "Gummibärchen", "SNACK", " ", Decimal("2.80"), 40, False),
    (13, "Kino-Menü (Popcorn M + Cola 0,5 l)", "MENUE", " ", Decimal("8.50"), 0, True),
    (14, "Kinder-Menü (Popcorn S + Apfelsaft)", "MENUE", " ", Decimal("6.00"), 0, True),
]
PROD = {p[0]: p for p in PRODUKTE}

VORNAMEN = ["Anna", "Ben", "Clara", "David", "Emma", "Felix", "Greta", "Hannah", "Jonas", "Lea",
            "Leon", "Lina", "Lukas", "Marie", "Max", "Mia", "Noah", "Paul", "Sophie", "Tim",
            "Elif", "Can", "Aylin", "Luca", "Nora", "Finn", "Ida", "Emil", "Maja", "Yusuf"]
NACHNAMEN = ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker",
             "Schulz", "Hoffmann", "Koch", "Richter", "Klein", "Wolf", "Neumann", "Schwarz",
             "Braun", "Zimmermann", "Krüger", "Hartmann", "Lang", "Bauer", "Kaya", "Yilmaz"]


def ascii_mail(s):
    return (s.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss"))


def euro(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def preis(grundpreis, d, saaltyp, dauer, erw, erm, kind):
    """Gleiche Regeln wie ZSS26_677_CL_PREISRECHNER (Plan 10.4)."""
    tag = Decimal("0.7") if d.weekday() == 1 else Decimal("1")
    zuschlag = Decimal("0")
    if saaltyp == "3D":
        zuschlag += Decimal("3.00")
    if dauer >= 150:
        zuschlag += Decimal("1.50")
    p_erw = euro(grundpreis * Decimal("1.0") * tag) + zuschlag
    p_erm = euro(grundpreis * Decimal("0.8") * tag) + zuschlag
    p_kind = euro(grundpreis * Decimal("0.6") * tag) + zuschlag
    return erw * p_erw + erm * p_erm + kind * p_kind


def gewichtet(items, gewichte):
    return random.choices(items, weights=gewichte, k=1)[0]


# ---------------------------------------------------------------- Vorstellungen
vorstellungen = []
vid = 0
d = START
while d <= ENDE:
    slots = SPIELPLAN.get(d.weekday(), [])
    heute = set()
    for (uhr, saal, gruppen, grundpreis, grundausl) in slots:
        kandidaten = [f for f in FILME
                      if f[8] is not None and f[8] <= d <= f[9] and f[6] in gruppen and f[0] not in heute]
        if not kandidaten:
            continue
        f = gewichtet(kandidaten, [k[7] for k in kandidaten])
        heute.add(f[0])
        vid += 1
        beginn = datetime.combine(d, datetime.strptime(uhr, "%H%M%S").time())
        ende = beginn + timedelta(minutes=f[3])
        vorstellungen.append(dict(vorst_id=vid, film_id=f[0], datum=d, uhrzeit=uhr, saal=saal,
                                  sitzplaetze=SAAL[saal][1], preis=grundpreis, ende=ende.strftime("%H%M%S"),
                                  status="GEPLANT", grundausl=grundausl, film=f))
    d += timedelta(days=1)

# Pruefung: keine Ueberschneidung im selben Saal (Ende + Reinigung vor naechstem Beginn)
nach_saal_tag = defaultdict(list)
for v in vorstellungen:
    nach_saal_tag[(v["saal"], v["datum"])].append(v)
for (saal, tag), liste in nach_saal_tag.items():
    liste.sort(key=lambda x: x["uhrzeit"])
    for a, b in zip(liste, liste[1:]):
        ende_a = datetime.combine(tag, datetime.strptime(a["ende"], "%H%M%S").time()) + timedelta(minutes=SAAL[saal][3])
        beginn_b = datetime.combine(tag, datetime.strptime(b["uhrzeit"], "%H%M%S").time())
        assert ende_a <= beginn_b, f"Ueberschneidung {saal} {tag}"

# Eine Vorstellung in der Zukunft absagen (zeigt Aktion "Absagen" bereits in den Daten)
zukunft = [v for v in vorstellungen if v["datum"] > STICHTAG]
abgesagt = random.choice(zukunft)
abgesagt["status"] = "ABGESAGT"

# ---------------------------------------------------------------- Buchungen
buchungen = []
bid = 0


def auslastung(v):
    f = v["film"]
    wochen_seit_start = (v["datum"] - f[8]).days // 7
    wochen_bis_ende = (f[9] - v["datum"]).days // 7
    lauf = 1.25 if wochen_seit_start == 0 else 1.10 if wochen_seit_start == 1 else 1.0
    if wochen_bis_ende <= 1:
        lauf *= 0.85
    saison = 1.10 if v["datum"].month >= 11 else 1.0
    a = v["grundausl"] * TAGESFAKTOR[v["datum"].weekday()] * f[7] * lauf * saison * SKALA * random.uniform(0.75, 1.2)
    if v["datum"] > STICHTAG:  # Vorverkauf
        tage = (v["datum"] - STICHTAG).days
        a *= 0.35 if tage <= 21 else 0.10
    return min(a, 0.97)


def gruppe_erwachsene():
    return gewichtet([1, 2, 3, 4, 5, 6], [20, 45, 15, 13, 4, 3])


for v in vorstellungen:
    if v["status"] == "ABGESAGT":
        continue
    f = v["film"]
    kinder_erlaubt = f[4] <= 6
    frei = v["sitzplaetze"]
    ziel = int(round(v["sitzplaetze"] * auslastung(v)))
    verkauft = 0
    while verkauft < ziel:
        if f[6] in ("KIND", "FAMILIE") and kinder_erlaubt and random.random() < (0.85 if f[6] == "KIND" else 0.45):
            erw = gewichtet([1, 2], [55, 45])
            kind = gewichtet([1, 2, 3], [45, 40, 15])
            erm = 0
        else:
            n = gruppe_erwachsene()
            erm_anteil = 0.35 if v["datum"].weekday() == 1 else 0.20
            erm = sum(1 for _ in range(n) if random.random() < erm_anteil)
            erw, kind = n - erm, 0
        tickets = erw + erm + kind
        if verkauft + tickets > ziel or verkauft + tickets > frei:
            break
        verkauft += tickets
        vorname, nachname = random.choice(VORNAMEN), random.choice(NACHNAMEN)
        mail = f"{ascii_mail(vorname)}.{ascii_mail(nachname)}@example.com" if random.random() < 0.6 else ""
        vergangen = v["datum"] <= STICHTAG
        if vergangen or random.random() < 0.25:
            status = "BEZAHLT"
            zahlung = gewichtet(["BAR", "KARTE"], [35, 65])
        else:
            status, zahlung = "RESERVIERT", ""
        bid += 1
        buchungen.append(dict(buch_id=bid, vorst_id=v["vorst_id"], kundenname=f"{vorname} {nachname}",
                              email=mail, anz_erw=erw, anz_erm=erm, anz_kind=kind, status=status,
                              zahlungsart=zahlung, v=v))
    # Stornos: etwa 5 % zusaetzlich, belegen keinen Platz
    for _ in range(sum(1 for b in buchungen if b["vorst_id"] == v["vorst_id"] and random.random() < 0.05)):
        bid += 1
        vorname, nachname = random.choice(VORNAMEN), random.choice(NACHNAMEN)
        buchungen.append(dict(buch_id=bid, vorst_id=v["vorst_id"], kundenname=f"{vorname} {nachname}",
                              email="", anz_erw=gruppe_erwachsene(), anz_erm=0, anz_kind=0,
                              status="STORNIERT", zahlungsart="", v=v))

# Pruefung: keine Ueberbuchung, nichts negativ
belegt = Counter()
for b in buchungen:
    assert min(b["anz_erw"], b["anz_erm"], b["anz_kind"]) >= 0
    assert b["anz_erw"] + b["anz_erm"] + b["anz_kind"] >= 1
    if b["status"] != "STORNIERT":
        belegt[b["vorst_id"]] += b["anz_erw"] + b["anz_erm"] + b["anz_kind"]
    if b["anz_kind"] > 0:
        assert b["v"]["film"][4] <= 6, "Kinderticket fuer FSK 12+"
for v in vorstellungen:
    assert belegt[v["vorst_id"]] <= v["sitzplaetze"], f"Ueberbucht {v['vorst_id']}"

# ---------------------------------------------------------------- Snackverkaeufe
verkaeufe, positionen = [], []
verk_id = pos_id = 0
SNACKQUOTE = {"110000": 0.30, "143000": 0.45, "173000": 0.55, "201500": 0.70}


def kassen_positionen(b):
    pos = Counter()
    n_erw = b["anz_erw"] + b["anz_erm"]
    n_kind = b["anz_kind"]
    abends = b["v"]["uhrzeit"] >= "173000"
    for _ in range(n_kind):
        r = random.random()
        if r < 0.40:
            pos[14] += 1
        elif r < 0.65:
            pos[1] += 1
            pos[10] += 1
        elif r < 0.80:
            pos[12] += 1
    for _ in range(n_erw):
        r = random.random()
        if r < 0.30:
            pos[13] += 1
            continue
        if random.random() < (0.55 if abends else 0.35):
            pos[gewichtet([2, 3, 4], [45, 40, 15])] += 1
        if random.random() < 0.75:
            pos[gewichtet([6, 7, 8, 9], [45, 15, 25, 15])] += 1
    if abends and random.random() < 0.15:
        pos[5] += 1
    if not pos:
        pos[6] += 1
    return pos


def automat_positionen():
    pos = Counter()
    for _ in range(gewichtet([1, 2], [70, 30])):
        pos[gewichtet([6, 8, 9, 10, 11, 12], [30, 20, 15, 10, 15, 10])] += gewichtet([1, 2], [80, 20])
    return pos


def neuer_verkauf(datum, uhrzeit, stelle, vorst_id, pos):
    global verk_id, pos_id
    verk_id += 1
    zahlung = gewichtet(["BAR", "KARTE"], [30, 70] if stelle == "AUTOMAT" else [40, 60])
    verkaeufe.append(dict(verk_id=verk_id, datum=datum, uhrzeit=uhrzeit, verkaufsstelle=stelle,
                          zahlungsart=zahlung, vorst_id=vorst_id))
    for prod_id, menge in sorted(pos.items()):
        pos_id += 1
        ep = PROD[prod_id][4]
        positionen.append(dict(pos_id=pos_id, verk_id=verk_id, prod_id=prod_id, menge=menge,
                               einzelpreis=ep, summe=ep * menge, datum=datum, vorst_id=vorst_id))


for b in buchungen:
    v = b["v"]
    if b["status"] == "STORNIERT" or v["datum"] > STICHTAG:
        continue
    quote = SNACKQUOTE[v["uhrzeit"]] * (1.15 if v["film"][7] >= 1.2 else 1.0)
    if random.random() >= quote:
        continue
    beginn = datetime.combine(v["datum"], datetime.strptime(v["uhrzeit"], "%H%M%S").time())
    zeit = (beginn - timedelta(minutes=random.randint(5, 25))).strftime("%H%M%S")
    if random.random() < 0.20:
        neuer_verkauf(v["datum"], zeit, "AUTOMAT", v["vorst_id"], automat_positionen())
    else:
        neuer_verkauf(v["datum"], zeit, "KASSE", v["vorst_id"], kassen_positionen(b))

# Snackautomat im Foyer ohne Vorstellung (etwa 40 Verkaeufe)
spieltage = sorted({v["datum"] for v in vorstellungen if v["datum"] <= STICHTAG})
for _ in range(40):
    tag = random.choice(spieltage)
    zeit = f"{random.randint(15, 21):02d}{random.randint(0, 59):02d}00"
    neuer_verkauf(tag, zeit, "AUTOMAT", "", automat_positionen())

# Lieferbestand: verkauft + Puffer; Nachos bewusst knapp (Ampel unter Mindestbestand)
verkauft_je_prod = Counter()
for p in positionen:
    verkauft_je_prod[p["prod_id"]] += p["menge"]
lieferbestand = {}
for p in PRODUKTE:
    puffer = 25 if p[0] == 5 else p[5] + random.randint(40, 200)
    lieferbestand[p[0]] = verkauft_je_prod[p[0]] + puffer

# ---------------------------------------------------------------- CSV schreiben


def schreibe(name, kopf, zeilen):
    with open(OUT / name, "w", encoding="utf-8", newline="\n") as fh:
        w = csv.writer(fh, delimiter=";", lineterminator="\n")
        w.writerow(kopf)
        w.writerows(zeilen)


schreibe("werte.csv", ["feld", "wert", "text"], WERTE)
schreibe("saal.csv", ["saal", "kapazitaet", "typ", "reinigung_min"], SAELE)
schreibe("film.csv", ["film_id", "titel", "genre", "dauer_min", "fsk", "plakat_url", "status"],
         [(f[0], f[1], f[2], f[3], f[4], f[5], film_status(f)) for f in FILME])
schreibe("vorst.csv", ["vorst_id", "film_id", "datum", "uhrzeit", "saal", "sitzplaetze", "preis", "waehrung", "ende", "status"],
         [(v["vorst_id"], v["film_id"], v["datum"].strftime("%Y%m%d"), v["uhrzeit"], v["saal"], v["sitzplaetze"],
           v["preis"], "EUR", v["ende"], v["status"]) for v in vorstellungen])
schreibe("buch.csv", ["buch_id", "vorst_id", "kundenname", "email", "anz_erw", "anz_erm", "anz_kind", "status", "zahlungsart"],
         [(b["buch_id"], b["vorst_id"], b["kundenname"], b["email"], b["anz_erw"], b["anz_erm"], b["anz_kind"],
           b["status"], b["zahlungsart"]) for b in buchungen])
schreibe("prod.csv", ["prod_id", "name", "kategorie", "groesse", "preis", "waehrung", "lieferbestand", "mindestbestand"],
         [(p[0], p[1], p[2], p[3].strip(), p[4], "EUR", lieferbestand[p[0]], p[5]) for p in PRODUKTE])
schreibe("snack.csv", ["verk_id", "datum", "uhrzeit", "verkaufsstelle", "zahlungsart", "vorst_id", "waehrung"],
         [(s["verk_id"], s["datum"].strftime("%Y%m%d"), s["uhrzeit"], s["verkaufsstelle"], s["zahlungsart"],
           s["vorst_id"], "EUR") for s in verkaeufe])
schreibe("snpos.csv", ["pos_id", "verk_id", "prod_id", "menge", "einzelpreis", "summe", "waehrung"],
         [(p["pos_id"], p["verk_id"], p["prod_id"], p["menge"], p["einzelpreis"], p["summe"], "EUR") for p in positionen])

# ---------------------------------------------------------------- Erwartungswerte (T19/T21)
ticket_monat = defaultdict(Decimal)
snack_monat = defaultdict(Decimal)
snack_je_besucher = defaultdict(lambda: [Decimal(0), 0])
for b in buchungen:
    if b["status"] == "STORNIERT":
        continue
    v = b["v"]
    betrag = preis(v["preis"], v["datum"], SAAL[v["saal"]][2], v["film"][3], b["anz_erw"], b["anz_erm"], b["anz_kind"])
    ticket_monat[v["datum"].strftime("%Y-%m")] += betrag
    if v["datum"] <= STICHTAG:
        snack_je_besucher[(v["film"][1], v["uhrzeit"])][1] += b["anz_erw"] + b["anz_erm"] + b["anz_kind"]
vorst_by_id = {v["vorst_id"]: v for v in vorstellungen}
for p in positionen:
    snack_monat[p["datum"].strftime("%Y-%m")] += p["summe"]
    if p["vorst_id"] != "":
        v = vorst_by_id[p["vorst_id"]]
        snack_je_besucher[(v["film"][1], v["uhrzeit"])][0] += p["summe"]

zeilen = [
    "# Erwartungswerte Testdaten (automatisch erzeugt, nicht hochladen)", "",
    f"Stichtag (Vergangenheit bis einschliesslich): {STICHTAG:%d.%m.%Y}", "",
    "| Datei | Zeilen |", "|---|---|",
    f"| werte.csv | {len(WERTE)} |", f"| saal.csv | {len(SAELE)} |", f"| film.csv | {len(FILME)} |",
    f"| vorst.csv | {len(vorstellungen)} |", f"| buch.csv | {len(buchungen)} |", f"| prod.csv | {len(PRODUKTE)} |",
    f"| snack.csv | {len(verkaeufe)} |", f"| snpos.csv | {len(positionen)} |", "",
    f"Stornierte Buchungen: {sum(1 for b in buchungen if b['status'] == 'STORNIERT')} · "
    f"Abgesagte Vorstellung: {abgesagt['vorst_id']} ({abgesagt['datum']:%d.%m.%Y}) · "
    f"Tickets gesamt (ohne Storno): {sum(belegt.values())}", "",
    "## Umsatz je Monat (Tickets nach Vorstellungsdatum, ohne Storno; Snacks nach Verkaufsdatum)", "",
    "| Monat | Tickets EUR | Snacks EUR | Gesamt EUR |", "|---|---|---|---|",
]
for m in sorted(set(ticket_monat) | set(snack_monat)):
    zeilen.append(f"| {m} | {ticket_monat[m]:.2f} | {snack_monat[m]:.2f} | {ticket_monat[m] + snack_monat[m]:.2f} |")
zeilen += ["", "## Snackumsatz je Besucher nach Film und Uhrzeit (nur Vergangenheit, Top 10 und Flop 5)", "",
           "| Film | Uhrzeit | Besucher | Snack EUR | je Besucher |", "|---|---|---|---|---|"]
liste = sorted(((k, s, n) for k, (s, n) in snack_je_besucher.items() if n >= 20), key=lambda x: x[1] / x[2], reverse=True)
for (film, uhr), s, n in liste[:10] + liste[-5:]:
    zeilen.append(f"| {film} | {uhr[:2]}:{uhr[2:4]} | {n} | {s:.2f} | {s / n:.2f} |")
zeilen += ["", "## Produkte: verkauft und verfuegbarer Bestand", "", "| Produkt | verkauft | Lieferbestand | verfuegbar | Mindestbestand |",
           "|---|---|---|---|---|"]
for p in PRODUKTE:
    zeilen.append(f"| {p[0]} {p[1]} {p[3].strip()} | {verkauft_je_prod[p[0]]} | {lieferbestand[p[0]]} | "
                  f"{lieferbestand[p[0]] - verkauft_je_prod[p[0]]} | {p[5]} |")
(Path(__file__).parent / "erwartung.md").write_text("\n".join(zeilen) + "\n", encoding="utf-8")
print("\n".join(zeilen[:16]))
