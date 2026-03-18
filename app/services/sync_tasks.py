"""
Gestionnaire de tâches de synchronisation en arrière-plan.

Stocke le statut des tâches dans un fichier JSON partagé sur le filesystem,
compatible multi-workers gunicorn (chaque worker est un processus séparé
mais partage le même filesystem).

Verrouillage via fcntl.flock pour éviter les race conditions.

Usage :
    task_id = sync_tasks.create()
    sync_tasks.update(task_id, progress="2/4 pages", percent=50)
    sync_tasks.complete(task_id, result={...})
"""

import uuid
import time
import json
import fcntl
import os
from typing import Optional

# Fichier partage entre tous les workers du meme container
_TASKS_FILE = "/tmp/sync_tasks.json"

# Durée de vie d'une tâche terminée (10 min)
_TTL = 600


def _read_tasks() -> dict[str, dict]:
    """Lire toutes les tâches depuis le fichier JSON."""
    if not os.path.exists(_TASKS_FILE):
        return {}
    try:
        with open(_TASKS_FILE, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            content = f.read()
            fcntl.flock(f, fcntl.LOCK_UN)
        if not content.strip():
            return {}
        return json.loads(content)
    except (json.JSONDecodeError, OSError):
        return {}


def _write_tasks(tasks: dict[str, dict]):
    """Écrire toutes les tâches dans le fichier JSON avec verrou exclusif."""
    try:
        with open(_TASKS_FILE, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            json.dump(tasks, f)
            f.flush()
            fcntl.flock(f, fcntl.LOCK_UN)
    except OSError:
        pass


def create(label: str = "sync") -> str:
    """Créer une nouvelle tâche et retourner son ID."""
    task_id = str(uuid.uuid4())[:8]
    tasks = _read_tasks()
    tasks[task_id] = {
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
    _write_tasks(tasks)
    return task_id


def update(task_id: str, progress: str = "", percent: int = 0):
    """Mettre à jour la progression d'une tâche."""
    tasks = _read_tasks()
    if task_id in tasks:
        tasks[task_id]["progress"] = progress
        tasks[task_id]["percent"] = min(percent, 99)
        tasks[task_id]["updated_at"] = time.time()
        _write_tasks(tasks)


def complete(task_id: str, result: dict):
    """Marquer une tâche comme terminée avec son résultat."""
    tasks = _read_tasks()
    if task_id in tasks:
        tasks[task_id]["status"] = "done"
        tasks[task_id]["progress"] = "Terminé"
        tasks[task_id]["percent"] = 100
        tasks[task_id]["result"] = result
        tasks[task_id]["updated_at"] = time.time()
        _write_tasks(tasks)


def fail(task_id: str, error: str):
    """Marquer une tâche comme échouée."""
    tasks = _read_tasks()
    if task_id in tasks:
        tasks[task_id]["status"] = "error"
        tasks[task_id]["progress"] = f"Erreur: {error}"
        tasks[task_id]["error"] = error
        tasks[task_id]["updated_at"] = time.time()
        _write_tasks(tasks)


def get(task_id: str) -> Optional[dict]:
    """Récupérer le statut d'une tâche."""
    tasks = _read_tasks()
    task = tasks.get(task_id)
    if task:
        return {**task}  # Copie
    return None


def cleanup():
    """Nettoyer les tâches terminées de plus de 10 minutes."""
    tasks = _read_tasks()
    now = time.time()
    expired = [
        tid for tid, t in tasks.items()
        if t["status"] in ("done", "error") and (now - t["updated_at"]) > _TTL
    ]
    if expired:
        for tid in expired:
            del tasks[tid]
        _write_tasks(tasks)
