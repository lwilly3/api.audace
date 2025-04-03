class GuestNotFoundException(Exception):
    """
    Exception levée lorsqu'un invité n'est pas trouvé dans la base de données.
    
    Attributes:
        guest_id (int): L'ID de l'invité recherché.
        message (str): Message d'erreur personnalisé.
    """
    def __init__(self, guest_id: int):
        self.guest_id = guest_id
        self.message = f"Invité avec l'ID {guest_id} non trouvé"
        super().__init__(self.message)


class DatabaseQueryException(Exception):
    """
    Exception levée en cas d'erreur lors d'une requête à la base de données.
    
    Attributes:
        message (str): Description de l'erreur rencontrée.
    """
    def __init__(self, message: str = "Erreur lors de l'exécution de la requête"):
        self.message = message
        super().__init__(self.message)