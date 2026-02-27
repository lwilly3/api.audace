"""
Planificateur périodique pour le module Social.

Tâches :
- Auto-sync : synchronise tous les comptes Facebook à intervalle régulier
- Auto-optimize : nettoie la BDD (orphelins, purge soft-deleted) à intervalle régulier

Configuration stockée en mémoire avec persistance via les endpoints REST.
Le scheduler est démarré au lancement de l'app et s'arrête proprement au shutdown.

Usage :
    from app.services.social_scheduler import scheduler
    scheduler.start()    # dans lifespan startup
    scheduler.stop()     # dans lifespan shutdown
"""

import threading
import time
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("social-scheduler")


# ────────────────────────────────────────────────────────────────
# Configuration par défaut
# ────────────────────────────────────────────────────────────────

DEFAULT_SETTINGS = {
    # Auto-sync
    "auto_sync_enabled": False,
    "auto_sync_interval_minutes": 30,   # toutes les 30 min par défaut
    "auto_sync_force": False,           # ne pas forcer les métriques

    # Auto-optimize (nettoyage BDD)
    "auto_optimize_enabled": False,
    "auto_optimize_interval_hours": 24, # toutes les 24h par défaut
    "auto_optimize_purge_days": 30,     # purger les éléments > 30 jours
}


class SocialScheduler:
    """Planificateur de tâches périodiques pour le module Social."""

    def __init__(self):
        self._settings: dict = {**DEFAULT_SETTINGS}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Timestamps de dernière exécution
        self._last_sync: Optional[str] = None
        self._last_optimize: Optional[str] = None
        self._last_sync_result: Optional[dict] = None
        self._last_optimize_result: Optional[dict] = None

    # ── Settings ────────────────────────

    def get_settings(self) -> dict:
        """Retourner les paramètres courants + statut."""
        with self._lock:
            return {
                **self._settings,
                "scheduler_running": self._running,
                "last_sync_at": self._last_sync,
                "last_optimize_at": self._last_optimize,
                "last_sync_result": self._last_sync_result,
                "last_optimize_result": self._last_optimize_result,
            }

    def update_settings(self, new_settings: dict) -> dict:
        """Mettre à jour les paramètres. Redémarre le scheduler si nécessaire."""
        with self._lock:
            for key, value in new_settings.items():
                if key in self._settings:
                    self._settings[key] = value

        # Redémarrer le scheduler si actif pour prendre en compte les nouveaux intervalles
        if self._running:
            self._restart()

        return self.get_settings()

    # ── Lifecycle ───────────────────────

    def start(self):
        """Démarrer le scheduler en arrière-plan."""
        if self._running:
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="social-scheduler")
        self._thread.start()
        logger.info("🟢 Social scheduler démarré")

    def stop(self):
        """Arrêter le scheduler proprement."""
        self._running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info("🔴 Social scheduler arrêté")

    def _restart(self):
        """Redémarrer le scheduler (changement de config)."""
        self.stop()
        self.start()

    # ── Main loop ───────────────────────

    def _loop(self):
        """Boucle principale du scheduler. Vérifie toutes les 30 secondes."""
        last_sync_time = 0.0
        last_optimize_time = 0.0

        while not self._stop_event.is_set():
            now = time.time()

            with self._lock:
                sync_enabled = self._settings["auto_sync_enabled"]
                sync_interval = self._settings["auto_sync_interval_minutes"] * 60
                sync_force = self._settings["auto_sync_force"]
                opt_enabled = self._settings["auto_optimize_enabled"]
                opt_interval = self._settings["auto_optimize_interval_hours"] * 3600
                opt_purge_days = self._settings["auto_optimize_purge_days"]

            # Auto-sync
            if sync_enabled and (now - last_sync_time) >= sync_interval:
                self._run_sync(sync_force)
                last_sync_time = now

            # Auto-optimize
            if opt_enabled and (now - last_optimize_time) >= opt_interval:
                self._run_optimize(opt_purge_days)
                last_optimize_time = now

            # Dormir 30 secondes entre chaque vérification
            self._stop_event.wait(timeout=30)

    # ── Tâches ──────────────────────────

    def _run_sync(self, force: bool):
        """Exécuter la synchronisation de tous les comptes Facebook."""
        from app.db.database import SessionLocal
        from app.db.crud.crud_social import sync_all_facebook_accounts

        logger.info("⏰ Auto-sync démarrée...")
        session = SessionLocal()
        try:
            result = sync_all_facebook_accounts(session, force=force)
            with self._lock:
                self._last_sync = datetime.now(timezone.utc).isoformat()
                self._last_sync_result = result
            logger.info(f"✅ Auto-sync terminée: {result}")
        except Exception as e:
            logger.error(f"❌ Auto-sync échouée: {e}")
            with self._lock:
                self._last_sync = datetime.now(timezone.utc).isoformat()
                self._last_sync_result = {"error": str(e)}
        finally:
            session.close()

    def _run_optimize(self, purge_days: int):
        """Exécuter le nettoyage/optimisation de la BDD."""
        from app.db.database import SessionLocal
        from app.db.crud.crud_social import cleanup_database

        logger.info(f"⏰ Auto-optimize démarrée (purge_days={purge_days})...")
        session = SessionLocal()
        try:
            result = cleanup_database(session, purge_days)
            with self._lock:
                self._last_optimize = datetime.now(timezone.utc).isoformat()
                self._last_optimize_result = result
            logger.info(f"✅ Auto-optimize terminée: {result}")
        except Exception as e:
            logger.error(f"❌ Auto-optimize échouée: {e}")
            with self._lock:
                self._last_optimize = datetime.now(timezone.utc).isoformat()
                self._last_optimize_result = {"error": str(e)}
        finally:
            session.close()


# Singleton global
scheduler = SocialScheduler()
