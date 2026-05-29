"""
Orchestrateur de synchronisation Social.

Centralise les synchronisations Facebook lancees depuis l'UI, le callback OAuth
et le scheduler. Le but est d'eviter les synchronisations concurrentes, de
conserver un statut observable et de rendre les erreurs explicites pour le
frontend.
"""

import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.model_user_permissions import UserPermissions
from app.services import sync_tasks

logger = logging.getLogger("social-sync-orchestrator")

SYNC_STALE_SECONDS = 30 * 60
POLL_FAILURE_HINT = (
    "La tache de synchronisation est introuvable ou expiree. "
    "Verifiez l'etat des donnees puis relancez une synchronisation si necessaire."
)


@dataclass(frozen=True)
class SyncLaunch:
    """Resultat de lancement/reprise d'une synchronisation."""

    task_id: str
    status: str
    message: str
    reused: bool = False

    def as_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "message": self.message,
            "reused": self.reused,
        }


class SocialSyncVerifier:
    """Verifications de permission, statut et taches orphelines."""

    @staticmethod
    def require_manage_accounts(db: Session, user_id: int) -> None:
        perms = db.query(UserPermissions).filter(UserPermissions.user_id == user_id).first()
        if not perms or not perms.social_manage_accounts:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission 'social_manage_accounts' requise",
            )

    @staticmethod
    def is_stale(task: dict) -> bool:
        if task.get("status") != "running":
            return False
        updated_at = float(task.get("updated_at") or task.get("created_at") or 0)
        return (time.time() - updated_at) > SYNC_STALE_SECONDS

    @staticmethod
    def normalize_missing_task(task_id: str) -> dict:
        return {
            "id": task_id,
            "label": "unknown",
            "status": "error",
            "progress": POLL_FAILURE_HINT,
            "percent": 0,
            "result": None,
            "error": POLL_FAILURE_HINT,
        }


class SocialSyncAgent:
    """Agent de base pour executer une sync et publier la progression."""

    label = "sync"

    def run(self, session: Session, force: bool, progress: Callable[[str, int], None]) -> dict:
        raise NotImplementedError


class AccountSyncAgent(SocialSyncAgent):
    label = "sync-account"

    def __init__(self, account_id: int):
        self.account_id = account_id

    def run(self, session: Session, force: bool, progress: Callable[[str, int], None]) -> dict:
        from app.db.crud.crud_social import sync_facebook_account

        return sync_facebook_account(
            session,
            self.account_id,
            force=force,
            on_progress=progress,
        )


class AllAccountsSyncAgent(SocialSyncAgent):
    label = "sync-all"

    def run(self, session: Session, force: bool, progress: Callable[[str, int], None]) -> dict:
        from app.db.crud.crud_social import sync_all_facebook_accounts

        return sync_all_facebook_accounts(session, force=force, on_progress=progress)


class SchedulerSyncAgent(AllAccountsSyncAgent):
    label = "scheduler-sync"


class SocialSyncOrchestrator:
    """
    Coordonne les agents de sync.

    La protection anti-concurrence est volontairement in-process + statut partage
    via sync_tasks. Elle empeche les doubles clics, les onglets multiples et les
    declenchements manuels concurrents dans le meme conteneur. Un backend multi-
    conteneur devrait remplacer sync_tasks par une table DB ou Redis.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._active_task_id: Optional[str] = None
        self._active_scope: Optional[str] = None

    def get_current(self) -> Optional[dict]:
        if not self._active_task_id:
            running = sync_tasks.get_running()
            if not running:
                return None
            self._active_task_id = running["id"]
            self._active_scope = running.get("label")
        task = sync_tasks.get(self._active_task_id)
        if not task:
            self._clear_active()
            return None
        if SocialSyncVerifier.is_stale(task):
            sync_tasks.fail(task["id"], "Synchronisation interrompue ou sans progression.")
            self._clear_active()
            return sync_tasks.get(task["id"])
        if task.get("status") != "running":
            self._clear_active()
        return task

    def get_status(self, task_id: str) -> dict:
        task = sync_tasks.get(task_id)
        if not task:
            return SocialSyncVerifier.normalize_missing_task(task_id)
        if SocialSyncVerifier.is_stale(task):
            sync_tasks.fail(task_id, "Synchronisation interrompue ou sans progression.")
            task = sync_tasks.get(task_id) or SocialSyncVerifier.normalize_missing_task(task_id)
            self._clear_active_if(task_id)
        return task

    def start_account_sync(self, account_id: int, force: bool = False) -> SyncLaunch:
        return self._start(AccountSyncAgent(account_id), force, scope=f"account:{account_id}")

    def start_all_sync(self, force: bool = False) -> SyncLaunch:
        return self._start(AllAccountsSyncAgent(), force, scope="all")

    def start_scheduler_sync(self, force: bool = False) -> SyncLaunch:
        return self._start(SchedulerSyncAgent(), force, scope="scheduler")

    def run_scheduler_sync_blocking(self, force: bool = False) -> dict:
        """Utilise par la boucle scheduler pour garder son resultat historique."""
        launch = self.start_scheduler_sync(force)
        task_id = launch.task_id
        while True:
            task = self.get_status(task_id)
            if task["status"] != "running":
                if task["status"] == "done":
                    return task.get("result") or {}
                return {"error": task.get("error") or task.get("progress") or "Sync echouee"}
            time.sleep(2)

    def _start(self, agent: SocialSyncAgent, force: bool, scope: str) -> SyncLaunch:
        sync_tasks.cleanup()
        with self._lock:
            current = self.get_current()
            if current and current.get("status") == "running":
                return SyncLaunch(
                    task_id=current["id"],
                    status="running",
                    message="Une synchronisation est deja en cours.",
                    reused=True,
                )

            task_id = sync_tasks.create(label=agent.label)
            self._active_task_id = task_id
            self._active_scope = scope

            thread = threading.Thread(
                target=self._run_agent,
                args=(task_id, agent, force),
                daemon=True,
                name=f"social-sync-{agent.label}",
            )
            thread.start()

            return SyncLaunch(
                task_id=task_id,
                status="running",
                message="Synchronisation lancee en arriere-plan",
            )

    def _run_agent(self, task_id: str, agent: SocialSyncAgent, force: bool) -> None:
        session = SessionLocal()
        try:
            def progress(msg: str, pct: int) -> None:
                sync_tasks.update(task_id, progress=msg, percent=pct)

            result = agent.run(session, force, progress)
            sync_tasks.complete(task_id, result)
        except Exception as e:
            logger.exception("Synchronisation sociale echouee")
            sync_tasks.fail(task_id, str(e))
        finally:
            session.close()
            self._clear_active_if(task_id)

    def _clear_active_if(self, task_id: str) -> None:
        with self._lock:
            if self._active_task_id == task_id:
                self._active_task_id = None
                self._active_scope = None

    def _clear_active(self) -> None:
        with self._lock:
            self._active_task_id = None
            self._active_scope = None


social_sync_orchestrator = SocialSyncOrchestrator()
