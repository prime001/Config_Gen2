from __future__ import print_function
import napalm
import os
import json
import getpass
import pprint
import time
import sqlite3

from easysnmp import Session
from jnpr.junos import Device
from jnpr.junos.utils.config import Config


def main():
    settings = {
        "config_dir": "~/ip_plan",
        "ssh_username": "",
        "ssh_password": getpass.getpass(),
    }

    node_list_path = "/var/opt/node.txt"

    with open(node_list_path, "r") as node_list_handle:
        node_dict = json.load(node_list_handle)

    # entries = []

    for node in node_dict:
        # Hardware List
        if node["Hardware"] in [
            "Juniper SRX100H2",
            "Juniper SRX210HE2",
            "Juniper SRX210HE-POE",
            "Juniper SRX210HE2-POE",
            "Juniper SRX240H2",
            "Juniper SRX300",
            "Juniper SRX320-POE",
            "Juniper SRX340",
            "Juniper SRX1500",
        ]:
            hostname = node["Address"]
        else:
            continue
        # Ignore list
        if node["SysName"] in [
            "DII-GBP-PBG-1EF01",
            "DII-RCA-HVAC-1EF01",
            "DII-RCA-PBG-1EF01",
            "CCI-CHADBOURNE-1EF01",
        ]:
            continue
        if node["SysName"].__contains__("STC-") is True:
            conn = sqlite3.connect("ip_plan.db")
            c = conn.cursor()

            """Load a config for the device."""

            # Use the appropriate network driver to connect to the device:
            driver = napalm.get_network_driver("junos")

            # Connect:
            device = driver(
                hostname=hostname,
                username="pam.dii.ea0033",
                password=settings["ssh_password"],
                timeout=30,
                optional_args={"port": 22},
            )

            print("Connecting to " + node["SysName"])

            try:
                device.open()
            except Exception as e:
                print("Open Error " + str(e))
                continue
            if device.is_alive()["is_alive"] is True:
                pass
            else:
                continue

            database = {}
            # Get Facts
            print("Get Facts")
            facts = device.get_facts()
            pprint.pprint("Hostname: " + facts["hostname"])
            database["Hostname"] = facts["hostname"]
            pprint.pprint("Model: " + facts["model"])
            database["Model"] = facts["model"]
            pprint.pprint("Version: " + facts["os_version"])
            database["Version"] = facts["os_version"]
            pprint.pprint("Serial: " + facts["serial_number"])
            database["Serial"] = facts["serial_number"]
            pprint.pprint("Vendor: " + facts["vendor"])
            database["Vendor"] = facts["vendor"]
            pprint.pprint("Uptime: " + str(facts["uptime"]))
            database["Uptime"] = facts["uptime"]

            # Get Supernet Block from get_route_to
            database["supernet"] = "Unknown"
            supernet = device.get_route_to(
                destination='10.', protocol='static')
            pprint.pprint("Supernets " + str(supernet))
            if supernet is not None:
                for supern in supernet:
                    if supern == "0.0.0.0/0":
                        pass
                    if supern == "10.0.0.0/9":
                        pass
                    if supern == "10.128.0.0/9":
                        pass
                    if "/22" in supern or "/23" in supern:

                        print("Supernet: " + supern)
                        database["supernet"] = supern
                        break
                    if "/21" in supern or "/24" in supern:
                        print("Supernet: " + supern)
                        database["supernet"] = supern
                        break
                    if "/16" in supern:
                        pass
                    else:
                        # Get Supernet Block from CLI
                        # get supernet block
                        commands = [
                            "show configuration routing-options aggregate"]
                        res = device.cli(commands)
                        # pprint.pprint(res)$$
                        myfile1 = open("supernet.txt", "w")
                        myfile1.write(
                            res["show configuration routing-options aggregate"]
                        myfile1.close()
                        myfile2=open("supernet.txt", "r")
                        myline=myfile2.readlines()
                        for line in myline:
                            if line.__contains__("route"):
                                subsplit=line.split(" ")
                                # print('Supernet: ' + subsplit[1])$
                                if subsplit[1].__contains__(";"):
                                    xen=subsplit[1].rstrip()
                                    xena=xen[0: len(xen) - 1]
                                    print("Supernet: " + xena.rstrip())
                                    database["supernet"]=xena.rstrip()
                                    # database['supernet'] = subsplit[1] $
                                else:
                                    print("Supernet " + subsplit[1].rstrip())
                                    database["supernet"]=subsplit[1].rstrip()
                        myfile2.close()
                else:
                    # Get Supernet Block from CLI
                    # get supernet block
                    commands=["show configuration routing-options aggregate"]
                    res=device.cli(commands)
                    # pprint.pprint(res)$$
                    myfile1=open("supernet.txt", "w")
                    myfile1.write(
                        res["show configuration routing-options aggregate"])
                    myfile1.close()
                    myfile2=open("supernet.txt", "r")
                    myline=myfile2.readlines()
                    for line in myline:
                        if line.__contains__("route"):
                            subsplit=line.split(" ")
                            # print('Supernet: ' + subsplit[1])$
                            if subsplit[1].__contains__(";"):
                                xen=subsplit[1].rstrip()
                                xena=xen[0: len(xen) - 1]
                                print("Supernet: " + xena.rstrip())
                                database["supernet"]=xena.rstrip()
                                # database['supernet'] = subsplit[1] $
                            else:
                                print("Supernet " + subsplit[1].rstrip())
                                database["supernet"]=subsplit[1].rstrip()
                    myfile2.close()

            # The hoodoo you don't doo people!
             commands2=[
                 "show configuration security zones security-zone TRUST interfaces"]
             commands3=[
                 "show configuration security zones security-zone UNTRUST_ISP_1 interfaces"]
             commands4=[
                 "show configuration security zones security-zone UNTRUST_ISP_2 interfaces"]
             getcmd2=device.cli(commands2)
             getcmd3=device.cli(commands3)
             getcmd4=device.cli(commands4)
             trust1=getcmd2['show configuration security zones security-zone TRUST interfaces'].split(
                 '\n')
             untrust1=getcmd3['show configuration security zones security-zone UNTRUST_ISP_1 interfaces'].split(
                 '\n')
             untrust3=getcmd4['show configuration security zones security-zone UNTRUST_ISP_2 interfaces'].split(
                 '\n')
             print('Trust Interface: ' + trust1[2])
             print('Untrust Interface: ' + untrust1[1])
             print('Untrust Interface2: ' + untrust3[1])
             trust=trust1[2]
             untrust=untrust1[1]
             untrust2=untrust3[1]

            # Get Interface IP's
            print("Get Interface IPs")
            interfaces=device.get_interfaces_ip()
            database["loopback"]="Unknown"
            database["isp1"]="Unknown"
            database["isp2"]="Unknown"
            database["st0_0"]="Unknown"
            database["st0_1"]="Unknown"
            database["st0_10"]="Unknown"
            database["st0_11"]="Unknown"
            for interface in interfaces:
                if interface == ("lo0.0"):
                    print("Loopback IP")
                    for ip in interfaces[interface]["ipv4"]:
                        if ip.__contains__("10."):
                            print(interface + " " + ip)
                            database["loopback"]=ip
                if interface == trust:
                    for ip in interfaces[interface]["ipv4"]:
                        if ip.__contains__("192") or ip.__contains__("10."):
                            print("core ip: " + interface + " " + ip)
                            database["core_link"]=ip
                if interface == untrust:
                    for ip in interfaces[interface]["ipv4"]:
                            print("ISP1: " + interface + " " + ip)
                            database["isp1"]=ip
                if interface == untrust2:
                    for ip in interfaces[interface]["ipv4"]:
                        print("ISP1: " + interface + " " + ip)
                        database["isp2"]=ip
                if interface == "reth0.901":
                    for ip in interfaces[interface]["ipv4"]:
                        print("Core Link: " + interface + " " + ip)
                        database["core_link"]=ip
                if interface == "reth1.0":
                    for ip in interfaces[interface]["ipv4"]:
                        print("ISP1: " + interface + " " + ip)
                        database["isp1"]=ip
                if interface == "reth2.0":
                    for ip in interfaces[interface]["ipv4"]:
                        print("ISP2: " + interface + " " + ip)
                        database["isp2"]=ip
                if interface == "st0.0":
                    for ip in interfaces[interface]["ipv4"]:
                        print(interface + " " + ip)
                        database["st0_0"]=ip
                if interface == "st0.1":
                    for ip in interfaces[interface]["ipv4"]:
                        print(interface + " " + ip)
                        database["st0_1"]=ip
                if interface == "st0.10":
                    for ip in interfaces[interface]["ipv4"]:
                        print(interface + " " + ip)
                        database["st0_10"]=ip
                if interface == "st0.11":
                    for ip in interfaces[interface]["ipv4"]:
                        print(interface + " " + ip)
                        database["st0_11"]=ip
                else:
                    continue

            # Get LLDP Neighbors
            neighbors=device.get_lldp_neighbors()
            name=node["SysName"]
            testvar=name[0: len(name) - 6]
            database["neighbor_device"]="None"
            database["neighbor_port"]="None"
            # pprint.pprint(neighbors)
            for neighbor in neighbors:
                # pprint.pprint('LLDP Neighbor ' + neighbors[neighbor][0]['hostname'])
                if neighbors[neighbor][0]["hostname"].__contains__(testvar):
                    pprint.pprint("LLDP Neighbor " +
                                  neighbors[neighbor][0]["hostname"])
                    pprint.pprint(
                        "LLDP Neighbor port: " + neighbors[neighbor][0]["port"]
                    )
                    database["neighbor_device"]=neighbors[neighbor][0]["hostname"]
                    database["neighbor_port"]=neighbors[neighbor][0]["port"]
                else:
                    print("No LLDP Neighbors")
                    print("Double check " + neighbors[neighbor][0]["hostname"])

            # Get SNMP location OID 1.3.6.1.2.1.1.6.0 sysLocation
            session=Session(hostname=hostname, community="dycom", version=2)
            print("Trying to get SNMP Location")
            database["snmp_location"]="Unknown"
            try:
                location=session.get("sysLocation.0")
                if location.value is None:
                    database["snmp_location"]="Unknown"
                if len(location.value) > 2:
                    print("SNMP Location: " + location.value)
                    database["snmp_location"]=location.value
                else:
                    print("SNMP Issue " + database["snmp_location"])
            except Exception as err:
                print(err)

            # Get ISP Description
            device_desc=device.get_interfaces()
            # pprint.pprint(device_desc)
            # pprint.pprint(device_desc['reth2.0']['description'])
            database["isp1_desc"]="Unknown"
            database["isp2_desc"]="None"
            y=0
            for devic in device_desc:
                if device_desc[devic]["description"].__contains__("ISP") and y == 0:
                    print("ISP1 " + devic + " " +
                          device_desc[devic]["description"])
                    database["isp1_desc"]=device_desc[devic]["description"]
                    y=y + 1
                    continue
                if device_desc[devic]["description"].__contains__("ISP") and y == 1:
                    print("ISP2 " + devic + " " +
                          device_desc[devic]["description"])
                    database["isp2_desc"]=device_desc[devic]["description"]

            # Get BGP Neighbors
            junos_output=device.get_bgp_config()
            database["bgp_neighbor1"]="Unknown"
            database["bgp_neighbor2"]="Unknown"
            database["bgp_neighbor3"]="Unknown"
            database["bgp_neighbor4"]="Unknown"
            database["asn"]="Unknown"
            y=0
            for junos_groups in junos_output:
                if junos_groups == "HUB_ISP1":
                    x=0
                    for neighbor in junos_output["HUB_ISP1"]["neighbors"]:
                        x=x + 1
                        if x == 1:
                            # Get ASN
                            asnum=device.get_bgp_neighbors_detail(
                                neighbor_address=neighbor
                            )
                            pprint.pprint(
                                "ASN: " +
                                str(asnum["global"][65499][0]["local_as"])
                            )
                            database["asn"]=asnum["global"][65499][0]["local_as"]
                            print("BGP Neighbor1: " + neighbor)
                            database["bgp_neighbor1"]=neighbor
                            continue
                        if x == 2:
                            print("BGP Neighbor2: " + neighbor)
                            database["bgp_neighbor2"]=neighbor
                            continue
                if junos_groups == "HUB_ISP2":
                    x=0
                    for neighbor in junos_output["HUB_ISP2"]["neighbors"]:
                        x=x + 1
                        if not neighbor:
                            y=0
                            break
                        if x == 1:
                            y=1
                            print("BGP Neighbor3: " + neighbor)
                            database["bgp_neighbor3"]=neighbor
                            continue
                        if x == 2:
                            print("BGP Neighbor4: " + neighbor)
                            database["bgp_neighbor4"] + neighbor
                            continue
                if junos_groups not in [
                    "HQ_ISP1",
                    "HQ_ISP2",
                    "SPOKE_ISP1",
                    "SPOKE_ISP2",
                    "HUB_ISP1",
                    "HUB_ISP2",
                ]:
                    print("BGP Group Not Matching " + junos_groups)

            pprint.pprint(database.values())
            insert_values=list(database.values())
            insert_values.insert(0, None)
            c.execute(
                "INSERT INTO ip_plan VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                insert_values,
            )
            conn.commit()
            print("Closing DB")
            conn.close()
            # entries.append(list(database.values()))
            # pprint.pprint(entries)
            print("Complete")
    print("Job Done!")


if __name__ == "__main__":
    main()
