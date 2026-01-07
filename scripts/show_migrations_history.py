#!/usr/bin/env python3
"""
Script pour visualiser l'historique des migrations Alembic.

Ce script affiche toutes les migrations dans l'ordre chronologique
avec leurs informations (ID, date, description).

Usage:
    python scripts/show_migrations_history.py
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def parse_migration_file(file_path):
    """
    Parse un fichier de migration Alembic pour extraire les informations.
    
    Returns:
        dict: Informations de la migration (revision, date, description, down_revision)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    info = {
        'file': file_path.name,
        'revision': None,
        'down_revision': None,
        'date': None,
        'description': None
    }
    
    # Extraire les informations du header
    for line in content.split('\n'):
        if line.startswith('"""') or line.startswith("'''"):
            # Description (première ligne du docstring)
            if info['description'] is None:
                info['description'] = line.strip('"\' ')
        elif line.startswith('Revision ID:'):
            info['revision'] = line.split(':', 1)[1].strip()
        elif line.startswith('Revises:'):
            info['down_revision'] = line.split(':', 1)[1].strip()
        elif line.startswith('Create Date:'):
            date_str = line.split(':', 1)[1].strip()
            try:
                info['date'] = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                info['date'] = date_str
    
    return info


def get_all_migrations():
    """
    Récupère toutes les migrations Alembic.
    
    Returns:
        list: Liste des migrations triées par date
    """
    migrations_dir = Path(__file__).parent.parent / 'alembic' / 'versions'
    
    if not migrations_dir.exists():
        print(f"❌ Répertoire des migrations non trouvé: {migrations_dir}")
        return []
    
    migrations = []
    
    for file_path in migrations_dir.glob('*.py'):
        if file_path.name == '__init__.py':
            continue
        
        try:
            info = parse_migration_file(file_path)
            migrations.append(info)
        except Exception as e:
            print(f"⚠️  Erreur lors du parsing de {file_path.name}: {e}")
    
    # Trier par date
    migrations.sort(key=lambda x: x['date'] if isinstance(x['date'], datetime) else datetime.min)
    
    return migrations


def display_migrations_history():
    """Affiche l'historique complet des migrations."""
    migrations = get_all_migrations()
    
    if not migrations:
        print("Aucune migration trouvée.")
        return
    
    print()
    print("=" * 80)
    print("HISTORIQUE DES MIGRATIONS ALEMBIC")
    print("=" * 80)
    print()
    print(f"Total: {len(migrations)} migration(s)")
    print()
    
    for i, migration in enumerate(migrations, 1):
        print(f"{i}. {migration['description']}")
        print(f"   Revision ID: {migration['revision']}")
        print(f"   Parent: {migration['down_revision']}")
        
        if isinstance(migration['date'], datetime):
            print(f"   Date: {migration['date'].strftime('%d/%m/%Y %H:%M:%S')}")
        else:
            print(f"   Date: {migration['date']}")
        
        print(f"   Fichier: {migration['file']}")
        print()
    
    print("=" * 80)


def generate_changelog_entry():
    """Génère une entrée de changelog pour la dernière migration."""
    migrations = get_all_migrations()
    
    if not migrations:
        print("Aucune migration trouvée.")
        return
    
    latest = migrations[-1]
    
    print()
    print("=" * 80)
    print("ENTRÉE CHANGELOG POUR LA DERNIÈRE MIGRATION")
    print("=" * 80)
    print()
    print("### Base de données")
    print(f"- Migration `{latest['revision'][:8]}` : {latest['description']}")
    
    if isinstance(latest['date'], datetime):
        print(f"  - Date: {latest['date'].strftime('%d/%m/%Y')}")
    
    print()
    print("Copiez cette entrée dans CHANGELOG.md dans la section appropriée.")
    print()


def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualiser l\'historique des migrations Alembic')
    parser.add_argument(
        '--changelog',
        action='store_true',
        help='Générer une entrée de changelog pour la dernière migration'
    )
    
    args = parser.parse_args()
    
    if args.changelog:
        generate_changelog_entry()
    else:
        display_migrations_history()


if __name__ == "__main__":
    main()
