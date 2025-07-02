#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KFZ-Kennzeichen Kartengenerator für Kinderbuch
Erstellt Karten mit deutschen KFZ-Kennzeichen und ihren zugehörigen Regionen.
"""

import os
import sys
import subprocess
import shutil
import json
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import fiona
import re
import PyPDF2
from PIL import Image
import io



# Funktion zum Bearbeiten des PDFs
def process_pdf(pdf_path, output_path="kfz_sammelbuch_final.pdf", config=None):
    from PyPDF2 import PdfReader, PdfWriter
    
    print("Bearbeite das PDF...")
    
    # Erstelle einen PDF-Writer für das Ergebnis
    writer = PdfWriter()
    
    # Füge das Titelbild als erste Seite hinzu
    # Wenn ein Home-Kennzeichen angegeben wurde, versuche zuerst das regionsspezifische Titelbild zu verwenden
    home_code = ''
    if config is not None:
        home_code = config.get('home', '')
    title_image_path = ""
    
    if home_code:
        region_title_image = f"output_maps/kfz_titelbild_{home_code}.pdf"
        if os.path.exists(region_title_image):
            title_image_path = region_title_image
            print(f"Verwende regionsspezifisches Titelbild für {home_code}: {title_image_path}")
        else:
            print(f"Kein regionsspezifisches Titelbild für {home_code} gefunden, verwende Standard-Titelbild.")
            title_image_path = "output_maps/kfz_titelbild.pdf"
    else:
        title_image_path = "output_maps/kfz_titelbild.pdf"
    
    if os.path.exists(title_image_path):
        print(f"Füge Titelbild hinzu: {title_image_path}")
        # Da wir jetzt direkt mit PDF-Dateien arbeiten, können wir das PDF direkt einfügen
        with open(title_image_path, "rb") as f:
            title_pdf = PdfReader(f)
            # Füge die erste Seite des Titelbilds als erste Seite des Hauptdokuments ein
            writer.add_page(title_pdf.pages[0])
        
        # Füge zwei leere Seiten nach der Titelseite hinzu
        print("Füge zwei leere Seiten nach der Titelseite hinzu")
        for _ in range(2):
            writer.add_blank_page(width=595, height=842)  # A4 Größe in Punkten
    else:
        print(f"WARNUNG: Titelbild nicht gefunden: {title_image_path}")
    
    # Füge das ursprüngliche PDF hinzu
    reader = PdfReader(pdf_path)
    for page in reader.pages:
        writer.add_page(page)
    
    # Berechne, wie viele leere Seiten am Ende hinzugefügt werden müssen
    total_pages = len(writer.pages)
    pages_to_add = (4 - (total_pages % 4)) % 4
    
    # Stelle sicher, dass mindestens eine leere Seite am Ende ist
    if pages_to_add == 0:
        pages_to_add = 4  # Füge einen kompletten Viererblock hinzu
        
    print(f"Füge {pages_to_add} leere Seiten am Ende hinzu (mindestens eine, und Gesamtseitenzahl durch 4 teilbar)")
    for _ in range(pages_to_add):
        writer.add_blank_page(width=595, height=842)  # A4 Größe in Punkten
    
    # Speichere das bearbeitete PDF
    with open(output_path, "wb") as output:
        writer.write(output)
    
    print(f"Bearbeitetes PDF gespeichert als: {output_path}")
    return output_path

import numpy as np
import matplotlib.patches as patches
from shapely.geometry import Point
import re
import random

# Konstanten
SHAPEFILE_PATH = "kfz250.utm32s.shape/kfz250/KFZ250.shp"
CSV_PATH = "/Users/tvluke/projects/kfz kennzeichen/kfz-kennz-d.csv"
OUTPUT_DIR = "output_maps"
CODES_PER_PAGE = 20  # Anzahl der Kennzeichen pro Seite
RARE_CODES_PER_PAGE = 60  # Anzahl der seltenen Kennzeichen pro Seite
PAGE_WIDTH = 8.27  # DIN-A4 Breite in Zoll
PAGE_HEIGHT = 11.69  # DIN-A4 Höhe in Zoll


def load_shapefile(shapefile_path):
    """
    Lädt ein Shapefile und gibt ein GeoDataFrame zurück.
    Versucht verschiedene Kodierungen, falls die Standardkodierung fehlschlägt.
    """
    print("Versuche Shapefile zu laden...")
    
    # Versuche zuerst mit UTF-8
    try:
        gdf = gpd.read_file(shapefile_path, encoding='utf-8')
        print("Shapefile erfolgreich mit UTF-8 geladen")
        return gdf
    except Exception as e:
        print(f"Fehler beim Laden mit UTF-8: {e}")
    
    # Versuche mit latin1
    try:
        gdf = gpd.read_file(shapefile_path, encoding='latin1')
        print("Shapefile erfolgreich mit latin1 geladen")
        return gdf
    except Exception as e:
        print(f"Fehler beim Laden mit latin1: {e}")
    
    # Versuche mit fiona direkt
    try:
        print("Versuche mit fiona zu laden...")
        with fiona.open(shapefile_path) as f:
            gdf = gpd.GeoDataFrame.from_features(f, crs=f.crs)
        print("Shapefile erfolgreich mit fiona geladen")
        return gdf
    except Exception as e:
        print(f"Fehler beim Laden mit fiona: {e}")
        
    # Wenn alles fehlschlägt
    print("Konnte das Shapefile nicht laden.")
    sys.exit(1)


def load_config():
    """
    Lädt die Konfigurationsdatei, falls vorhanden.
    Gibt ein Dictionary mit den Konfigurationseinstellungen zurück.
    """
    config = {
        "home": None,
        "version": "Version 1.1.0 Aalen Ostalbkreis"
    }
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                config.update(loaded_config)
            
            if config['home']:
                print(f"Konfiguration geladen: Home-Kennzeichen ist {config['home']}")
            else:
                print("Konfiguration geladen: Kein Home-Kennzeichen definiert")
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration: {e}")
    else:
        print("Keine Konfigurationsdatei gefunden, verwende Standardeinstellungen")
    
    return config

def normalize_text(text):
    """
    Normalisiert Text, um Probleme mit Umlauten zu beheben.
    """
    if not isinstance(text, str):
        return ""
    
    # Häufige Fehlkodierungen korrigieren
    text = text.replace('Ã¤', 'ä').replace('Ã¶', 'ö').replace('Ã¼', 'ü')
    text = text.replace('Ã', 'Ä').replace('Ã–', 'Ö').replace('Ã', 'Ü')
    text = text.replace('Ã', 'ß')
    
    # Weitere Normalisierungen
    replacements = {
        'Ã¤': 'ä', 'Ã¶': 'ö', 'Ã¼': 'ü',
        'Ã': 'Ä', 'Ã': 'Ö', 'Ã': 'Ü',
        'Ã': 'ß', 'Ã©': 'é', 'Ã¨': 'è',
        'Ã ': 'à', 'Ã¹': 'ù', 'Ã®': 'î',
        'Ã´': 'ô', 'Ã»': 'û', 'Ãª': 'ê',
        'Ã§': 'ç'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text.strip()


def load_csv_data(csv_path):
    """
    Lädt die CSV-Datei mit den KFZ-Kennzeichen und gibt zwei Dictionaries zurück:
    1. Kennzeichen zu Regionsnamen
    2. Kennzeichen zu Bundesland
    """
    print(f"Lade CSV-Datei: {csv_path}")
    try:
        # Lese die CSV-Datei
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        # Überprüfe die Spalten
        if len(df.columns) < 2:
            print("Warnung: CSV-Datei hat weniger als 2 Spalten. Format könnte falsch sein.")
            return {}, {}
        
        # Erstelle Dictionaries mit Kennzeichen als Schlüssel
        code_to_csv_name = {}
        code_to_state = {}
        
        # Erste Spalte enthält die Kennzeichen, zweite Spalte die Regionsnamen, dritte Spalte das Bundesland
        for _, row in df.iterrows():
            code = str(row.iloc[0]).strip()
            if code.startswith('"'):
                code = code[1:]
            if code.endswith('"'):
                code = code[:-1]
            
            # Normalisiere den Code
            code = normalize_text(code)
            
            # Zweite Spalte enthält den Regionsnamen
            region_name = normalize_text(str(row.iloc[1]))
            
            # Dritte Spalte enthält das Bundesland (falls vorhanden)
            state = ""
            if len(df.columns) >= 3 and pd.notna(row.iloc[2]):
                state = normalize_text(str(row.iloc[2]))
            
            # Speichere in den Dictionaries
            if code:
                code_to_csv_name[code] = region_name
                code_to_state[code] = state
        
        print(f"CSV-Datei erfolgreich geladen. {len(code_to_csv_name)} Kennzeichen gefunden.")
        return code_to_csv_name, code_to_state
    
    except Exception as e:
        print(f"Fehler beim Laden der CSV-Datei: {e}")
        return {}, {}


def create_home_region_box(code, region_name, state, other_codes):
    """
    Erstellt einen gelben Infokasten für die Heimatregion.
    """
    if not region_name:
        return ""
    
    text = f"\\textbf{{{region_name}}} ist unser Zuhause! "
    text += f"Wir haben das Kennzeichen \\textbf{{{code}}}"
    
    if state:
        text += f" und wohnen im Bundesland \\textbf{{{state}}}"
    
    text += "."
    
    # Füge Informationen über weitere Kennzeichen hinzu, falls vorhanden
    if other_codes:
        if len(other_codes) == 1:
            text += f" Bei uns gibt es auch das Kennzeichen \\textbf{{{other_codes[0]}}}."
        else:
            joined_codes = ', '.join([f"\\textbf{{{c}}}" for c in other_codes[:-1]])
            text += f" Bei uns gibt es auch die Kennzeichen {joined_codes} und \\textbf{{{other_codes[-1]}}}."
    
    return create_yellow_box(text)


def create_largest_region_box(code, region_name, area, home_region_name=None, home_region_area=None):
    """
    Erstellt einen gelben Infokasten für die größte Region in Deutschland.
    Vergleicht die Größe mit der Heimatregion, wenn möglich.
    """
    if not region_name or area <= 0:
        return ""
    
    # Umrechnung in Quadratkilometer
    area_km2 = area
    
    # Vergleiche mit bekannten Größen
    football_fields = int(area_km2 * 100 / 0.71)  # Ein Fußballfeld ist ca. 0,71 Hektar = 0,0071 km²
    
    text = f"\\textbf{{{region_name}}} mit dem Kennzeichen \\textbf{{{code}}} ist die größte Region in Deutschland. "
    text += f"Mit einer Fläche von ungefähr {area_km2:.0f} Quadratkilometern ist sie so groß wie {football_fields} Fußballfelder!"
    
    # Vergleich mit der Heimatregion, wenn verfügbar
    if home_region_name and home_region_area and home_region_area > 0:
        times_larger = area_km2 / home_region_area
        if times_larger > 1.5:
            text += f" Das ist ungefähr {times_larger:.1f}-mal größer als unsere Heimatregion {home_region_name}!"
    
    # Markiere die größte Region als angezeigt
    global largest_region_shown
    largest_region_shown = True
    
    return create_yellow_box(text)


def create_farthest_from_home_box(code, region_name, distance_km, home_code, home_region_name):
    """
    Erstellt einen gelben Infokasten für die Region, die am weitesten von der Heimatregion entfernt ist.
    """
    if not region_name or not home_region_name:
        return ""
    
    # Prüfe, ob die Entfernung gültig ist
    if not isinstance(distance_km, (int, float)) or distance_km <= 0 or distance_km > 1000 or distance_km != distance_km:  # letzte Bedingung prüft auf NaN
        print(f"Warnung: Ungültige Entfernung ({distance_km}) für {code} zu {home_code}")
        return ""
    
    # Runde die Entfernung auf ganze Kilometer
    try:
        distance_km_rounded = round(distance_km)
    except (OverflowError, ValueError) as e:
        print(f"Fehler beim Runden der Entfernung ({distance_km}) für {code}: {e}")
        return ""
    
    text = f"\\textbf{{{region_name}}} mit dem Kennzeichen \\textbf{{{code}}} ist am weitesten von unserem Zuhause \\textbf{{{home_region_name}}} (\\textbf{{{home_code}}}) entfernt. "
    text += f"Die Entfernung beträgt ungefähr {distance_km_rounded} Kilometer. "
    
    # Berechne Reisezeiten mit verschiedenen Fortbewegungsmitteln
    auto_stunden = round(distance_km_rounded / 100)  # Bei durchschnittlich 100 km/h
    fahrrad_stunden = round(distance_km_rounded / 10)  # Bei durchschnittlich 10 km/h
    zu_fuss_stunden = round(distance_km_rounded / 3)  # Bei durchschnittlich 3 km/h
    
    # Formatiere die Zeiten kindgerecht
    auto_text = f"{auto_stunden} Stunde" if auto_stunden == 1 else f"{auto_stunden} Stunden"
    fahrrad_text = f"{fahrrad_stunden} Stunde" if fahrrad_stunden == 1 else f"{fahrrad_stunden} Stunden"
    
    # Für Fußgänger die Zeit in Tagen angeben, wenn sie zu lang ist
    if zu_fuss_stunden >= 24:
        zu_fuss_tage = round(zu_fuss_stunden / 24)
        zu_fuss_text = f"{zu_fuss_tage} Tag" if zu_fuss_tage == 1 else f"{zu_fuss_tage} Tage"
        zu_fuss_zusatz = "(wenn man 8 Stunden am Tag läuft)"
    else:
        zu_fuss_text = f"{zu_fuss_stunden} Stunde" if zu_fuss_stunden == 1 else f"{zu_fuss_stunden} Stunden"
        zu_fuss_zusatz = ""
    
    # Füge kindgerechte Vergleiche hinzu
    text += f"Mit dem Auto würde man ungefähr {auto_text} brauchen, "
    text += f"mit dem Fahrrad {fahrrad_text} "
    text += f"und zu Fuß sogar {zu_fuss_text} {zu_fuss_zusatz}!"
    
    return create_yellow_box(text)


def create_extreme_location_box(code, region_name, position_type, is_absolute=True):
    """
    Erstellt einen gelben Infokasten für die nördlichste, südlichste, westlichste oder östlichste Region.
    """
    if not region_name:
        return ""
    
    position_descriptions = {
        'north': 'nördlichste',
        'south': 'südlichste',
        'west': 'westlichste',
        'east': 'östlichste'
    }
    
    position_facts = {
        'north': 'Wenn du von hier aus nach Norden gehst, kommst du zur Ostsee oder nach Dänemark!',
        'south': 'Wenn du von hier aus nach Süden gehst, kommst du bald in die Alpen!',
        'west': 'Wenn du von hier aus nach Westen gehst, kommst du bald nach Frankreich, Belgien oder in die Niederlande!',
        'east': 'Wenn du von hier aus nach Osten gehst, kommst du bald nach Polen!'
    }
    
    description = position_descriptions.get(position_type, '')
    fact = position_facts.get(position_type, '')
    
    if not description:
        return ""
    
    # Markiere diese Extremposition als verwendet
    global used_extreme_positions
    used_extreme_positions.add(position_type)
    
    location_text = "in Deutschland" if is_absolute else "auf dieser Seite"
    text = f"\\textbf{{{region_name}}} mit dem Kennzeichen \\textbf{{{code}}} ist die {description} Region {location_text}. {fact}"
    
    return create_yellow_box(text)


def create_yellow_box(text):
    """
    Erstellt einen gelben Infokasten mit dem gegebenen Text.
    Der Kasten hat abgerundete Ecken und einen dickeren Rand in einem dunkleren Gelbton.
    """
    if not text:
        return ""
    
    # LaTeX-Code für einen schönen gelben Kasten mit abgerundeten Ecken
    # Definiere die Farben
    yellow_box = r"\definecolor{lightyellow}{RGB}{255,250,205}" + "\n"
    yellow_box += r"\definecolor{darkeryellow}{RGB}{255,204,0}" + "\n"
    
    # Beginne den Kasten
    yellow_box += r"\begin{center}" + "\n"
    
    # Verwende tcolorbox für schönere Kästen mit abgerundeten Ecken
    yellow_box += r"\begin{tcolorbox}[" + "\n"
    yellow_box += r"    enhanced," + "\n"
    yellow_box += r"    width=0.95\textwidth," + "\n"
    yellow_box += r"    colback=lightyellow," + "\n"
    yellow_box += r"    colframe=darkeryellow," + "\n"
    yellow_box += r"    arc=8pt," + "\n"  # Abgerundete Ecken
    yellow_box += r"    boxrule=2pt," + "\n"  # Dickerer Rand
    yellow_box += r"    fontupper=\normalfont," + "\n"
    yellow_box += r"    top=6pt," + "\n"
    yellow_box += r"    bottom=6pt," + "\n"
    yellow_box += r"    left=8pt," + "\n"
    yellow_box += r"    right=8pt" + "\n"
    yellow_box += r"]" + "\n"
    
    # Füge den Text ein
    yellow_box += text + "\n"
    
    # Schließe den Kasten
    yellow_box += r"\end{tcolorbox}" + "\n"
    yellow_box += r"\end{center}" + "\n"
    
    return yellow_box


# Globale Variablen
farthest_region_from_home = None
largest_region_info = None

# Speichert die bereits verwendeten Extrempositionen (nördlichste, südlichste, etc.)
used_extreme_positions = set()

# Flag, ob die größte Region bereits angezeigt wurde
largest_region_shown = False

# Speichert die bereits verwendeten Kennzeichen für die Buchstaben-Matching-Box
used_letter_matching_codes = set()

# Speichert die absoluten Extrempositionen in Deutschland
absolute_extreme_positions = {
    'north': None,
    'south': None,
    'west': None,
    'east': None
}

# Flag, ob bereits eine spezielle Faktenbox gezeigt wurde
special_fact_shown = False

# Spezielle Fakten für bestimmte Städte/Regionen
special_facts = {
    'WOB': '\\textbf{Wolfsburg} mit dem Kennzeichen \\textbf{WOB} ist die Stadt aus der VW kommt. Viele VW Autos werden dort auch hergestellt.',
    'S': '\\textbf{Stuttgart} mit dem Kennzeichen \\textbf{S} ist die Heimat von Mercedes-Benz und Porsche',
    'M': '\\textbf{München} mit dem Kennzeichen \\textbf{M} ist die Stadt, in der BMW seinen Hauptsitz hat. BMW steht für Bayerische Motoren Werke.',
    'IN': '\\textbf{Ingolstadt} mit dem Kennzeichen \\textbf{IN} ist die Heimatstadt von Audi. Dort werden viele Audi-Modelle gebaut.',
    'B': '\\textbf{Berlin} mit dem Kennzeichen \\textbf{B} ist die Hauptstadt von Deutschland und hat über 3,6 Millionen Einwohner.',
    'HH': '\\textbf{Hamburg} mit dem Kennzeichen \\textbf{HH} hat den größten Hafen Deutschlands. HH steht für Hansestadt Hamburg.',
    'K': '\\textbf{Köln} mit dem Kennzeichen \\textbf{K} hat einen der größten und schönsten Dome der Welt.',
    'F': '\\textbf{Frankfurt} mit dem Kennzeichen \\textbf{F} hat den größten Flughafen Deutschlands und viele Hochhäuser.',
    'N': '\\textbf{Nürnberg} mit dem Kennzeichen \\textbf{N} ist bekannt für seine Lebkuchen.'
}

def find_farthest_region_from_home(all_codes, code_to_region, code_to_name, home_code):
    """
    Findet die am weitesten von der Heimat entfernte Region unter ALLEN Regionen.
    Gibt ein Dictionary mit den Informationen zur entferntesten Region zurück.
    """
    global farthest_region_from_home
    
    # Wir berechnen die entfernteste Region immer neu, um sicherzustellen, dass wir
    # auch mehrfach vorkommende Kennzeichen korrekt berücksichtigen
    
    # Wenn kein Home-Code konfiguriert ist oder der Home-Code nicht in den Regionen ist
    if not home_code or home_code not in code_to_region:
        farthest_region_from_home = None
        return None
    
    home_region = code_to_region[home_code]
    home_region_name = code_to_name.get(home_code, "")
    
    if 'geometry' not in home_region or not hasattr(home_region['geometry'], 'centroid'):
        farthest_region_from_home = None
        return None
    
    home_centroid = home_region['geometry'].centroid
    
    max_distance = 0
    farthest_code = None
    farthest_distance = 0
    
    # Durchlaufe ALLE Codes, nicht nur die auf der aktuellen Seite
    for code in all_codes:
        if code != home_code and code in code_to_region:
            region = code_to_region[code]
            if 'geometry' in region and hasattr(region['geometry'], 'centroid'):
                centroid = region['geometry'].centroid
                # Berechne die Entfernung in Kilometern mit einer robusten Methode
                try:
                    # Prüfe, ob die Zentroide gültige Koordinaten haben
                    if (home_centroid.x is None or home_centroid.y is None or 
                        centroid.x is None or centroid.y is None):
                        # Ungültige Koordinaten, überspringe diesen Code
                        continue
                    
                    # Wir gehen davon aus, dass die Daten im Koordinatensystem EPSG:25832 vorliegen
                        
                    from shapely.geometry import Point
                    p1 = Point(home_centroid.x, home_centroid.y)
                    p2 = Point(centroid.x, centroid.y)
                    
                    # Direkte Berechnung der euklidischen Distanz im UTM-Koordinatensystem
                    # Da EPSG:25832 bereits in Metern ist, ist dies eine genaue Distanz
                    from math import sqrt
                    
                    # Euklidische Distanz berechnen (in Metern)
                    dx = p2.x - p1.x
                    dy = p2.y - p1.y
                    distance_meters = sqrt(dx*dx + dy*dy)
                    
                    # Umrechnung in Kilometer
                    distance = distance_meters / 1000
                    
                    # Sanity Check: Distanzen in Deutschland sind < 1000 km
                    if distance <= 0 or distance > 1000 or not isinstance(distance, (int, float)) or distance != distance:  # letzte Bedingung prüft auf NaN
                        # Versuche alternative Methode mit GeoPandas
                        try:
                            from geopandas import GeoSeries
                            # Wir erstellen GeoSeries mit dem korrekten CRS
                            gs1 = GeoSeries([p1], crs="EPSG:25832")
                            gs2 = GeoSeries([p2], crs="EPSG:25832")
                            # Da wir bereits im metrischen System sind, ist keine Umrechnung nötig
                            distance = gs1.distance(gs2)[0] / 1000
                            
                            # Nochmaliger Sanity Check
                            if distance <= 0 or distance > 1000 or not isinstance(distance, (int, float)) or distance != distance:  # letzte Bedingung prüft auf NaN
                                continue
                        except Exception as e:
                            print(f"Fehler bei der alternativen Distanzberechnung für {code}: {e}")
                            continue
                except Exception as e:
                    # Bei Fehlern diese Region überspringen
                    print(f"Fehler bei der Distanzberechnung für {code}: {e}")
                    continue
                
                if distance > max_distance:
                    max_distance = distance
                    farthest_code = code
                    farthest_distance = distance
    
    if farthest_code:
        farthest_region_from_home = {
            'code': farthest_code,
            'name': code_to_name.get(farthest_code, ""),
            'distance': farthest_distance,
            'home_code': home_code,
            'home_name': home_region_name
        }
        return farthest_region_from_home
    else:
        farthest_region_from_home = None
        return None


def find_extreme_positions(all_codes, code_to_region, code_to_name):
    """
    Findet die absoluten Extrempositionen (nördlichste, südlichste, westlichste, östlichste) in Deutschland.
    Verwendet die tatsächlichen äußersten Punkte der Regionsgrenzen, nicht die Zentroide.
    """
    global absolute_extreme_positions
    
    # Wenn wir die Extrempositionen bereits berechnet haben, gib sie zurück
    if absolute_extreme_positions['north'] is not None:
        return absolute_extreme_positions
    
    extremes = {
        'north': {'y': -float('inf'), 'code': None},
        'south': {'y': float('inf'), 'code': None},
        'west': {'x': float('inf'), 'code': None},
        'east': {'x': -float('inf'), 'code': None}
    }
    
    for code in all_codes:
        if code in code_to_region:
            region = code_to_region[code]
            if 'geometry' in region:
                # Verwende die Bounds-Methode, die für alle Geometrietypen funktioniert
                # bounds gibt (minx, miny, maxx, maxy) zurück
                if hasattr(region['geometry'], 'bounds'):
                    minx, miny, maxx, maxy = region['geometry'].bounds
                    
                    # Nördlichste (höchster y-Wert)
                    if maxy > extremes['north']['y']:
                        extremes['north']['y'] = maxy
                        extremes['north']['code'] = code
                    
                    # Südlichste (niedrigster y-Wert)
                    if miny < extremes['south']['y']:
                        extremes['south']['y'] = miny
                        extremes['south']['code'] = code
                    
                    # Westlichste (niedrigster x-Wert)
                    if minx < extremes['west']['x']:
                        extremes['west']['x'] = minx
                        extremes['west']['code'] = code
                    
                    # Östlichste (höchster x-Wert)
                    if maxx > extremes['east']['x']:
                        extremes['east']['x'] = maxx
                        extremes['east']['code'] = code
    
    # Speichere die Ergebnisse
    for position in ['north', 'south', 'west', 'east']:
        code = extremes[position]['code']
        if code:
            region_name = code_to_name.get(code, "")
            absolute_extreme_positions[position] = {
                'code': code,
                'name': region_name
            }
    
    return absolute_extreme_positions

def find_largest_region(all_codes, code_to_region, code_to_name):
    """
    Findet die größte Region unter allen Regionen.
    """
    global largest_region_info
    
    # Wenn wir die größte Region bereits berechnet haben, gib sie zurück
    if largest_region_info:
        return largest_region_info
    
    max_area = 0
    largest_code = None
    largest_area = 0
    
    for code in all_codes:
        if code in code_to_region:
            region = code_to_region[code]
            if 'geometry' in region and hasattr(region['geometry'], 'area'):
                # Berechne die Fläche in Quadratkilometern (ungefähr)
                area = region['geometry'].area * (111**2) / 1000000  # Umrechnung in km²
                
                if area > max_area:
                    max_area = area
                    largest_code = code
                    largest_area = area
    
    if largest_code:
        region_name = code_to_name.get(largest_code, "")
        largest_region_info = {
            'code': largest_code,
            'name': region_name,
            'area': largest_area
        }
        return largest_region_info
    
    return None

def create_letter_matching_box(code, region_name):
    """
    Erstellt einen gelben Infokasten für Kennzeichen mit einem Buchstaben, die mit dem Anfangsbuchstaben der Region übereinstimmen.
    """
    if not region_name or not code or len(code) != 1:
        return ""
    
    text = f"\\textbf{{{region_name}}} hat das Kennzeichen \\textbf{{{code}}}. Das ist der gleiche Buchstabe, mit dem auch der Name der Region anfängt. Das ist ein schöner Zufall!"
    
    return create_yellow_box(text)


def create_special_fact_box(code):
    """
    Erstellt einen gelben Infokasten mit einem speziellen Fakt zu einer Stadt/Region.
    """
    global special_facts
    
    if code not in special_facts:
        return ""
    
    text = special_facts[code]
    
    return create_yellow_box(text)

def get_info_box_for_page(page_num, page_codes, gdf, code_to_region, code_to_name, code_to_state, code_to_other_codes, config, code_to_name_multi=None):
    """
    Generiert einen gelben Infokasten für die Seite basierend auf den Kennzeichen auf dieser Seite.
    Priorisiert die verschiedenen Arten von Kästen in der folgenden Reihenfolge:
    1. Heimatregion
    2. Am weitesten von der Heimat entfernt (nur auf der Seite, wo diese Region vorkommt)
    3. Größte Region in Deutschland (nur einmal im Buch)
    4. Extreme Position (Nördlichste, Südlichste, Westlichste, Östlichste)
    5. Kennzeichen mit einem Buchstaben, der mit dem Anfangsbuchstaben der Region übereinstimmt
    6. Kennzeichen mit mehreren Regionen
    """
    # Prüfe, ob ein Home-Kennzeichen konfiguriert ist
    home_code = None
    if config and 'home' in config and config['home']:
        home_code = str(config['home']).strip()
    
    # 1. Prüfe, ob die Heimatregion auf dieser Seite ist
    if home_code and home_code in page_codes:
        region_name = code_to_name.get(home_code, "")
        state = code_to_state.get(home_code, "")
        other_codes = code_to_other_codes.get(home_code, [])
        return create_home_region_box(home_code, region_name, state, other_codes)
    
    # Wenn die Heimatregion nicht auf dieser Seite ist, prüfe die anderen Möglichkeiten
    
    # 2. Finde die am weitesten von der Heimat entfernte Region unter ALLEN Regionen
    # und zeige sie nur auf der Seite an, auf der sie vorkommt
    if home_code:
        # Verwende alle regulären Codes, nicht nur die auf der aktuellen Seite
        all_codes = list(code_to_region.keys())
        farthest_region = find_farthest_region_from_home(all_codes, code_to_region, code_to_name, home_code)
        
        # Wenn die entfernteste Region auf dieser Seite ist, zeige den Infokasten an
        if farthest_region and farthest_region['code'] in page_codes:
            return create_farthest_from_home_box(
                farthest_region['code'],
                farthest_region['name'],
                farthest_region['distance'],
                farthest_region['home_code'],
                farthest_region['home_name']
            )
    
    # 3. Größte Region in Deutschland (nur einmal im Buch zeigen)
    global largest_region_shown
    if not largest_region_shown:
        all_codes = list(code_to_region.keys())
        largest_region = find_largest_region(all_codes, code_to_region, code_to_name)
        
        if largest_region and largest_region['code'] in page_codes:
            # Wenn wir eine Heimatregion haben, vergleiche mit dieser
            home_region_name = None
            home_region_area = None
            
            if home_code and home_code in code_to_region:
                home_region = code_to_region[home_code]
                if 'geometry' in home_region and hasattr(home_region['geometry'], 'area'):
                    home_region_name = code_to_name.get(home_code, "")
                    home_region_area = home_region['geometry'].area * (111**2) / 1000000  # Umrechnung in km²
            
            return create_largest_region_box(
                largest_region['code'],
                largest_region['name'],
                largest_region['area'],
                home_region_name,
                home_region_area
            )
    
    # 4. Finde absolute Extrempositionen in Deutschland (Nördlichste, Südlichste, Westlichste, Östlichste)
    # Aber nur solche, die noch nicht im Buch verwendet wurden
    all_codes = list(code_to_region.keys())
    find_extreme_positions(all_codes, code_to_region, code_to_name)
    
    # Filtere die Positionen, die bereits verwendet wurden
    global used_extreme_positions, absolute_extreme_positions
    available_positions = [pos for pos in ['north', 'south', 'west', 'east'] 
                          if pos not in used_extreme_positions 
                          and absolute_extreme_positions[pos] is not None
                          and absolute_extreme_positions[pos]['code'] in page_codes]
    
    # Wenn keine Position mehr verfügbar ist, gehe weiter zum nächsten Schritt
    if available_positions:
        # Wähle eine zufällige verfügbare extreme Position aus
        import random
        random.shuffle(available_positions)
        position = available_positions[0]
        
        extreme_info = absolute_extreme_positions[position]
        return create_extreme_location_box(extreme_info['code'], extreme_info['name'], position, is_absolute=True)
    
    # 5. Suche nach Kennzeichen mit einem Buchstaben, die mit dem Anfangsbuchstaben der Region übereinstimmen
    # Aber nur, wenn noch keine solche Box im Buch gezeigt wurde
    global used_letter_matching_codes
    
    # Flag, ob bereits eine Buchstaben-Matching-Box im Buch gezeigt wurde
    letter_matching_shown = len(used_letter_matching_codes) > 0
    
    if not letter_matching_shown:
        for code in page_codes:
            if len(code) == 1 and code not in used_letter_matching_codes:
                if code in code_to_name:
                    region_name = code_to_name[code]
                    if region_name and region_name.startswith(code):
                        used_letter_matching_codes.add(code)
                        return create_letter_matching_box(code, region_name)
    
    # 6. Spezielle Fakten für bestimmte Städte/Regionen
    # Aber nur, wenn noch keine solche Box im Buch gezeigt wurde
    global special_fact_shown
    
    if not special_fact_shown:
        for code in page_codes:
            if code in special_facts:
                special_fact_shown = True
                return create_special_fact_box(code)
    
    # Wenn keine passende Info gefunden wurde, gib einen leeren String zurück
    return ""


def extract_kfz_codes(gdf):
    """
    Extrahiert alle KFZ-Kennzeichen aus dem GeoDataFrame und erstellt Zuordnungen.
    Jedes Kennzeichen wird einzeln erfasst mit Verweis auf seine Region.
    Prüft, ob das Kennzeichen in der CSV-Datei enthalten ist und teilt sie entsprechend auf.
    """
    # Lade die CSV-Datei mit den offiziellen Kennzeichen und Namen
    csv_code_to_name, csv_code_to_state = load_csv_data(CSV_PATH)
    
    # Listen für reguläre und seltene Kennzeichen
    regular_codes = []
    rare_codes = []
    
    # Dictionaries für Zuordnungen
    code_to_region = {}
    code_to_name = {}  # Kann jetzt mehrere Regionen pro Kennzeichen enthalten
    code_to_name_multi = {}  # Speichert, ob ein Kennzeichen mehrere Regionen hat
    code_to_state = {}
    code_to_other_codes = {}
    
    # Sammle alle Codes aus dem Shapefile
    shapefile_codes = set()
    
    for _, row in gdf.iterrows():
        if 'KFZ' in row and isinstance(row['KFZ'], str):
            kfz_field = normalize_text(row['KFZ'])
            region_name = normalize_text(row.get('NAME', '')) if 'NAME' in row else ''
            
            # Teile nach Komma und Leerzeichen
            comma_split = [part.strip() for part in kfz_field.split(',')]
            all_parts = []
            
            for part in comma_split:
                if ' ' in part:
                    space_split = [p.strip() for p in part.split()]
                    all_parts.extend(space_split)
                else:
                    all_parts.append(part)
            
            # Normalisiere alle Codes
            codes = [normalize_text(code) for code in all_parts if code.strip()]
            
            # Füge jeden Code einzeln hinzu
            for code in codes:
                if not code:
                    continue
                
                # Merke dir, dass dieser Code im Shapefile vorkommt
                shapefile_codes.add(code)
                    
                # Prüfe, ob der Code bereits verarbeitet wurde
                # Wir überspringen nicht mehr, sondern prüfen auf mehrfache Vorkommen
                already_processed = code in regular_codes or code in rare_codes
                
                # Wenn der Code noch nicht verarbeitet wurde, initialisiere die Einträge
                if not already_processed:
                    # Speichere die Region und andere Codes
                    code_to_region[code] = row
                    
                    # Speichere alle anderen Codes dieser Region
                    other_codes = [c for c in codes if c != code]
                    code_to_other_codes[code] = other_codes
                
                # Prüfe, ob der Code in der CSV-Datei enthalten ist
                if code in csv_code_to_name:
                    # Prüfe, ob der Code bereits eine Region hat
                    if code in code_to_name:
                        # Wenn ja, füge die neue Region hinzu und markiere als mehrfach
                        existing_name = code_to_name[code]
                        new_name = csv_code_to_name[code]
                        if existing_name != new_name:
                            code_to_name[code] = f"{existing_name} oder {new_name}"
                            code_to_name_multi[code] = True
                    else:
                        # Verwende den Namen aus der CSV-Datei
                        code_to_name[code] = csv_code_to_name[code]
                    
                    # Speichere auch das Bundesland
                    code_to_state[code] = csv_code_to_state.get(code, "")
                    
                    # Füge den Code zu den regulären Codes hinzu, wenn er noch nicht drin ist
                    if not already_processed:
                        regular_codes.append(code)
                else:
                    # Prüfe, ob der Code bereits eine Region hat
                    if code in code_to_name:
                        # Wenn ja, füge die neue Region hinzu und markiere als mehrfach
                        existing_name = code_to_name[code]
                        if existing_name != region_name and region_name:
                            code_to_name[code] = f"{existing_name} oder {region_name}"
                            code_to_name_multi[code] = True
                    else:
                        # Verwende den Namen aus dem Shapefile
                        code_to_name[code] = region_name
                        code_to_state[code] = ""
                    
                    # Füge den Code zu den seltenen Codes hinzu, wenn er noch nicht drin ist
                    if not already_processed and code not in regular_codes:
                        rare_codes.append(code)
    
    # Füge Codes hinzu, die nur in der CSV-Datei vorkommen
    csv_only_codes = []
    for code in csv_code_to_name:
        if code not in shapefile_codes and code not in rare_codes:
            code_to_name[code] = csv_code_to_name[code]
            code_to_state[code] = csv_code_to_state.get(code, "")
            code_to_other_codes[code] = []
            csv_only_codes.append(code)
    
    # Füge die CSV-only Codes zu den seltenen Kennzeichen hinzu
    rare_codes.extend(csv_only_codes)
    
    # Sortiere alphabetisch
    regular_codes.sort()
    rare_codes.sort()
    
    print(f"Insgesamt {len(regular_codes)} reguläre KFZ-Kennzeichen gefunden (in CSV und Shapefile enthalten)")
    print(f"Insgesamt {len(rare_codes)} seltene KFZ-Kennzeichen gefunden ({len(rare_codes) - len(csv_only_codes)} nur im Shapefile, {len(csv_only_codes)} nur in der CSV)")

    
    return regular_codes, rare_codes, code_to_region, code_to_name, code_to_state, code_to_other_codes, code_to_name_multi


def create_map_pages(gdf, regular_codes, code_to_region, code_to_name, code_to_state, code_to_other_codes, config=None):
    """
    Erstellt Kartenbilder für die regulären KFZ-Kennzeichen, aufgeteilt auf mehrere Seiten.
    Wenn ein Home-Kennzeichen konfiguriert ist, wird es auf jeder Karte mit einem roten Kreis markiert.
    """
    # Erstelle den Ausgabeordner, falls er nicht existiert
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Berechne die Anzahl der Seiten
    num_pages = (len(regular_codes) + CODES_PER_PAGE - 1) // CODES_PER_PAGE
    print(f"Erstelle {num_pages} Seiten mit je {CODES_PER_PAGE} regulären Kennzeichen")
    
    # Erstelle eine Farbpalette mit kräftigen, unterscheidbaren Farben
    # Kombiniere mehrere Farbpaletten und filtere Grautöne heraus
    base_colors = []
    for cmap_name in ['tab10', 'tab20', 'Dark2', 'Set1', 'Set2', 'Paired']:
        cmap = plt.cm.get_cmap(cmap_name)
        base_colors.extend([cmap(i) for i in np.linspace(0, 1, cmap.N)])
    
    # Filtere Grautöne heraus (Farben, bei denen R, G und B sehr ähnlich sind)
    filtered_colors = []
    for color in base_colors:
        r, g, b = color[:3]
        # Wenn die Differenz zwischen den Farbkanälen groß genug ist, ist es kein Grauton
        if max(abs(r-g), abs(r-b), abs(g-b)) > 0.15:
            filtered_colors.append(color)
    
    # Stelle sicher, dass wir genügend Farben haben
    while len(filtered_colors) < CODES_PER_PAGE:
        filtered_colors.extend(filtered_colors)
        
    # Erstelle ein Wörterbuch, um Regionen konsistente Farben zuzuweisen
    # Der Schlüssel ist die Region-ID (oder ein anderer eindeutiger Identifikator)
    region_to_color = {}
    
    # Erstelle eine Karte für jede Seite
    for page in range(1, num_pages + 1):
        print(f"Erstelle Karte für Seite {page} mit Kennzeichen: ", end="")
        
        # Bestimme die Kennzeichen für diese Seite
        start_idx = (page - 1) * CODES_PER_PAGE
        end_idx = min(start_idx + CODES_PER_PAGE, len(regular_codes))
        page_codes = regular_codes[start_idx:end_idx]
        
        print(", ".join(page_codes))
        
        # Erstelle eine neue Figur mit DIN-A4 Größe
        fig, ax = plt.subplots(figsize=(PAGE_WIDTH, PAGE_HEIGHT))
        
        # Prüfe, ob ein Home-Kennzeichen konfiguriert ist
        home_code = None
        if config and 'home' in config and config['home']:
            home_code = str(config['home']).strip()
        
        # Zeichne die Grundkarte von Deutschland mit weißem Hintergrund und dünnen Grenzen
        gdf.plot(ax=ax, color='white', edgecolor='lightgray', linewidth=0.3)
        
        # Zeichne einen dickeren Rahmen um die gesamte Deutschlandkarte
        # Dazu erstellen wir eine Kopie des GeoDataFrames und lösen alle inneren Grenzen auf
        germany_outline = gdf.copy()
        germany_outline['dissolve_key'] = 1  # Gleicher Wert für alle Zeilen
        germany_outline = germany_outline.dissolve(by='dissolve_key')
        germany_outline.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=2.0)
        
        # Sammle die Zentroide und Codes für diese Seite
        centroids_and_codes = []
        
        # Verfolge die auf dieser Seite verwendeten Farben
        used_colors_on_page = set()
        color_index = 0
        
        # Zeichne die Regionen für die Kennzeichen dieser Seite
        for code in page_codes:
            # Finde die Region für dieses Kennzeichen
            if code in code_to_region:
                region = code_to_region[code]
                
                # Weise dieser Region eine Farbe zu, falls noch nicht geschehen
                # Verwende eine eindeutige ID für die Region als Schlüssel
                region_id = str(region.name)  # Verwende den Index als eindeutigen Schlüssel
                if region_id not in region_to_color:
                    # Wähle eine Farbe aus der gefilterten Liste
                    color_idx = len(region_to_color) % len(filtered_colors)
                    region_to_color[region_id] = filtered_colors[color_idx]
                
                # Zeichne die Region mit der zugewiesenen Farbe
                region_id = str(region.name)  # Verwende den gleichen eindeutigen Schlüssel
                region_name = region.get('NAME', '')
                if isinstance(region_name, pd.Series) and not region_name.empty:
                    region_name = region_name.iloc[0]  # Extrahiere den ersten Wert aus der Series
                
                region_geom = gdf[gdf['NAME'] == region_name]
                if not region_geom.empty:
                    # Zeichne die Region mit der zugewiesenen Farbe
                    region_geom.plot(ax=ax, color=region_to_color[region_id], edgecolor='black', linewidth=0.5, alpha=0.7)
                
                # Berechne den Zentroid
                centroid = region_geom.geometry.centroid.iloc[0]
                
                # Füge den Zentroid und den Code hinzu
                region_id = str(region.name)  # Verwende den gleichen eindeutigen Schlüssel
                centroids_and_codes.append((centroid, code, region_to_color[region_id]))
        
        # Stelle sicher, dass das Ausgabeverzeichnis existiert
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Bestimme die Grenzen der Karte
        bounds = gdf.total_bounds
        
        # Berechne die Position für die Labels am rechten Rand
        text_x = bounds[2] + 0.1  # Rechter Rand + Abstand
        
        # Sortiere Zentroide von Nord nach Süd
        centroids_and_codes.sort(key=lambda x: -x[0].y)  # Sortiere nach y-Koordinate (absteigend)
        
        # Berechne den vertikalen Abstand zwischen den Labels
        y_range = bounds[3] - bounds[1]
        
        # Berechne den vertikalen Abstand zwischen den Labels
        label_spacing = y_range / (len(centroids_and_codes) + 1)
        
        # Füge Labels für jede Region hinzu, sortiert von Nord nach Süd
        for i, (centroid, code, color) in enumerate(centroids_and_codes):
            # Berechne die y-Position für das Label
            text_y = bounds[3] - (i + 1) * label_spacing
            
            # Setze den Text für das Label
            code_text = code
            is_home = False
            if home_code and home_code == str(code).strip():
                is_home = True
            
            # Zeichne eine dickere schwarze Linie vom Zentroid zum Label
            ax.plot([centroid.x, text_x - 0.2], [centroid.y, text_y], 
                   color='black', linewidth=1.0, zorder=2)
            
            # Wenn es das Home-Kennzeichen ist, zeichne einen auffälligen Marker
            if is_home:
                # Zeichne einen roten Kreis um den Zentroid
                ax.scatter(centroid.x, centroid.y, s=120, color='red', marker='o', edgecolors='black', linewidths=1.5, zorder=10)
            
            # Zeichne zuerst den farbigen Punkt (außerhalb des Labels)
            circle_x = text_x - 0.05
            ax.scatter(circle_x, text_y, s=100, color=color, alpha=0.9, 
                      edgecolor='black', linewidth=0.5, zorder=10)
            
            # Füge den Text hinzu - Code und Name (falls vorhanden)
            region_name = code_to_name.get(code, '')
            region_name = normalize_text(region_name)
            
            # Hauptkennzeichen und Regionsname
            if region_name:
                main_label = f"{code_text} - {region_name}"
            else:
                main_label = code_text
                
            # Weitere Kennzeichen mit Zeilenumbruch bei Bedarf
            other_codes = code_to_other_codes.get(code, [])
            if other_codes:
                # Gruppiere die Codes in Zeilen mit maximal 30 Zeichen
                grouped_codes = []
                current_line = []
                current_length = 0
                
                for c in other_codes:
                    # Prüfe, ob das nächste Kennzeichen in die aktuelle Zeile passt
                    if current_length + len(c) + 2 > 30:  # +2 für Komma und Leerzeichen
                        grouped_codes.append(', '.join(current_line))
                        current_line = [c]
                        current_length = len(c)
                    else:
                        current_line.append(c)
                        current_length += len(c) + 2  # Komma und Leerzeichen
                
                # Füge die letzte Zeile hinzu
                if current_line:
                    grouped_codes.append(', '.join(current_line))
                
                # Erstelle den Text mit Zeilenumbrüchen
                if len(grouped_codes) == 1:
                    other_codes_text = f"Weitere Kennzeichen: {grouped_codes[0]}"
                else:
                    other_codes_text = "Weitere Kennzeichen:\n" + "\n".join(grouped_codes)
            else:
                other_codes_text = ""
            
            # Erstelle einen einzigen Text mit allen Informationen
            label_text = main_label
            if other_codes_text:
                label_text += '\n' + other_codes_text
            
            # Füge dann das Label hinzu (rechts vom Punkt)
            ax.text(text_x, text_y, label_text, 
                   fontsize=6, ha='left', va='center', 
                   multialignment='left',
                   bbox=dict(facecolor='white', alpha=0.9, 
                             boxstyle='round,pad=0.8',
                             edgecolor=color, linewidth=1.0))
        
        # Zeichne das Home-Kennzeichen auf der Karte, falls konfiguriert
        if home_code and home_code in code_to_region:
            home_region = code_to_region[home_code]
            home_region_name = home_region.get('NAME', '')
            if isinstance(home_region_name, pd.Series) and not home_region_name.empty:
                home_region_name = home_region_name.iloc[0]  # Extrahiere den ersten Wert aus der Series
            
            home_geom = gdf[gdf['NAME'] == home_region_name]
            
            if not home_geom.empty:
                # Berechne den Zentroid der Home-Region
                centroid = home_geom.geometry.centroid.iloc[0]
                
                # Zeichne einen auffälligen roten Kreis für die Home-Region
                ax.scatter(centroid.x, centroid.y, s=120, color='red', marker='o', 
                          edgecolors='black', linewidths=1.5, zorder=10)
                
                # Kein Label für die Home-Region hinzufügen, wie gewünscht
        
        # Entferne Achsen und setze Grenzen
        ax.set_axis_off()
        
        # Erweitere die Grenzen, um Platz für die Labels zu schaffen
        ax.set_xlim(bounds[0] - 0.1, bounds[2] + 1.0)
        ax.set_ylim(bounds[1] - 0.1, bounds[3] + 0.1)
        
        # Speichere die Karte
        output_file = os.path.join(OUTPUT_DIR, f"kfz_karte_seite_{page:02d}.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        print(f"Karte gespeichert als: {output_file}")


def generate_license_section(config=None):
    """
    Generiert den LaTeX-Code für den Lizenzabschnitt des Sammelbuchs.
    
    Args:
        config (dict, optional): Konfigurationsdictionary mit Versionsinformation
    
    Returns:
        str: LaTeX-Code für den Lizenzabschnitt
    """
    license_content = ""
    license_content += r"\clearpage" + "\n"
    license_content += r"\section*{Lizenzinformationen}" + "\n"
    license_content += r"\begin{center}" + "\n"
    license_content += r"\begin{minipage}{0.8\textwidth}" + "\n"
    license_content += r"\vspace{1cm}" + "\n"
    
    license_content += r"\textbf{1. KfzKennzeichen-Repository}\\" + "\n"
    license_content += r"Quelle: \url{https://github.com/Octoate/KfzKennzeichen/}\\" + "\n"
    license_content += r"Lizenz: MIT Lizenz\\" + "\n"
    license_content += r"Copyright \copyright{} 2014 Tim Riemann\\[0.5cm]" + "\n"
    
    license_content += r"\textbf{2. Geodaten zu Kfz-Kennzeichen}\\" + "\n"
    license_content += r"Quelle: \url{https://mis.bkg.bund.de/trefferanzeige?docuuid=D7BCF56C-ECDF-4672-9C19-8C668C67E378}\\" + "\n"
    license_content += r"Lizenz: Datenlizenz Deutschland Namensnennung 2.0 (\url{https://www.govdata.de/dl-de/by-2-0})\\" + "\n"
    license_content += r"Herausgeber: Bundesamt für Kartographie und Geodäsie\\[0.5cm]" + "\n"
    
    # Füge die Versionsinformation hinzu
    version_text = "Version 1.1.0 Aalen Ostalbkreis"
    if config and "version" in config:
        version_text = config["version"]
    
    license_content += r"Mein großes Kennzeichen Buch\\" + "\n"
    license_content += f"\\textbf{{{version_text}}}\\\\" + "\n"
    license_content += r"CC-BY-NC \url{https://creativecommons.org/licenses/by-nc/4.0/deed.de}\\Lukas Ruge" + str(2025) + "\\" + "\n"
    license_content += r"\vspace{1cm}" + "\n"
    license_content += r"\end{minipage}" + "\n"
    license_content += r"\end{center}" + "\n"
    
    return license_content


def generate_word_puzzles(regular_codes, code_to_name):
    """
    Generiert Worträtsel mit KFZ-Kennzeichen und gibt sowohl den LaTeX-Code als auch die Lösungstexte zurück.
    
    Args:
        regular_codes (list): Liste mit regulären KFZ-Kennzeichen
        code_to_name (dict): Dictionary mit Zuordnung von Kennzeichen zu Regionsnamen
    
    Returns:
        tuple: (puzzle_content, solution_text) - LaTeX-Code für die Rätsel und Text für die Lösungen
    """
    import random
    
    # Generiere KFZ-Kennzeichen-Rätsel
    try:
        import kfz_puzzle_generator
        puzzles = kfz_puzzle_generator.generiere_raetsel(regular_codes, code_to_name)
        print(f"Rätsel erfolgreich generiert: {len(puzzles)} Rätsel erstellt.")
    except Exception as e:
        print(f"Fehler beim Generieren der Rätsel: {e}")
        puzzles = []
        return "", ""
    
    # Filtere Rätsel ohne UE, OU, AE, SS und mit max. 12 Zeichen
    filtered_puzzles = [p for p in puzzles if not any(combo in p['wort'] for combo in ['UE', 'OU', 'AE', 'SS']) and len(p['wort']) <= 12]
    
    # Wähle 3 zufällige Rätsel aus
    if len(filtered_puzzles) > 3:
        selected_puzzles = random.sample(filtered_puzzles, 3)
    else:
        selected_puzzles = filtered_puzzles
        
    if not selected_puzzles:
        return "", ""
        
    puzzle_content = ""
    solution_text = ""
    
    # Gruppiere die Rätsel in einer Gruppe
    puzzle_groups = [selected_puzzles]
    
    # Erstelle die Rätselseiten
    for page_num, page_puzzles in enumerate(puzzle_groups):
        if page_num > 0:
            puzzle_content += r"\clearpage" + "\n"
        
        puzzle_content += r"\begin{center}" + "\n"
        puzzle_content += r"\textbf{Welches Wort wird gesucht?}" + "\n"
        puzzle_content += r"\end{center}" + "\n"
        
        # Erstelle die Rätsel auf dieser Seite
        for i, puzzle in enumerate(page_puzzles):
            word = puzzle['wort']
            solution = puzzle['loesung']
            
            puzzle_content += r"\begin{tcolorbox}[colback=yellow!10!white,colframe=yellow!50!black,title=Rätsel " + str(page_num * 3 + i + 1) + "]" + "\n"
            
            # Zeige die Regionen an
            puzzle_content += r"Finde das Wort aus diesen Orten:\\" + "\n"
            puzzle_content += r"\begin{itemize}[leftmargin=*]" + "\n"
            for region in solution:
                puzzle_content += r"\item " + region['name'] + "\n"
            puzzle_content += r"\end{itemize}" + "\n"
            
            # Erstelle die Unterstriche für die Buchstaben
            puzzle_content += r"\vspace{0.5cm}" + "\n"
            puzzle_content += r"\begin{center}" + "\n"
            for _ in word:
                puzzle_content += r"\rule{1cm}{0.4pt}\hspace{0.2cm}"
            puzzle_content += "\n"
            puzzle_content += r"\end{center}" + "\n"
            
            puzzle_content += r"\end{tcolorbox}" + "\n"
            puzzle_content += r"\vspace{0.5cm}" + "\n"
    
    # Erstelle die Lösungstexte
    for page_num, page_puzzles in enumerate(puzzle_groups):
        if page_num > 0:
            solution_text += r"\vspace{1cm}" + "\n"
        
        solution_text += r"Lösungen für Rätsel " + str(page_num * 3 + 1) + " - " + str(page_num * 3 + len(page_puzzles)) + r"\\" + "\n"
        
        for i, puzzle in enumerate(page_puzzles):
            word = puzzle['wort']
            solution = puzzle['loesung']
            
            solution_text += r"Rätsel " + str(page_num * 3 + i + 1) + ": " + word + r"\\" + "\n"
            
            # Zeige die Lösung mit den Codes
            code_sequence = " + ".join([region['code'] for region in solution])
            solution_text += code_sequence + "\\" + "\n"
    
    return puzzle_content, solution_text

def generate_matching_puzzle(regular_codes, code_to_name, config=None):
    """
    Generiert ein Verbindungsrätsel mit KFZ-Kennzeichen und gibt sowohl den LaTeX-Code als auch die Lösungstexte zurück.
    
    Args:
        regular_codes (list): Liste mit regulären KFZ-Kennzeichen
        code_to_name (dict): Dictionary mit Zuordnung von Kennzeichen zu Regionsnamen
        config (dict, optional): Konfigurationsdictionary
    
    Returns:
        tuple: (puzzle_content, solution_text) - LaTeX-Code für das Verbindungsrätsel und Text für die Lösung
    """
    import random
    puzzle_content = ""
    solution_text = ""
    
    # Wähle 7 zufällige Regionen aus, wobei die Home-Region (falls vorhanden) immer dabei ist
    regions_to_match = []
    home_code = config.get('home', '') if config else ''
    
    # Füge die Home-Region hinzu, falls konfiguriert
    if home_code and home_code in regular_codes and home_code in code_to_name:
        regions_to_match.append((home_code, code_to_name[home_code]))
    
    # Wähle zufällige andere Regionen
    available_codes = [code for code in regular_codes if code != home_code and code in code_to_name]
    num_additional_regions = 7 - len(regions_to_match)
    if num_additional_regions > 0 and len(available_codes) >= num_additional_regions:
        selected_codes = random.sample(available_codes, num_additional_regions)
        for code in selected_codes:
            regions_to_match.append((code, code_to_name[code]))
    
    # Erstelle das Verbindungsrätsel
    if len(regions_to_match) == 7:
        puzzle_content += r"\subsection*{Verbindungsrätsel}" + "\n"
        
        puzzle_content += r"\begin{center}" + "\n"
        puzzle_content += r"\textbf{Verbinde die Orte mit ihren Kennzeichen}" + "\n"
        puzzle_content += r"\end{center}" + "\n"
        
        # Erstelle eine Kopie der Regionen und mische die Kennzeichen
        region_names = [region[1] for region in regions_to_match]
        codes = [region[0] for region in regions_to_match]
        random.shuffle(codes)
        
        # Erstelle ein dynamisches Verbindungsrätsel mit TikZ
        puzzle_content += r"\vspace{1cm}" + "\n"
        puzzle_content += r"\begin{center}" + "\n"
        
        # Beginne das TikZ-Bild mit Definitionen für die Stile
        puzzle_content += r"\begin{tikzpicture}[" + "\n"
        puzzle_content += r"    region/.style={draw=blue!70, fill=blue!10, rounded corners, text width=5.5cm, align=center, inner sep=6pt}," + "\n"
        puzzle_content += r"    code/.style={draw=black, fill=yellow!20, circle, text width=1.5cm, align=center, inner sep=3pt, font=\bfseries}" + "\n"
        puzzle_content += r"]" + "\n"
        
        # Setze die Regionen auf der linken Seite mit leicht variierenden X-Positionen
        # Mehr nach links gerückt (von -4 auf -5)
        for i in range(7):
            # Berechne eine leicht variierende X-Position für dynamischeres Aussehen
            x_offset = -0.5 if i % 2 == 0 else 0.5
            y_pos = -i * 2.2  # Vertikaler Abstand zwischen den Elementen
            puzzle_content += f"\\node[region] (region{i}) at ({x_offset-5}, {y_pos}) {{{region_names[i]}}};" + "\n"
        
        # Setze die Kennzeichen auf der rechten Seite mit leicht variierenden X-Positionen
        # Mehr nach rechts gerückt (von +4 auf +5)
        for i in range(7):
            # Berechne eine leicht variierende X-Position für dynamischeres Aussehen
            x_offset = 0.5 if i % 2 == 0 else -0.5
            y_pos = -i * 2.2  # Gleicher vertikaler Abstand wie bei den Regionen
            puzzle_content += f"\\node[code] (code{i}) at ({x_offset+5}, {y_pos}) {{\\textbf{{{codes[i]}}}}};" + "\n"
        
        puzzle_content += r"\end{tikzpicture}" + "\n"
        puzzle_content += r"\end{center}" + "\n"
        puzzle_content += r"\vspace{1cm}" + "\n"
        
        # Erstelle den Lösungstext
        solution_text += r"Lösung zum Verbindungsrätsel\\" + "\n"
        solution_text += r"\begin{center}" + "\n"
        solution_text += r"\begin{tabular}{ll}" + "\n"
        
        # Füge die Regionen und ihre korrekten Kennzeichen in die Tabelle ein
        for region_code, region_name in regions_to_match:
            solution_text += region_name + r" & " + region_code + r"\\" + "\n"
        
        solution_text += r"\end{tabular}" + "\n"
        solution_text += r"\end{center}" + "\n"
    
    return puzzle_content, solution_text


def generate_letter_finding_puzzle(regular_codes, code_to_name, config=None):
    """
    Generiert ein Buchstabenrätsel, bei dem die Buchstaben des Kennzeichens im Ortsnamen gefunden werden müssen.
    
    Args:
        regular_codes (list): Liste mit regulären KFZ-Kennzeichen
        code_to_name (dict): Dictionary mit Zuordnung von Kennzeichen zu Regionsnamen
        config (dict, optional): Konfigurationsdictionary
    
    Returns:
        tuple: (puzzle_content, solution_text) - LaTeX-Code für das Rätsel und Text für die Lösung
    """
    puzzle_content = ""
    solution_text = ""
    
    
    # Wähle Kennzeichen aus, die gut für dieses Rätsel geeignet sind
    suitable_codes = []
    for code in regular_codes:
        if code in code_to_name:
            region_name = code_to_name[code].upper()
            # Prüfe, ob alle Buchstaben des Kennzeichens im Regionsnamen vorkommen
            # und ob der Name nicht länger als 16 Zeichen ist
            if all(letter in region_name for letter in code) and len(region_name) <= 16:
                suitable_codes.append((code, region_name))
    
    # Wähle bis zu 7 zufällige Kennzeichen aus
    if len(suitable_codes) > 7:
        suitable_codes = random.sample(suitable_codes, 7)
    
    # Füge Überschrift und Anleitung hinzu
    puzzle_content += r"\section{Rätsel}" + "\n"
    puzzle_content += r"\subsection*{Buchstabenrätsel}" + "\n"
    puzzle_content += r"\begin{tcolorbox}[colback=white, colframe=black, arc=5mm, boxrule=1pt]" + "\n"
    puzzle_content += r"\Large Kennzeichen bestehen aus den Buchstaben, die auch im Ort vorkommen." + "\n"
    puzzle_content += r"\\[0.3cm]" + "\n"
    puzzle_content += r"\Large Finde die Buchstaben aus dem Kennzeichen und umkreise sie." + "\n"
    puzzle_content += r"\end{tcolorbox}" + "\n"
    puzzle_content += r"\vspace{0.8cm}" + "\n"
    
    # Beispiel hinzufügen mit tatsächlich umkreisten Buchstaben
    puzzle_content += r"\Large \textbf{Beispiel:}" + "\n"
    puzzle_content += r"\begin{center}" + "\n"
    puzzle_content += r"\Large BRB - " + "\n"
    
    # Erstelle den Ortsnamen mit umkreisten Buchstaben für das Beispiel
    example_city = "BRANDENBURG"
    example_code = "BRB"
    example_with_circles = ""
    
    # Verfolge, welche Buchstaben bereits umkreist wurden (in der Reihenfolge des Kennzeichens)
    used_positions = []
    
    # Zuerst finde die Positionen der Buchstaben in der richtigen Reihenfolge
    for code_letter in example_code:
        for i, city_letter in enumerate(example_city):
            if city_letter == code_letter and i not in used_positions:
                used_positions.append(i)
                break
    
    # Dann erstelle den String mit den umkreisten Buchstaben und mehr Abstand zwischen den Buchstaben
    for i, letter in enumerate(example_city):
        if i in used_positions:
            # Umkreise den Buchstaben mit TikZ - dickere Linie (line width=1pt)
            example_with_circles += r"\tikz[baseline=(char.base)]{"
            example_with_circles += r"\node[draw=red, circle, line width=1pt, inner sep=1pt] (char) {" + letter + r"};}\hspace{0.2cm}" 
        else:
            example_with_circles += letter + r"\hspace{0.2cm}"
    
    puzzle_content += r"\Large " + example_with_circles + "\n"
    puzzle_content += r"\end{center}" + "\n"
    puzzle_content += r"\vspace{1.5cm}" + "\n"
    
    # Erstelle das Rätsel mit größerer Schrift
    puzzle_content += r"\begin{center}" + "\n"
    puzzle_content += r"\Large" + "\n"
    puzzle_content += r"\begin{tabular}{p{3cm} p{10cm}}" + "\n"
    
    # Füge die Lösungen hinzu
    solution_text += r"Lösung zum Buchstabenrätsel:\\" + "\n"
    solution_text += r"\begin{itemize}" + "\n"
    
    # Füge die Kennzeichen und Regionsnamen hinzu
    for code, region_name in suitable_codes:
        # Füge mehr Abstand zwischen den Buchstaben ein
        spaced_region_name = ""
        for letter in region_name:
            spaced_region_name += letter + r"\hspace{0.2cm}"
        puzzle_content += r"\textbf{" + code + r"} & " + spaced_region_name + r"\\[0.8cm]" + "\n"
        
        # Erstelle die Lösung mit markierten Buchstaben
        solution = ""
        
        # Verfolge, welche Buchstaben bereits markiert wurden (in der Reihenfolge des Kennzeichens)
        used_positions = []
        
        # Zuerst finde die Positionen der Buchstaben in der richtigen Reihenfolge
        for code_letter in code:
            for i, city_letter in enumerate(region_name):
                if city_letter == code_letter and i not in used_positions:
                    used_positions.append(i)
                    break
        
        # Dann erstelle den String mit den markierten Buchstaben
        for i, letter in enumerate(region_name):
            if i in used_positions:
                solution += r"\textbf{" + letter + r"}"
            else:
                solution += letter
        solution_text += r"\item " + code + r" - " + solution + "\n"
    
    puzzle_content += r"\end{tabular}" + "\n"
    puzzle_content += r"\end{center}" + "\n"
    
    solution_text += r"\end{itemize}" + "\n"
    
    return puzzle_content, solution_text


def generate_puzzle_section(regular_codes, code_to_name, config=None):
    """
    Generiert den LaTeX-Code für den Rätsel-Abschnitt des Sammelbuchs.
    
    Args:
        regular_codes (list): Liste mit regulären KFZ-Kennzeichen
        code_to_name (dict): Dictionary mit Zuordnung von Kennzeichen zu Regionsnamen
        config (dict, optional): Konfigurationsdictionary
    
    Returns:
        str: LaTeX-Code für den Rätsel-Abschnitt
    """
    puzzle_content = ""
    puzzle_content += r"\clearpage" + "\n"
    
    # Generiere Buchstabenrätsel
    letter_puzzle_content, letter_solution_text = generate_letter_finding_puzzle(regular_codes, code_to_name, config)
    
    # Generiere Worträtsel
    word_puzzle_content, word_solution_text = generate_word_puzzles(regular_codes, code_to_name)
    
    # Generiere Verbindungsrätsel
    matching_puzzle_content, matching_solution_text = generate_matching_puzzle(regular_codes, code_to_name, config)
    
    # Füge das Buchstabenrätsel hinzu
    puzzle_content += letter_puzzle_content
    puzzle_content += r"\clearpage" + "\n"
    puzzle_content += word_puzzle_content
    
    # Füge das Verbindungsrätsel hinzu
    puzzle_content += r"\clearpage" + "\n"
    puzzle_content += matching_puzzle_content
    
    # Füge die Lösungsseite hinzu
    puzzle_content += r"\clearpage" + "\n"
    puzzle_content += r"\section{Lösungen}" + "\n"
    
    # Normaler Text für die Seitenzahl
    puzzle_content += r"\begin{center}" + "\n"
    puzzle_content += r"Die Lösungen stehen auf dem Kopf, damit du nicht aus Versehen spickst." + "\n"
    puzzle_content += r"\end{center}" + "\n"
    
    # Beginne den umgedrehten Bereich für die Lösungen
    puzzle_content += r"\begin{center}" + "\n"
    puzzle_content += r"\rotatebox[origin=c]{180}{" + "\n"
    puzzle_content += r"\begin{minipage}{0.9\textwidth}" + "\n"
    
    # Füge die Lösungen für das Buchstabenrätsel hinzu
    puzzle_content += letter_solution_text + "\n"
    
    # Füge eine Trennlinie ein
    puzzle_content += r"\vspace{1cm}" + "\n"
    puzzle_content += r"\hrulefill" + "\n"
    puzzle_content += r"\vspace{1cm}" + "\n"
    
    # Füge die Lösungen für die Worträtsel hinzu
    puzzle_content += word_solution_text + "\n"
    
    # Füge eine Trennlinie ein
    puzzle_content += r"\vspace{1cm}" + "\n"
    puzzle_content += r"\hrulefill" + "\n"
    puzzle_content += r"\vspace{1cm}" + "\n"
    
    # Füge die Lösungen für das Verbindungsrätsel hinzu
    puzzle_content += matching_solution_text + "\n"
    
    # Ende des umgedrehten Bereichs
    puzzle_content += r"\end{minipage}" + "\n"
    puzzle_content += r"}" + "\n"
    puzzle_content += r"\end{center}" + "\n"
    
    return puzzle_content

def generate_latex_template(regular_codes, rare_codes, code_to_name, code_to_state, code_to_other_codes, gdf, code_to_region, code_to_name_multi=None, config=None, output_file="kfz_sammelbuch.tex"):
    """
    Generiert eine LaTeX-Vorlage für das Sammelbuch mit Kennzeichen zum Ankreuzen.
    """
    # Berechne die Anzahl der Seiten
    num_regular_pages = (len(regular_codes) + CODES_PER_PAGE - 1) // CODES_PER_PAGE
    num_rare_pages = (len(rare_codes) + RARE_CODES_PER_PAGE - 1) // RARE_CODES_PER_PAGE
    
    # Berechne die mittlere Seite für die Übersichtskarte
    middle_page = num_regular_pages // 2
    
    latex_content = r"""\documentclass[a4paper]{article}
% Font setup for XeLaTeX to use Futura
\usepackage{fontspec}
\setmainfont{Futura}
\setsansfont{Futura}
\usepackage[ngerman]{babel}
\usepackage{graphicx}
\usepackage{geometry}
\usepackage{tabularx}
\usepackage{booktabs}
\usepackage{array}
\usepackage{tikz}
\usetikzlibrary{shapes,positioning}
\usepackage{multicol}
\usepackage{enumitem}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage{rotating}
\usepackage{pdflscape}
\usepackage{url}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{tcolorbox}
\tcbuselibrary{skins}

\geometry{a4paper, margin=1.5cm}
\setlength{\columnsep}{1cm}

% Anpassen der Seitenformatierung
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\fancyfoot[C]{\thepage}

\titleformat{\section}{\normalfont\Large\bfseries}{}{0em}{}

% Definition eines Kreises zum Ankreuzen
\newcommand{\checkbox}{\tikz\draw[black, thick] (0,0) circle (0.4em);}

\begin{document}

\tableofcontents
\clearpage
"""
    
    # Füge die Karten und Checklisten ein
    for page in range(1, num_regular_pages + 1):
        
        # Bestimme die Kennzeichen für diese Seite
        start_idx = (page - 1) * CODES_PER_PAGE
        end_idx = min(start_idx + CODES_PER_PAGE, len(regular_codes))
        page_codes = regular_codes[start_idx:end_idx]
        
        # Erstelle eine neue Seite
        latex_content += r"\clearpage" + "\n"
        
        # Erstelle einen Seitentitel mit dem Bereich der Kennzeichen
        first_code = page_codes[0]
        last_code = page_codes[-1]
        latex_content += r"\section{" + first_code + " - " + last_code + "}\n\n"
        
        # Erstelle die Checkliste
        latex_content += r"\begin{multicols}{2}" + "\n"
        # Füge den Hinweistext hinzu
        latex_content += r"\textbf{Kreuze alle Kennzeichen an, die du findest:}\\[0.3cm]" + "\n"
        latex_content += r"\begin{enumerate}[leftmargin=*,label={}]" + "\n"
        
        # Füge die Kennzeichen in die Liste ein
        for code in page_codes:
            region_name = normalize_text(code_to_name.get(code, ''))
            latex_content += r"\item \checkbox~\textbf{" + code + r"} " + region_name + "\n"
        
        latex_content += r"\end{enumerate}" + "\n"
        latex_content += r"\end{multicols}" + "\n\n"
        
        # Füge die Deutschlandkarte unter der Liste ein
        latex_content += r"\begin{center}" + "\n"
        latex_content += r"\includegraphics[width=0.8\textwidth,height=0.5\textheight,keepaspectratio]{" + f"output_maps/kfz_karte_seite_{page:02d}.png" + "}\n"
        latex_content += r"\end{center}" + "\n\n"
        
        # Füge den Informationskasten hinzu, falls vorhanden
        info_box = get_info_box_for_page(page, page_codes, gdf, code_to_region, code_to_name, code_to_state, code_to_other_codes, config, code_to_name_multi)
        if info_box:
            latex_content += info_box + "\n"
    
    # Füge einen Abschnitt für seltene Kennzeichen hinzu
    if rare_codes:
        latex_content += r"\clearpage" + "\n"
        latex_content += r"\section{Seltene Kennzeichen}" + "\n"
        # Setze Spaltenabstand und Ausrichtung für die Mehrspaltigkeit
        latex_content += r"\setlength{\columnsep}{1cm}" + "\n"
        latex_content += r"\setlength{\columnseprule}{0.2pt}" + "\n"
        latex_content += r"\begin{multicols}{3}" + "\n"
        
        # Füge den Hinweistext für seltene Kennzeichen hinzu
        latex_content += r"\textbf{Kreuze alle Kennzeichen an, die du findest:}\\[0.3cm]" + "\n"
        
        # Erstelle die Seiten mit seltenen Kennzeichen (ohne Karten)
        for page in range(1, num_rare_pages + 1):
            # Bestimme die Kennzeichen für diese Seite
            start_idx = (page - 1) * RARE_CODES_PER_PAGE
            end_idx = min(start_idx + RARE_CODES_PER_PAGE, len(rare_codes))
            page_codes = rare_codes[start_idx:end_idx]
            
            # Erstelle eine Liste mit den seltenen Kennzeichen mit verbesserter Formatierung
            latex_content += r"\begin{enumerate}[leftmargin=1.5em,itemindent=0em,labelsep=0.5em,align=left,label={}]" + "\n"
            
            # Füge die Kennzeichen in die Liste ein
            for code in page_codes:
                region_name = normalize_text(code_to_name.get(code, ''))
                # Füge einen Stern hinzu, wenn das Kennzeichen mehrere Regionen hat
                if code in code_to_name_multi and code_to_name_multi[code]:
                    latex_content += r"\item \checkbox~\textbf{" + code + r"}* " + region_name + "\n"
                else:
                    latex_content += r"\item \checkbox~\textbf{" + code + r"} " + region_name + "\n"
            
            latex_content += r"\end{enumerate}" + "\n"
            
            # Neue Seite für die nächsten seltenen Kennzeichen, außer bei der letzten Seite
            if page < num_rare_pages:
                latex_content += r"\columnbreak" + "\n"
        
        latex_content += r"\end{multicols}" + "\n"
        
        # Füge einen Hinweiskasten für seltene Kennzeichen hinzu
        info_box = create_yellow_box(
            "Viele der seltenen Kennzeichen waren früher die üblichen Kennzeichen. "
            "Irgendwann wurden sie abgeschafft, aber seit einigen Jahren darf man sie wieder benutzen. "
            "Dabei haben sich manchmal die Gebiete geändert. Das Kennzeichen ROL, für \\textbf{Rottenburg an der Laaber}, "
            "kann daher zum Beispiel an Autos aus Kelheim und aus Landshut stehen. "
            "Kennzeichen mit einem * können zu mehreren Regionen gehören."
        )
        latex_content += info_box + "\n"
    
    # Füge den Rätsel-Abschnitt hinzu
    latex_content += generate_puzzle_section(regular_codes, code_to_name, config)
    
    # Füge die Lizenzinformationen hinzu
    latex_content += generate_license_section(config)
    
    latex_content += r"\end{document}" + "\n"
    # Speichere die LaTeX-Vorlage in einer Datei
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(latex_content)
    
    print(f"LaTeX-Vorlage gespeichert als: {output_file}")
    return output_file


def compile_latex_document(tex_file):
    """
    Kompiliert ein LaTeX-Dokument zu PDF mit XeLaTeX für Futura-Schriftart.
    """
    # Prüfe, ob xelatex installiert ist
    if shutil.which("xelatex") is None:
        print("WARNUNG: xelatex ist nicht installiert oder nicht im PATH. Das PDF kann nicht erstellt werden.")
        return False
    
    try:
        # Führe xelatex zweimal aus, um Inhaltsverzeichnis korrekt zu erstellen
        for _ in range(2):
            # Verwende text=False, um die Ausgabe als Binärdaten zu behandeln
            process = subprocess.run(
                ["xelatex", "-interaction=nonstopmode", tex_file],
                capture_output=True,
                text=False,  # Wichtig: Behandle die Ausgabe als Binärdaten
                check=False
            )
            
            if process.returncode != 0:
                print("Fehler beim Kompilieren des LaTeX-Dokuments")
                return False
        
        # Prüfe, ob die PDF-Datei erstellt wurde
        pdf_file = tex_file.replace(".tex", ".pdf")
        if os.path.exists(pdf_file):
            print(f"PDF erfolgreich erstellt: {pdf_file}")
            return pdf_file
        else:
            print("PDF konnte nicht erstellt werden.")
            return False
    
    except Exception as e:
        print(f"Fehler beim Kompilieren des LaTeX-Dokuments: {str(e)}")
        return False


def find_multi_region_codes(code_to_name):
    """
    Findet alle Kennzeichen, die in mehreren Regionen vorkommen.
    """
    multi_region_codes = {}
    
    for code, name in code_to_name.items():
        if ' oder ' in name:
            regions = name.split(' oder ')
            if len(regions) > 1:
                multi_region_codes[code] = regions
    
    return multi_region_codes


def main(home_code=None, output_suffix="", debug_multi_regions=False):
    """
    Hauptfunktion zum Erstellen des Sammelbuchs und der Karten.
    """
    print("KFZ-Kennzeichen Kartengenerator für Kinderbuch")
    print("=============================================\n")
    
    # Konfiguration laden
    # Lade die Konfiguration
    config = load_config()
    
    # Überschreibe die Home-Einstellung, wenn ein Kennzeichen übergeben wurde
    if home_code:
        config['home'] = str(home_code).strip()
        print(f"Home-Kennzeichen überschrieben: {config['home']}")
    
    # Lade das Shapefile
    gdf = load_shapefile(SHAPEFILE_PATH)
    
    # Debug: Zeige die Spalten und ein Beispiel an
    print("\nSpalten im GeoDataFrame:", list(gdf.columns))
    print("\nBeispiel für die erste Zeile:")
    for col, val in gdf.iloc[0].items():
        print(f"  {col}: {val}")
    print("\n")
    
    # Extrahiere die KFZ-Kennzeichen und Zuordnungen
    regular_codes, rare_codes, code_to_region, code_to_name, code_to_state, code_to_other_codes, code_to_name_multi = extract_kfz_codes(gdf)
    
    # Debug: Finde und zeige Kennzeichen mit mehreren Regionen
    if debug_multi_regions or True:  # Immer aktiviert für Debugging
        multi_region_codes = find_multi_region_codes(code_to_name)
        print(f"\nGefundene Kennzeichen mit mehreren Regionen: {len(multi_region_codes)}")
        for code, regions in multi_region_codes.items():
            print(f"  - {code}: {', '.join(regions)}")
        print()
    
    # Sortiere die Kennzeichen alphabetisch
    regular_codes.sort()
    rare_codes.sort()
    
    # Erstelle die Karten für die regulären Kennzeichen
    num_regular_pages = create_map_pages(gdf, regular_codes, code_to_region, code_to_name, code_to_state, code_to_other_codes, config)
    
    # Erstelle die LaTeX-Vorlage
    home_code = config.get('home', '')
    tex_file_name = f"kfz_sammelbuch_{home_code}{output_suffix}.tex"
    tex_file = generate_latex_template(regular_codes, rare_codes, code_to_name, code_to_state, code_to_other_codes, gdf, code_to_region, code_to_name_multi, config, output_file=tex_file_name)
    
    # Kompiliere das LaTeX-Dokument zu PDF
    pdf_file = compile_latex_document(tex_file)
    
    # Bearbeite das PDF (füge Titelbild hinzu, etc.)
    if pdf_file and os.path.exists(pdf_file):
        home_suffix = f"_{config['home']}" if config.get('home') else ""
        final_pdf = f"kfz_sammelbuch{home_suffix}{output_suffix}_final.pdf"
        process_pdf(pdf_file, final_pdf, config)
        print(f"\nFertiges Buch erstellt: {final_pdf}")
    else:
        print("\nFehler: LaTeX-Kompilierung fehlgeschlagen oder PDF-Datei wurde nicht gefunden.")



if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="KFZ-Kennzeichen Kartengenerator für Kinderbuch")
    parser.add_argument("--home", type=str, help="Das Kennzeichen, das als Home markiert werden soll")
    parser.add_argument("--suffix", type=str, default="", help="Ein Suffix für die Ausgabedateien")
    
    args = parser.parse_args()
    
    main(home_code=args.home, output_suffix=args.suffix)

