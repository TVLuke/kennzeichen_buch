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

# Import der Home-Printer-Version der LaTeX-Generierung
from generate_home_print_latex_template import generate_latex_template
from normalizer import normalize_text
from map_creator import create_map_pages_for_home_printer, create_map_pages_for_professional_print


# Funktion zum Bearbeiten des PDFs
def process_pdf(pdf_path, output_path="kfz_sammelbuch_final.pdf", config=None, home_printer=False):
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
        if not home_printer:
            print("Füge zwei leere Seiten nach der Titelseite hinzu")
            for _ in range(2):
                writer.add_blank_page(width=595, height=842)  # A4 Größe in Punkten
        else:
            print("Füge eine leere Seite nach der Titelseite hinzu")
            for _ in range(1):
                writer.add_blank_page(width=595, height=842)  # A4 Größe in Punkten
    else:
        print(f"WARNUNG: Titelbild nicht gefunden: {title_image_path}")
    
    # Füge das ursprüngliche PDF hinzu
    reader = PdfReader(pdf_path)
    for page in reader.pages:
        writer.add_page(page)
    
    if not home_printer:
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
CSV_PATH = "kfz-kennz-d.csv"
CSV_PATH_OCTOATE = "kfzkennzeichen-deutschland.csv"
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




def load_octoate_csv_data(csv_path):
    """
    Lädt die Octoate CSV-Datei mit den KFZ-Kennzeichen und gibt ein Dictionary zurück:
    Kennzeichen zu Regionsnamen
    
    Die Octoate CSV hat ein einfacheres Format mit nur zwei Spalten: Kennzeichen und Regionsname
    """
    print(f"Lade Octoate CSV-Datei: {csv_path}")
    try:
        # Lese die CSV-Datei
        df = pd.read_csv(csv_path, encoding='utf-8', header=None)
        
        # Überprüfe die Spalten
        if len(df.columns) < 2:
            print("Warnung: Octoate CSV-Datei hat weniger als 2 Spalten. Format könnte falsch sein.")
            return {}
        
        # Erstelle Dictionary mit Kennzeichen als Schlüssel
        code_to_name = {}
        
        # Debug: Zeige die ersten 10 Zeilen der CSV-Datei
        print("DEBUG: Erste 10 Zeilen der Octoate CSV-Datei:")
        for i in range(min(10, len(df))):
            print(f"DEBUG: {df.iloc[i, 0]} -> {df.iloc[i, 1]}")
        
        # Erste Spalte enthält die Kennzeichen, zweite Spalte die Regionsnamen
        for _, row in df.iterrows():
            code = str(row.iloc[0]).strip()
            
            # Normalisiere den Code
            code = normalize_text(code)
            
            # Zweite Spalte enthält den Regionsnamen
            region_name = normalize_text(str(row.iloc[1]))
            
            # Ersetze eckige Klammern durch normale Klammern
            region_name = region_name.replace('[', '(').replace(']', ')')
            
            # Debug: Zeige AIB, wenn es gefunden wird
            if code == 'AIB':
                print(f"DEBUG: AIB gefunden in Octoate CSV mit Namen: {region_name}")
            
            # Speichere in dem Dictionary
            if code:
                code_to_name[code] = region_name
        
        # Debug: Überprüfe, ob AIB im Dictionary ist
        if 'AIB' in code_to_name:
            print(f"DEBUG: AIB ist im Octoate Dictionary mit Namen: {code_to_name['AIB']}")
        else:
            print("DEBUG: AIB ist NICHT im Octoate Dictionary")
        
        print(f"Octoate CSV-Datei erfolgreich geladen. {len(code_to_name)} Kennzeichen gefunden.")
        return code_to_name
    
    except Exception as e:
        print(f"Fehler beim Laden der Octoate CSV-Datei: {e}")
        return {}


def load_csv_data(csv_path):
    """
    Lädt die CSV-Datei mit den KFZ-Kennzeichen und gibt zwei Dictionaries zurück:
    Kennzeichen zu Regionsnamen und Kennzeichen zu Bundesland
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



def extract_kfz_codes(gdf):
    """
    Extrahiert alle KFZ-Kennzeichen aus dem GeoDataFrame und erstellt Zuordnungen.
    Jedes Kennzeichen wird einzeln erfasst mit Verweis auf seine Region.
    Prüft, ob das Kennzeichen in den CSV-Dateien enthalten ist und teilt sie entsprechend auf.
    """
    # Lade die CSV-Dateien mit den offiziellen Kennzeichen und Namen
    csv_code_to_name, csv_code_to_state = load_csv_data(CSV_PATH)
    
    # Lade die Octoate CSV-Datei mit zusätzlichen Kennzeichen
    octoate_code_to_name = load_octoate_csv_data(CSV_PATH_OCTOATE)
    
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
    
    # Für seltene Kennzeichen: Bevorzuge Daten aus der Octoate CSV-Datei, wenn vorhanden
    octoate_replaced_count = 0
    
    for code in rare_codes:
        if code in octoate_code_to_name:
            # Speichere den alten Namen für Debug-Ausgabe
            old_name = code_to_name.get(code, "")
            new_name = octoate_code_to_name[code]
            
            # Debug: Zeige Ersetzungen für bestimmte Codes
            if code == 'AIB':
                print(f"DEBUG: Ersetze AIB: '{old_name}' -> '{new_name}'")
            
            # Ersetze den Namen nur, wenn er sich unterscheidet
            if old_name != new_name:
                code_to_name[code] = new_name
                octoate_replaced_count += 1
                if code == 'AIB':
                    print(f"DEBUG: AIB wurde ersetzt, neuer Name: {code_to_name.get('AIB', 'nicht gefunden')}")
    

    print(f"Für {octoate_replaced_count} seltene Kennzeichen wurden Namen aus der Octoate CSV-Datei bevorzugt")
    
    # Sortiere alphabetisch
    regular_codes.sort()
    rare_codes.sort()
    
    print(f"Insgesamt {len(regular_codes)} reguläre KFZ-Kennzeichen gefunden (in CSV und Shapefile enthalten)")
    print(f"Insgesamt {len(rare_codes)} seltene KFZ-Kennzeichen gefunden ({len(rare_codes) - len(csv_only_codes)} nur im Shapefile, {len(csv_only_codes)} nur in der CSV)")

    
    return regular_codes, rare_codes, code_to_region, code_to_name, code_to_state, code_to_other_codes, code_to_name_multi

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
    home_printer = True
    
    # Überschreibe die Home-Einstellung, wenn ein Kennzeichen übergeben wurde
    if home_code:
        config['home'] = str(home_code).strip()
        print(f"Home-Kennzeichen überschrieben: {config['home']}")
    print(f"Home-Code in main: {config['home']}")

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
    if home_printer:
        create_map_pages_for_home_printer(gdf, regular_codes, code_to_region, code_to_name, code_to_state, code_to_other_codes, config)
    else:
        create_map_pages_for_professional_print(gdf, regular_codes, code_to_region, code_to_name, code_to_state, code_to_other_codes, config)
    
    # Erstelle die LaTeX-Vorlage
    home_code = config.get('home', '')
    if home_printer:
        tex_file_name = f"kfz_sammelbuch_{home_code}{output_suffix}_printerfriendly.tex"
        tex_file = generate_latex_template(regular_codes, rare_codes, code_to_name, code_to_state, code_to_other_codes, gdf, code_to_region, code_to_name_multi, config, output_file=tex_file_name)
    else:
        tex_file_name = f"kfz_sammelbuch_{home_code}{output_suffix}.tex"
        tex_file = generate_latex_template(regular_codes, rare_codes, code_to_name, code_to_state, code_to_other_codes, gdf, code_to_region, code_to_name_multi, config, output_file=tex_file_name)
    
    # Kompiliere das LaTeX-Dokument zu PDF
    pdf_file = compile_latex_document(tex_file)
    
    # Bearbeite das PDF (füge Titelbild hinzu, etc.)
    if pdf_file and os.path.exists(pdf_file):
        home_suffix = f"_{config['home']}" if config.get('home') else ""
        if home_printer:
            final_pdf = f"kfz_sammelbuch{home_suffix}{output_suffix}_printerfriendly_final.pdf"
        else:
            final_pdf = f"kfz_sammelbuch{home_suffix}{output_suffix}_final.pdf"
        process_pdf(pdf_file, final_pdf, config, home_printer)
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

