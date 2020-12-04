from netmiko import Netmiko
from netmiko import NetMikoAuthenticationException
from netmiko import NetMikoTimeoutException
from paramiko.ssh_exception import SSHException, NoValidConnectionsError
import logging


def deviceconnection(deviceip, loginUser, loginPass, netmikotype):
    """ This function actually does the device connecting"""

    netmikohost = {
        "host": deviceip,
        "username": loginUser,
        "password": loginPass,
        "device_type": netmikotype,
        "verbose": True,
        "auth_timeout": 60,
        "banner_timeout": 7,
        "global_delay_factor": 2
    }
    print(deviceip + " --Connecting(" + netmikotype + "): " + loginUser)
    netmikodevice = Netmiko(**netmikohost)
    return netmikodevice


def devicelogin(deviceip, loginlist, conntype="SSH"):
    """ This recursive function tries to connect to a device using SSH if unsuccessful it then tries
    Telnet. It also tries a list of username/password from the provided loginlist
    if connection is un-successful it will try the others
    Returns Netmiko Device and Connection Status
    loginlist = [{"admin": "password1"},
                 {"admin": "password2"},
                 {"administrator": "password3"},
                 ]
   """
    if conntype == "SSH":
        netmikotype = "cisco_ios"
    elif conntype == "TELNET":
        netmikotype = "cisco_ios_telnet"
    elif conntype == "WLC":
        netmikotype = "cisco_wlc"
    elif conntype == "LINUX":
        netmikotype = "linux"
    else:
        netmikotype = "cisco_ios_telnet"

    # Try to connect using each login
    for loginentry in loginlist:
        for username, password in loginentry.items():
            try:
                netmikodevice = deviceconnection(deviceip,
                                                 username,
                                                 password,
                                                 netmikotype
                                                 )
                print(deviceip + " --Connected(" + conntype + "): {}".format(username))
                logging.info(deviceip + " --Connected(" + conntype + "): {}".format(username))
                return netmikodevice

            except NetMikoAuthenticationException:
                logging.error(deviceip + " --Error: Invalid User {}".format(username))

            except ConnectionAbortedError:
                print(deviceip + " --Error: Connection Aborted")
                logging.error(deviceip + " --Error: Connection Aborted")
                netmikodevice = None
                conntype = "ERROR"
                return netmikodevice

            except EOFError:
                print(deviceip + " --Error: Invalid Users")
                logging.error(deviceip + " --Error: Invalid Users")
                netmikodevice = None
                conntype = "ERROR"
                continue

            except ValueError:
                print(deviceip + " --Error: Can not find Prompt")
                logging.error(deviceip + " --Error: Can not find Prompt")
                netmikodevice = None
                conntype = "ERROR"
                return netmikodevice, conntype

            except (SSHException, NetMikoTimeoutException, NoValidConnectionsError, TimeoutError):
                logging.error(deviceip + " --Error({}): Not Responding".format(conntype))
                if conntype == "TELNET":
                    netmikodevice = None
                    conntype = "ERROR"
                    return netmikodevice, conntype
                else:
                    # If you get this far SSH didn't work, Recursive function, this time using telnet,
                    return devicelogin(deviceip, loginlist, "TELNET")
