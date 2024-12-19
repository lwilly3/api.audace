import os
import re

def update_pydantic_config(file_path):
    """
    Met à jour les classes utilisant `class Config` vers `model_config` avec `ConfigDict`.
    """
    with open(file_path, 'r') as file:
        content = file.read()

    # Recherche les classes avec "class Config" et remplace par "model_config"
    updated_content = re.sub(
        r'class Config:\n\s+from_attributes\s*=\s*True',
        r'model_config = ConfigDict(from_attributes=True)',
        content,
        flags=re.MULTILINE
    )

    # Si le fichier a été modifié, sauvegarde le résultat
    if updated_content != content:
        with open(file_path, 'w') as file:
            file.write(updated_content)
        print(f"Fichier mis à jour : {file_path}")
    else:
        print(f"Aucun changement nécessaire : {file_path}")


def update_project_files(project_directory):
    """
    Parcourt tous les fichiers `.py` dans le répertoire et applique la mise à jour.
    """
    for root, _, files in os.walk(project_directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                update_pydantic_config(file_path)


if __name__ == "__main__":
    # Remplacez par le chemin de votre projet
    project_directory = "/Users/happi/App/API/FASTAPI/app/schemas"
    update_project_files(project_directory)
