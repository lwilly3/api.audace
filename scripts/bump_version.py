#!/usr/bin/env python3
"""
Script pour bumper (incrémenter) la version de l'API.

Usage:
    python scripts/bump_version.py [major|minor|patch] [--dry-run]
"""

import sys
import re
from pathlib import Path
from datetime import date

VERSION_FILE = Path(__file__).parent.parent / 'app' / '__version__.py'


def read_current_version():
    """Lit la version actuelle depuis __version__.py."""
    with open(VERSION_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'__version__\s*=\s*["\']([0-9]+\.[0-9]+\.[0-9]+)["\']', content)
    if not match:
        raise ValueError("Version non trouvée dans __version__.py")
    
    return match.group(1), content


def parse_version(version_str):
    """Parse une version X.Y.Z en tuple (X, Y, Z)."""
    parts = version_str.split('.')
    if len(parts) != 3:
        raise ValueError(f"Format de version invalide: {version_str}")
    
    return tuple(int(p) for p in parts)


def bump_version(current, bump_type):
    """
    Incrémente une version selon le type de bump.
    
    Args:
        current: Version actuelle (X, Y, Z)
        bump_type: 'major', 'minor', ou 'patch'
        
    Returns:
        tuple: Nouvelle version (X, Y, Z)
    """
    major, minor, patch = current
    
    if bump_type == 'major':
        return (major + 1, 0, 0)
    elif bump_type == 'minor':
        return (major, minor + 1, 0)
    elif bump_type == 'patch':
        return (major, minor, patch + 1)
    else:
        raise ValueError(f"Type de bump invalide: {bump_type}")


def format_version(version_tuple):
    """Formate un tuple de version en string X.Y.Z."""
    return '.'.join(str(v) for v in version_tuple)


def update_version_file(content, old_version, new_version, dry_run=False):
    """Met à jour le fichier __version__.py avec la nouvelle version."""
    # Remplacer la version
    new_content = re.sub(
        r'__version__\s*=\s*["\'][0-9]+\.[0-9]+\.[0-9]+["\']',
        f'__version__ = "{new_version}"',
        content
    )
    
    # Mettre à jour la date de release
    today = date.today().strftime('%Y-%m-%d')
    new_content = re.sub(
        r'"release_date":\s*"[0-9]{4}-[0-9]{2}-[0-9]{2}"',
        f'"release_date": "{today}"',
        new_content
    )
    
    if dry_run:
        print("\n[DRY RUN] Contenu qui serait écrit :")
        print("=" * 70)
        # Afficher seulement les lignes pertinentes
        for line in new_content.split('\n')[:20]:
            print(line)
        print("...")
        return
    
    with open(VERSION_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)


def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bumper la version de l\'API')
    parser.add_argument(
        'bump_type',
        choices=['major', 'minor', 'patch'],
        help='Type de bump: major (X.0.0), minor (X.Y.0), ou patch (X.Y.Z)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simule le bump sans modifier les fichiers'
    )
    
    args = parser.parse_args()
    
    print()
    print("=" * 70)
    print("BUMP DE VERSION")
    print("=" * 70)
    print()
    
    try:
        # Lire la version actuelle
        current_version_str, content = read_current_version()
        current_version = parse_version(current_version_str)
        
        print(f"Version actuelle : {current_version_str}")
        print(f"Type de bump     : {args.bump_type}")
        print()
        
        # Calculer la nouvelle version
        new_version = bump_version(current_version, args.bump_type)
        new_version_str = format_version(new_version)
        
        print(f"Nouvelle version : {new_version_str}")
        print()
        
        # Demander confirmation
        if not args.dry_run:
            response = input("Confirmer le bump ? (o/n) : ").strip().lower()
            if response not in ['o', 'oui', 'y', 'yes']:
                print("❌ Opération annulée")
                return
            print()
        
        # Mettre à jour le fichier
        update_version_file(content, current_version_str, new_version_str, args.dry_run)
        
        if args.dry_run:
            print("\n[DRY RUN] Aucun fichier modifié")
        else:
            print(f"✅ Version mise à jour : {current_version_str} → {new_version_str}")
        
        print()
        print("=" * 70)
        print("PROCHAINES ÉTAPES")
        print("=" * 70)
        print()
        print("1. Mettre à jour CHANGELOG.md :")
        print(f"   python scripts/add_changelog_entry.py")
        print()
        print("2. Committer les changements :")
        print(f"   git add app/__version__.py CHANGELOG.md")
        print(f"   git commit -m \"chore: bump version to {new_version_str}\"")
        print()
        print("3. Créer un tag Git :")
        print(f"   git tag -a v{new_version_str} -m \"Version {new_version_str}\"")
        print(f"   git push origin v{new_version_str}")
        print()
        
        if args.bump_type == 'major':
            print("⚠️  BREAKING CHANGE DETECTÉ !")
            print("   N'oubliez pas de :")
            print("   - Documenter les breaking changes dans VERSION_INFO")
            print("   - Mettre à jour la documentation")
            print("   - Communiquer aux utilisateurs")
            print()
        
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
