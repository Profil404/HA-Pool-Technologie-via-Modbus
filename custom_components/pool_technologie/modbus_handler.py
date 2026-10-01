import logging
import threading

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

_LOGGER = logging.getLogger(__name__)


class ModbusHandler:
    """Wraps a persistent Modbus TCP connection to the Pool Technologie device.

    pymodbus's ModbusTcpClient is synchronous. Every method here is blocking
    and must be called from an executor thread (hass.async_add_executor_job),
    never directly from the HA event loop. The connection is kept open
    between calls instead of reconnecting every time, and a lock serializes
    access since sensor/number entities share the same handler instance.
    """

    def __init__(self, host="192.168.1.100", port=502, unit_id=1, timeout=3):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self._client = ModbusTcpClient(host=self.host, port=self.port, timeout=timeout)
        self._lock = threading.Lock()

    def connect(self):
        """Open the persistent connection. Safe to call repeatedly/on startup."""
        with self._lock:
            self._ensure_connected()

    def close(self):
        with self._lock:
            self._client.close()

    def _ensure_connected(self):
        if not self._client.connected:
            self._client.connect()

    def _execute(self, method, address, **kwargs):
        """Exécute une requête Modbus, avec une reconnexion + un nouvel essai si
        le socket s'avère mort. À appeler avec self._lock déjà pris.

        pymodbus ne détecte pas lui-même une connexion coupée côté appareil
        (ConnectionResetError après un RST TCP, typiquement une passerelle
        Modbus TCP qui ferme les sessions inactives ou trop longues) :
        client.connected se contente de vérifier que l'objet socket existe, et
        reste donc à True sur un socket mort. Sans fermeture explicite, toutes
        les requêtes suivantes échouent sans jamais tenter de reconnexion.

        Le nouvel essai n'a lieu que si une connexion était déjà établie avant
        l'appel (socket périmé). Si l'appareil est simplement éteint (coupure
        de pompe la nuit), la connexion échoue d'emblée et on n'insiste pas :
        pas de double timeout par lecture, le backoff du controller s'applique.
        """
        for attempt in (1, 2):
            was_connected = self._client.connected
            try:
                self._ensure_connected()
                return getattr(self._client, method)(
                    address=address, device_id=self.unit_id, **kwargs
                )
            except (OSError, ModbusException) as err:
                # Socket dans un état inconnu (réponse partielle, RST, timeout) :
                # on repart toujours d'une connexion propre.
                self._client.close()
                if attempt == 2 or not was_connected:
                    raise
                _LOGGER.debug(
                    "Connexion Modbus perdue (adresse %s) : %s — reconnexion et nouvel essai",
                    address,
                    err,
                )

    def read_register(self, address, count=1):
        with self._lock:
            try:
                result = self._execute("read_holding_registers", address, count=count)
                if result.isError():
                    _LOGGER.debug("Modbus read error at %s: %s", address, result)
                    return None
                return result.registers
            except Exception as err:
                _LOGGER.debug("Modbus read exception at %s: %s", address, err)
                return None

    def write_register(self, address, value):
        with self._lock:
            try:
                result = self._execute("write_register", address, value=value)
                return not result.isError()
            except Exception as err:
                _LOGGER.debug("Modbus write exception at %s: %s", address, err)
                return False

    def write_registers(self, address, values):
        with self._lock:
            try:
                result = self._execute("write_registers", address, values=values)
                return not result.isError()
            except Exception as err:
                _LOGGER.debug("Modbus write exception at %s: %s", address, err)
                return False

    def read_register_verified(self, address, expected_value, count=1, tolerance=0):
        """Read a register back after a write to confirm it was actually applied.

        Runs as a separate locked operation from the write itself (not nested),
        so call it after write_register/write_registers, with a short delay
        if the device needs time to process the write.
        """
        result = self.read_register(address, count=count)
        if result is None:
            return False
        return abs(result[0] - expected_value) <= tolerance
