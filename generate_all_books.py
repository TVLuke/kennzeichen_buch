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

# Pfad zur CSV-Datei
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kfz-kennz-d.csv")

def load_csv_data(csv_path):
    """
    Lädt die CSV-Datei mit den KFZ-Kennzeichen.
    """
    try:
        # Versuche, die CSV-Datei zu laden
        df = pd.read_csv(csv_path, encoding='utf-8', sep=';', header=None)
        
        # Überprüfe, ob die Datei die erwartete Struktur hat
        if df.shape[1] < 2:
            print(f"Fehler: Die CSV-Datei {csv_path} hat nicht das erwartete Format.")
            return None
        
        # Extrahiere die Kennzeichen (erste Spalte)
        codes = df[0].tolist()
        
        print(f"CSV-Datei erfolgreich geladen. {len(codes)} Kennzeichen gefunden.")
        return codes
    
    except Exception as e:
        print(f"Fehler beim Laden der CSV-Datei {csv_path}: {e}")
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
    # Normalisiere das Kennzeichen für den Dateinamen
    suffix = f"_{code}"
    
    # Führe das Hauptskript mit dem Kennzeichen als Home aus
    cmd = [
        sys.executable,
        "generate_kfz_maps_neu.py",
        "--home", code,
        "--suffix", suffix
    ]
    
    for attempt in range(max_retries):
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Fehler bei der Generierung für {code} (Versuch {attempt+1}/{max_retries}):")
            print(f"Fehlercode: {e.returncode}")
            print(f"Ausgabe: {e.output}")
            print(f"Fehler: {e.stderr}")
            
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
                pdf_file = f"kfz_sammelbuch_{code}_final.pdf"
                if os.path.exists(pdf_file):
                    target_path = os.path.join(output_dir, pdf_file)
                    os.rename(pdf_file, target_path)
                else:
                    # Suche nach Dateien, die mit dem Kennzeichen enden
                    for file in os.listdir():
                        if file.endswith(f"_{code}_final.pdf"):
                            target_path = os.path.join(output_dir, file)
                            os.rename(file, target_path)
                            break
            pbar.update(1)
    
    # Zähle die erfolgreich generierten Bücher
    generated_files = [f for f in os.listdir(output_dir) if f.endswith("_final.pdf")]
    
    print("\n=======================================================")
    print(f"Fertig! {len(generated_files)} von {len(codes)} Büchern wurden erfolgreich generiert.")
    print(f"Die PDFs befinden sich im Verzeichnis: {output_dir}")
    print("=======================================================")

if __name__ == "__main__":
    main()
