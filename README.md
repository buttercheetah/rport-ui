# rport-ui
This is probably the messiest way of temporarily forwarding ports using rport.

Q: Are there better ways of doing this?
A: Probably

Please dont blame me if this messes something up for you.

## Please note, even though this repository is named 'rport-ui', this script is only has a cli.

# To run the program.
Steps
1. run the executable under the releases tab
1.1 *optionaly:* run the program as an python script.

If desired, you can run the command with arguments passed directly, so no interaction from the user is required. please note, any argument not passed (with the exception of sshuser) will need to be entered by the user directly. Please note, arguments passed directly will take precedence over arguments passed through the configuration file.

Note: any unwanted options in the configuration file can be removed, the program will ask for user input if required.

| Command          | Description                                           |
| ---------------- | ----------------------------------------------------- |
| --cfile          | Pass a file with all arguments. See the example file  |
| --server         | The name of the machine in rport                      |
| --port           | The private port of the machine                       |
| --pport          | The port that you wish to forward on the rport server |
| --protocol       | The protocol of the connection either tcp or udp      |
| --iplock         | if the tunnel is locked to your current ip address (recommended for security)    |
| --sshuser        | if the tunnel port is 22 it is assumed to be a ssh connection and writes a temporary ssh file. for this, it requires a ssh user to create the file|
| Server_Host      | The FQDN of the rport server. Include http/https      |
| Server_Username  | The username of the rport server                      |
| Server_Password  | The API key of the rport server                       |




>`python rport-ui.py [--server SERVERNAME] [--port SERVERPORT] [--pport PPORT] [--protocol PROTOCOL] [--IPLock IPLOCK] [--sshuser SSHUSER] Server_Host Server_Username Server_Password`

example for ssh
>`python rport-ui.py --server VM1 --port 22 --pport -1 --protocol tcp --IPLock True --sshuser username1 https://www.domain.com rportAdmin rportAPIKey`

example for http server
>`python rport-ui.py --server webserver1 --port 80 --pport 80 --protocol tcp --IPLock False username1 https://www.domain.com rportAdmin rportAPIKey`
