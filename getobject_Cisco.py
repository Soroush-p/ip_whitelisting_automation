import re
from netmiko import ConnectHandler
import ipaddress

def extract_ip_addresses_cisco(text):
    # Regex patterns to match different types of IP address definitions
    ip_netmask_pattern = re.compile(r'network-object\s+(\d{1,3}(?:\.\d{1,3}){3})\s+(\d{1,3}(?:\.\d{1,3}){3})')
    host_pattern = re.compile(r'network-object\s+host\s+(\d{1,3}(?:\.\d{1,3}){3})')
    
    # Find all matches for IP/netmask and host patterns
    ip_netmask_matches = ip_netmask_pattern.findall(text)
    host_matches = host_pattern.findall(text)
    
    # Collect results
    results = []

    for match in ip_netmask_matches:
        ip = match[0]
        netmask = match[1]
        network = ipaddress.IPv4Network(f'{ip}/{netmask}', strict=False)
        results.append(str(network))

    for match in host_matches:
        ip = match
        netmask = '255.255.255.255'  # Hosts have a default netmask of 255.255.255.255
        network = ipaddress.IPv4Network(f'{ip}/{netmask}', strict=False)
        results.append(str(network))
    #if not results:
    #    return text
    #else:
    return results


def get_network_objects(cisco_device, context):
    """
    Connects to a FortiGate device and retrieves network object configurations.
    
    Args:
        device (dict): Dictionary containing device connection details.
        
    Returns:
        str: Network object configurations from the FortiGate.
    """
    try:
        # Establish an SSH connection to the FortiGate device
        connection = ConnectHandler(**cisco_device)
        
        # Send the command to retrieve network objects
        if not context:
            output = connection.send_command("show run object-group")
        else:
            output = connection.send_command("changeto  context %s" %context)
            output = connection.send_command("show run object-group")
        
        # Close the connection
        connection.disconnect()
        
        return output
    except Exception as e:
        return f"An error occurred: {e}"

def is_ipcidr_exist(new_cidr_list, ciscoASA, context):
    ipcidrlist = extract_ip_addresses_cisco(get_network_objects(ciscoASA, context))
    ## if an error occurred
    #match = ""
    #error_pattern = re.compile(r"An\s+error\s+occurred:")
    #match = re.findall(error_pattern, ipcidrlist)
    #if match == "":
    cidr_exist = []
    for new_item in new_cidr_list:
        new_network = ipaddress.ip_network(new_cidr_list[new_item]['address'])
        #print(new_cidr_list[new_item]['address'])
        #dic_iplist[item]['address']
        for item in ipcidrlist:
            network = ipaddress.ip_network(item)
            if network.supernet_of(new_network) or network == new_network:
            #print("IP address %s already exist" %item)
                cidr_exist.append(item)       
    if not cidr_exist:
        return False
    else:
        return cidr_exist
    #else:
    #    return ipcidrlist
