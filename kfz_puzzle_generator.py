#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os

# Liste von verkehrsbezogenen Nomen für Kinder
VERKEHRS_WOERTER = [
    "AMPEL", "AUTO", "ZEBRASTREIFEN", "STRASSE", "FAHRRAD", "FUSSGAENGER", 
    "KREUZUNG", "AUTOBAHN", "BAHNHOF", "BRUECKE", "TUNNEL", "PARKPLATZ", 
    "TANKSTELLE", "BUSHALTESTELLE", "STRASSENBAHN", "MOTORRAD", "LASTWAGEN", 
    "POLIZEIAUTO", "FEUERWEHR", "KRANKENWAGEN", "VERKEHRSSCHILD", "BAUSTELLE",
    "RADWEG", "FUSSGAENGERZONE", "KREISVERKEHR", "UNTERFUEHRUNG", "UEBERFUEHRUNG",
    "FAHRBAHNMARKIERUNG", "LEITPLANKE", "VERKEHRSINSEL", "STRASSENLATERNE",
    "BLINKLICHT", "NEBELSCHEINWERFER", "AUTOSITZ", "KINDERSITZ", "SICHERHEITSGURT",
    "FAHRRADHELM", "WARNWESTE", "VERKEHRSAMPEL", "STOPPSCHILD", "VORFAHRTSSCHILD",
    "GESCHWINDIGKEITSBEGRENZUNG", "AUTOBAHNAUSFAHRT", "AUTOBAHNAUFFAHRT", 
    "RASTPLATZ", "RASTSTAETTE", "MAUTSTELLE", "FAHRSCHULE", "FUEHRERSCHEIN",
    "VERKEHRSREGELN", "VERKEHRSERZIEHUNG", "SCHULWEG", "SCHULBUS", "FAHRRADSTAENDER",
    "FAHRRADSCHLOSS", "FAHRRADKLINGEL", "FAHRRADKORB", "FAHRRADLICHT", "REFLEKTOREN",
    "STRASSENVERKEHR", "FUSSGAENGERAMPEL", "VERKEHRSUEBERWACHUNG", "BLITZANLAGE",
    "VERKEHRSKONTROLLE", "FAHRZEUGPAPIERE", "AUTOKENNZEICHEN", "NUMMERNSCHILD",
    "FAHRTRICHTUNG", "EINBAHNSTRASSE", "GEGENVERKEHR", "UEBERHOLVERBOT",
    "PARKVERBOT", "HALTEVERBOT", "PARKSCHEIBE", "PARKUHR", "PARKKRALLE",
    "ABSCHLEPPWAGEN", "WERKSTATT", "REIFENWECHSEL", "WINTERREIFEN", "SOMMERREIFEN",
    "SCHNEEKETTEN", "WARNDREIECK", "VERBANDSKASTEN", "FEUERLOESCHER", "WAGENHEBER",
    "RESERVERAD", "AUTOSCHLUESSEL", "ZUENDSCHLUESSEL", "FERNBEDIENUNG", "AUTOTUER",
    "KOFFERRAUM", "MOTORHAUBE", "WINDSCHUTZSCHEIBE", "SCHEIBENWISCHER", "SEITENSPIEGEL",
    "RUECKSPIEGEL", "BLINKER", "SCHEINWERFER", "RUECKLICHT", "BREMSLICHT", "NEBELSCHLUSSLEUCHTE",
    "STOSSSTANGE", "AUSPUFF", "KATALYSATOR", "KRAFTSTOFFTANK", "BENZIN", "DIESEL",
    "ELEKTROAUTO", "HYBRIDAUTO", "LADESTELLE", "STECKDOSE", "BATTERIE", "LADESTATION"
]

def finde_woerter_aus_kennzeichen(regular_codes, code_to_name):
    """
    Findet Wörter, die aus KFZ-Kennzeichen gebildet werden können.
    
    Args:
        regular_codes: Liste der regulären KFZ-Kennzeichen
        code_to_name: Dictionary, das KFZ-Kennzeichen auf Regionsnamen abbildet
    
    Returns:
        Eine Liste von Rätseln
    """
    puzzles = []
    
    # Filtere Wörter mit mindestens 7 und maximal 12 Zeichen
    filtered_words = [word for word in VERKEHRS_WOERTER if 7 <= len(word) <= 12]
    print(f"Verarbeite {len(filtered_words)} Wörter mit mindestens 7 Zeichen...")
    
    for word_index, wort in enumerate(filtered_words):
        if word_index % 10 == 0:
            print(f"Fortschritt: {word_index}/{len(filtered_words)} Wörter verarbeitet")
        
        # Finde alle möglichen Lösungen für dieses Wort
        loesungen = finde_loesungen_fuer_wort(wort, regular_codes, set())
        
        # Wenn Lösungen gefunden wurden, wähle die kürzeste
        if loesungen:
            # Sortiere nach Anzahl der verwendeten Kennzeichen (kürzeste zuerst)
            loesungen.sort(key=len)
            beste_loesung = loesungen[0]
            
            # Prüfe, ob die Lösung mindestens 3 Kennzeichen verwendet
            if len(beste_loesung) >= 3:
                puzzle = {
                    "wort": wort,
                    "loesung": [{"code": code, "name": code_to_name.get(code, "Unbekannt")} for code in beste_loesung]
                }
                puzzles.append(puzzle)
                print(f"Rätsel gefunden für '{wort}': {'-'.join(beste_loesung)}")
    
    return puzzles

def finde_loesungen_fuer_wort(wort, codes, verwendete_codes, position=0, aktuelle_loesung=None):
    """
    Rekursive Funktion, um alle möglichen Lösungen für ein Wort zu finden.
    
    Args:
        wort: Das zu bildende Wort
        codes: Liste der verfügbaren KFZ-Kennzeichen
        verwendete_codes: Set der bereits verwendeten Codes (um Duplikate zu vermeiden)
        position: Aktuelle Position im Wort
        aktuelle_loesung: Liste der bisher verwendeten Codes
    
    Returns:
        Liste aller möglichen Lösungen
    """
    if aktuelle_loesung is None:
        aktuelle_loesung = []
    
    # Abbruchbedingung: Wenn das gesamte Wort gebildet wurde
    if position >= len(wort):
        return [aktuelle_loesung]
    
    loesungen = []
    
    # Versuche, die nächsten 1-3 Buchstaben mit einem Kennzeichen zu matchen
    for laenge in range(1, 4):
        if position + laenge > len(wort):
            break
            
        teil = wort[position:position+laenge]
        
        # Prüfe, ob dieser Teil einem Kennzeichen entspricht
        if teil in codes and teil not in verwendete_codes:
            # Füge dieses Kennzeichen zur Lösung hinzu und suche weiter
            neue_verwendete_codes = verwendete_codes.copy()
            neue_verwendete_codes.add(teil)
            neue_loesung = aktuelle_loesung + [teil]
            
            weitere_loesungen = finde_loesungen_fuer_wort(
                wort, codes, neue_verwendete_codes, position + laenge, neue_loesung
            )
            
            loesungen.extend(weitere_loesungen)
    
    return loesungen

def speichere_raetsel_als_json(puzzles, output_file="kfz_puzzles.json"):
    """
    Speichert die Rätsel als JSON-Datei.
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(puzzles, f, ensure_ascii=False, indent=4)
    
    print(f"{len(puzzles)} Rätsel wurden in '{output_file}' gespeichert.")
    
    # Gib einige Beispielrätsel aus
    print("\nBeispiele für generierte Rätsel:")
    for i, puzzle in enumerate(puzzles[:5], 1):
        codes = [item["code"] for item in puzzle["loesung"]]
        names = [item["name"] for item in puzzle["loesung"]]
        print(f"{i}. Wort: {puzzle['wort']}")
        print(f"   Lösung: {' - '.join(names)} ({'-'.join(codes)})")
        print()

def generiere_raetsel(regular_codes, code_to_name):
    """
    Hauptfunktion zum Generieren der KFZ-Kennzeichen-Rätsel.
    Diese Funktion wird vom Hauptskript aufgerufen.
    
    Args:
        regular_codes: Liste der regulären KFZ-Kennzeichen
        code_to_name: Dictionary, das KFZ-Kennzeichen auf Regionsnamen abbildet
    
    Returns:
        Liste der generierten Rätsel
    """
    puzzles = finde_woerter_aus_kennzeichen(regular_codes, code_to_name)
    speichere_raetsel_als_json(puzzles)
    return puzzles

if __name__ == "__main__":
    print("Dieses Skript sollte aus dem Hauptskript aufgerufen werden.")
    print("Es benötigt die KFZ-Kennzeichen und Regionsnamen als Parameter.")
