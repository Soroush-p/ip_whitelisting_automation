import re
from netmiko import ConnectHandler
import ipaddress


def extract_ip_addresses(text):
    #ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    ipv4_pattern = r'(?<=\s)([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\b'
    ip_addresses = re.findall(ipv4_pattern, text)
    if not ip_addresses:
        return text
    else:
        return ip_addresses   
    

def convert_to_cidr(ip_subnet_list):
    """
    Converts a list of IP addresses and subnet masks to CIDR notation.
    
    Args:
        ip_subnet_list (list): List where odd-indexed items are IP addresses and even-indexed items are subnet masks.
        
    Returns:
        list: List of IP addresses in CIDR notation.
    """
    # Check if the list length is even
    if len(ip_subnet_list) % 2 != 0:
        raise ValueError("List length should be even, with pairs of IP addresses and subnet masks.")

    cidr_list = []
    for i in range(0, len(ip_subnet_list), 2):
        ip = ip_subnet_list[i]
        subnet_mask = ip_subnet_list[i+1]
        try:
            # Create an IPv4Network object from the IP address and subnet mask
            network = ipaddress.IPv4Network(f'{ip}/{subnet_mask}', strict=False)
            # Append the IP address in CIDR notation to the result list
            cidr_list.append(str(network))
        except ValueError as e:
            print(f"Invalid IP/subnet mask combination: {ip}/{subnet_mask} - {e}")

    return cidr_list

def get_network_objects(device, context):
    """
    Connects to a FortiGate device and retrieves network object configurations.
    
    Args:
        device (dict): Dictionary containing device connection details.
        
    Returns:
        str: Network object configurations from the FortiGate.
    """
    try:
        # Establish an SSH connection to the FortiGate device
        connection = ConnectHandler(**device)
        
        # Send the command to retrieve network objects
        if not context:
            output = connection.send_command("show firewall address")
        else:
            output = connection.send_command("config vdom")
            output = connection.send_command("edit %s" %context)
            output = connection.send_command("show firewall address")
        # Close the connection
        connection.disconnect()
        
        return output
    except Exception as e:
        return f"An error occurred: {e}"


def is_ipcidr_exist(new_cidr_list,fortigate, context):
    """
    check if any of the new IP CIDRs already exist on the firewall
    
    Args:
        new_cidr_list (list): List containing new IP CIDRs.
        
    Returns:
        Boolean: IP exist or not.
    """
    # get all objects exist on the device in the form of text
    # extract IP addresses from the text and save in a list
    network_objects = get_network_objects(fortigate, context)
    # if an error happens while making a connection to the device
    #error_pattern = re.compile(r"An\s+error\s+occurred:")
    #match = re.findall(error_pattern, network_objects)
    #if not match:
    cidr_list = convert_to_cidr(extract_ip_addresses(network_objects))
    cidr_exist = []
    for new_item in new_cidr_list:
        new_network = ipaddress.ip_network(new_cidr_list[new_item]['cidr'])
        #print(new_cidr_list[new_item]['address'])
        #dic_iplist[item]['address']
        for item in cidr_list:
            network = ipaddress.ip_network(item)
            if network.supernet_of(new_network) or network == new_network:
            #print("IP address %s already exist" %item)
                cidr_exist.append(item)       
    if not cidr_exist:
        return False
    else:
        return cidr_exist
        #print(network_objects)
    #else:
    #    # error happened while making a connection to the device
    #   # returing the error description
    #    return network_objects