import requests
import platform
import json
import os
import logging
import sys
from subprocess import run as subprocess_run
import argparse
parser = argparse.ArgumentParser(description='Control Tunnels using rport')
#parser.add_argument('--serverhost', dest='Server_Host', type=str,  help='The FQDN of the rport server')
#parser.add_argument('--serverusername', dest='Server_Username', type=str,  help='The username of the rport server')
#parser.add_argument('--serverpassword', dest='Server_Password', type=str,  help='The password of the rport server')
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

parser.add_argument('--verbose', '-v', action='count', default=0)

args = parser.parse_args()


# create a logger Log with name 'Main'
log = logging.getLogger('Main')
# create file handler which logs even ERROR messages or higher
log.setLevel(logging.INFO)
fh = logging.FileHandler('log.log')
fh.setLevel(logging.INFO)
# create formatter and add it to the file handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
# add the file handler to the (root) logger
log.addHandler(fh)



def getstats(baseurl,username,password):
    # * Gets status
    log.info('Getting server status')
    x = requests.get(f'{baseurl}/api/v1/status',auth=(username, password))
    return x.status_code
def getlinuxservers(baseurl,username,password):
    # * Gets all linux servers
    log.info('Getting Available Linux servers')
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
    log.info('Getting Open tunnels')
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
    log.info('Printing available Linux servers')
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
                log.info(f'Set Server_Host from config file to {datafile["Server_Host"]}')
            if 'Server_Username' in datafile:
                ServerUsername = datafile['Server_Username']
                log.info(f'Set Server_Username from config file to {datafile["Server_Username"]}')
            if 'Server_Password' in datafile:
                ServerPassword = datafile['Server_Password']
                log.info(f'Set Server_Password from config file to {datafile["Server_Password"]}')
            if 'servername' in datafile:
                ServerName = datafile['servername']
                log.info(f'Set Server_Name from config file to {datafile["servername"]}')
            if 'sshuser' in datafile:
                user = datafile['sshuser']
                log.info(f'Set SSH User from config file to {datafile["sshuser"]}')
            if 'port' in datafile:
                porttoopen = datafile['port']
                log.info(f'Set Port from config file to {datafile["port"]}')
            if 'protocol' in datafile:
                protocol = datafile['protocol']
                log.info(f'Set Protocol from config file to {datafile["protocol"]}')
            if 'IPLock' in datafile:
                iplocked = datafile['IPLock']
                log.info(f'Set IPLock from config file to {datafile["IPLock"]}')
            if 'pport' in datafile:
                publicport = datafile['pport']
                log.info(f'Set Public Port from config file to {datafile["pport"]}')
            if 'crun' in datafile:
                crun = datafile['crun']
                log.info(f'Set Crun from config file to {datafile["crun"]}')
        except Exception as e:
            print(e)
            log.critical(e)
            sys.exit(1)
    # * Check args

    if args.verbose > 0:
        verbose = True
    else:
        verbose = False
    if args.Server_Host:
        ServerHost = args.Server_Host
        log.info(f'Set Server Host from argument to {args.Server_Host}')
    if args.Server_Username:
        ServerUsername = args.Server_Username
        log.info(f'Set Server Username from argument to {args.Server_Username}')
    if args.Server_Password:
        ServerPassword = args.Server_Password
        log.info(f'Set Server Password from argument to {args.Server_Password}')
    
    if args.servername:
        ServerName = args.servername
        log.info(f'Set Crun from argument to {datafile["crun"]}')
    if args.serverport:
        porttoopen = args.serverport
        log.info(f'Set Server Port from argument to {datafile["serverport"]}')
    if porttoopen == 22:
        if args.sshuser:
            user = args.sshuser
            log.info(f'Set SSH User from argument to {user}')
    if args.pport:
        publicport = args.pport
        log.info(f'Set Public Port from argument to {publicport}')
    if args.protocol:
        protocol = args.protocol
        log.info(f'Set SSH Protocol from argument to {protocol}')
    if args.iplock:
        iplocked = args.iplock
        log.info(f'Set IPLock from argument to {iplocked}')
    if args.crun:
        crun = args.crun
        log.info(f'Set Crun from argument to {crun}')

    # * requests input from user
    if ServerHost == None:
        ServerHost = input("Enter Rport Server Host: ")
        log.info(f'Set Server Host from user input to {ServerHost}')
    if ServerUsername == None:
        ServerUsername = input("Enter Rport Server Username: ")
        log.info(f'Set Server Username from user input to {ServerUsername}')
    if ServerPassword == None:
        ServerPassword = input("Enter Rport Server Password: ")
        log.info(f'Set Server Password from user input to {ServerPassword}')
    ServerResponse = getstats(ServerHost,ServerUsername,ServerPassword)
    if ServerResponse != 200:
        log.error(f'Server Response Code: {ServerResponse}')
        print(f"Server responded with code {ServerResponse}")
        input("press enter to close")
        sys.exit(1)
    log.info(f'Server response code: {ServerResponse}')
    AvailableLinuxServers,LinuxServerNumericID = getlinuxservers(ServerHost,ServerUsername,ServerPassword)
    openservices = getopentunnels(ServerHost,ServerUsername,ServerPassword)
    if ServerName:
        for count, value in enumerate(AvailableLinuxServers):
            if value==ServerName:
                # * Sets UI to server numeric id
                ui = LinuxServerNumericID[count]
        log.info(f'Got Server ID from name: {ui}')
    if ui == None:
        printAvailableLinuxServers(AvailableLinuxServers)
        ui = LinuxServerNumericID[int(input())]
        log.info(f'Set Server ID from user input to {ui}')
    if porttoopen == None:
        porttoopen = getport()
        log.info(f'Set Port from user input to {porttoopen}')
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
        log.info(f'Set Public Port from user input to {publicport}')
    if protocol == None:
        protocol = getprotocol()
        log.info(f'Set SSH Protocol from user input to {protocol}')
    if iplocked == None:
        iplocked = getiplock()
        log.info(f'Set IPLock from user input to {iplocked}')
    if not checkifservernameisavailable(ui,AvailableLinuxServers):
        log.critical('Server name is not found')
        print("server not found")
        input("press enter to close")
        sys.exit()
    return ui, user, porttoopen, protocol, iplocked, publicport, ServerHost, ServerUsername, ServerPassword, crun, verbose
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
    if verbose:
        print("Created new tunnel")
    log.info("Created new tunnel")
    jsondata = x.json()
    try:
        jsondata['errors']
        log.critical(jsondata['errors'])
        print("server returned error")
        input("\n\npress enter to close")
        sys.exit()
    except:
        pass
    return jsondata['data']

def main():
    global datafile, openservices, LinuxServerNumericID, AvailableLinuxServers, ip

    ip = requests.get('https://api.ipify.org').content.decode('utf8')
    ui, user, porttoopen, protocol, iplocked, publicport,baseurl,username,password,crun,verbose = getinput()
    AvailableLinuxServers,LinuxServerNumericID = getlinuxservers(baseurl,username,password)
    openservices = getopentunnels(baseurl,username,password)
    if AvailableLinuxServers[ui] in openservices: # * Checks if requested server has open ports
        if verbose:
            print("server has exposed ports")
        log.info("Server has exposed ports")
        for count, value in enumerate(openservices[AvailableLinuxServers[ui]]): # * Itterates over open ports
            #print(value['RecievePort'])
            if str(value['RecievePort']) == str(porttoopen): # * if the wanted port is already open
                if value['ip'] == str(ip) or value['ip'] == "0.0.0.0" or value['ip'] == None: # * if the tunnel allows current IP address
                    data = {'lport':value['port']}
                    log.info("Found existing tunnel")
                    if verbose: print("Found existing tunnel")
                else: # * Tunnel does not allow current IP address, so close the tunnel and create a new one.
                    closetunnel(AvailableLinuxServers[ui],value['id'],baseurl,username,password)
                    log.info("delete old tunnel")
                    if verbose: print("deleted old tunnel")
                    data = opentunnel(AvailableLinuxServers[ui],porttoopen,protocol,publicport, iplocked)
    else: # * No tunnels are opened on requested server, so create a new tunnel.
        data = opentunnel(AvailableLinuxServers[ui],porttoopen,protocol,publicport,baseurl,username,password,iplocked)
    wrotefile = False # * sets wrotefile to False to prevent errors when removing temporary file
    if crun =='ssh': # * if the tunnel is for port 22 (ssh)
        if platform.system() == 'Linux':
            CommandToRun = f"ssh -o StrictHostKeyChecking=no -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -p {data['lport']} {user}@{baseurl.replace('https://', '')}"
        else:
            CommandToRun = f"ssh -o StrictHostKeyChecking=no -o LogLevel=ERROR -o UserKnownHostsFile=\\\\.\\NUL -p {data['lport']} {user}@{baseurl.replace('https://', '')}"
        rc = subprocess_run(CommandToRun, shell=True)
    elif crun != None:
        try:
            rc = subprocess_run(crun, shell=True)
        except Exception as e:
            print("Error running command\n")
            log.warn("Error running command")
            log.warn(e)
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
    log.info("Closing connection")
    if verbose: print("closing connection")
    # * updates openservices with new tunnel information
    openservices = getopentunnels(baseurl,username,password)
    for count, value in enumerate(openservices[AvailableLinuxServers[ui]]): # * for each tunnel open to requested server
        if value['port'] == data['lport']: # * if the destination port is the requested port
            closetunnel(AvailableLinuxServers[ui],value['id'],baseurl,username,password) # * close the tunnel
            print(f'Connection ID {value["id"]} closed') # * print the tunnel id
    input("press enter to close program") # * just waits for user input before closing the program.
if __name__ == '__main__':
    main()