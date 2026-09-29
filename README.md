# Inkrementelle Aktualisierung der Wissensbasis

Dieses Beispiel zeigt, wie eine RAG-Wissensbasis bei regelmäßig aktualisierten Datenquellen effizient aktuell gehalten werden kann.

## Setup

Das Beispiel verwendet **Python 3.11** und `uv` für das Dependency-Management.

Falls `uv` noch nicht installiert ist, kann es entsprechend der [Installationsanleitung](https://docs.astral.sh/uv/getting-started/installation/) installiert werden.

Anschließend die Abhängigkeiten installieren:

```bash
uv sync
```

## Idee

Statt bei jeder Aktualisierung alle Dokumente erneut zu verarbeiten und zu embeddieren, werden zwei Datenstände miteinander verglichen.

Für jedes Dokument werden unter anderem folgende Informationen gespeichert:

* Dokument-ID
* Version
* Gültigkeitszeitraum
* Inhalt
* Hash des Inhalts
* Quelldatei

Anhand dieser Informationen werden Dokumente in vier Kategorien eingeteilt:

* **added** – neue Dokumente
* **changed** – geänderte Dokumente oder Metadaten
* **unchanged** – unveränderte Dokumente
* **removed** – nicht mehr vorhandene Dokumente

Nur neue und geänderte Dokumente müssen anschließend erneut verarbeitet und eingebettet werden.

## Verwendung

Das Skript erwartet zwei Ordner mit PDF-Dokumenten:

```text
Dateien/
├── SGBVI1-25-057.000.000/
│   └── *.pdf
└── SGBVI1-25-057.335.017/
    └── *.pdf
```

Ausführung:

```bash
uv run python code_example.py
```

Beispielausgabe:

```text
added: 1
changed: 26
unchanged: 0
removed: 0
```

## Aktualisierung der Wissensbasis

Nach der Erkennung der Änderungen werden neue Dokumente indexiert und alte Versionen geänderter Dokumente deaktiviert:

```text
Datenquelle
    ↓
Dokumente einlesen
    ↓
Metadaten und Content-Hash bestimmen
    ↓
Mit vorherigem Datenstand vergleichen
    ↓
┌─────────┬─────────┬────────────┬─────────┐
│ added   │ changed │ unchanged  │ removed │
└─────────┴─────────┴────────────┴─────────┘
    ↓          ↓                       ↓
  index    alte Version            deaktivieren
           deaktivieren
              ↓
           indexieren
```

Die Funktionen `index_document()` und `deactivate_old_version()` sind im Beispiel Platzhalter. In einer vollständigen RAG-Anwendung würden sie die Verarbeitung der Dokumente, Chunking, Embedding und Speicherung in der Vector Database übernehmen.


