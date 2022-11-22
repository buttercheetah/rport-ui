import requests
import platform
import json
import os
import sys
from subprocess import call, run



def getstats():
    # * Gets status
    x = requests.get(f'{datafile["baseurl"]}/api/v1/status',auth=(datafile['username'], 'datafile["password"]'))
    return x
def getlinuxservers():
    # * Gets all linux servers
    x = requests.get(f'{datafile["baseurl"]}/api/v1/clients?filter[os_kernel]=linux',auth=(datafile['username'], datafile['password']))
    jsondata = x.json()
    data = jsondata['data']
    # * Creates new data structure with response
    AvailableLinuxServers = {}
    LinuxServerNumericID = {}
    for count, x in enumerate(data):
        AvailableLinuxServers[x['name']] = x['id']
        LinuxServerNumericID[count] = x['name']
    return AvailableLinuxServers, LinuxServerNumericID
def getopentunnels():
    # * checks all open ports
    x = requests.get(f'{datafile["baseurl"]}/api/v1/tunnels',auth=(datafile['username'], datafile['password']))
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
def getuserinput():
    # * requests input from user
    ui = LinuxServerNumericID[int(input())]
    porttoopen = int(input("Enter port to open: "))
    if porttoopen == 22:
        protocol = 'tcp'
        user = input("Enter username: ")
        if user == "":
            user = "bhghdhfh"
        publicport = -1
    else:
        print('Which protocol do you want?\n1) TCP\n2) UDP\n')
        tmpui = input(":")
        if tmpui == '2':
            protocol = 'udp'
        else:
            protocol = 'tcp'
        print('IP locked? [Y/n]')
        tmpui = input(":")
        if tmpui.upper() == 'N':
            iplocked = False
        else:
            iplocked = True
        user = ""
        print("What port would you like to open?")
        print("leave blank for auto-configuration")
        tmpui = input(":")
        if tmpui == '' or not tmpui.isnumeric():
            publicport = -1
        else:
            publicport = int(tmpui)
    return ui, user, porttoopen, protocol, iplocked, publicport
def checkifservernameisavailable(sn,sl):
    return sn in sl
def closetunnel(client,tunnel):
    x = requests.delete(f'{datafile["baseurl"]}/api/v1/clients/{client}/tunnels/{tunnel}?force=true',auth=(datafile['username'], datafile['password']))
def opentunnel(client,port,protocol,publicport,iplocked=True):
    tmpstr = "&check_port=0"
    if iplocked:
        tmpstr += '&acl='+str(ip)
    if port != 22:
        tmpstr += '&auto-close=24h'
    if publicport != -1:
        tmpstr += '&local='+str(publicport)
    tmpstr += "&protocol="+str(protocol)
    port = str(port)
    x = requests.put(f'{datafile["baseurl"]}/api/v1/clients/{client}/tunnels?remote={port}{tmpstr}',auth=(datafile['username'], datafile['password']))
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
def writesshfile(port,user,ext):
    # * Creates script to ssh to server
    try:
        with open('tempfile.'+ext, 'w') as f:
            if platform.system() == 'Linux':
                f.write("#!/bin/bash\n")
                f.write("ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o 'LogLevel ERROR' -p "+port+" "+user+"@rport.iefi.xyz")
            else:
                f.write("ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=\\\\.\\NUL -p "+port+" "+user+"@rport.iefi.xyz")
            print('Wrote File')
        if platform.system() == 'Linux':
            run(["chmod","+x",str(os.getcwd()+'/tempfile.'+ext)])
        return True
    except:
        return False

def main():
    # Opening JSON file
    f = open('config.json')
    
    # returns JSON object as 
    # a dictionary
    datafile = json.load(f)

    #cleanup
    f.close()

    ip = requests.get('https://api.ipify.org').content.decode('utf8')
    AvailableLinuxServers,LinuxServerNumericID = getlinuxservers()
    openservices = getopentunnels()
    # * Checks if arguments were passed, assume ssh
    if len(sys.argv) > 1:
        porttoopen = 22
        protocol = 'tcp'
        publicport = -1
        iplocked = True
        if not checkifservernameisavailable(sys.argv[1],AvailableLinuxServers):
            print("server not found")
            input("press enter to close")
            sys.exit()
        if len(sys.argv) > 2:
            # * if two arguments are passed, the second is server username
            user = sys.argv[2]
        else:
            # * otherwise, the user is defaulted to bhghdhfh
            user = "bhghdhfh"
        for count, value in enumerate(AvailableLinuxServers):
            if value==sys.argv[1]:
                # * Sets UI to server numeric id
                ui = LinuxServerNumericID[count]
    else: # * no arguments
        printAvailableLinuxServers(AvailableLinuxServers)
        ui, user, porttoopen, protocol, iplocked, publicport = getuserinput()
    if AvailableLinuxServers[ui] in openservices: # * Checks if requested server has open ports
        print("server has exposed ports")
        for count, value in enumerate(openservices[AvailableLinuxServers[ui]]): # * Itterates over open ports
            #print(value['RecievePort'])
            if str(value['RecievePort']) == str(porttoopen): # * if the wanted port is already open
                if value['ip'] == str(ip) or value['ip'] == "0.0.0.0" or value['ip'] == None: # * if the tunnel allows current IP address
                    data = {'lport':value['port']}
                    print("Found existing tunnel")
                else: # * Tunnel does not allow current IP address, so close the tunnel and create a new one.
                    closetunnel(AvailableLinuxServers[ui],value['id'])
                    print("deleted old tunnel")
                    data = opentunnel(AvailableLinuxServers[ui],porttoopen,protocol,publicport, iplocked)
    else: # * No tunnels are opened on requested server, so create a new tunnel.
        data = opentunnel(AvailableLinuxServers[ui],porttoopen,protocol,publicport,iplocked)
    wrotefile = False # * sets wrotefile to False to prevent errors when removing temporary file
    if porttoopen == 22: # * if the tunnel is for port 22 (ssh)
        wrotefile = True
        # * sets the file extension based on host os
        if platform.system() == 'Windows':
            ext = 'cmd'
        elif platform.system() == 'Linux':
            ext ='sh'
        if writesshfile(str(data['lport']), user, ext): # * tries to write to the file, if it errors out, it does not call the file.
            rc = call(os.getcwd()+'/tempfile.'+ext, shell=True) # * calls tempfile
        else:
            print("error writing temp file")
    else:
        # * a simple while loop or user input
        run = True
        while run:
            # * prints out the tunnel information
            print(f"Port {porttoopen}->{data['lport']}")
            print("This connection will be open for 24 hours")
            # * prints out the baseurl with the port number for easy copying
            print(f'{datafile["baseurl"].replace("https://", "")}:{data["lport"]}')
            print("press q to close connection")
            uit = input()
            if uit.lower() == 'q': # * if user inputs q
                run = False # * exit while loop
    if wrotefile: # * if the file has been written, remove the file.
        print("Removing temporary file")
        os.remove(f'tempfile.{ext}')
    print("closing connection")
    # * updates openservices with new tunnel information
    openservices = getopentunnels()
    for count, value in enumerate(openservices[AvailableLinuxServers[ui]]): # * for each tunnel open to requested server
        if value['port'] == data['lport']: # * if the destination port is the requested port
            closetunnel(AvailableLinuxServers[ui],value['id']) # * close the tunnel
            print(f'Connection ID {value["id"]} closed') # * print the tunnel id
    input("press enter to close program") # * just waits for user input before closing the program.
if __name__ == '__main__':
    main()