#!/usr/bin/env python3
"""
Script pour archiver automatiquement les anciennes versions du CHANGELOG.

Ce script vérifie la taille du CHANGELOG.md et archive automatiquement
les versions par année si le fichier dépasse 300 lignes.

Usage:
    python scripts/archive_changelog.py [--dry-run]
"""

import re
import sys
from pathlib import Path
from datetime import datetime


CHANGELOG_PATH = Path(__file__).parent.parent / 'CHANGELOG.md'
ARCHIVE_DIR = Path(__file__).parent.parent / 'docs' / 'changelog'
MAX_LINES = 300


def count_lines(file_path):
    """Compte le nombre de lignes dans un fichier."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return len(f.readlines())


def read_changelog():
    """Lit le contenu du CHANGELOG."""
    with open(CHANGELOG_PATH, 'r', encoding='utf-8') as f:
        return f.read()


def extract_versions_by_year(content):
    """
    Extrait les versions du changelog groupées par année.
    
    Returns:
        dict: {year: [version_content]}
    """
    versions_by_year = {}
    
    # Pattern pour détecter les versions : ## [X.Y.Z] - YYYY-MM-DD
    version_pattern = r'^## \[(\d+\.\d+\.\d+)\] - (\d{4})-(\d{2})-(\d{2})'
    
    lines = content.split('\n')
    current_version = None
    current_year = None
    current_content = []
    
    # Trouver où commencent les versions (après [Non publié])
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip() == '---' and i > 50:  # Après la section [Non publié]
            start_idx = i + 1
            break
    
    if start_idx is None:
        return {}
    
    for i in range(start_idx, len(lines)):
        line = lines[i]
        match = re.match(version_pattern, line)
        
        if match:
            # Sauvegarder la version précédente
            if current_version and current_year:
                if current_year not in versions_by_year:
                    versions_by_year[current_year] = []
                versions_by_year[current_year].append('\n'.join(current_content))
            
            # Nouvelle version
            current_version = match.group(1)
            current_year = match.group(2)
            current_content = [line]
        elif current_version:
            current_content.append(line)
    
    # Sauvegarder la dernière version
    if current_version and current_year:
        if current_year not in versions_by_year:
            versions_by_year[current_year] = []
        versions_by_year[current_year].append('\n'.join(current_content))
    
    return versions_by_year


def create_archive(year, versions, dry_run=False):
    """
    Crée ou met à jour un fichier d'archive pour une année.
    
    Args:
        year: L'année à archiver
        versions: Liste des contenus de versions pour cette année
        dry_run: Si True, n'écrit pas les fichiers
    """
    archive_path = ARCHIVE_DIR / f'CHANGELOG-{year}.md'
    
    header = f"""# Changelog {year}

Archive des versions publiées en {year}.

Retour au [CHANGELOG principal](../../CHANGELOG.md)

---

"""
    
    content = header + '\n\n'.join(versions)
    content += f'\n\n---\n\n_Archive créée le {datetime.now().strftime("%d %B %Y")}_\n'
    
    if dry_run:
        print(f"  [DRY RUN] Créerait/mettrait à jour : {archive_path}")
        return
    
    # Créer le répertoire si nécessaire
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(archive_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ Archive créée/mise à jour : {archive_path}")


def update_main_changelog(content, archived_years, dry_run=False):
    """
    Met à jour le CHANGELOG principal pour supprimer les versions archivées
    et ajouter les liens vers les archives.
    
    Args:
        content: Contenu actuel du CHANGELOG
        archived_years: Liste des années archivées
        dry_run: Si True, n'écrit pas le fichier
    """
    lines = content.split('\n')
    
    # Trouver la section archives
    archives_section_idx = None
    for i, line in enumerate(lines):
        if '## 📚 Archives des versions précédentes' in line:
            archives_section_idx = i
            break
    
    # Extraire la partie avant les versions archivées
    if archives_section_idx:
        # Garder jusqu'à la fin de la section [Non publié]
        new_lines = []
        in_unpublished = False
        unpublished_ended = False
        
        for i, line in enumerate(lines):
            if '## [Non publié]' in line:
                in_unpublished = True
            elif in_unpublished and line.strip().startswith('## ') and '[' not in line:
                unpublished_ended = True
            
            if not unpublished_ended or i < archives_section_idx + 10:
                new_lines.append(line)
            elif line.strip().startswith('## Format des entrées'):
                # Garder la section de format
                new_lines.extend(lines[i:])
                break
        
        content = '\n'.join(new_lines)
    else:
        # Ajouter la section archives après [Non publié]
        # Trouver la fin de [Non publié]
        pattern = r'^## \[(\d+\.\d+\.\d+)\]'
        first_version_idx = None
        
        for i, line in enumerate(lines):
            if re.match(pattern, line):
                first_version_idx = i
                break
        
        if first_version_idx:
            # Créer la section archives
            archives_section = [
                '',
                '## 📚 Archives des versions précédentes',
                ''
            ]
            
            for year in sorted(archived_years, reverse=True):
                archives_section.append(f'- [{year}](docs/changelog/CHANGELOG-{year}.md) - Versions de {year}')
            
            archives_section.append('')
            archives_section.append('---')
            
            # Insérer avant la première version
            new_lines = lines[:first_version_idx] + archives_section
            
            # Garder la section Format des entrées si elle existe
            for i in range(first_version_idx, len(lines)):
                if lines[i].strip().startswith('## Format des entrées'):
                    new_lines.extend(lines[i:])
                    break
            
            content = '\n'.join(new_lines)
    
    if dry_run:
        print(f"  [DRY RUN] Mettrait à jour : {CHANGELOG_PATH}")
        return
    
    with open(CHANGELOG_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ CHANGELOG principal mis à jour")


def archive_old_versions(dry_run=False):
    """
    Archive les anciennes versions si le CHANGELOG dépasse MAX_LINES.
    
    Args:
        dry_run: Si True, simule les actions sans les effectuer
    """
    print()
    print("=" * 70)
    print("ARCHIVAGE DU CHANGELOG")
    print("=" * 70)
    print()
    
    # Compter les lignes
    line_count = count_lines(CHANGELOG_PATH)
    print(f"Nombre de lignes actuel : {line_count}/{MAX_LINES}")
    print()
    
    if line_count <= MAX_LINES:
        print("✅ Le CHANGELOG est sous la limite. Aucun archivage nécessaire.")
        return
    
    print(f"⚠️  Le CHANGELOG dépasse {MAX_LINES} lignes. Archivage en cours...")
    print()
    
    # Lire le contenu
    content = read_changelog()
    
    # Extraire les versions par année
    versions_by_year = extract_versions_by_year(content)
    
    if not versions_by_year:
        print("❌ Aucune version trouvée à archiver.")
        return
    
    print(f"Versions trouvées par année :")
    for year, versions in sorted(versions_by_year.items()):
        print(f"  - {year} : {len(versions)} version(s)")
    print()
    
    # Archiver toutes les années sauf l'année en cours
    current_year = str(datetime.now().year)
    archived_years = []
    
    for year, versions in sorted(versions_by_year.items()):
        if year != current_year:
            print(f"Archivage de {year}...")
            create_archive(year, versions, dry_run)
            archived_years.append(year)
    
    if archived_years:
        print()
        print("Mise à jour du CHANGELOG principal...")
        update_main_changelog(content, archived_years, dry_run)
    
    print()
    print("=" * 70)
    if dry_run:
        print("✅ SIMULATION TERMINÉE (utilisez sans --dry-run pour appliquer)")
    else:
        print("✅ ARCHIVAGE TERMINÉ")
    print("=" * 70)
    print()


def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Archive automatiquement les anciennes versions du CHANGELOG'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simule les actions sans les effectuer'
    )
    
    args = parser.parse_args()
    
    try:
        archive_old_versions(dry_run=args.dry_run)
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
