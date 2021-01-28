import time
import libscrc

from serial.tools import list_ports

from digi.xbee.devices import ZigBeeDevice
from digi.xbee.models.status import NetworkDiscoveryStatus



# Global constants
PAN_ID = b'\x00\x00\x00\x00\x00\x00\x30\x06'

ALLOWED_FIRMWARE_LOCAL = [
    b'\x21\xA7'
]

NODOS = {
    'maquina1':'MAQUINA1'
}

MODBUS_WRITE = b'\x01\x06\x10\x00\x00\xFF\xCD\x4A'




# Funciones

def pan_id_check(bytes1, bytes2):
    """ 
    Checks if the byte objects sent are equal
    """

    if bytes1 == bytes2:
        return True

    return False

def firmware_check(firmware, list_firmwares):
    """
    Checks if the firmware is in list_firmwares

    Arguments:
        firmware: bytes object
        list_firmwares: list of allowed firmwares
    """
    if firmware in list_firmwares:
        return True

    return False


def find_xbee_coordinator(serial_port_list):

    """
    Finds a xbee coordinator, and open its communication interface

    Arguments: 
        serial_port_list: list of available serial ports
    """

    global PAN_ID, ALLOWED_FIRMWARE_LOCAL

    for port in serial_port_list:

        device = ZigBeeDevice(port, 9600)

        try:
            device.open()
            local_pan_id = device.get_pan_id()
            local_firmware = device.get_firmware_version()
            if pan_id_check(local_pan_id, PAN_ID) and firmware_check(local_firmware, ALLOWED_FIRMWARE_LOCAL):
                return device

        except:
            continue

    return None


# Callback for discovered devices.
def callback_device_discovered(remote):
    print(f"Xbee descubierto: {remote}")

# Callback for discovery finished.
def callback_discovery_finished(status):
    if status == NetworkDiscoveryStatus.SUCCESS:
        print("Proceso de descubrimiento finalizado.")
    else:
        print(f"Error al descubrir la red: {status.description}")


def find_xbee_network(device, callback_device_discovered, callback_discovery_finished):

    """
    Creates a thread searching for xbees on network

    Arguments:
        device: Local xbee object
        callback_device_discovered(remote_xbee_object): function to execute when a xbee is found
        callback_discovery_finished(network_discovery_status): function to execute when discovery process is finished
    """

    xbee_network = device.get_network()
    xbee_network.set_discovery_timeout(5)
    xbee_network.clear()

    # Add callbacks
    xbee_network.add_device_discovered_callback(callback_device_discovered)
    xbee_network.add_discovery_process_finished_callback(callback_discovery_finished)

    #Start discovery
    xbee_network.start_discovery_process()

    print("Descubriendo nodos...")

    while xbee_network.is_discovery_running():
        time.sleep(0.2)

    return xbee_network




def crc_modbus(modbus_frame):
    """
    Arguments:
        modbus_frame: bytes object
    """

    crc = libscrc.modbus(modbus_frame)
    print(crc.hex())
    crc16 = crc.to_bytes(2, byteorder='little')
    print(crc16.hex())




def create_modbus(address, command, reg_address, data_16):
    """
    address = b'\x01'
    command = b'\x06'
    reg_address = b'\x10\x00' (most - less)
    data_16 = b'\x00\xFF' (most - less)
    crc = b'\xCD\x4A'(less - most)
    """
    
    modbus_frame = address + command + reg_address + data_16











serial_port_list = [i.device for i in list_ports.comports()]

device = find_xbee_coordinator(serial_port_list)

if device:
    print(f'Se encontro un xbee coordinador con pan id: {device.get_pan_id().hex()}')

    xbee_network = find_xbee_network(device, callback_device_discovered, callback_discovery_finished)
    xbee_maquina1 = xbee_network.get_device_by_node_id(NODOS['maquina1'])

    device.send_data(xbee_maquina1, MODBUS_WRITE)


    address = b'\x01\x06\x10\x00\x00\xFF\xCD\x4A'

    crc_modbus(address)



else:
    print("No se encontro ningun xbee coordinador")
