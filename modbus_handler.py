from pymodbus.client import ModbusTcpClient 

class ModbusHandler:
    def __init__(self, host="192.168.1.100", port=502, unit_id=1, timeout=3):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.client = ModbusTcpClient(host=self.host, port=self.port, timeout=timeout)

    def read_register(self, address, count=1):
        try:
            self.client.connect()
            result = self.client.read_holding_registers(address=address, count=count, device_id=self.unit_id)
            if result.isError():
                return None
            return result.registers
        except Exception:
            return None
        finally:
            self.client.close()

    def write_register(self, address, value):
        try:
            self.client.connect()
            result = self.client.write_register(address=address, value=value, device_id=self.unit_id)
            return not result.isError()
        except Exception:
            return False
        finally:
            self.client.close()

    def write_registers(self, address, values):
        try:
            self.client.connect()
            result = self.client.write_registers(address=address, values=values, device_id=self.unit_id)
            return not result.isError()
        except Exception:
            return False
        finally:
            self.client.close()
