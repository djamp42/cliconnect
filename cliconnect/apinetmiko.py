from netmiko import Netmiko
from netmiko import NetMikoAuthenticationException
from netmiko import NetMikoTimeoutException
from netmiko.ssh_exception import NetMikoTimeoutException
from paramiko.ssh_exception import SSHException, NoValidConnectionsError
import logging


def deviceconnection(deviceip, username, password, netmikotype):
    """ This function actually does the device connecting"""
    netmikohost = {
        "host": deviceip,
        "username": username,
        "password": password,
        "device_type": netmikotype,
        "verbose": True,
        "auth_timeout": 60,
        "banner_timeout": 7,
        "global_delay_factor": 2
    }
    if netmikotype == "linux":
        netmikohost['secret'] = password

    print(f"{deviceip}: Connecting ({netmikotype}) - {username}")
    logging.error(f"{deviceip}: Connecting ({netmikotype}) - {username}")
    netmikodevice = Netmiko(**netmikohost)
    return netmikodevice


def devicelogin(deviceip, logindict, conntype="SSH"):
    """ This recursive function tries to connect to a device using SSH if unsuccessful it then tries
    Telnet. It also tries a list of username/password from the provided loginlist
    if connection is un-successful it will try the others
    Returns Netmiko Device and Connection Status
    logindict = {"admin": "password1"},
                {"admin": "password2"},
                {"administrator": "password3"}

   """
    if conntype == "SSH":
        netmikotype = "cisco_ios"
    elif conntype == "TELNET":
        netmikotype = "cisco_ios_telnet"
    elif conntype == "WLC":
        netmikotype = "cisco_wlc_ssh"
    elif conntype == "LINUX":
        netmikotype = "linux"
    else:
        netmikotype = "cisco_ios_telnet"

    # Try to connect using each login
    for username, password in logindict.items():
        try:
            netmikodevice = deviceconnection(deviceip,
                                             username,
                                             password,
                                             netmikotype
                                             )
            print(f"{deviceip}: Connected ({conntype}) - {username}")
            logging.info(f"{deviceip}: Connected ({conntype}) - {username}")
            return netmikodevice

        except NetMikoAuthenticationException:
            print(f"{deviceip}: Authentication Error ({conntype}) - {username}")
            logging.error(f"{deviceip}: Authentication Error ({conntype}) - {username}")

        except ConnectionRefusedError:
            print(f"{deviceip}: Unable to Connect ({conntype}) - {username}")
            logging.error(f"{deviceip}: Unable to Connect ({conntype}) - {username}")

        except ConnectionAbortedError:
            print(f"{deviceip}: Connection Aborted ({conntype}) - {username}")
            logging.error(f"{deviceip}: Connection Aborted  ({conntype}) - {username}")
            netmikodevice = None
            conntype = "ERROR"
            return netmikodevice

        except EOFError:
            print(f"{deviceip}: Unable to find valid Login ({conntype}) - {username}")
            logging.error(f"{deviceip}: Unable to find valid Login ({conntype}) - {username}")
            netmikodevice = None
            conntype = "ERROR"
            continue

        except ValueError:
            print(f"{deviceip}: Unable to find prompt ({conntype}) - {username}")
            logging.info(f"{deviceip}: Unable to find prompt ({conntype}) - {username}")
            netmikodevice = None
            conntype = "ERROR"
            return netmikodevice, conntype

        except (SSHException, NetMikoTimeoutException, NoValidConnectionsError, TimeoutError):
            print(f"{deviceip}: Not Responding ({conntype}) - {username}")
            logging.info(f"{deviceip}: Not Responding ({conntype}) - {username}")
            if conntype == "TELNET":
                netmikodevice = None
                conntype = "ERROR"
                return netmikodevice, conntype
            else:
                # If you get this far SSH didn't work, Recursive function, this time using telnet,
                return devicelogin(deviceip, logindict, "TELNET")
