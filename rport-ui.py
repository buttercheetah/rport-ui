import requests
import platform
import json
import os
import sys
from subprocess import run as subprocess_run
import argparse
parser = argparse.ArgumentParser(description='Control Tunnels using rport')
parser.add_argument('Server_Host', nargs='?', help='The FQDN of the rport server')
parser.add_argument('Server_Username', nargs='?', help='The username of the rport server')
parser.add_argument('Server_Password', nargs='?', help='The password of the rport server')
parser.add_argument('--server', dest='servername', type=str, help='Name of the server')
parser.add_argument('--port', dest='serverport', type=int, help='Port Number of the recieving server')
parser.add_argument('--pport', dest='pport', type=int, help='port number of the public tunnel, set to -1 for random port')
parser.add_argument('--protocol', dest='protocol', type=str, help='the tunnel protocol [tcp/udp]')
parser.add_argument('--iplock', dest='iplock', type=bool, help='if the tunnel will be locked to your current ip [True/False]')
parser.add_argument("--cfile", dest='cfile', type=argparse.FileType('r'), help="A config file to house all options")
parser.add_argument('--sshuser', dest='sshuser', type=str, help='if connection is for ssh. Please provide the username for ssh connection')
parser.add_argument('--crun', dest='crun', type=str, help='Optional command to run while tunnel is open, please note that when this command is finished the tunnel will be closed. enter just [ssh] to open a ssh connection')

args = parser.parse_args()
def getstats(baseurl,username,password):
    # * Gets status
    x = requests.get(f'{baseurl}/api/v1/status',auth=(username, password))
    return x.status_code
def getlinuxservers(baseurl,username,password):
    # * Gets all linux servers
    x = requests.get(f'{baseurl}/api/v1/clients?filter[os_kernel]=linux',auth=(username, password))
    jsondata = x.json()
    data = jsondata['data']
    # * Creates new data structure with response
    AvailableLinuxServers = {}
    LinuxServerNumericID = {}
    for count, x in enumerate(data):
        AvailableLinuxServers[x['name']] = x['id']
        LinuxServerNumericID[count] = x['name']
    return AvailableLinuxServers, LinuxServerNumericID
def getopentunnels(baseurl,username,password):
    # * checks all open ports
    x = requests.get(f'{baseurl}/api/v1/tunnels',auth=(username, password))
    jsondata = x.json()
    openservices = {}
    for data in jsondata['data']:
        if data['client_id'] not in openservices:
            openservices[data['client_id']] = []
        #*          
        openservices[data['client_id']].append({'port':data['lport'],'ip':data['acl'],'id':data['id'],'RecievePort':data['rport']})
    return openservices
def printAvailableLinuxServers(AvailableLinuxServers):
    # * prints available servers
    for count, value in enumerate(AvailableLinuxServers):
        print(count, value)
def getinput():
    ServerName, ui, user, porttoopen, protocol, iplocked, ServerHost, ServerUsername, ServerPassword, publicport, crun = None, None, None, None, None, None, None, None, None, None, None
    # * Check if Config File was passed
    if args.cfile:
        try:
            # Opening JSON file
            #f = open(args.cfile)
            # returns JSON object as 
            # a dictionary
            datafile = json.load(args.cfile)
            #cleanup
            if 'Server_Host' in datafile:
                ServerHost = datafile['Server_Host']
            if 'Server_Username' in datafile:
                ServerUsername = datafile['Server_Username']
            if 'Server_Password' in datafile:
                ServerPassword = datafile['Server_Password']
            if 'servername' in datafile:
                ServerName = datafile['servername']
            if 'sshuser' in datafile:
                user = datafile['sshuser']
            if 'port' in datafile:
                porttoopen = datafile['port']
            if 'protocol' in datafile:
                protocol = datafile['protocol']
            if 'IPLock' in datafile:
                iplocked = datafile['IPLock']
            if 'pport' in datafile:
                publicport = datafile['pport']
            if 'crun' in datafile:
                crun = datafile['crun']
        except Exception as e:
            print(e)
            sys.exit(1)
    # * Check args
    if args.servername:
        ServerName = args.servername
    if args.serverport:
        porttoopen = args.serverport
    if porttoopen == 22:
        if args.sshuser:
            user = args.sshuser
    if args.pport:
        publicport = args.pport
    if args.protocol:
        protocol = args.protocol
    if args.iplock:
        iplocked = args.iplock
    if args.crun:
        crun = args.crun

    # * requests input from user
    if ServerHost == None:
        ServerHost = input("Enter Rport Server Host: ")
    if ServerUsername == None:
        ServerUsername = input("Enter Rport Server Username: ")
    if ServerPassword == None:
        ServerPassword = input("Enter Rport Server Password: ")
    ServerResponse = getstats(ServerHost,ServerUsername,ServerPassword)
    if ServerResponse != 200:
        print(f"Server responded with code {ServerResponse}")
        input("press enter to close")
        sys.exit(1)
    AvailableLinuxServers,LinuxServerNumericID = getlinuxservers(ServerHost,ServerUsername,ServerPassword)
    openservices = getopentunnels(ServerHost,ServerUsername,ServerPassword)
    if ServerName:
        ui = list(LinuxServerNumericID.keys())[list(LinuxServerNumericID.values()).index(ServerName)]
    if ui == None:
        printAvailableLinuxServers(AvailableLinuxServers)
        ui = LinuxServerNumericID[int(input())]
    if porttoopen == None:
        porttoopen = getport()
    if porttoopen == 22:
        if crun == None:
            print("is this for ssh? [Y/n]")
            if input("").lower() != "n":
                protocol = 'tcp'
                iplocked = True
                crun = 'ssh'
        if crun == 'ssh' and user == None:
            user = input("Enter username: ")
    if publicport == None:
        publicport = GetPublicPort()
    if protocol == None:
        protocol = getprotocol()
    if iplocked == None:
        iplocked = getiplock()
    for count, value in enumerate(AvailableLinuxServers):
        if value==ServerName:
            # * Sets UI to server numeric id
            ui = LinuxServerNumericID[count]
    if not checkifservernameisavailable(ui,AvailableLinuxServers):
        print("server not found")
        input("press enter to close")
        sys.exit()
    return ui, user, porttoopen, protocol, iplocked, publicport, ServerHost, ServerUsername, ServerPassword, crun
def getport():
    porttoopen = int(input("Enter port to open: "))
    return porttoopen
def getprotocol():
    protocol = ""
    while protocol not in ['udp', 'tcp']:
        print('Which protocol do you want?\n1) TCP\n2) UDP\n')
        tmpui = input(":")
        if tmpui == '2':
            protocol = 'udp'
        elif tmpui == '1':
            protocol = 'tcp'
    return protocol
def getiplock():
    iplocked = None
    while iplocked == None:
        print('IP locked? [Y/n]')
        tmpui = input(":")
        if tmpui.upper() == 'N':
            iplocked = False
        else:
            iplocked = True
    return iplocked
def GetPublicPort():
    print("What port would you like to open?")
    print("leave blank for auto-configuration")
    tmpui = input(":")
    if tmpui == '' or not tmpui.isnumeric():
        publicport = -1
    else:
        publicport = int(tmpui)
def checkifservernameisavailable(sn,sl):
    return sn in sl
def closetunnel(client,tunnel,baseurl,username,password):
    x = requests.delete(f'{baseurl}/api/v1/clients/{client}/tunnels/{tunnel}?force=true',auth=(username, password))
def opentunnel(client,port,protocol,publicport,baseurl,username,password,iplocked=True):
    tmpstr = "&check_port=0"
    if iplocked:
        tmpstr += '&acl='+str(ip)
    if port != 22:
        tmpstr += '&auto-close=24h'
    if publicport != -1:
        tmpstr += '&local='+str(publicport)
    tmpstr += "&protocol="+str(protocol)
    port = str(port)
    x = requests.put(f'{baseurl}/api/v1/clients/{client}/tunnels?remote=127.0.0.1:{port}{tmpstr}',auth=(username, password))
    print("Created new tunnel")
    jsondata = x.json()
    try:
        jsondata['errors']
        print("server returned error\n\n")
        print(jsondata)
        input("\n\npress enter to close")
        sys.exit()
    except:
        pass
    return jsondata['data']

def main():
    global datafile, openservices, LinuxServerNumericID, AvailableLinuxServers, ip

    ip = requests.get('https://api.ipify.org').content.decode('utf8')
    ui, user, porttoopen, protocol, iplocked, publicport,baseurl,username,password,crun = getinput()
    AvailableLinuxServers,LinuxServerNumericID = getlinuxservers(baseurl,username,password)
    openservices = getopentunnels(baseurl,username,password)
    if AvailableLinuxServers[ui] in openservices: # * Checks if requested server has open ports
        print("server has exposed ports")
        for count, value in enumerate(openservices[AvailableLinuxServers[ui]]): # * Itterates over open ports
            #print(value['RecievePort'])
            if str(value['RecievePort']) == str(porttoopen): # * if the wanted port is already open
                if value['ip'] == str(ip) or value['ip'] == "0.0.0.0" or value['ip'] == None: # * if the tunnel allows current IP address
                    data = {'lport':value['port']}
                    print("Found existing tunnel")
                else: # * Tunnel does not allow current IP address, so close the tunnel and create a new one.
                    closetunnel(AvailableLinuxServers[ui],value['id'],baseurl,username,password)
                    print("deleted old tunnel")
                    data = opentunnel(AvailableLinuxServers[ui],porttoopen,protocol,publicport, iplocked)
    else: # * No tunnels are opened on requested server, so create a new tunnel.
        data = opentunnel(AvailableLinuxServers[ui],porttoopen,protocol,publicport,baseurl,username,password,iplocked)
    wrotefile = False # * sets wrotefile to False to prevent errors when removing temporary file
    if crun =='ssh': # * if the tunnel is for port 22 (ssh)
        if platform.system() == 'Linux':
            CommandToRun = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {data['lport']} {user}@{baseurl.replace('https://', '')}"
        else:
            CommandToRun = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=\\\\.\\NUL -p {data['lport']} {user}@{baseurl.replace('https://', '')}"
        rc = subprocess_run(CommandToRun, shell=True)
    elif crun != None:
        try:
            rc = subprocess_run(crun, shell=True)
        except Exception as e:
            print("Error running command\n")
            print(e)
    else:
        # * a simple while loop or user input
        run = True
        while run:
            # * prints out the tunnel information
            print(f"Port {porttoopen}->{data['lport']}")
            print("This connection will be open for 24 hours")
            # * prints out the baseurl with the port number for easy copying
            print(f'{baseurl.replace("https://", "")}:{data["lport"]}')
            print("press q to close connection")
            uit = input()
            if uit.lower() == 'q': # * if user inputs q
                run = False # * exit while loop
    print("closing connection")
    # * updates openservices with new tunnel information
    openservices = getopentunnels(baseurl,username,password)
    for count, value in enumerate(openservices[AvailableLinuxServers[ui]]): # * for each tunnel open to requested server
        if value['port'] == data['lport']: # * if the destination port is the requested port
            closetunnel(AvailableLinuxServers[ui],value['id'],baseurl,username,password) # * close the tunnel
            print(f'Connection ID {value["id"]} closed') # * print the tunnel id
    input("press enter to close program") # * just waits for user input before closing the program.
if __name__ == '__main__':
    main()