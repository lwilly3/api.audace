#!/usr/bin/env python3
"""
Assistant interactif pour ajouter une entrée au CHANGELOG.

Ce script guide l'utilisateur pour créer une entrée de changelog
formatée correctement.

Usage:
    python scripts/add_changelog_entry.py
"""

from datetime import datetime
from pathlib import Path


TYPES = {
    '1': ('Ajouté', 'Nouvelles fonctionnalités'),
    '2': ('Modifié', 'Changements dans les fonctionnalités existantes'),
    '3': ('Déprécié', 'Fonctionnalités qui seront bientôt supprimées'),
    '4': ('Supprimé', 'Fonctionnalités supprimées'),
    '5': ('Corrigé', 'Corrections de bugs'),
    '6': ('Sécurité', 'Vulnérabilités corrigées'),
    '7': ('Base de données', 'Changements de schéma (migrations)'),
    '8': ('Documentation', 'Changements de documentation'),
}


def print_header():
    """Affiche l'en-tête du script."""
    print()
    print("=" * 70)
    print("ASSISTANT CHANGELOG")
    print("=" * 70)
    print()
    print("Cet assistant vous aide à ajouter une entrée au CHANGELOG.md")
    print()


def select_type():
    """Permet à l'utilisateur de sélectionner le type de changement."""
    print("Type de changement:")
    print()
    for key, (type_name, description) in TYPES.items():
        print(f"  {key}. {type_name} - {description}")
    print()
    
    while True:
        choice = input("Sélectionnez un type (1-8) : ").strip()
        if choice in TYPES:
            return TYPES[choice][0]
        print("❌ Choix invalide, réessayez.")


def get_description():
    """Demande la description du changement."""
    print()
    print("Description du changement:")
    print("(Soyez clair et concis. Appuyez sur Entrée deux fois pour terminer)")
    print()
    
    lines = []
    empty_count = 0
    
    while True:
        line = input()
        if not line.strip():
            empty_count += 1
            if empty_count >= 2 or (lines and empty_count >= 1):
                break
        else:
            empty_count = 0
            lines.append(line.strip())
    
    return '\n'.join(lines)


def format_entry(change_type, description):
    """Formate l'entrée du changelog."""
    # Indenter les lignes multiples
    lines = description.split('\n')
    formatted_lines = [f"- {lines[0]}"]
    for line in lines[1:]:
        formatted_lines.append(f"  {line}")
    
    return '\n'.join(formatted_lines)


def get_changelog_path():
    """Retourne le chemin vers CHANGELOG.md."""
    return Path(__file__).parent.parent / 'CHANGELOG.md'


def read_changelog():
    """Lit le contenu actuel du CHANGELOG."""
    changelog_path = get_changelog_path()
    if not changelog_path.exists():
        return ""
    
    with open(changelog_path, 'r', encoding='utf-8') as f:
        return f.read()


def insert_entry(content, change_type, entry):
    """Insère l'entrée dans le CHANGELOG dans la section [Non publié]."""
    lines = content.split('\n')
    
    # Trouver la section [Non publié]
    unpublished_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('## [Non publié]'):
            unpublished_idx = i
            break
    
    if unpublished_idx is None:
        print("❌ Section [Non publié] non trouvée dans CHANGELOG.md")
        return content
    
    # Trouver ou créer la section du type
    type_section = f"### {change_type}"
    type_idx = None
    
    for i in range(unpublished_idx + 1, len(lines)):
        if lines[i].strip().startswith('## '):
            # Nouvelle version trouvée, insérer avant
            break
        if lines[i].strip() == type_section:
            type_idx = i
            break
    
    if type_idx is None:
        # Créer la section du type après [Non publié]
        insert_pos = unpublished_idx + 1
        # Chercher la première ligne vide ou section existante
        for i in range(unpublished_idx + 1, len(lines)):
            if lines[i].strip().startswith('###') or lines[i].strip().startswith('##'):
                insert_pos = i
                break
            elif not lines[i].strip() and i > unpublished_idx + 1:
                insert_pos = i
                break
        
        lines.insert(insert_pos, '')
        lines.insert(insert_pos + 1, type_section)
        lines.insert(insert_pos + 2, entry)
        type_idx = insert_pos + 1
    else:
        # Ajouter l'entrée après la section existante
        insert_pos = type_idx + 1
        # Chercher la position après les entrées existantes
        while insert_pos < len(lines) and lines[insert_pos].strip().startswith(('-', ' ')):
            insert_pos += 1
        lines.insert(insert_pos, entry)
    
    return '\n'.join(lines)


def save_changelog(content):
    """Sauvegarde le CHANGELOG mis à jour."""
    changelog_path = get_changelog_path()
    with open(changelog_path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    """Point d'entrée principal."""
    print_header()
    
    # Sélection du type
    change_type = select_type()
    
    # Description
    description = get_description()
    
    if not description:
        print("❌ Aucune description fournie, abandon.")
        return
    
    # Formatage
    entry = format_entry(change_type, description)
    
    # Prévisualisation
    print()
    print("=" * 70)
    print("PRÉVISUALISATION")
    print("=" * 70)
    print()
    print(f"### {change_type}")
    print(entry)
    print()
    
    # Confirmation
    confirm = input("Ajouter cette entrée au CHANGELOG ? (o/n) : ").strip().lower()
    
    if confirm not in ['o', 'oui', 'y', 'yes']:
        print("❌ Opération annulée.")
        return
    
    # Lecture du CHANGELOG actuel
    content = read_changelog()
    
    if not content:
        print("❌ CHANGELOG.md non trouvé ou vide.")
        return
    
    # Insertion
    updated_content = insert_entry(content, change_type, entry)
    
    # Sauvegarde
    save_changelog(updated_content)
    
    print()
    print("=" * 70)
    print("✅ ENTRÉE AJOUTÉE AVEC SUCCÈS")
    print("=" * 70)
    print()
    print(f"L'entrée a été ajoutée dans la section '### {change_type}'")
    print(f"du CHANGELOG.md sous [Non publié].")
    print()
    print("N'oubliez pas de :")
    print("  1. Vérifier le CHANGELOG.md")
    print("  2. Committer les changements")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Opération annulée par l'utilisateur.")
    except Exception as e:
        print(f"\n\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
