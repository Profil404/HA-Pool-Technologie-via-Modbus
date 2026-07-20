import logging
import threading

from pymodbus.client import ModbusTcpClient

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

    def read_register(self, address, count=1):
        with self._lock:
            try:
                self._ensure_connected()
                result = self._client.read_holding_registers(
                    address=address, count=count, device_id=self.unit_id
                )
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
                self._ensure_connected()
                result = self._client.write_register(
                    address=address, value=value, device_id=self.unit_id
                )
                return not result.isError()
            except Exception as err:
                _LOGGER.debug("Modbus write exception at %s: %s", address, err)
                return False

    def write_registers(self, address, values):
        with self._lock:
            try:
                self._ensure_connected()
                result = self._client.write_registers(
                    address=address, values=values, device_id=self.unit_id
                )
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
