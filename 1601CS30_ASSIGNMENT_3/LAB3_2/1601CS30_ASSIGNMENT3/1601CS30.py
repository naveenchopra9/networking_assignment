from socket import *
serverSocket = socket(AF_INET, SOCK_STREAM)

host = "172.16.147.234"	
port = 8036

print('The Web server is up on the IP:      ', host)
print('The Web server is up on port number: ', port)
serverSocket.bind((host, port))		

n = int(input("Enter the number of requests: "))
serverSocket.listen(n)
while (n>0):
	connectionSocket, addr = serverSocket.accept()
	print('Ready to operate... ', connectionSocket)
	try:
		message = connectionSocket.recv(1024).decode()
		print(message, '::', message.split()[0], ':', message.split()[1])
		filename = message.split()[1]
		if filename=="/":
			filename = "/index.html"
		f = open(filename[1:])
		outputdata = f.read()
		print(outputdata)
		connectionSocket.send(bytes('HTTP/1.1 200 OK\r\n\r\n','UTF-8'))
		connectionSocket.sendall(outputdata.encode('utf-8'))
		connectionSocket.close()
		n = n-1
	except IOError:
		connectionSocket.send(bytes('HTTP/1.1 404 Not Found\r\n\r\n','UTF-8'))
		connectionSocket.close()
connectionSocket.close()
serverSocket.close()