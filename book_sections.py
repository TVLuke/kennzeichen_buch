def generate_license_section(config=None):
    """
    Generiert den LaTeX-Code für den Lizenzabschnitt des Sammelbuchs.
    
    Args:
        config (dict, optional): Konfigurationsdictionary mit Versionsinformation
    
    Returns:
        str: LaTeX-Code für den Lizenzabschnitt
    """
    license_content = ""
    license_content += r"\clearpage" + "\n"
    license_content += r"\section*{Lizenzinformationen}" + "\n"
    license_content += r"\begin{center}" + "\n"
    license_content += r"\begin{minipage}{0.8\textwidth}" + "\n"
    license_content += r"\vspace{1cm}" + "\n"
    
    license_content += r"\textbf{1. KfzKennzeichen-Repository}\\" + "\n"
    license_content += r"Quelle: \url{https://github.com/Octoate/KfzKennzeichen/}\\" + "\n"
    license_content += r"Lizenz: MIT Lizenz\\" + "\n"
    license_content += r"Copyright \copyright{} 2014 Tim Riemann\\[0.5cm]" + "\n"
    
    license_content += r"\textbf{2. Geodaten zu Kfz-Kennzeichen}\\" + "\n"
    license_content += r"Quelle: \url{https://mis.bkg.bund.de/trefferanzeige?docuuid=D7BCF56C-ECDF-4672-9C19-8C668C67E378}\\" + "\n"
    license_content += r"Lizenz: Datenlizenz Deutschland Namensnennung 2.0 (\url{https://www.govdata.de/dl-de/by-2-0})\\" + "\n"
    license_content += r"Herausgeber: Bundesamt für Kartographie und Geodäsie\\[0.5cm]" + "\n"
    
    license_content += r"\textbf{3. KfzKennzeichen  Liste von Berlin Open Data}\\" + "\n"
    license_content += r"Quelle: \url{https://www.govdata.de/suche/daten/kfz-kennzeichen-deutschland3785e}\\" + "\n"
    license_content += r"Lizenz: CC BY 4.0\\" + "\n"
    license_content += r"Herausgeber: Berlin Open Data (2016)\\[0.5cm]" + "\n"

    # Füge die Versionsinformation hinzu
    version_text = "Version 1.3.0 Aachen"
    if config and "version" in config:
        version_text = config["version"]
    
    license_content += r"Mein großes Kennzeichen Buch\\" + "\n"
    license_content += f"\\textbf{{{version_text}}}\\\\" + "\n"
    license_content += r"CC-BY-NC \url{https://creativecommons.org/licenses/by-nc/4.0/deed.de}\\Lukas Ruge" + str(2025) + "\\" + "\n"
    license_content += r"\vspace{1cm}" + "\n"
    license_content += r"\end{minipage}" + "\n"
    license_content += r"\end{center}" + "\n"
    
    return license_content