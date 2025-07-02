#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
from matplotlib.font_manager import FontProperties
import fiona
from PIL import Image, ImageDraw, ImageFont
from wordcloud import WordCloud
import random
from shapely.geometry import box
import subprocess
# Import ReportLab für PDF-Erstellung
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

def load_shapefile(shapefile_path):
    """
    Lädt ein Shapefile und gibt es als GeoDataFrame zurück.
    Versucht verschiedene Kodierungen und Methoden.
    """
    try:
        print("Versuche mit fiona zu laden...")
        with fiona.open(shapefile_path) as f:
            gdf = gpd.GeoDataFrame.from_features(f, crs=f.crs)
        print("Shapefile erfolgreich mit fiona geladen")
        return gdf
    except Exception as e:
        print(f"Fehler beim Laden mit fiona: {e}")
        return None

def normalize_text(text):
    """
    Normalisiert Text, um Probleme mit Umlauten zu beheben.
    """
    if not isinstance(text, str):
        return ""
    
    # Häufige Fehlkodierungen korrigieren
    text = text.replace('Ã¤', 'ä').replace('Ã¶', 'ö').replace('Ã¼', 'ü')
    text = text.replace('Ã„', 'Ä').replace('Ã–', 'Ö').replace('Ãœ', 'Ü')
    text = text.replace('ÃŸ', 'ß')
    
    return text.strip()

def extract_codes_from_shapefile(gdf):
    """
    Extrahiert alle KFZ-Kennzeichen aus dem GeoDataFrame.
    """
    all_codes = []
    code_to_region = {}
    code_to_geometry = {}
    region_to_codes = {}
    
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
                if code and code not in all_codes:
                    all_codes.append(code)
                    code_to_region[code] = region_name
                    code_to_geometry[code] = row.geometry
            
            # Speichere auch die Zuordnung Region -> Codes
            if region_name:
                if region_name not in region_to_codes:
                    region_to_codes[region_name] = []
                region_to_codes[region_name].extend(codes)
    
    # Sortiere alphabetisch
    all_codes.sort()
    print(f"Insgesamt {len(all_codes)} einzigartige KFZ-Kennzeichen gefunden")
    print(f"Insgesamt {len(region_to_codes)} einzigartige Regionen gefunden")
    
    return all_codes, code_to_region, code_to_geometry, region_to_codes

def create_title_image(gdf, all_codes, code_to_region, code_to_geometry, region_to_codes, output_path, region_code=None, csv_region_name=None):
    """
    Erstellt ein Titelbild mit farbiger Deutschlandkarte und TagCloud der Regionen.
    Speichert das Ergebnis als PDF-Datei.
    """
    
    # Debug-Ausgabe für das übergebene Kennzeichen
    if region_code:
        print(f"\nDEBUG: Informationen für Kennzeichen {region_code}:")
        # Finde alle Regionen mit diesem Kennzeichen
        regions_with_code = [region for region, codes in region_to_codes.items() if region_code in codes]
        print(f"DEBUG: Gefundene Regionen mit Kennzeichen {region_code}: {regions_with_code}")
        print(f"DEBUG: Anzahl der Regionen mit Kennzeichen {region_code}: {len(regions_with_code)}")
        
        # Prüfe, ob es Geometrien für dieses Kennzeichen gibt
        geom = code_to_geometry.get(region_code)
        if geom is not None:
            print(f"DEBUG: Geometrie für {region_code} gefunden")
        else:
            print(f"DEBUG: Keine Geometrie für {region_code} gefunden")
            
        # Finde die beste Region für die Markierung
        # Bevorzuge eine Region, die nur das gesuchte Kennzeichen hat
        selected_region_for_marker = None
        
        # Zuerst suchen wir nach einer Region, die NUR das gesuchte Kennzeichen hat
        for region, codes in region_to_codes.items():
            if region_code in codes and len(codes) == 1:
                selected_region_for_marker = region
                print(f"DEBUG: Region {region} hat nur das Kennzeichen {region_code} - wird bevorzugt")
                break
        
        # Wenn keine Region gefunden wurde, die nur das gesuchte Kennzeichen hat,
        # nehmen wir die erste Region mit diesem Kennzeichen
        if selected_region_for_marker is None and regions_with_code:
            selected_region_for_marker = regions_with_code[0]
            print(f"DEBUG: Keine Region mit nur diesem Kennzeichen gefunden, wähle erste Region: {selected_region_for_marker}")
        
        print(f"DEBUG: Ausgewählte Region für Markierung: {selected_region_for_marker}")

    # Erstelle eine Figur in DIN A4-Größe (210 x 297 mm)
    # Wir verwenden ein Seitenverhältnis von 1:sqrt(2) für DIN A4
    plt.figure(figsize=(8.27, 11.69))  # 8.27 x 11.69 Zoll = 210 x 297 mm (DIN A4)
    
    # Erstelle zuerst die WordCloud der Regionen
    print("Erstelle WordCloud der Regionen...")
    
    # Erstelle eine Farbpalette mit genügend Farben
    num_colors = len(all_codes)
    cmap_name = 'tab20'  # Eine Farbpalette mit 20 unterschiedlichen Farben
    cmap = plt.colormaps.get_cmap(cmap_name)
    
    # Wenn wir mehr als 20 Farben benötigen, erweitern wir die Palette
    if num_colors > 20:
        # Erstelle eine erweiterte Farbpalette durch Kombination mehrerer Farbpaletten
        colors1 = plt.colormaps['tab20'](np.linspace(0, 1, 20))
        colors2 = plt.colormaps['tab20b'](np.linspace(0, 1, 20))
        colors3 = plt.colormaps['tab20c'](np.linspace(0, 1, 20))
        colors4 = plt.colormaps['Set3'](np.linspace(0, 1, 12))
        colors5 = plt.colormaps['Paired'](np.linspace(0, 1, 12))
        
        # Kombiniere die Farben
        all_colors = np.vstack([colors1, colors2, colors3, colors4, colors5])
        
        # Mische die Farben für mehr Variation
        np.random.seed(42)  # Für reproduzierbare Ergebnisse
        np.random.shuffle(all_colors)
        
        # Erstelle eine benutzerdefinierte Farbpalette
        cmap = mcolors.ListedColormap(all_colors)
    
    # Erstelle eine Zuordnung von Codes zu Farben
    code_to_color = {}
    for i, code in enumerate(all_codes):
        color_idx = i % cmap.N  # Wiederhole die Farben, wenn nötig
        code_to_color[code] = cmap(color_idx)
    
    # Zeichne die Grundkarte von Deutschland in hellgrau
    ax = plt.gca()
    gdf.plot(ax=ax, color='lightgray', edgecolor='gray', linewidth=0.3)
    
    # Zeichne jede Region in der Farbe ihres ersten Kennzeichens
    for region_name, codes in region_to_codes.items():
        if codes:
            # Verwende das erste Kennzeichen für die Farbe
            code = codes[0]
            color = code_to_color.get(code, 'lightgray')
            
            # Finde alle Geometrien für diese Region
            geometries = [code_to_geometry.get(c) for c in codes if c in code_to_geometry]
            geometries = [g for g in geometries if g is not None]
            
            # Zeichne alle Geometrien dieser Region
            if geometries:
                for geom in geometries:
                    if geom is not None:
                        # Zeichne die Geometrie mit der Farbe des Kennzeichens
                        gpd.GeoSeries([geom], crs=gdf.crs).plot(ax=ax, facecolor=color, edgecolor='white', linewidth=0.2, alpha=0.8)
    
    # Setze einen Marker für die ausgewählte Region, falls eine gefunden wurde
    if region_code and selected_region_for_marker:
        # Hole die Codes für die ausgewählte Region
        region_codes = region_to_codes.get(selected_region_for_marker, [])
        
        # Finde die Geometrie für das gesuchte Kennzeichen in dieser Region
        if region_code in region_codes and region_code in code_to_geometry:
            geom = code_to_geometry[region_code]
            if geom is not None:
                try:
                    centroid = geom.centroid
                    print(f"DEBUG: Markiere Punkt für Region {selected_region_for_marker} mit Kennzeichen {region_code} bei Koordinaten {centroid.x}, {centroid.y}")
                    ax.scatter(centroid.x, centroid.y, s=120, color='red', marker='o', edgecolors='black', linewidths=1.5, zorder=10)
                except Exception as e:
                    print(f"Fehler beim Zeichnen des Markers: {e}")
        else:
            print(f"DEBUG: Keine Geometrie für Kennzeichen {region_code} in Region {selected_region_for_marker} gefunden")
    
    # Entferne Achsen und Rahmen
    ax.set_axis_off()
    
    # Speichere die Karte als temporäre PNG-Datei mit transparentem Hintergrund
    temp_map_path = "temp_map.png"
    plt.savefig(temp_map_path, bbox_inches='tight', pad_inches=0, dpi=300, transparent=True)
    plt.close()
    
    # Erstelle eine TagCloud der Regionen
    # Gewichte basierend auf der Anzahl der Kennzeichen pro Region
    region_weights = {region: len(codes) for region, codes in region_to_codes.items()}
    
    # Erstelle ein Wörterbuch für die WordCloud
    wordcloud_dict = {}
    for region, weight in region_weights.items():
        if region:  # Überspringe leere Regionen
            wordcloud_dict[region] = weight * 10  # Verstärke die Gewichtung
    
    # Erstelle die WordCloud
    # Versuche, die Schriftart zu laden, oder verwende eine Standardschriftart
    try:
        font_path = '/System/Library/Fonts/Helvetica.ttc'
        # Prüfe, ob die Schriftart existiert
        if not os.path.exists(font_path):
            font_path = None
    except:
        font_path = None
        
    wordcloud = WordCloud(
        width=2000, 
        height=1600,  # Größere Dimensionen für bessere Sichtbarkeit
        background_color='white',
        max_words=300,  # Mehr Wörter für bessere Abdeckung
        prefer_horizontal=0.6,
        colormap='Greys',  # Graustufen für hellgrauen Hintergrund
        font_path=font_path,  # Verwende die Schriftart, wenn verfügbar
        relative_scaling=0.7,
        min_font_size=10,
        max_font_size=120,  # Größere maximale Schriftgröße
        random_state=42
    ).generate_from_frequencies(wordcloud_dict)
    
    # Speichere die WordCloud als temporäre Datei
    temp_cloud_path = "temp_cloud.png"
    wordcloud.to_file(temp_cloud_path)
    
    # Lade die beiden Bilder mit PIL
    map_img = Image.open(temp_map_path)
    cloud_img = Image.open(temp_cloud_path)
    
    # Erstelle ein neues Bild mit der Größe der Karte
    final_img = Image.new('RGBA', map_img.size, (255, 255, 255, 255))
    
    # Füge die WordCloud als Hintergrund hinzu (skaliert auf die Größe der Karte)
    cloud_img = cloud_img.resize(map_img.size, Image.LANCZOS)
    cloud_img = cloud_img.convert('RGBA')
    
    # Mache den Hintergrund der WordCloud transparent und die Wörter hellgrau
    data = cloud_img.getdata()
    new_data = []
    for item in data:
        # Wenn es sich um einen weißen Pixel handelt, mache ihn transparent
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            new_data.append((255, 255, 255, 0))
        else:
            # Mache nicht-weiße Pixel hellgrau und teilweise transparent
            # Hellgrau mit Alpha = 60 (sehr transparent)
            gray_value = 200  # Hellgrauer Farbwert
            new_data.append((gray_value, gray_value, gray_value, 60))
    
    cloud_img.putdata(new_data)
    
    # Füge die WordCloud als Hintergrund ein
    final_img.paste(cloud_img, (0, 0), cloud_img)
    
    # Konvertiere die Karte zu RGBA, falls sie es noch nicht ist
    map_img = map_img.convert("RGBA")
    
    # Mache weiße Pixel in der Karte transparent
    map_data = map_img.getdata()
    new_map_data = []
    for item in map_data:
        # Wenn es sich um einen weißen oder sehr hellen Pixel handelt, mache ihn transparent
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            new_map_data.append((255, 255, 255, 0))  # Vollständig transparent
        else:
            new_map_data.append(item)  # Behalte die Originalfarbe und -transparenz
    
    map_img.putdata(new_map_data)
    
    # Verkleinere die Deutschlandkarte auf 70% der Originalgröße
    map_width, map_height = map_img.size
    new_width = int(map_width * 0.7)
    new_height = int(map_height * 0.7)
    map_img = map_img.resize((new_width, new_height), Image.LANCZOS)
    
    # Positioniere die Karte unten bündig und mittig, aber 4 cm (ca. 160 Pixel) höher
    paste_x = (final_img.width - new_width) // 2
    paste_y = final_img.height - new_height - 210  # 210 Pixel Abstand vom unteren Rand (50 + 160)
    
    # Füge die verkleinerte Karte mit Transparenz ein
    final_img.paste(map_img, (paste_x, paste_y), map_img)
    
    # Erstelle ein Kennzeichen-Bild, wenn ein Kennzeichen angegeben wurde
    if region_code and len(region_code) <= 3:
        try:
            # Bestimme die Position des Ortes (Nord/Süd)
            is_south = False
            if region_code in code_to_geometry:
                geom = code_to_geometry[region_code]
                if geom is not None:
                    # Berechne den Schwerpunkt der Geometrie
                    centroid = geom.centroid
                    # Bestimme, ob der Ort in Süddeutschland liegt (y-Koordinate kleiner als Mittelpunkt)
                    # Die genaue Grenze hängt vom Koordinatensystem ab, hier ein Beispielwert
                    map_center_y = gdf.total_bounds[1] + (gdf.total_bounds[3] - gdf.total_bounds[1]) / 2
                    is_south = centroid.y < map_center_y
            
            # Generiere das Kennzeichen-Bild mit unserem Skript
            temp_license_plate = 'temp_license_plate.png'
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generate_license_plate.py')
            
            # Führe das Skript aus - die SVG-Vorlage wird automatisch basierend auf der Länge des Kennzeichens ausgewählt
            cmd = [sys.executable, script_path, region_code, '--output', temp_license_plate]
            subprocess.run(cmd, check=True)
            
            # Lade das Kennzeichen-Bild
            if os.path.exists(temp_license_plate):
                license_img = Image.open(temp_license_plate)
                license_img = license_img.convert('RGBA')
                
                # Skaliere das Kennzeichen auf eine angemessene Größe (ca. 60% der Kartenbreite)
                license_width = int(new_width * 0.6)
                license_height = int(license_width * license_img.height / license_img.width)
                license_img = license_img.resize((license_width, license_height), Image.LANCZOS)
                
                # Wähle einen zufälligen Neigungswinkel zwischen -10 und +10 Grad
                rotation_angle = random.uniform(-10, 10)
                license_img = license_img.rotate(rotation_angle, resample=Image.BICUBIC, expand=True, fillcolor=(0, 0, 0, 0))
                
                # Nach der Rotation könnte sich die Größe geändert haben
                rotated_width, rotated_height = license_img.size
                
                # Positioniere das Kennzeichen abhängig von der Position der Deutschlandkarte
                # und ob der Ort im Norden oder Süden liegt
                
                # Horizontale Zentrierung
                license_x = (final_img.width - rotated_width) // 2
                
                # Die Position der Deutschlandkarte ist durch paste_y und new_height definiert
                # paste_y ist die obere Kante der Karte
                # new_height ist die Höhe der Karte
                
                # Teile die Karte in Drittel
                map_top = paste_y
                map_bottom = paste_y + new_height
                map_height = new_height
                map_third = map_height / 3
                
                if is_south:
                    # Für süddeutsche Kennzeichen: Platziere im oberen Drittel der Karte
                    # Mitte des oberen Drittels = obere Kante + 1/6 der Höhe
                    target_center_y = map_top + map_third / 2
                else:
                    # Für norddeutsche Kennzeichen: Platziere im unteren Drittel der Karte
                    # Mitte des unteren Drittels = obere Kante + 5/6 der Höhe
                    target_center_y = map_bottom - map_third / 2
                
                # Positioniere das Kennzeichen so, dass seine Mitte auf der berechneten Position liegt
                license_y = int(target_center_y - rotated_height / 2)
                
                # Füge das Kennzeichen ein
                final_img.paste(license_img, (license_x, license_y), license_img)
        except Exception as e:
            print(f"Fehler beim Erstellen des Kennzeichen-Bildes: {e}")
    
    # Erstelle ein Draw-Objekt für das Bild (wird für andere Operationen benötigt)
    draw = ImageDraw.Draw(final_img)
    
    # Wir laden keine Schriftarten für das Bild, da wir den Text direkt ins PDF einfügen werden
    # Der Titel und Untertitel werden später im PDF-Teil hinzugefügt
    
    # Wir zeichnen keinen Text auf das Bild, da wir den Text direkt ins PDF einfügen werden
    # Bestimme den Regionsnamen, wenn ein Kennzeichen angegeben wurde
    region_text = ""
    if region_code:
        # Bevorzuge den Namen aus der CSV-Datei, wenn vorhanden
        if csv_region_name:
            region_name = csv_region_name
        elif region_code in code_to_region:
            region_name = code_to_region[region_code]
        else:
            region_name = None
            
        if region_name:
            region_text = f"{region_name} Edition"
    
    # Autor-Text
    author_text = "von Lukas Ruge"
    
    # Speichere das finale Bild als temporäre Datei
    temp_img_path = "temp_final_img.png"
    try:
        final_img.save(temp_img_path, format='PNG', dpi=(300, 300))
    except Exception as e:
        print(f"Fehler beim Speichern mit DPI: {e}")
        # Fallback ohne DPI-Angabe
        final_img.save(temp_img_path, format='PNG')
    
    # Erstelle ein PDF mit ReportLab
    # Stelle sicher, dass die Ausgabedatei die Endung .pdf hat
    if not output_path.lower().endswith('.pdf'):
        pdf_output_path = output_path.rsplit('.', 1)[0] + '.pdf'
    else:
        pdf_output_path = output_path
    
    # Erstelle ein neues PDF in DIN A4-Größe
    c = canvas.Canvas(pdf_output_path, pagesize=A4)
    width, height = A4  # A4 ist 210 x 297 mm
    
    # Füge das Bild ins PDF ein
    # Konvertiere zu RGB für PDF-Kompatibilität
    img = Image.open(temp_img_path)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    # Füge das Bild ins PDF ein (ohne Text)
    c.drawImage(temp_img_path, 0, 0, width, height)
    
    # Füge den Text direkt ins PDF ein
    # Titel
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(width/2, height - 3*cm, "Mein großes Kennzeichen Buch")
    
    # Untertitel
    c.setFont("Helvetica", 24)
    c.drawCentredString(width/2, height - 4*cm, "Ein Sammelbuch für deutsche Autokennzeichen")
    
    # Wenn eine Region angegeben wurde, füge sie unten ein
    if region_text:
        c.setFont("Helvetica", 18)
        c.drawCentredString(width/2, 3*cm, region_text)
    
    # Füge den Autor hinzu
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, 2*cm, author_text)
    
    # Speichere das PDF
    c.save()
    
    # Lösche temporäre Dateien
    os.remove(temp_map_path)
    os.remove(temp_cloud_path)
    os.remove(temp_img_path)
    
    # Lösche temporäre Kennzeichen-Datei, falls vorhanden
    if 'temp_license_plate.png' in locals() and os.path.exists('temp_license_plate.png'):
        os.remove('temp_license_plate.png')
    
    print(f"Titelbild erfolgreich als PDF erstellt: {pdf_output_path}")
    return pdf_output_path

def main():
    # Pfade
    shapefile_path = "kfz250.utm32s.shape/kfz250/KFZ250.shp"
    output_dir = "output_maps"
    output_path = os.path.join(output_dir, "kfz_titelbild.pdf")
    region_code = None
    
    # Prüfe, ob ein Kennzeichen als Argument übergeben wurde
    if len(sys.argv) > 1:
        region_code = sys.argv[1]
        # Wenn ein Kennzeichen angegeben wurde, passe den Ausgabepfad an
        output_path = os.path.join(output_dir, f"kfz_titelbild_{region_code}.pdf")
    
    # Erstelle Output-Verzeichnis, falls es nicht existiert
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 80)
    print("Erstelle Titelbild für das KFZ-Kennzeichen Sammelbuch")
    if region_code:
        print(f"Region: {region_code}")
    print("=" * 80)
    
    # Lade Shapefile
    gdf = load_shapefile(shapefile_path)
    if gdf is None:
        print("Fehler beim Laden des Shapefiles.")
        sys.exit(1)
    
    # Extrahiere Kennzeichen
    all_codes, code_to_region, code_to_geometry, region_to_codes = extract_codes_from_shapefile(gdf)
    
    # Prüfe, ob das angegebene Kennzeichen gültig ist
    if region_code and region_code not in code_to_region:
        print(f"Warnung: Kennzeichen '{region_code}' nicht gefunden. Erstelle allgemeines Titelbild.")
        region_code = None
    
    # Erstelle Titelbild
    title_image_path = create_title_image(gdf, all_codes, code_to_region, code_to_geometry, region_to_codes, output_path, region_code)
    
    print(f"Titelbild wurde erstellt: {title_image_path}")
    print("Dieses Bild kann nun als Titelbild für das Sammelbuch verwendet werden.")

if __name__ == "__main__":
    main()
