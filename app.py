import time
import libscrc
import eel

from serial.tools import list_ports

from digi.xbee.devices import ZigBeeDevice
from digi.xbee.models.status import NetworkDiscoveryStatus


eel.init('web')

# Global constants
PAN_ID = b'\x00\x00\x00\x00\x00\x00\x30\x06'

ALLOWED_FIRMWARE_LOCAL = [
    b'\x21\xA7'
]

NODOS = {
    'maquina1':'MAQUINA1'
}

READ_RESPONSE_TIME_OUT = 0.2


# Classes

class modbus_response:

    def __init__(self, address, command, bytes_number, data, data_int):
        self.address = address
        self.command = command
        self.bytes_number = bytes_number
        self.data = data
        self.data_int = data_int


# Callbacks

def callback_device_discovered(remote):
    """
    Callback for discovered devices.
    """
    print(f"Xbee descubierto: {remote}")

def callback_discovery_finished(status):
    """
    Callback for discovery finished.
    """
    if status == NetworkDiscoveryStatus.SUCCESS:
        print("Proceso de descubrimiento finalizado.")
    else:
        print(f"Error al descubrir la red: {status.description}")

def data_received_callback(xbee_message):
    """
    Function to execute when data is received
    
    Arguments:
        xbee_message: Xbee message object
    """
    address = xbee_message.remote_device.get_64bit_addr()
    data = xbee_message.data.hex()
    print(f"Received data from {address}: {data}")


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
    crc = libscrc.modbus(modbus_frame) #retorna un entero
    crc16 = crc.to_bytes(2, byteorder='little') # convertir el entero a bytes (less - most)
    return crc16 # objeto bytes

def create_modbus(address, command, reg_address, data_16):
    """
    address = b'\x01'
    command = b'\x06'
    reg_address = b'\x10\x00' (most - less)
    data_16 = b'\x00\xFF' (most - less)
    crc = b'\xCD\x4A'(less - most)
    """

    modbus_frame = address + command + reg_address + data_16
    modbus_frame += crc_modbus(modbus_frame)
    return modbus_frame

def read_modbus_response(response):
    
    if crc_modbus(response[:-2]) == response[-2:]:

        address = response[0].to_bytes(1, byteorder='big')
        command = response[1].to_bytes(1, byteorder='big')
        bytes_number = response[2]
        data = response[3:3+bytes_number]
        bytes_number = bytes_number.to_bytes(1, byteorder='big')
        data_int = int.from_bytes(data, 'big')

        return modbus_response(address, command, bytes_number, data, data_int)

    else:
        return None

def convert_temp_plc_units(temp):
    plc_units = temp * 2000 / 180
    plc_units = int(round(plc_units, 0))
    return plc_units

def convert_plc_units_temp(plc_units):
    temp = plc_units * 180 / 2000
    return temp

def set_lower_limit(temp, device, remote):

    plc_units = convert_temp_plc_units(temp)
    hex_lower_temp = plc_units.to_bytes(2, byteorder='big')

    modbus_lower_temp = create_modbus(
        address = b'\x01',
        command = b'\x06',
        reg_address = b'\x10\x01',
        data_16 = hex_lower_temp
    )

    device.send_data(remote, modbus_lower_temp)
    xbee_message_lower = device.read_data(READ_RESPONSE_TIME_OUT)

    if xbee_message_lower.data == modbus_lower_temp:
        return True
    
    return False

def set_upper_limit(temp, device, remote):

    plc_units = convert_temp_plc_units(temp)
    hex_upper_temp = plc_units.to_bytes(2, byteorder='big')

    modbus_upper_temp = create_modbus(
        address = b'\x01',
        command = b'\x06',
        reg_address = b'\x10\x00',
        data_16 = hex_upper_temp
    )

    device.send_data(remote, modbus_upper_temp)
    xbee_message_upper = device.read_data(READ_RESPONSE_TIME_OUT)

    if xbee_message_upper.data == modbus_upper_temp:
        return True
    
    return False

def set_gradient(temp, device, remote):

    plc_units = convert_temp_plc_units(temp)
    hex_gradient = plc_units.to_bytes(2, byteorder='big')

    modbus_gradient = create_modbus(
        address = b'\x01',
        command = b'\x06',
        reg_address = b'\x10\x02',
        data_16 = hex_gradient
    )

    device.send_data(remote, modbus_gradient)
    xbee_message_gradient = device.read_data(READ_RESPONSE_TIME_OUT)

    if xbee_message_gradient == modbus_gradient:
        return True
    
    return False

def iniciar_proceso(device, remote):
    hex_iniciar = b'\xFF\x00'
    modbus_iniciar = create_modbus(
        address = b'\x01',
        command = b'\x05',
        reg_address = b'\x08\x00',
        data_16 = hex_iniciar
    )
    device.send_data(remote, modbus_iniciar)

def detener_proceso(device, remote):
    hex_detener = b'\x00\x00'
    modbus_detener = create_modbus(
        address = b'\x01',
        command = b'\x05',
        reg_address = b'\x08\x00',
        data_16 = hex_detener
    )
    device.send_data(remote, modbus_detener)

def leer_temperatura_actual(device, remote):

    device.send_data(remote, create_modbus(
                address = b'\x01',
                command = b'\x03',
                reg_address = b'\x14\x57',
                data_16 = b'\x00\x01'
            ))

    xbee_message = device.read_data(READ_RESPONSE_TIME_OUT)
    modbus_res = read_modbus_response(xbee_message.data)
    temp = convert_plc_units_temp(modbus_res.data_int)
    return temp

@eel.expose
def getData():
    global device, xbee_maquina1

    value = leer_temperatura_actual(device, xbee_maquina1);
    return {"temperatura_actual":value}

@eel.expose
def iniciar(lower, upper, gradient):
    lower_flag = set_lower_limit(lower, device, xbee_maquina1)
    if lower_flag:
        upper_flag = set_upper_limit(upper, device, xbee_maquina1)
        if upper_flag:
            gradient_flag = set_gradient(gradient, device, xbee_maquina1)
            if gradient_flag:
                iniciar_proceso(device, xbee_maquina1)
                return {"message":"Proceso iniciado", "flag":True}
            else:
                return {"message":"Error escribiendo gradient", "flag":False}
        else:
            return {"message":"Error escribiendo upper_limit", "flag":False}
    else:
        return {"message":"Error escribiendo lower_limit", "flag":False}

@eel.expose
def terminar():
    detener_proceso(device, xbee_maquina1)
    return {"message":"Proceso finalizado"}



serial_port_list = [i.device for i in list_ports.comports()]

device = find_xbee_coordinator(serial_port_list)
#device.add_data_received_callback(data_received_callback)

if device:
    print(f'Se encontro un xbee coordinador con pan id: {device.get_pan_id().hex()}')

    xbee_network = find_xbee_network(device, callback_device_discovered, callback_discovery_finished)

    xbee_maquina1 = xbee_network.get_device_by_node_id(NODOS['maquina1'])

    eel.start('index.html', size=(800, 480))


else:
    print("No se encontro ningun xbee coordinador")