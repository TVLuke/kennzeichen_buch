#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generiert für jedes Kennzeichen in der CSV-Datei ein eigenes Sammelbuch.
Das jeweilige Kennzeichen wird als Home markiert.
"""

import os
import sys
import pandas as pd
import subprocess
import time
import concurrent.futures
from tqdm import tqdm
import geopandas as gpd
from create_title_image import load_shapefile, extract_codes_from_shapefile, create_title_image

# Pfade zu den Dateien
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kfz-kennz-d.csv")
SHAPEFILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kfz250.utm32s.shape/kfz250/KFZ250.shp")
OUTPUT_MAPS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_maps")

def load_csv_data(csv_path):
    """
    Lädt die CSV-Datei mit den KFZ-Kennzeichen und gibt ein Dictionary zurück,
    das Kennzeichen auf Regionsnamen abbildet.
    
    Returns:
        dict: Dictionary mit Kennzeichen als Schlüssel und Regionsnamen als Werte
    """
    try:
        # Versuche, die CSV-Datei zu laden - die Datei verwendet Kommas als Trennzeichen und hat eine Kopfzeile
        df = pd.read_csv(csv_path, encoding='utf-8', sep=',', header=0)
        
        # Überprüfe, ob die Datei die erwartete Struktur hat
        if df.shape[1] < 2:
            print(f"Fehler: Die CSV-Datei {csv_path} hat nicht das erwartete Format.")
            return None
        
        # Extrahiere die Kennzeichen und Regionsnamen
        # Annahme: Erste Spalte enthält Kennzeichen, zweite Spalte enthält Regionsnamen
        kennzeichen_spalte = df.columns[0]
        region_spalte = df.columns[1]
        
        # Erstelle ein Dictionary, das Kennzeichen auf Regionsnamen abbildet
        code_to_region = {}
        for _, row in df.iterrows():
            kennzeichen = row[kennzeichen_spalte]
            region = row[region_spalte]
            if pd.notna(kennzeichen) and pd.notna(region):
                code_to_region[kennzeichen] = region
        
        print(f"CSV-Datei erfolgreich geladen. {len(code_to_region)} Kennzeichen mit Regionsnamen gefunden.")
        return code_to_region
    
    except Exception as e:
        print(f"Fehler beim Laden der CSV-Datei {csv_path}: {e}")
        return None

def create_title_image_for_code(code):
    """
    Erstellt ein Titelbild für ein bestimmtes Kennzeichen.
    
    Args:
        code (str): Das Kennzeichen, für das ein Titelbild erstellt werden soll.
    
    Returns:
        str: Pfad zum erstellten Titelbild oder None bei Fehler.
    """
    try:
        # Stelle sicher, dass das Ausgabeverzeichnis existiert
        os.makedirs(OUTPUT_MAPS_DIR, exist_ok=True)
        
        # Lade das Shapefile
        gdf = load_shapefile(SHAPEFILE_PATH)
        if gdf is None:
            print(f"Fehler beim Laden des Shapefiles für Titelbild {code}.")
            return None
        
        # Extrahiere die Kennzeichen aus dem Shapefile
        all_codes, code_to_region, code_to_geometry, region_to_codes = extract_codes_from_shapefile(gdf)
        
        # Prüfe, ob das angegebene Kennzeichen gültig ist
        if code not in code_to_region:
            print(f"Warnung: Kennzeichen '{code}' nicht gefunden. Erstelle allgemeines Titelbild.")
            return None
        
        # Lade die CSV-Daten, um den Namen aus der CSV zu bevorzugen
        csv_data = load_csv_data(CSV_PATH)
        csv_region_name = None
        
        if csv_data and code in csv_data:
            csv_region_name = csv_data[code]
            print(f"Verwende Regionsnamen aus CSV für {code}: {csv_region_name}")
        
        # Erstelle das Titelbild als PDF
        output_path = os.path.join(OUTPUT_MAPS_DIR, f"kfz_titelbild_{code}.pdf")
        title_image_path = create_title_image(gdf, all_codes, code_to_region, code_to_geometry, 
                                             region_to_codes, output_path, code, csv_region_name)
        
        print(f"Titelbild für {code} erfolgreich erstellt: {title_image_path}")
        return title_image_path
    except Exception as e:
        print(f"Fehler beim Erstellen des Titelbildes für {code}: {e}")
        return None

def generate_book_for_code(code, max_retries=3):
    """
    Generiert ein Sammelbuch für ein bestimmtes Kennzeichen.
    
    Args:
        code (str): Das Kennzeichen, das als Home markiert werden soll.
        max_retries (int): Maximale Anzahl von Wiederholungsversuchen bei Fehlern.
    
    Returns:
        bool: True bei Erfolg, False bei Fehler.
    """
    # Erstelle zuerst das Titelbild für dieses Kennzeichen
    print(f"Erstelle Titelbild für Kennzeichen {code}...")
    create_title_image_for_code(code)
    
    # Führe das Hauptskript mit dem Kennzeichen als Home aus
    # Wir lassen das Suffix leer, da das Hauptskript bereits das Kennzeichen im Dateinamen verwendet
    cmd = [
        sys.executable,
        "generate_kfz_maps_neu.py",
        "--home", code,
        "--suffix", ""
    ]
    
    print(f"Starte Generierung für Kennzeichen {code}...")
    
    for attempt in range(max_retries):
        try:
            # Führe das Skript ohne Timeout aus
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"Generierung für {code} erfolgreich abgeschlossen.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Fehler bei der Generierung für {code} (Versuch {attempt+1}/{max_retries}):")
            print(f"Fehlercode: {e.returncode}")
            print(f"Ausgabe: {e.output}")
            print(f"Fehler: {e.stderr}")
        except Exception as e:
            print(f"Unerwarteter Fehler bei der Generierung für {code}: {str(e)}")
        
        if attempt < max_retries - 1:
            print(f"Versuche es erneut in 2 Sekunden...")
            time.sleep(2)
        else:
            print(f"Maximale Anzahl von Versuchen erreicht. Überspringe {code}.")
            return False

def main():
    """
    Hauptfunktion zum Ausführen des Skripts.
    """
    print("KFZ-Kennzeichen Sammelbuch Generator für alle Kennzeichen")
    print("=======================================================")
    
    # Lade die Kennzeichen aus der CSV-Datei
    codes = load_csv_data(CSV_PATH)
    if not codes:
        print("Fehler: Keine Kennzeichen gefunden.")
        return
    
    # Erstelle den Ausgabeordner für alle Bücher
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "all_books")
    os.makedirs(output_dir, exist_ok=True)
    
    # Frage den Benutzer, ob alle Bücher generiert werden sollen
    print(f"\nEs wurden {len(codes)} Kennzeichen gefunden.")
    user_input = input(f"Möchten Sie für alle {len(codes)} Kennzeichen ein Buch generieren? (j/n): ")
    
    if user_input.lower() not in ['j', 'ja', 'y', 'yes']:
        # Frage nach einem bestimmten Kennzeichen oder einer Teilmenge
        user_input = input("Geben Sie ein einzelnes Kennzeichen oder eine Anzahl ein (z.B. '10' für die ersten 10): ")
        
        if user_input.isdigit():
            # Begrenze die Anzahl der zu generierenden Bücher
            num_codes = min(int(user_input), len(codes))
            codes = codes[:num_codes]
            print(f"Generiere Bücher für die ersten {num_codes} Kennzeichen.")
        else:
            # Suche nach dem angegebenen Kennzeichen
            user_code = user_input.upper()
            if user_code in codes:
                codes = [user_code]
                print(f"Generiere Buch nur für das Kennzeichen {user_code}.")
            else:
                print(f"Kennzeichen {user_code} nicht gefunden. Breche ab.")
                return
    
    # Generiere die Bücher
    print(f"\nGeneriere {len(codes)} Bücher...")
    
    # Verwende einen Fortschrittsbalken
    with tqdm(total=len(codes), desc="Fortschritt") as pbar:
        # Sequentielle Verarbeitung (sicherer, aber langsamer)
        for code in codes:
            success = generate_book_for_code(code)
            if success:
                # Verschiebe die generierten Dateien in den Ausgabeordner
                # Das Format sollte jetzt kfz_sammelbuch_CODE_final.pdf sein
                pdf_file = f"kfz_sammelbuch_{code}_final.pdf"
                if os.path.exists(pdf_file):
                    target_path = os.path.join(output_dir, pdf_file)
                    os.rename(pdf_file, target_path)
                    print(f"PDF {pdf_file} in {output_dir} verschoben.")
                else:
                    # Suche nach Dateien mit dem Kennzeichen im Namen
                    found = False
                    for file in os.listdir():
                        if "_final.pdf" in file and code in file:
                            target_path = os.path.join(output_dir, file)
                            os.rename(file, target_path)
                            print(f"PDF {file} in {output_dir} verschoben.")
                            found = True
                            break
                    
                    if not found:
                        print(f"Warnung: Keine PDF-Datei für Kennzeichen {code} gefunden.")
                        
            pbar.update(1)
    
    # Zähle die erfolgreich generierten Bücher
    generated_files = [f for f in os.listdir(output_dir) if f.endswith("_final.pdf")]
    
    print("\n=======================================================")
    print(f"Fertig! {len(generated_files)} von {len(codes)} Büchern wurden erfolgreich generiert.")
    print(f"Die PDFs befinden sich im Verzeichnis: {output_dir}")
    print("=======================================================")

if __name__ == "__main__":
    main()
