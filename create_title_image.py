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

def create_title_image(gdf, all_codes, code_to_region, code_to_geometry, region_to_codes, output_path):
    """
    Erstellt ein Titelbild mit farbiger Deutschlandkarte und TagCloud der Regionen.
    """
    # Erstelle eine große Figur für hohe Auflösung
    plt.figure(figsize=(20, 16), dpi=300)
    
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
            
            if geometries:
                for geom in geometries:
                    if geom is not None:
                        # Zeichne die Geometrie mit der Farbe des Kennzeichens
                        gpd.GeoSeries([geom], crs=gdf.crs).plot(ax=ax, facecolor=color, edgecolor='white', linewidth=0.2, alpha=0.8)
    
    # Entferne Achsen und Rahmen
    ax.set_axis_off()
    
    # Speichere die Karte als temporäre Datei mit transparentem Hintergrund
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
    
    # Positioniere die Karte unten bündig und mittig
    paste_x = (final_img.width - new_width) // 2
    paste_y = final_img.height - new_height - 50  # 50 Pixel Abstand vom unteren Rand
    
    # Füge die verkleinerte Karte mit Transparenz ein
    final_img.paste(map_img, (paste_x, paste_y), map_img)
    
    # Füge einen Titel hinzu
    draw = ImageDraw.Draw(final_img)
    # Versuche verschiedene Schriftarten zu laden
    try:
        # Liste möglicher Schriftarten
        font_paths = [
            '/System/Library/Fonts/Helvetica.ttc',
            '/System/Library/Fonts/Arial.ttf',
            '/Library/Fonts/Arial.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        ]
        
        # Versuche, eine der Schriftarten zu laden
        title_font = None
        subtitle_font = None
        
        for path in font_paths:
            if os.path.exists(path):
                title_font = ImageFont.truetype(path, 140)  # Größere Schrift
                subtitle_font = ImageFont.truetype(path, 90)  # Größere Schrift
                break
                
        # Wenn keine Schriftart gefunden wurde, verwende die Standardschriftart
        if title_font is None:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
    except:
        # Fallback zu Standardschriftart
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    
    title = "Mein großes Kennzeichen Buch"
    subtitle = "Ein Sammelbuch für deutsche Autokennzeichen"
    
    # Positioniere den Titel oben mittig mit mehr Abstand nach unten
    # Verwende textlength für die Breite und schätze die Höhe basierend auf der Schriftgröße
    title_width = draw.textlength(title, font=title_font)
    title_height = title_font.size
    subtitle_width = draw.textlength(subtitle, font=subtitle_font)
    subtitle_height = subtitle_font.size
    
    # Mehr Abstand vom oberen Rand
    top_margin = 100
    
    # Füge einen Schatten hinzu für bessere Lesbarkeit
    shadow_offset = 3
    try:
        draw.text(((final_img.width - title_width) // 2 + shadow_offset, top_margin + shadow_offset), 
                title, font=title_font, fill=(50, 50, 50, 200))
        draw.text(((final_img.width - subtitle_width) // 2 + shadow_offset, top_margin + title_height + 30 + shadow_offset), 
                subtitle, font=subtitle_font, fill=(50, 50, 50, 200))
    except Exception as e:
        print(f"Warnung beim Zeichnen des Schattens: {e}")
    
    # Zeichne den Text
    try:
        draw.text(((final_img.width - title_width) // 2, top_margin), 
                title, font=title_font, fill=(0, 0, 0, 255))
        draw.text(((final_img.width - subtitle_width) // 2, top_margin + title_height + 30), 
                subtitle, font=subtitle_font, fill=(0, 0, 0, 255))
    except Exception as e:
        print(f"Warnung beim Zeichnen des Textes: {e}")
        # Fallback: Zeichne Text ohne Positionierung
        try:
            draw.text((50, top_margin), title, font=title_font, fill=(0, 0, 0, 255))
            draw.text((50, top_margin + 100), subtitle, font=subtitle_font, fill=(0, 0, 0, 255))
        except:
            print("Konnte Text nicht zeichnen.")
    
    # Speichere das finale Bild
    try:
        final_img.save(output_path, format='PNG', dpi=(300, 300))
    except Exception as e:
        print(f"Fehler beim Speichern mit DPI: {e}")
        # Fallback ohne DPI-Angabe
        final_img.save(output_path, format='PNG')
    
    # Lösche temporäre Dateien
    os.remove(temp_map_path)
    os.remove(temp_cloud_path)
    
    print(f"Titelbild erfolgreich erstellt: {output_path}")
    return output_path

def main():
    # Pfade
    shapefile_path = "kfz250.utm32s.shape/kfz250/KFZ250.shp"
    output_dir = "output_maps"
    output_path = os.path.join(output_dir, "kfz_titelbild.png")
    
    # Erstelle Output-Verzeichnis, falls es nicht existiert
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 80)
    print("Erstelle Titelbild für das KFZ-Kennzeichen Sammelbuch")
    print("=" * 80)
    
    # Lade Shapefile
    gdf = load_shapefile(shapefile_path)
    if gdf is None:
        print("Fehler beim Laden des Shapefiles.")
        sys.exit(1)
    
    # Extrahiere Kennzeichen
    all_codes, code_to_region, code_to_geometry, region_to_codes = extract_codes_from_shapefile(gdf)
    
    # Erstelle Titelbild
    title_image_path = create_title_image(gdf, all_codes, code_to_region, code_to_geometry, region_to_codes, output_path)
    
    print(f"Titelbild wurde erstellt: {title_image_path}")
    print("Dieses Bild kann nun als Titelbild für das Sammelbuch verwendet werden.")

if __name__ == "__main__":
    main()
