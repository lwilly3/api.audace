# print(format_datetime("2025-01-01"))        # ➝ "2025-01-01T00:00:00"
# print(format_datetime("2025/01/01"))        # ➝ "2025-01-01T00:00:00"
# print(format_datetime("01/01/2025"))        # ➝ "2025-01-01T00:00:00"
# print(format_datetime("01-01-2025"))        # ➝ "2025-01-01T00:00:00"
# print(format_datetime("01 01 2025"))        # ➝ "2025-01-01T00:00:00"
# print(format_datetime("2025-01-01T15:30:45"))  # ➝ "2025-01-01T15:30:45"

# # Cas d'erreur : retourne la date du jour
# print(format_datetime("2025.01.01"))        # ❌ Format invalide → Retourne aujourd’hui
# print(format_datetime("01-13-2025"))        # ❌ Mois invalide → Retourne aujourd’hui
# print(format_datetime(""))                  # ❌ Chaîne vide → Retourne aujourd’hui



from datetime import datetime

def format_datetime(date_str: str) -> str:
    """
    Convertit une date en chaîne de caractères au format 'YYYY-MM-DDTHH:MM:SS'.
    En cas d'erreur, retourne la date du jour au format standardisé.

    Args:
        date_str (str): La date sous forme de chaîne à formater.

    Returns:
        str: La date formatée en 'YYYY-MM-DDTHH:MM:SS' ou la date du jour en cas d'erreur.
    """
    if not date_str:
        return datetime.now().strftime("%Y-%m-%dT00:00:00")

    # Liste des formats acceptés
    formats = [
        "%Y-%m-%dT%H:%M:%S",  # Format ISO complet
        "%Y-%m-%d",  # Format ISO court
        "%Y/%m/%d",  # Format avec "/"
        "%d/%m/%Y",  # Format français JJ/MM/AAAA
        "%d-%m-%Y",  # Format français avec "-"
        "%d %m %Y",  # Format français avec espace
    ]

    for fmt in formats:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime("%Y-%m-%dT%H:%M:%S")  # Format standardisé
        except ValueError:
            continue  # Essayer un autre format

    # Si aucun format ne correspond, on retourne la date du jour
    return datetime.now().strftime("%Y-%m-%dT00:00:00")





