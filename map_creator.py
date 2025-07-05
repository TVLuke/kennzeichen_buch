import os
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib import colors
from normalizer import normalize_text

OUTPUT_DIR = "output_maps"  # Verzeichnis für die Ausgabedateien
CODES_PER_PAGE = 20    # Anzahl der Kennzeichen pro Seite für reguläre Kennzeichen
RARE_CODES_PER_PAGE = 60  # Anzahl der Kennzeichen pro Seite für seltene Kennzeichen
SHAPEFILE_PATH = "kfz250.utm32s.shape/kfz250/KFZ250.shp"
CSV_PATH = "kfz-kennz-d.csv"
CSV_PATH_OCTOATE = "kfzkennzeichen-deutschland.csv"
PAGE_WIDTH = 8.27  # DIN-A4 Breite in Zoll
PAGE_HEIGHT = 11.69  # DIN-A4 Höhe in Zoll

def create_right_page_map(ax, gdf, page_codes, code_to_region, code_to_name, code_to_other_codes, home_code=None):
    # Debug: Zeige den Home-Code
    print(f"Home-Code in create_right_page_map: {home_code}")
    """
    Erstellt die rechte Seite der Doppelseite mit der Europakarte und Deutschland im Zentrum.
    
    Parameter:
    - ax: Die Matplotlib-Achse, auf der gezeichnet werden soll
    - gdf: Der GeoDataFrame mit den KFZ-Regionen
    - page_codes: Die KFZ-Codes für diese Seite
    - code_to_region: Dictionary, das KFZ-Codes auf Regionen abbildet
    - code_to_name: Dictionary, das KFZ-Codes auf Regionsnamen abbildet
    - code_to_other_codes: Dictionary, das KFZ-Codes auf weitere Codes der Region abbildet
    - home_code: Der Code der Heimatregion (optional)
    """
    # Setze die Hintergrundfarbe der Achse und entferne alle Achsen und Ränder
    ax.set_facecolor('#4a79a5')  # Blauer Hintergrund
    ax.set_axis_off()
    ax.set_frame_on(False)
    
    # Lade zusätzliche Shapefiles für den Kartenhintergrund
    base_dir = '.'
    europecoastline_path = os.path.join(base_dir, 'basisdaten', 'europecoastline.shp')
    secondbackground_path = os.path.join(base_dir, 'basisdaten', 'secondbackground.shp')
    germany_path = os.path.join(base_dir, 'basisdaten', 'germanyshape.shp')
    lakes_path = os.path.join(base_dir, 'basisdaten', 'lakes.shp')
    
    try:
        # Lade die Shapefiles mit der Methode aus create_title_image.py
        print(f"Versuche Shapefiles zu laden...")
        
        # Importiere fiona hier, um Konflikte zu vermeiden
        import fiona
        
        # Lade die Shapefiles mit fiona.open
        with fiona.open(europecoastline_path) as f:
            europecoastline_gdf = gpd.GeoDataFrame.from_features(f, crs=f.crs)
        print("europecoastline.shp geladen")
        
        with fiona.open(secondbackground_path) as f:
            secondbackground_gdf = gpd.GeoDataFrame.from_features(f, crs=f.crs)
        print("secondbackground.shp geladen")
        
        with fiona.open(germany_path) as f:
            germany_gdf = gpd.GeoDataFrame.from_features(f, crs=f.crs)
        print("germanyshape.shp geladen")
        
        with fiona.open(lakes_path) as f:
            lakes_gdf = gpd.GeoDataFrame.from_features(f, crs=f.crs)
        print("lakes.shp geladen")
        
        # Stelle sicher, dass alle Shapefiles das gleiche CRS haben
        # Verwende EPSG:25832 als gemeinsames CRS, da die KFZ-Regionen in diesem CRS sind
        europecoastline_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
        
        secondbackground_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
        
        germany_gdf.set_crs(epsg=25832, inplace=True, allow_override=True)
        
        lakes_gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
        lakes_gdf = lakes_gdf.to_crs(epsg=25832)
        
        # Stelle sicher, dass auch das gdf mit den KFZ-Regionen im richtigen CRS ist
        if gdf.crs is None or gdf.crs.to_epsg() != 25832:
            gdf = gdf.set_crs(epsg=25832, allow_override=True)
        
        print("Zusätzliche Shapefiles erfolgreich geladen")
        
        # Setze den Hintergrund auf Blau (#4a79a5)
        ax.set_facecolor('#4a79a5')
        
        # Zeichne die Hintergrundebenen
        europecoastline_gdf.plot(ax=ax, color='#e9e6be', edgecolor='none')  # Helles Europa
        secondbackground_gdf.plot(ax=ax, color='#4a79a5', edgecolor='none')  # Wasser
        germany_gdf.plot(ax=ax, color='#dcd798', edgecolor='none')  # Dunklerer Hintergrund für Deutschland
        
        # Zoom auf Deutschland - Vergrößere die Karte, damit Deutschland mehr Platz einnimmt
        # Hole die Grenzen von Deutschland
        minx, miny, maxx, maxy = germany_gdf.total_bounds
        # Erweitere die Grenzen um einen Faktor, um etwas Kontext zu behalten
        width = maxx - minx
        height = maxy - miny
        # Erweitere die Grenzen um 20% in jede Richtung, aber verschiebe nach links für Platz für Labels
        minx -= width * 0.01  # Weniger Platz links (um ca. 1 cm nach links verschieben)
        maxx += width * 0.39  # Mehr Platz rechts für Labels
        miny -= height * 0.2
        maxy += height * 0.2
        # Setze die Grenzen der Karte
        ax.set_xlim(minx, maxx)
        ax.set_ylim(miny, maxy)
        
        # Erstelle eine Farbpalette mit kräftigen, unterscheidbaren Farben
        base_colors = []
        for cmap_name in ['tab10', 'tab20', 'Dark2', 'Set1', 'Set2', 'Paired']:
            cmap = plt.cm.get_cmap(cmap_name)
            base_colors.extend([cmap(i) for i in np.linspace(0, 1, cmap.N)])
        
        # Filtere Grautöne heraus
        filtered_colors = []
        for color in base_colors:
            r, g, b = color[:3]
            if max(abs(r-g), abs(r-b), abs(g-b)) > 0.15:
                filtered_colors.append(color)
        
        # Stelle sicher, dass wir genügend Farben haben
        while len(filtered_colors) < len(page_codes):
            filtered_colors.extend(filtered_colors)
        
        # Erstelle ein Wörterbuch, um Regionen konsistente Farben zuzuweisen
        region_to_color = {}
        
        # Sammle die Zentroide und Codes für die Labels
        centroids_and_codes = []
        
        # Zeichne die Regionen für die Kennzeichen dieser Seite
        for code in page_codes:
            if code in code_to_region:
                region = code_to_region[code]
                
                # Weise dieser Region eine Farbe zu, falls noch nicht geschehen
                region_id = str(region.name)
                if region_id not in region_to_color:
                    color_idx = len(region_to_color) % len(filtered_colors)
                    region_to_color[region_id] = filtered_colors[color_idx]
                
                # Zeichne die Region mit der zugewiesenen Farbe
                region_name = region.get('NAME', '')
                if isinstance(region_name, pd.Series) and not region_name.empty:
                    region_name = region_name.iloc[0]
                
                region_geom = gdf[gdf['NAME'] == region_name]
                if not region_geom.empty:
                    region_geom.plot(ax=ax, color=region_to_color[region_id], 
                                    edgecolor='black', linewidth=0.5, alpha=0.7)
                    
                    # Berechne den Zentroid für Labels
                    centroid = region_geom.geometry.centroid.iloc[0]
                    centroids_and_codes.append((centroid, code, region_to_color[region_id]))
        
        # Markiere die Home-Region, falls konfiguriert (unabhängig von page_codes)
        if home_code and home_code in code_to_region:
            home_region = code_to_region[home_code]
            home_region_name = home_region.get('NAME', '')
            if isinstance(home_region_name, pd.Series) and not home_region_name.empty:
                home_region_name = home_region_name.iloc[0]
            
            home_region_geom = gdf[gdf['NAME'] == home_region_name]
            if not home_region_geom.empty:
                print(f"Home-Region gefunden: {home_code}")
                home_centroid = home_region_geom.geometry.centroid.iloc[0]
                ax.scatter(home_centroid.x, home_centroid.y, s=120, color='blue', marker='o', 
                          edgecolors='black', linewidths=1.5, zorder=10)
        
        # Zeichne die Seen über der Karte
        lakes_gdf.plot(ax=ax, color='#4a79a5', edgecolor='none')
        
        # Füge Labels am rechten Rand hinzu
        # Bestimme die Grenzen der Karte
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        
        # Berechne die Position für die Labels am rechten Rand
        text_x = x_max - (x_max - x_min) * 0.25  # Rechter Rand - moderater Abstand vom Rand (ca. 2 cm nach links)
        # Sortiere Zentroide von Nord nach Süd
        centroids_and_codes.sort(key=lambda x: -x[0].y)  # Sortiere nach y-Koordinate (absteigend)
        
        # Berechne den vertikalen Abstand zwischen den Labels
        y_range = y_max - y_min
        label_spacing = y_range / (len(centroids_and_codes) + 1)
        
        # Füge Labels für jede Region hinzu, sortiert von Nord nach Süd
        for i, (centroid, code, color) in enumerate(centroids_and_codes):
            # Berechne die y-Position für das Label
            text_y = y_max - (i + 1) * label_spacing
            
            # Setze den Text für das Label
            code_text = code
            is_home = False
            if home_code and home_code == str(code).strip():
                is_home = True
            
            # Zeichne eine dickere schwarze Linie vom Zentroid zum Label
            ax.plot([centroid.x, text_x - 0.05], [centroid.y, text_y], 
                   color='black', linewidth=1.0, zorder=2)
            
            # Wenn es das Home-Kennzeichen ist, zeichne einen auffälligen Marker
            if is_home:
                # Zeichne einen blauen Kreis um den Zentroid
                ax.scatter(centroid.x, centroid.y, s=120, color='blue', marker='o', edgecolors='black', linewidths=1.5, zorder=10)
            
            # Zeichne zuerst den farbigen Punkt (außerhalb des Labels)
            #circle_x = text_x - 0.05
            #ax.scatter(circle_x, text_y, s=100, color=color, alpha=0.9, 
            #          edgecolor='black', linewidth=0.5, zorder=10)
            
            # Füge den Text hinzu - Code und Name (falls vorhanden)
            region_name = code_to_name.get(code, '')
            if region_name:
                region_name = normalize_text(region_name)
            
            # Hauptkennzeichen und Regionsname
            if region_name:
                main_label = f"{code_text} - {region_name}"
            else:
                main_label = code_text
                
            # Weitere Kennzeichen mit Zeilenumbruch bei Bedarf
            other_codes = code_to_other_codes.get(code, [])
            if other_codes:
                # Gruppiere die Codes in Zeilen mit maximal 22 Zeichen
                grouped_codes = []
                current_line = []
                current_length = 0
                
                for c in other_codes:
                    # Prüfe, ob das nächste Kennzeichen in die aktuelle Zeile passt
                    if current_length + len(c) + 2 > 22:  # +2 für Komma und Leerzeichen
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
        
        # Entferne die Achsen und stelle sicher, dass die Karte den gesamten verfügbaren Platz nutzt
        ax.set_axis_off()
        # Verwende 'datalim' statt 'equal', um die Daten an die Achsengröße anzupassen
        ax.set_aspect('auto', adjustable='datalim')
        
    except Exception as e:
        print(f"Fehler beim Laden der zusätzlichen Shapefiles: {e}")
        print("Verwende nur die Hauptkarte ohne Hintergrundebenen")
    
    # Entferne Achsen
    ax.set_axis_off()


def create_map_pages_for_professional_print(gdf, regular_codes, code_to_region, code_to_name, code_to_state, code_to_other_codes, config=None):
    """
    Erstellt ein professionelles Drucklayout im DIN A3 Querformat mit blauem Hintergrund.
    Die linke Seite enthält eine Checkliste, die rechte Seite eine Europakarte mit Deutschland im Zentrum.
    """
    # Erstelle den Ausgabeordner, falls er nicht existiert
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Berechne die Anzahl der Seiten
    num_pages = (len(regular_codes) + CODES_PER_PAGE - 1) // CODES_PER_PAGE
    print(f"Erstelle {num_pages} Seiten mit je {CODES_PER_PAGE} regulären Kennzeichen")
    
    # Definiere die Größe für DIN A3 Querformat (420mm × 297mm)
    # A3 ist doppelt so groß wie A4
    a3_width = PAGE_WIDTH * 2   # 420mm in Zoll
    a3_height = PAGE_HEIGHT  # 297mm in Zoll
    
    # Liste für die Pfade der erstellten PDFs
    pdf_paths = []
    
    # Hole den Home-Code aus der Konfiguration, falls vorhanden
    home_code = None
    if config and 'home' in config and config['home']:
        home_code = str(config['home']).strip()
    
    print(f"Home-Code in create_map_pages_for_professional_print: {home_code}")
    # Erstelle eine Seite für jede Gruppe von Kennzeichen
    for page in range(1, num_pages + 1):
        print(f"Erstelle Seite {page} von {num_pages}")
        
        # Bestimme die Kennzeichen für diese Seite
        start_idx = (page - 1) * CODES_PER_PAGE
        end_idx = min(start_idx + CODES_PER_PAGE, len(regular_codes))
        page_codes = regular_codes[start_idx:end_idx]
        
        # Definiere den Dateinamen für diese Seite
        pdf_path = os.path.join(OUTPUT_DIR, f"kfz_professional_print_seite_{page:02d}.pdf")
        pdf_paths.append(pdf_path)
        
        # Erstelle eine Figur im A3 Querformat mit blauem Hintergrund
        fig = plt.figure(figsize=(a3_width, a3_height), facecolor='#4a79a5')
        
        # Erstelle zwei Subplots nebeneinander (linke und rechte Seite) ohne Abstände
        gs = fig.add_gridspec(1, 2, width_ratios=[1, 1], wspace=0)
        
        # Linke Seite (wird später für die Checkliste verwendet)
        ax_left = fig.add_subplot(gs[0, 0])
        ax_left.set_facecolor('#4a79a5')  # Blauer Hintergrund
        ax_left.set_axis_off()
        ax_left.set_frame_on(False)
        ax_left.set_position([0, 0, 0.5, 1])  # Nutze die linke Hälfte der Figur vollständig
        
        # Rechte Seite (Karte)
        ax_right = fig.add_subplot(gs[0, 1])
        ax_right.set_position([0.5, 0, 0.5, 1])  # Nutze die rechte Hälfte der Figur vollständig
        
        # Erstelle die Karte auf der rechten Seite
        create_right_page_map(ax_right, gdf, page_codes, code_to_region, code_to_name, code_to_other_codes, home_code)
        
        # Speichere die Figur als PDF ohne jegliche Ränder
        # Verwende keine Anpassungen, die Ränder hinzufügen könnten
        fig.tight_layout(pad=0, h_pad=0, w_pad=0)
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)
        
        # Speichere exakt mit den Abmessungen der Figur, ohne jegliche Ränder
        fig.savefig(pdf_path, format='pdf', facecolor='#4a79a5', 
                   bbox_inches=None, pad_inches=0, dpi=300)
        plt.close(fig)
    
    print(f"Professionelle Drucklayouts gespeichert als: {', '.join(pdf_paths)}")
    # Keine Rückgabe notwendig

def create_map_pages_for_home_printer(gdf, regular_codes, code_to_region, code_to_name, code_to_state, code_to_other_codes, config=None):
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