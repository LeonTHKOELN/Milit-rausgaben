# Militaerausgaben

Streamlit-App zu den Verteidigungsausgaben Deutschlands 2014–2026e, erstellt für das Gruppenprojekt im Modul
Management und Unternehmenssteuerung (TH Köln, WS 26/27).

## Inhalt

- **Entwicklung:** Ausgaben nominal und real, reale Veränderung zum Vorjahr
- **BIP-Anteil:** Deutschland im Vergleich, Trend je Land für alle 31 Alliierten
- **Kategorien & Personal:** Ausrüstung, Personal, Infrastruktur, Sonstiges (real und in %), Index, Militärpersonal
- **Abgleich SIPRI:** NATO- und SIPRI-Werte 2014–2025 im Vergleich
- **Langfristvergleich:** SIPRI-Reihe 1953–2025, Anteil an den Staatsausgaben ab 1991
- **Einordnung, Daten & Quellen:** Tabellen, CSV-Download, Quellenliste

## Lokal starten

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Online veröffentlichen

Auf [share.streamlit.io](https://share.streamlit.io) mit GitHub anmelden, „Create app“ wählen, dieses Repository,
Branch `main` und die Datei `app.py` angeben.

## Daten (`data/`)

| Datei | Inhalt | Quelle |
|---|---|---|
| `germany.csv` | Deutschland 2014–2026e, Tabellen 1–8 | NATO-Bericht 2026 |
| `vergleich.csv` | BIP-Anteil ausgewählter Länder | NATO-Bericht 2026, Tabelle 3 |
| `allies.csv` | Alle Alliierten 2014 und 2026e | NATO-Bericht 2026, Tabelle 4 |
| `bip_trend.csv` | BIP-Anteil je Land 2014–2026e | NATO-Bericht 2026, Tabelle 3 |
| `sipri_de.csv` | Deutschland 1949–2025 | SIPRI Milex v1.2 (April 2026) |
| `abgleich_alliierte.csv` | BIP-Anteil 2025, NATO und SIPRI | NATO und SIPRI |

Die NATO-Werte wurden aus den Tabellen des Berichts übernommen. Werte für 2025 und 2026 sind NATO-Schätzungen.

- [NATO: Defence Expenditure of NATO Countries (2026)](https://www.nato.int/content/dam/nato/webready/documents/finance/def-exp-2026-en.pdf)
- [SIPRI Military Expenditure Database](https://sipri.org/databases/milex)
