#!/usr/bin/python3

import tornado.ioloop
import tornado.web
import tornado.template
import os.path
import csv
import json
import ipaddress
from jinja2 import Template
#from netmiko.fortinet import FortinetSSH
from netmiko import ConnectHandler
from netmiko import NetmikoTimeoutException, NetmikoAuthenticationException
import getobject
import logging
import getobject_Cisco
import re


setting = dict(
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    debug=True
)

urls = []
IPaddress = []
site = ""
firewall = ""
contextName = ""
mgmtIP = ""
intin = ""
intout = ""
dstip = ""
port = ""
nat = ""
urls_dic = {}



def csv_reader():
    """
    reads the csv files and creates a dictionary with urls as keys and lists of url related info as values
    {url1: ["", "", ""], url2: ["","",""]}
    """
    global urls,urls_dic
    
    try:
        with open("urls.csv") as file_obj:
            url_reader = csv.reader(file_obj)
            for row in url_reader:
                    urls.append(row[0])
                    urls_dic.update({row[0]:[row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9]]})
    except IOError:
        print("can not open CSV file")


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        """
            loads the html template passes the variables
        """
        self.render("templateIP.html", urls=urls, firewall=firewall, contextName=contextName, mgmtIP=mgmtIP, intin=intin, intout=intout, dstip=dstip, port=port, nat=nat)

class ViewHandler(tornado.web.RequestHandler):
    def post(self):
        """
            fills url dropbox based on the vlaues read from the csv file
            return selected value.
        """
        value = self.get_argument('drpbx_URL')
        #print(value)
        #print(urls_dic)
        #firewall_txt = urls_dic[value][1]
        #mgmtIP_txt = urls_dic[value][2]
        #dic_over = mk_dict_schl(Mngip[value])
        url_list = urls_dic[value]
        #print(url_list)
        selected_dic = {}
        y = 0
        for item in url_list:
           selected_dic.update({y: item})
           y +=1
        #print(selected_dic)
        self.write(selected_dic)

class FormHandler(tornado.web.RequestHandler):
    def post(self):
        """
                generate the code after validating the IP addresses. The Dic_iplist is dictionary of
                dictionaries with outer dictionary keys are numbers and values are dictionaries with
                address and netmask as keys.
                {1: {'address': '58.10.30.0/24', 'netmask': '58.10.30.0/24'}, 2: {address: '', netmask: ''}}
        """
        def is_public_ip(ip_cidr):
            """
            Validates if the given IP address is a public IP address.
    
            Args:
                ip_cidr (str): The IP address in string format.
        
            Returns:
                bool: True if the IP address is public, False otherwise.
            """
            try:
                network = ipaddress.ip_network(ip_cidr, strict=True)
                ip = network.network_address
                #ip = ipaddress.ip_address(ip_str)
                return not ip.is_private and not ip.is_reserved and not ip.is_loopback and not ip.is_multicast
            except ValueError:
                return False
    
        """
        reads the table with IP CIDRs and create a dictionary of dictionaries
        """
        try:
            i = 1
            #lst_ip = []
            global dic_iplist
            dic_iplist = {}
            mylist = self.get_argument('table[%d][ip_addr]' % i)
            while mylist != "":
                ipAddr = str(self.get_argument('table[%d][ip_addr]' % i))
                network = ipaddress.ip_network(ipAddr,strict=False)
                netmask = network.netmask
                #print(ipAddr)
                #lst_ip.extend(address: 'network', netmask: 'ipAddr')
                dic_iplist.update({i:{"address": network.network_address, "netmask": str(netmask), "cidr": ipAddr}})
                i += 1
                mylist = self.get_argument('table[%d][ip_addr]' % i)
           # print(dic_iplist)
           #self.write(dic_iplist)
        except:
           pass


        intin = self.get_argument("intin")
        intout = self.get_argument("intout")
        firewall = self.get_argument("firewall")
        context = self.get_argument("context")
        port = self.get_argument("port")
        dstip = self.get_argument("dstip")
        customername = self.get_argument("customername")
        nat = self.get_argument("nat")
        ips_valid = 0
        for item in dic_iplist:
            if not is_public_ip (dic_iplist[item]['cidr']):
                #print ("IP %s is not valid IP CIDR " %dic_iplist[item]['address'])
                ips_valid = 0
                self.write("IP CIDR %s is not valid or it is a private address"  %dic_iplist[item]['cidr'])
                break
            else:
                ips_valid = 1

        """
        uses the Jinja templates to create the config based on the firewall type
        """
        if ips_valid and firewall == "Cisco":
           with open('cisco.j2') as cisco_j2:
              templateCisco = Template(cisco_j2.read())
           self.write(templateCisco.render(iplist=dic_iplist,objectname=customername,context=context ,intin=intin, intout=intout ,port=port, nat=nat, dstip=dstip,))
        elif ips_valid and firewall == "Fortinet":
           with open('Fortinet.j2') as fortinet_j2:
              templateFortinet = Template(fortinet_j2.read())
           self.write(templateFortinet.render(iplist=dic_iplist, objectname=customername, context=context, intin=intin, intout=intout, port=port, nat=nat, dstip=dstip))


class PushHandler(tornado.web.RequestHandler):
    def post(self):

        CodeStr = str(self.get_argument('code'))
        firewall = self.get_argument('firewall')
        mgmtIP = self.get_argument('mgmtIP')
        username = self.get_argument('username')
        password = self.get_argument('password')
        context = self.get_argument('context')
        fortigate = {
        'device_type' : 'fortinet',
        'host' : mgmtIP,
        'username' : username,
        'password' : password,
        'port' : 22,
        'verbose': True
       }
        ciscoASA = {
       'device_type': 'cisco_asa',
        'host': mgmtIP,
        'username': username,
        'password': password,
        'secret': 'your_enable_password',  # Optional, only if you need to enter enable mode
        }
        logging.basicConfig(
        filename='netmiko_log.txt',  # Log file name
        level=logging.DEBUG,         # Log level
        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s'  # Log format
        )

        # Enable Netmiko logging
        logger = logging.getLogger('netmiko')
        logger.setLevel(logging.DEBUG)
        #print (dic_iplist)
        def split_config(config, chunk_size=5):
            config_lines = config.strip().split('\n')
            for i in range(0, len(config_lines), chunk_size):
                yield config_lines[i:i + chunk_size]
            result_output = ""

        
        if firewall == "Fortinet":
            iplist_exist = getobject.is_ipcidr_exist(dic_iplist, fortigate, context)
            #error_pattern = re.compile(r"An\s+error\s+occurred:")
            #match = re.findall(error_pattern, iplist_exist)      
            if not (iplist_exist):
                try:
                    with ConnectHandler(**fortigate) as net_connect:
                        for chunk in split_config(CodeStr):
                            command_string = '\n'.join(chunk)
                            print(f"Sending chunk:\n{command_string}\n")
                            output = net_connect.send_config_set(command_string.split('\n'))
                            result_output = output
                            result_output += result_output
                        net_connect.disconnect()
                        self.write({'result': result_output})
                        #self.write(output)
                        #print (dic_iplist)
                except Exception as e:
                    print(f"Failled to connect: {e}")  
            #elif match:
            #    self.write({'result': iplist_exist})
            else:  
                self.write({'result': 'The IP %s exist on the firewall' %iplist_exist})
        elif firewall == "Cisco":
            #match = ""
            iplist_exist = getobject_Cisco.is_ipcidr_exist(dic_iplist, ciscoASA, context)
            #error_pattern = re.compile(r"An\s+error\s+occurred:")
            #match = re.findall(error_pattern, iplist_exist)
            if not (iplist_exist):
                try:
                    with ConnectHandler(**ciscoASA) as net_connect:
                        for chunk in split_config(CodeStr):
                            command_string = '\n'.join(chunk)
                            print(f"Sending chunk:\n{command_string}\n")
                            output = net_connect.send_config_set(command_string.split('\n'))
                            result_output = output
                            result_output += result_output
                        net_connect.disconnect()
                        self.write({'result': result_output})
                except Exception as e:
                    print(f"Failled to connect: {e}")
            #elif match != "":
            #    print ("when error pattern match")
            #    print (match)
            #    self.write({'result': iplist_exist}, match)
            else:
                self.write({'result': 'The IP %s exist on the firewall' %iplist_exist})
                  



def make_app():
    return tornado.web.Application([(r"/", MainHandler),(r"/api/view", ViewHandler),(r"/form", FormHandler),(r"/api/push", PushHandler)], **setting)

if __name__ == "__main__":
    csv_reader()
    print("app started")
    app = make_app()
    app.listen(8080)
    tornado.ioloop.IOLoop.current().start()