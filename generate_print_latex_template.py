def generate_latex_template(regular_codes, rare_codes, code_to_name, code_to_state, code_to_other_codes, gdf, code_to_region, code_to_name_multi=None, config=None, output_file="kfz_sammelbuch.tex"):
    """
    Generiert eine LaTeX-Vorlage für das Sammelbuch mit Kennzeichen zum Ankreuzen.
    """
    