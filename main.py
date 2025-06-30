#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hauptskript für die Erstellung des KFZ-Kennzeichen Sammelbuchs
Führt zuerst create_title_image.py und dann generate_kfz_maps_neu.py aus
"""

import os
import sys
import subprocess
import importlib.util

def run_script(script_path):
    """
    Führt ein Python-Skript aus, entweder durch direkten Import oder als Subprocess
    """
    print(f"\n{'=' * 50}")
    print(f"Führe {script_path} aus...")
    print(f"{'=' * 50}\n")
    
    try:
        # Versuche, das Skript als Modul zu importieren und auszuführen
        spec = importlib.util.spec_from_file_location("module.name", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Wenn das Skript eine main-Funktion hat, führe diese aus
        if hasattr(module, 'main'):
            module.main()
            
        print(f"\n{script_path} erfolgreich ausgeführt.")
        return True
    except Exception as e:
        print(f"Fehler beim Ausführen von {script_path} als Modul: {e}")
        print("Versuche, das Skript als Subprocess auszuführen...")
        
        try:
            # Führe das Skript als Subprocess aus
            result = subprocess.run([sys.executable, script_path], check=True)
            print(f"\n{script_path} erfolgreich als Subprocess ausgeführt.")
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            print(f"Fehler beim Ausführen von {script_path} als Subprocess: {e}")
            return False

def main(home_code=None, output_suffix=""):
    """
    Hauptfunktion, die die Skripte in der richtigen Reihenfolge ausführt
    
    Args:
        home_code (str, optional): Das Kennzeichen, das als Home markiert werden soll.
        output_suffix (str, optional): Ein Suffix für die Ausgabedateien.
    """
    print("KFZ-Kennzeichen Sammelbuch Generator")
    print("===================================")
    
    # Kommandozeilenparameter für generate_kfz_maps_neu.py
    cmd_args = []
    
    # Aktuelles Verzeichnis
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Pfade zu den Skripten
    title_image_script = os.path.join(current_dir, "create_title_image.py")
    generate_maps_script = os.path.join(current_dir, "generate_kfz_maps_neu.py")
    
    # Prüfe, ob die Skripte existieren
    if not os.path.exists(title_image_script):
        print(f"FEHLER: {title_image_script} nicht gefunden!")
        return False
    
    if not os.path.exists(generate_maps_script):
        print(f"FEHLER: {generate_maps_script} nicht gefunden!")
        return False
    
    # Führe die Skripte nacheinander aus
    title_success = run_script(title_image_script)
    if not title_success:
        print("FEHLER: Erstellung des Titelbilds fehlgeschlagen!")
        return False
    
    # Bereite Kommandozeilenparameter vor
    if home_code:
        cmd_args.extend(["--home", home_code])
    if output_suffix:
        cmd_args.extend(["--suffix", output_suffix])
    
    # Führe das Skript mit den Parametern aus
    if cmd_args:
        try:
            cmd = [sys.executable, generate_maps_script] + cmd_args
            result = subprocess.run(cmd, check=True)
            maps_success = result.returncode == 0
        except subprocess.CalledProcessError as e:
            print(f"Fehler beim Ausführen von {generate_maps_script} mit Parametern: {e}")
            maps_success = False
    else:
        maps_success = run_script(generate_maps_script)
    
    if not maps_success:
        print("FEHLER: Erstellung des Sammelbuchs fehlgeschlagen!")
        return False
    
    print("\n===================================")
    print("Sammelbuch erfolgreich erstellt!")
    home_suffix = f"_{home_code}" if home_code else ""
    pdf_name = f"kfz_sammelbuch{home_suffix}{output_suffix}_final.pdf"
    print(f"Das fertige PDF finden Sie unter: {pdf_name}")
    print("===================================")
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="KFZ-Kennzeichen Sammelbuch Generator")
    parser.add_argument("--home", type=str, help="Das Kennzeichen, das als Home markiert werden soll")
    parser.add_argument("--suffix", type=str, default="", help="Ein Suffix für die Ausgabedateien")
    
    args = parser.parse_args()
    
    success = main(home_code=args.home, output_suffix=args.suffix)
    sys.exit(0 if success else 1)
