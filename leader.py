import sys
import os
import re
import numpy as np
import subprocess
import getpass
import socket
import SocketServer
from subprocess import Popen, PIPE
import time
from select import select

def raiseError(message="", exit = False, exitCode = 1):
    print message
    if exit:
        sys.exit(exitCode)
        
def extractArgFor(thisOption): 
    for x in range(1,len(sys.argv),2):
        if(sys.argv[x])==thisOption:
            return sys.argv[x+1]
    return ""

def checkArgValidity():
    if len(sys.argv)<7:
        raiseError(message="Too few arguments.", exit = True)
    if len(sys.argv)>7:
        raiseError(message="Too many arguments.", exit = True)
    port = extractArgFor("-p")
    if (port.isdigit()==False):
        raiseError(message="Port should be integer.", exit = True)
    elif 1023<int(port)<65536:
        pass
    else:
        raiseError(message="Port is out of range.", exit = True)
    hostFile = extractArgFor("-h")
    if hostFile == "":
        raiseError(message="Hostfile is non existant", exit = True)
    numHost = sum(1 for line in open(hostFile))
    if numHost<1:
        raiseError(message="Hostfile is empty", exit = True)
    maxCrashes = extractArgFor("-f")
    if (maxCrashes.isdigit()==False):
        raiseError(message="Number of max crash should be integer.", exit = True)
    elif 0<int(maxCrashes)<numHost-2:
        pass
    else:
        raiseError(message="Max crash is out of range.", exit = True)

    return int(port), hostFile, int(maxCrashes)

def editFile(filePath,lineNums,newLines):
    f =  open(filePath)
    temp = f.readlines()
    f.close()
    for x in range(len(lineNums)):
        temp[lineNums[x]] = newLines[x]
    f = open(filePath,'w')
    for line in temp:
        f.write(line)
    f.close()

def setUpMessagePrinter(): 
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.bind((socket.gethostname(),0))
    port = s.getsockname()[1]
    s.listen(50)
    timeout = 2000
    inputsockets = [s]
    t = os.fork()
    if  t==0:
        while True:
            rlist, wlist, xlist = select(inputsockets,[],[],timeout)
            if not rlist and not wlist and not xlist:
                s.close()
                sys.exit(0)
            for insock in rlist:
                if insock is s:
                    new_socket, addr = s.accept()
                    inputsockets.append(new_socket)      
                else:
                    data = insock.recv(1024)
                    if data:
                        print data
                        insock.close()
                        inputsockets.remove(insock)
    return (socket.gethostbyname(socket.gethostname()),port)

class Host(object):
    def __init__(self, hid, hname, pathToScript):
        self.id = hid;
        self.name = hname;
        command = 'python '+pathToScript
        ssh = subprocess.Popen(["ssh", "%s" %self.name, command],shell=False,stdout=None, stderr=None, stdin=None)

if __name__ == '__main__':
    lPort, hostFile, maxCrashes = checkArgValidity()
    processScript = os.getcwd()+'/process.py'
    mHost, mPort = setUpMessagePrinter()
    hosts = {}
    with open(hostFile, 'r') as hf:
        for line in hf:
            x = line.split()
            hosts[int(x[0])] = x[1]
    editFile(processScript,[0,1,2,3,4,5],['lPort = '+str(lPort)+'\n','mPort = '+str(mPort)+'\n','mHost = \"'+str(mHost)+'\"\n','otherHosts = '+str(hosts)+'\n','waitTill = '+str(time.time()+len(hosts))+'\n','maxCrashes = '+str(maxCrashes)+'\n'])
    for hid in hosts:
        Host(hid, hosts[hid], processScript)
