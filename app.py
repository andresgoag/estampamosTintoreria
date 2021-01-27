from serial.tools import list_ports

from digi.xbee.devices import ZigBeeDevice



# Global constants
PAN_ID = b'\x00\x00\x00\x00\x00\x00\x30\x06'

ALLOWED_FIRMWARE_LOCAL = [
    b'\x21\xA7'
]

NODOS = {
    'maquina1':'MAQUINA1'
}




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
    """
    if firmware in list_firmwares:
        return True

    return False


def find_xbee_coordinator(serial_port_list):

    """
    Finds a xbee coordinator, aand open its communication interface
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
    print("Device discovered: %s" % remote)

# Callback for discovery finished.
def callback_discovery_finished(status):
    if status == NetworkDiscoveryStatus.SUCCESS:
        print("Discovery process finished successfully.")
    else:
        print("There was an error discovering devices: %s" % status.description)

def find_xbee_network(device):

    xbee_network = device.get_network()
    xbee_network.set_discovery_timeout(5)
    xbee_network.clear()

    # Add callbacks
    xbee_network.add_device_discovered_callback(callback_device_discovered)
    xbee_network.add_discovery_process_finished_callback(callback_discovery_finished)

    #Start discovery
    xbee_network.start_discovery_process()

    print("Discovering remote XBee devices...")

    while xbee_network.is_discovery_running():
        time.sleep(0.2)

    return xbee_network









serial_port_list = [i.device for i in list_ports.comports()]

device = find_xbee_coordinator(serial_port_list)

if device:
    print(f'Se encontro un xbee coordinador con pan id: {device.get_pan_id().hex()}')

    xbee_network = find_xbee_network(device)


    xbee_maquina1 = xbee_network.get_device_by_node_id("MAQUINA1")


    #xbee_maquina1.read_device_info()


    print(xbee_maquina1.get_node_id())

else:
    print("No se encontro ningun xbee coordinador")
