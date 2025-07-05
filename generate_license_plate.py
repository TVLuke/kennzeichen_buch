#!/usr/bin/env python3
"""
Skript zum Erstellen eines Kennzeichens als PNG mit Transparenz.
Nimmt ein Kennzeichen als Parameter und ersetzt den Text im SVG.
"""

import sys
import os
from lxml import etree
import cairosvg
import argparse

def generate_license_plate(kennzeichen, svg_path=None, output_path=None, font_path=None):
    """
    Generiert ein Kennzeichen-PNG aus einer SVG-Vorlage.
    Wählt automatisch die passende SVG-Vorlage basierend auf der Länge des Kennzeichens.
    
    Args:
        kennzeichen (str): Das Kennzeichen, das eingefügt werden soll (z.B. "HH")
        svg_path (str, optional): Pfad zur SVG-Vorlage. Wenn nicht angegeben, wird
                                 basierend auf der Länge des Kennzeichens ausgewählt.
        output_path (str, optional): Pfad für die Ausgabedatei. Wenn nicht angegeben, 
                                     wird 'kennzeichen_[KENNZEICHEN].png' verwendet.
        font_path (str, optional): Pfad zur Schriftartdatei
    
    Returns:
        str: Pfad zur erzeugten PNG-Datei
    """
    # Standardwerte setzen
    if output_path is None:
        output_path = f"kennzeichen_{kennzeichen}.png"
    
    # Wähle die passende SVG-Vorlage basierend auf der Länge des Kennzeichens
    if svg_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if len(kennzeichen) == 1:
            svg_path = os.path.join(base_dir, "raw1.svg")
        elif len(kennzeichen) == 2:
            svg_path = os.path.join(base_dir, "raw2.svg")
        elif len(kennzeichen) == 3:
            svg_path = os.path.join(base_dir, "raw3.svg")
        else:
            # Für längere Kennzeichen verwenden wir raw3.svg
            svg_path = os.path.join(base_dir, "raw3.svg")
        print(f"Verwende SVG-Vorlage: {svg_path} für Kennzeichen mit {len(kennzeichen)} Zeichen")
    
    # SVG-Datei einlesen
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(svg_path, parser)
    root = tree.getroot()
    
    # Namespace für SVG
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}
    
    # Finde das Textelement mit der ID "Kenz"
    kenz_group = root.xpath('//svg:g[@id="Kenz"]', namespaces=namespaces)[0]
    text_element = kenz_group.xpath('.//svg:text', namespaces=namespaces)[0]
    
    # Ersetze den Text
    text_element.text = kennzeichen
    
    # Temporäre SVG-Datei erstellen
    temp_svg_path = f"temp_{kennzeichen}.svg"
    tree.write(temp_svg_path, pretty_print=True, xml_declaration=True, encoding="utf-8")
    
    # SVG in PNG mit Transparenz konvertieren
    cairosvg.svg2png(url=temp_svg_path, write_to=output_path)
    
    # Temporäre SVG-Datei löschen
    os.remove(temp_svg_path)
    
    print(f"Kennzeichen '{kennzeichen}' wurde als '{output_path}' gespeichert.")
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Generiert ein Kennzeichen-PNG aus einer SVG-Vorlage.')
    parser.add_argument('kennzeichen', help='Das Kennzeichen, das eingefügt werden soll (z.B. "HH")')
    parser.add_argument('--svg', 
                        help='Pfad zur SVG-Vorlage. Wenn nicht angegeben, wird automatisch basierend auf der Länge des Kennzeichens ausgewählt.')
    parser.add_argument('--output', help='Pfad für die Ausgabedatei')
    parser.add_argument('--font', default='EuroPlate.ttf',
                        help='Pfad zur Schriftartdatei')
    
    args = parser.parse_args()
    
    generate_license_plate(args.kennzeichen, args.svg, args.output, args.font)

if __name__ == "__main__":
    main()
