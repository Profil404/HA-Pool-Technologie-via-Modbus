import asyncio
import logging

from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)
_PROBE_INTERVAL = 5  # une tentative de reconnexion toutes les N cycles de poll ignorés

class PoolController:
    def __init__(self, hass, update_callback, scan_interval, handler):
        self._hass = hass
        self._update_callback = update_callback
        self._scan_interval = scan_interval
        self._remove_listener = None
        self._handler = handler
        self.modbus_ok = False
        self._modbus_fail_count = 0
        self._modbus_fail_threshold = 5
        self._probe_counter = 0
        self._poll_listeners = []

    @property
    def scan_interval(self):
        return self._scan_interval

    @property
    def handler(self):
        return self._handler

    def add_poll_listener(self, callback):
        """Enregistre un callback appelé après chaque cycle de poll réussi
        (piloté par le même timer que les capteurs, cf. update_sensors)."""
        self._poll_listeners.append(callback)

    def remove_poll_listener(self, callback):
        self._poll_listeners = [cb for cb in self._poll_listeners if cb is not callback]

    async def start(self):
        await self._hass.async_add_executor_job(self._handler.connect)
        self._start_polling()

    async def stop(self):
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None
        await self._hass.async_add_executor_job(self._handler.close)

    def _start_polling(self):
        if self._remove_listener:
            self._remove_listener()
        self._remove_listener = async_track_time_interval(
            self._hass, self._dispatch_update, timedelta(seconds=self._scan_interval)
        )

    async def _dispatch_update(self, now):
        """Indirection nécessaire : au moment où start() enregistre le timer
        (avant que les plateformes soient chargées), self._update_callback est
        encore le no-op passé par __init__.py. sensor.py le remplace ensuite
        par update_sensors, mais async_track_time_interval aurait figé pour
        toujours la référence passée en argument si on la lui avait donnée
        directement. En passant par cette méthode, on relit l'attribut à
        chaque déclenchement, donc le remplacement par sensor.py est bien pris
        en compte.
        """
        result = self._update_callback(now)
        if asyncio.iscoroutine(result):
            await result

    async def update_interval(self, new_interval):
        self._scan_interval = new_interval
        self._modbus_fail_count = 0
        self._probe_counter = 0
        self._start_polling()

    def notify_modbus_success(self):
        self._modbus_fail_count = 0
        self._probe_counter = 0
        self.modbus_ok = True

    def notify_modbus_failure(self):
        self._modbus_fail_count += 1
        if self._modbus_fail_count >= self._modbus_fail_threshold:
            self.modbus_ok = False

    def should_skip_poll(self) -> bool:
        """Retourne True si le poll doit être sauté car l'électrolyseur est déconnecté.

        Autorise quand même une tentative de reconnexion toutes les
        _PROBE_INTERVAL cycles, sinon la connexion ne se rétablirait jamais.
        """
        if self._modbus_fail_count < self._modbus_fail_threshold:
            return False
        self._probe_counter += 1
        if self._probe_counter >= _PROBE_INTERVAL:
            self._probe_counter = 0
            _LOGGER.debug("Modbus déconnecté — tentative de reconnexion")
            return False
        _LOGGER.debug(
            "Modbus déconnecté — poll ignoré (%d/%d avant nouvelle tentative)",
            self._probe_counter,
            _PROBE_INTERVAL,
        )
        return True
