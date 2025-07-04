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