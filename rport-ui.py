import requests
import platform
import json
import os
import sys
from subprocess import call, run

# Opening JSON file
f = open('config.json')
  
# returns JSON object as 
# a dictionary
datafile = json.load(f)

#cleanup
f.close()

ip = requests.get('https://api.ipify.org').content.decode('utf8')

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

else:
    printAvailableLinuxServers(AvailableLinuxServers)
    ui, user, porttoopen, protocol, iplocked, publicport = getuserinput()
if AvailableLinuxServers[ui] in openservices:
    print("server has exposed ports")
    for count, value in enumerate(openservices[AvailableLinuxServers[ui]]):
        print(value['RecievePort'])
        if str(value['RecievePort']) == str(porttoopen):
            if value['ip'] == str(ip) or value['ip'] == "0.0.0.0" or value['ip'] == None:
                data = {'lport':value['port']}
                print("Found existing tunnel")
            else:
                closetunnel(AvailableLinuxServers[ui],value['id'])
                print("deleted old tunnel")
                data = opentunnel(AvailableLinuxServers[ui],porttoopen,protocol,publicport, iplocked)
else:
    data = opentunnel(AvailableLinuxServers[ui],porttoopen,protocol,publicport,iplocked)
wrotefile = False
if porttoopen == 22:
    wrotefile = True
    if platform.system() == 'Windows':
        ext = 'cmd'
    elif platform.system() == 'Linux':
        ext ='sh'
    if writesshfile(str(data['lport']), user, ext):
        rc = call(os.getcwd()+'/tempfile.'+ext, shell=True)
    else:
        print("error writing temp file")
else:
    run = True
    while run:
        print(f"Port {porttoopen}->{data['lport']}")
        print("This connection will be open for 24 hours")
        print(f'{datafile["baseurl"].replace("https://", "")}:{data["lport"]}')
        print("press q to close connection")
        uit = input()
        if uit == 'q':
            run = False
if wrotefile:
    print("Removing temporary file")
    os.remove(f'tempfile.{ext}')
print("closing connection")
openservices = getopentunnels()
for count, value in enumerate(openservices[AvailableLinuxServers[ui]]):
    if value['port'] == data['lport']:
        closetunnel(AvailableLinuxServers[ui],value['id'])
        print(f'Connection ID {value["id"]} closed')
input("press enter to close program")