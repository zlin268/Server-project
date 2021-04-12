import socket
import os
import datetime
import signal
import sys
import argparse
from urllib.parse import urlparse
from socket import timeout

# Constant for our buffer size

BUFFER_SIZE = 1024

# Signal handler for graceful exiting.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    sys.exit(0)

# Create an HTTP response

def prepare_response_message(value):
    date = datetime.datetime.now()
    date_string = 'Date: ' + date.strftime('%a, %d %b %Y %H:%M:%S EDT')
    message = 'HTTP/1.1 '
    if value == '200':
        message = message + value + ' OK\r\n' + date_string + '\r\n'
    elif value == '404':
        message = message + value + ' Not Found\r\n' + date_string + '\r\n'
    elif value == '501':
        message = message + value + ' Method Not Implemented\r\n' + date_string + '\r\n'
    elif value == '505':
        message = message + value + ' Version Not Supported\r\n' + date_string + '\r\n'
    elif value == '301':
        message = message + value + ' Moved Permanently\r\n' + date_string + '\r\n'
    return message

def prepare_get_message(host, port, file_name):
    request = f'GET {file_name} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n' 
    return request


def send_response_to_client(sock, code, server_addr):
    file_size = os.path.getsize("301.html")
    header = prepare_response_message(code) + 'Content-Type: text/html' + '\r\nContent-Length: ' + str(len(server_addr) + len('Location:/\n') + file_size) + '\r\n\r\n'
    sock.send(header.encode())
    sock.send(str.encode('Location: ' + server_addr + "\n"))

    with open("301.html", 'rb') as file_to_send:
        while True:
            chunk = file_to_send.read(BUFFER_SIZE)
            if chunk:
                sock.send(chunk)
            else:
                break



# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.

def get_line_from_socket(sock):

    done = False
    line = ''
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\r'):
            pass
        elif (char == '\n'):
            done = True
        else:
            line = line + char
    return line

# Our main function.

def sort_by_response(response_times, server_hosts, server_ports, server_urls): 


    # sort each array with response time using insertion sort
    for i in range(1, len(response_times)): 
        host_key = server_hosts[i]
        port_key = server_ports[i]
        response_key = response_times[i]
        url_key = server_urls[i]
        j = i-1
        while j >=0 and response_key < response_times[j] : 
                server_hosts[j+1] = server_hosts[j]
                server_ports[j+1] = server_ports[j]
                response_times[j+1] = response_times[j] 
                server_urls[j+1] = server_urls[j]
                j -= 1
        response_times[j+1] = response_key
        server_ports[j+1] = port_key
        server_hosts[j+1] = host_key
        server_urls[j+1] = url_key

def save_file_from_socket(sock, bytes_to_read, file_name):
    with open(file_name, 'wb') as file_to_write:
        bytes_read = 0
        while (bytes_read < bytes_to_read):
            chunk = sock.recv(BUFFER_SIZE)
            bytes_read += len(chunk)
            file_to_write.write(chunk)

def get_server_responses(server_hosts, server_ports):


    response_times = []

    # connect to each server
    # obtain the largest file and compute response time
    for i, host in enumerate(server_hosts):
        port = server_ports[i]
        print('Connecting to server ...', "http://" + host + ":" + str(port))
        try:

            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            start = datetime.datetime.now()
            client_socket.connect((host, port))

            # reterive test.txt
            message = prepare_get_message(host, port, "test.txt")
            client_socket.send(message.encode())
            response_line = get_line_from_socket(client_socket)

            response_list = response_line.split(' ')
            headers_done = False
            if response_list[1] != '200':
                print('Error:  An error response was received from the server:\n', "http://" + host + ":" + str(port))
                response_times.append(start - datetime.datetime.now())    
            else:
                bytes_to_read = 0
                while (not headers_done):
                    header_line = get_line_from_socket(client_socket)
                    header_list = header_line.split(' ')
                    if (header_line == ''):
                        headers_done = True
                    elif (header_list[0] == 'Content-Length:'):
                        bytes_to_read = int(header_list[1])
                save_file_from_socket(client_socket, bytes_to_read, 'savedText.txt')
            end = datetime.datetime.now()
            client_socket.close()
            print("Response time", end - start)

            # update response time
            response_times.append(end - start)
        except ConnectionRefusedError:
            print('Error:  That host or port is not accepting connections.', "http://" + host + ":" + str(server_ports[i]))
            response_times.append(start - datetime.datetime.now())
    return response_times

def main():

    # Register our signal handler for shutting down.

    # Check command line arguments to retrieve a URL.

    argc = len(sys.argv)

    if argc < 2:
        print("Please provide at-least one url")
        sys.exit(1)
    parser = argparse.ArgumentParser()

    for i in range(1, argc):
        parser.add_argument("url" + str(i), help="URL to fetch with an HTTP GET request")
    args = parser.parse_args()

    # Check the URL passed in and make sure it's valid.  If so, keep track of
    # things for later.

    server_urls = []
    server_ports = []
    server_hosts = []
    #check if urls provided are in current format --> http://host:port
    for i in range(1, argc):
        parsed_url = urlparse(args.__dict__['url' + str(i)])
        try:
            if ((parsed_url.scheme != 'http') or (parsed_url.port == None) or (parsed_url.hostname == None)):
                raise ValueError
            host = parsed_url.hostname
            port = parsed_url.port
            server_hosts.append(host)
            server_ports.append(port)
            server_urls.append('http://' + host + ':' + str(port))
        except ValueError:
            print('Error:  Invalid URL.  Enter a URL of the form:  http://host:port')
            sys.exit(1)

    print(server_urls)
    # connect to each server and obtain response times
    response_times = get_server_responses(server_hosts, server_ports)


    # sort the server with reponse times
    sort_by_response(response_times, server_hosts, server_ports, server_urls)
    print(response_times, server_urls)
    signal.signal(signal.SIGINT, signal_handler)

    # Create the socket.  We will ask this to work on any interface and to pick
    # a free port at random.  We'll print this out for clients to use.

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', 0))
    print('Will wait for client connections at port ' + str(server_socket.getsockname()[1]))
    server_socket.listen(1)
    server_socket.settimeout(60)
    # index of the server that is currently serving
    serv_idx = 0
    total_servers = len(server_urls)


    # if current server is down then pick the next server
    q = 0
    while response_times[serv_idx].total_seconds() < 0 and q < total_servers:
        serv_idx = (serv_idx + 1) % total_servers
        q += 1

    #fastest server serves maximum requests
    current_serving_attemps = total_servers - serv_idx
     # Keep the balancer running forever.
    while(1):
        print('Waiting for incoming client connection ...')
        
        try:
            conn, addr = server_socket.accept()
            print('Accepted connection from client address:', addr)
            print('Connection to client established, waiting to receive message...')


            # We obtain our request from the socket.  We look at the request and
            # figure out what to do based on the contents of things.

        
            request = get_line_from_socket(conn)
            print('Received request:  ' + request)
            request_list = request.split()

            # This server doesn't care about headers, so we just clean them up.

            while (get_line_from_socket(conn) != ''):
                pass

            # If we did not get a GET command respond with a 501.

            if request_list[0] != 'GET':
                print('Invalid type of request received ... responding with error!')
                send_response_to_client(conn, '501', '501.html')

            # If we did not get the proper HTTP version respond with a 505.

            elif request_list[2] != 'HTTP/1.1':
                print('Invalid HTTP version received ... responding with error!')
                send_response_to_client(conn, '505', '505.html')

            # We have the right request and version, so check if file exists.
                      
            else:

                # if prvious server's requests are finished then select new server
                if current_serving_attemps <= 0:


                    serv_idx = (serv_idx + 1) % total_servers
                    # if current server is down then pick the next server
                    q = 0
                    while response_times[serv_idx].total_seconds() < 0 and q < total_servers:
                        serv_idx = (serv_idx + 1) % total_servers
                        q+=1

                    # if total_servers are three 
                    # then server 1 (fastest) will serve three requests
                    # then server 2 (normal) will serve two requests
                    # then server 3 (slowest) will serve one request
                    current_serving_attemps = total_servers - serv_idx
                # If requested file begins with a / we strip it off.

                server_addr = server_urls[serv_idx]
                print('Request Received, Sending Message')

                # send the address of server
                send_response_to_client(conn, '301', server_addr)
                current_serving_attemps -= 1
                    
            # We are all done with this client, so close the connection and
            # Go back to get another one!

        except timeout:
            response_times = get_server_responses(server_hosts, server_ports)
            sort_by_response(response_times, server_hosts, server_ports, server_urls)
            print("/////////////////////////////////////////////////////////////////")
            print("List updated")
            print(response_times, server_urls)
            serv_idx = 0
            q = 0
            # if current server is down then pick the next server
            while response_times[serv_idx].total_seconds() < 0 and q < total_servers:
                serv_idx = (serv_idx + 1) % total_servers
                q+=1
            current_serving_attemps = total_servers - serv_idx

    conn.close();
    

if __name__ == '__main__':
    main()

