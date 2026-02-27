"""
Gestionnaire de tâches de synchronisation en arrière-plan.

Utilise un dictionnaire en mémoire pour stocker le statut des tâches.
Les tâches sont nettoyées automatiquement après 10 minutes.

Usage :
    task_id = sync_tasks.create()
    sync_tasks.update(task_id, progress="2/4 pages", percent=50)
    sync_tasks.complete(task_id, result={...})
"""

import uuid
import time
import threading
from typing import Optional

_tasks: dict[str, dict] = {}
_lock = threading.Lock()

# Durée de vie d'une tâche terminée (10 min)
_TTL = 600


def create(label: str = "sync") -> str:
    """Créer une nouvelle tâche et retourner son ID."""
    task_id = str(uuid.uuid4())[:8]
    with _lock:
        _tasks[task_id] = {
            "id": task_id,
            "label": label,
            "status": "running",
            "progress": "Démarrage...",
            "percent": 0,
            "result": None,
            "error": None,
            "created_at": time.time(),
            "updated_at": time.time(),
        }
    return task_id


def update(task_id: str, progress: str = "", percent: int = 0):
    """Mettre à jour la progression d'une tâche."""
    with _lock:
        if task_id in _tasks:
            _tasks[task_id]["progress"] = progress
            _tasks[task_id]["percent"] = min(percent, 99)
            _tasks[task_id]["updated_at"] = time.time()


def complete(task_id: str, result: dict):
    """Marquer une tâche comme terminée avec son résultat."""
    with _lock:
        if task_id in _tasks:
            _tasks[task_id]["status"] = "done"
            _tasks[task_id]["progress"] = "Terminé"
            _tasks[task_id]["percent"] = 100
            _tasks[task_id]["result"] = result
            _tasks[task_id]["updated_at"] = time.time()


def fail(task_id: str, error: str):
    """Marquer une tâche comme échouée."""
    with _lock:
        if task_id in _tasks:
            _tasks[task_id]["status"] = "error"
            _tasks[task_id]["progress"] = f"Erreur: {error}"
            _tasks[task_id]["error"] = error
            _tasks[task_id]["updated_at"] = time.time()


def get(task_id: str) -> Optional[dict]:
    """Récupérer le statut d'une tâche."""
    with _lock:
        task = _tasks.get(task_id)
        if task:
            return {**task}  # Copie
    return None


def cleanup():
    """Nettoyer les tâches terminées de plus de 10 minutes."""
    now = time.time()
    with _lock:
        expired = [
            tid for tid, t in _tasks.items()
            if t["status"] in ("done", "error") and (now - t["updated_at"]) > _TTL
        ]
        for tid in expired:
            del _tasks[tid]
