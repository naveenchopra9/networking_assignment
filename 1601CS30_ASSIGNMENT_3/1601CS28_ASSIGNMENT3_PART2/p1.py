#import socket module
from socket import *
serverSocket = socket(AF_INET, SOCK_STREAM)
#Prepare a sever socket
#Fill in start

host = "172.16.184.88"		# Get local machine name
port = 8000			 # Reserve a port for your service.

print (host)
print (port)
print()
serverSocket.bind((host, port))		# Bind to the port


serverSocket.listen(1)
print ('the web server is up on port:',port)
while True:
	 #Establish the connection
	 connectionSocket, addr = serverSocket.accept()
	 print('Ready to serve...')
	 try:
		 message = connectionSocket.recv(1024).decode()
		 print (message,'::',message.split()[0],':',message.split()[1])
		 filename = message.split()[1]
		 # print (filename,'||',filename[1:])
		 f = open(filename[1:])
		 outputdata = f.read()
		 print(outputdata)
		 #Send one HTTP header line into socket
		 #Fill in start
		 connectionSocket.send(bytes('HTTP/1.1 200 OK\r\n\r\n','UTF-8'))
		 connectionSocket.sendall(outputdata.encode('utf-8'))
		 #Fill in end
		 #Send the content of the requested file to the client
		 for i in range(0, len(outputdata)):
			 connectionSocket.send(outputdata[i].encode('utf-8'))
		 connectionSocket.close()	 
	 except IOError:
		 #Send response message for file not found
		 #Fill in start
		 connectionSocket.send('\nHTTP/1.1 404 Not Found\n\n')
		 #Close client socket
		 connectionSocket.close()
connectionSocket.close()
