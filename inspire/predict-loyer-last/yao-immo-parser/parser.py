import re
from pathlib import Path
import pandas as pd

# ---------- 1. FONCTIONS D'EXTRACTION ----------

def extraire_prix(texte):
    """Extrait le prix mensuel en FCFA (entier)."""
    patterns = [
        r'(\d+(?:[.,]\d{3})?)\s*(?:f|FCFA|fcfa|mill[ea]|mil)\b',
        r'(\d+(?:[.,]\d{3})?)\s*(?:mill[ea]|mil)\b',
        r'(\d+(?:\s?\d{3})?)\s*FCFA\s*/mois',
    ]
    for pat in patterns:
        match = re.search(pat, texte)
        if match:
            prix_str = match.group(1).replace('.', '').replace(',', '').replace(' ', '')
            return int(prix_str)
    return None

def extraire_caution_mois(texte):
    """Extrait le nombre de mois de caution (ex: 6+2 -> 6)."""
    match = re.search(r'\(?(\d+)\s*\+\s*\d+\)?', texte)
    if match:
        return int(match.group(1))
    match = re.search(r'(\d+)\s*(?:mois|moi|m)\b', texte, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def extraire_quartier(texte):
    """Extrait le quartier."""
    patterns = [
        r'[#📍]?\s*(?:Localisation|Quartier|Lieu)\s*:?\s*([A-Za-zÀ-ÿ\s]+?)(?:\n|,|\.|$)',
        r'📍\s*([A-Za-zÀ-ÿ\s]+?)(?:\n|,|\.|$)',
        r'à\s+([A-Za-zÀ-ÿ\s]+?)(?:\n|,|\.|$)',
        r'quartier\s*:?\s*([A-Za-zÀ-ÿ\s]+?)(?:\n|,|\.|$)',
    ]
    for pat in patterns:
        match = re.search(pat, texte, re.IGNORECASE)
        if match:
            quartier = match.group(1).strip()
            quartier = re.sub(r'(?:carrefour|vers|proche|totalement|goudronnée?|\(.*?\))', '', quartier, flags=re.IGNORECASE)
            quartier = ' '.join(quartier.split())
            if len(quartier) > 2:
                return quartier
    lignes = [l.strip() for l in texte.split('\n') if l.strip()]
    if lignes:
        premier = lignes[0]
        if not re.search(r'(louer|chambre|studio|appartement|prix)', premier, re.IGNORECASE):
            return premier[:50]
    return None

def extraire_type_bien(texte):
    """chambre, studio, appartement."""
    texte_lower = texte.lower()
    if 'studio' in texte_lower:
        return 'studio'
    if 'appartement' in texte_lower or 'appart' in texte_lower:
        return 'appartement'
    if 'chambre' in texte_lower:
        return 'chambre'
    return 'inconnu'

def extraire_nombre(texte, mot_cle, max_val=10):
    """Extrait un entier associé à un mot-clé (ex: '3 chambres')."""
    pattern = r'(\d+)\s*' + mot_cle
    match = re.search(pattern, texte, re.IGNORECASE)
    if match:
        val = int(match.group(1))
        if val <= max_val:
            return val
    return None

def extraire_equipement(texte, mots_cles):
    """Retourne 1 si un des mots-clés est présent."""
    texte_lower = texte.lower()
    for mot in mots_cles:
        if mot in texte_lower:
            return 1
    return 0

def extraire_acces_moto(texte):
    """Extrait le prix de la moto."""
    pattern = r'(?:moto|accès\s*moto)\s*:?\s*(\d+)'
    match = re.search(pattern, texte, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def extraire_contact(texte):
    """Extrait un numéro de téléphone (9 chiffres ou plus)."""
    match = re.search(r'(\d{9,})', texte)
    if match:
        return match.group(1)
    return None

# ---------- 2. PARSER UNE ANNONCE ----------

def parser_annonce(texte_brut):
    """Prend le texte d'une annonce et retourne un dictionnaire."""
    texte = re.sub(r'[•●▪️]', ' ', texte_brut)
    texte = re.sub(r'\s+', ' ', texte)

    data = {}
    data['prix'] = extraire_prix(texte)
    data['caution_mois'] = extraire_caution_mois(texte)
    data['quartier'] = extraire_quartier(texte)
    data['type_bien'] = extraire_type_bien(texte)

    # Chambres : on accepte "chambre", "chambres", "pièces", "pièce"
    data['chambres'] = extraire_nombre(texte, r'chambres?|pièces?', 10)
    data['douches'] = extraire_nombre(texte, r'douches?|salle de bain', 10)
    data['salon'] = 1 if re.search(r'salon|séjour', texte, re.IGNORECASE) else 0
    data['cuisine'] = 1 if re.search(r'cuisine', texte, re.IGNORECASE) else 0
    data['parking'] = extraire_equipement(texte, ['parking'])
    data['gardien'] = extraire_equipement(texte, ['gardien', 'guardien'])
    data['forage'] = extraire_equipement(texte, ['forage'])
    data['eau_camwater'] = extraire_equipement(texte, ['camwater', 'eau camwater'])
    data['prepaye'] = extraire_equipement(texte, ['prépayé', 'prépaiement'])
    data['climatisation'] = extraire_equipement(texte, ['climatisation', 'clim'])
    data['eau_chaude'] = extraire_equipement(texte, ['eau chaude'])
    data['balcon'] = extraire_equipement(texte, ['balcon'])
    data['cloture'] = extraire_equipement(texte, ['barrière', 'cloture', 'dans la barrière'])
    data['acces_moto'] = extraire_acces_moto(texte)
    data['contact'] = extraire_contact(texte)

    return data

# ---------- 3. LECTURE DU FICHIER D'ANNONCES ----------

def lire_annonces_depuis_fichier(chemin):
    """Lit un fichier texte où les annonces sont séparées par '---' ou deux sauts de ligne."""
    with open(chemin, 'r', encoding='utf-8') as f:
        contenu = f.read()
    if '---' in contenu:
        annonces_brutes = contenu.split('---')
    else:
        annonces_brutes = re.split(r'\n\s*\n', contenu)
    return [a.strip() for a in annonces_brutes if a.strip()]

# ---------- 4. MAIN ----------

def main():
    input_file = Path(__file__).parent / "data" / "annonces_brutes.txt"
    output_file = Path(__file__).parent / "data" / "annonces_parsees.csv"

    if not input_file.exists():
        print(f"Erreur : fichier {input_file} introuvable.")
        return

    annonces_brutes = lire_annonces_depuis_fichier(input_file)
    print(f"Nombre d'annonces détectées : {len(annonces_brutes)}")

    resultats = []
    for i, annonce in enumerate(annonces_brutes, 1):
        print(f"Traitement annonce {i}...")
        data = parser_annonce(annonce)
        resultats.append(data)

    df = pd.DataFrame(resultats)
    colonnes_ordre = ['quartier', 'type_bien', 'prix', 'caution_mois', 'chambres', 'douches',
                      'salon', 'cuisine', 'parking', 'gardien', 'forage', 'eau_camwater',
                      'prepaye', 'climatisation', 'eau_chaude', 'balcon', 'cloture',
                      'acces_moto', 'contact']
    # On ne garde que les colonnes qui existent (certaines peuvent manquer si le DataFrame est vide)
    colonnes_existantes = [c for c in colonnes_ordre if c in df.columns]
    df = df[colonnes_existantes]

    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Fichier CSV généré : {output_file}")
    print("\nAperçu :")
    print(df.head())

if __name__ == "__main__":
    main()
