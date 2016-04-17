lPort = 7000
mPort = 55084
mHost = "128.10.12.136"
otherHosts = {1: 'xinu01.cs.purdue.edu', 2: 'xinu12.cs.purdue.edu', 3: 'xinu03.cs.purdue.edu', 4: 'xinu04.cs.purdue.edu', 5: 'xinu05.cs.purdue.edu', 6: 'xinu11.cs.purdue.edu', 7: 'xinu07.cs.purdue.edu', 8: 'xinu08.cs.purdue.edu', 9: 'xinu09.cs.purdue.edu', 10: 'xinu10.cs.purdue.edu'}
waitTill = 1459007150.83
maxCrashes = 3
maxMsgLen = 1024
import sys
import os
from socket import *
from select import select
import SocketServer
from subprocess import Popen, PIPE
import time
import random
from sets import Set
myName = gethostname()
emptyVal = -2
heartBeat = -3
voteRequest = -4
acceptVoteRequest = -5
rejectVoteRequest = -6
heartBeatResponse = -7
diedSuffix = 100
myId = emptyVal
currentValues = {}
currentLeader = emptyVal
acceptedHosts = Set([])
respondedToHeartBeat = Set([])
currentState = 0   # 0 for follower 1 for candidate 2 for leader
leader = 2; candidate = 1; follower = 0;
currentTerm = 0 # everyone starts in 0th term
currentElectionRound = 0
timeoutRangeMin = 150 # this is in millisecond
timeoutRangeMax = 300 # this is in millisecond
electionTimeout = 0 # this will be set in main for the first time
heartBeatTimeout = 0 # useful only if I am leader
votedForThisTerm = False
votedFor = emptyVal

def sendLog(msg,level):
    if level<1:
        return
    #print(msg)
    msg = time.strftime("%H:%M:%S", time.localtime(time.time())) + " Node "+str(myId)+": " +msg
    sock = socket(AF_INET,SOCK_STREAM)
    sock.connect((mHost, mPort))
    try:
        sock.sendall(msg)
    finally:
        sock.close()

def setUpCommonParameters():    # deletes self from host dict and sets myId
    global myId
    #global otherHosts
    for i in otherHosts:
        if otherHosts[i] == myName:
            del otherHosts[i]
            myId = i
            break
    fillRespondedToHeartBeat()

def contestingElection():
    return currentElectionRound > 0

def fillRespondedToHeartBeat(): 
    global respondedToHeartBeat
    respondedToHeartBeat = Set([])
    for i in otherHosts:
        respondedToHeartBeat.add(i)

def currentLeaderDied():
    if currentLeader != emptyVal:
        sendLog("leader node "+str(currentLeader)+" has crashed",2)
        setCurrentLeaderTo(emptyVal)

def sendVoteRequestToAll(): 
    for host in otherHosts.keys():
        sendVoteRequestTo(host)

def sendVoteRequestTo(host):
    sendTo(host,voteRequest)

def died(this):
    if this == emptyVal:
        return
    global otherHosts
    global respondedToHeartBeat
    sendLog("Node "+str(this)+" died",0)
    if this in otherHosts:
        del otherHosts[this]
    if this in respondedToHeartBeat:
        respondedToHeartBeat.remove(this)
    if this == currentLeader:
        currentLeaderDied()

def diedDetected(this):
    died(this)
    sendToAll(diedSuffix+this)

def checkIfAnyOneDied():
    temp = []
    for host in otherHosts:
        if host not in respondedToHeartBeat:
            temp.append(host)
    for host in temp:
        diedDetected(host)
    temp = []

def sendHeartBeatToAll():
    global respondedToHeartBeat
    sendLog("Sending heartbeat",0)
    checkIfAnyOneDied()
    respondedToHeartBeat = Set([])
    for host in otherHosts.keys():
        sendHeartBeatTo(host)
    refreshHeartBeatTimeout()

def sendHeartBeatTo(hid):
    if currentState == leader:
        sendTo(hid,heartBeat)

def refreshHeartBeatTimeout():
    global heartBeatTimeout
    heartBeatTimeout = int(round(time.time()*1000)+timeoutRangeMin/2)

def setCurrentTermTo(this): # sets only if this is greater than currentTerm
    global currentTerm
    global votedForThisTerm
    global votedFor
    if this > currentTerm:
        currentTerm = this
        votedForThisTerm = False
        votedFor = emptyVal

def setCurrentLeaderTo(this):
    global currentLeader
    if currentLeader != this and this != emptyVal:
        sendLog("node "+str(this)+" is elected as new leader",2)
    currentLeader = this
    if this != emptyVal:
        setCurrentElectionRoundTo(0)

def sendHeartBeatResponseTo(this):
    sendTo(this,heartBeatResponse)

def setCurrentElectionRoundTo(this):
    global currentElectionRound
    currentElectionRound = this

def setCurrentStateTo(this):
    global currentState
    currentState = this

def refreshElectionTimeout():
    global electionTimeout
    electionTimeout = int(round(time.time()*1000)+random.uniform(timeoutRangeMin,timeoutRangeMax))

def sendToAll(value):
    for host in otherHosts.keys():
        sendTo(host,value)

def sendTo(hid, value):
    hName = otherHosts[hid]
    s = socket(AF_INET,SOCK_DGRAM)
    data = str(myId)+" "+str(currentTerm)+" "+str(value)
    s.sendto(data, (hName,lPort))
    s.close()
    sendLog("sending: "+ str(value) +" to : "+hName,0)

def recvMsg(sock):
    msg, addr = sock.recvfrom(maxMsgLen)
    msg = msg.split()
    sendersId = int(msg[0])
    sendersTerm = int(msg[1])
    sendersValue = int(msg[2])
    sendLog("recvd: "+ str(sendersValue) +" from : "+str(sendersId),0)
    actOnMsg(sendersId, sendersTerm, sendersValue)

def voteFor(this): 
    global votedForThisTerm
    global votedFor
    votedForThisTerm = True
    votedFor = this
    if this != myId:
        sendTo(this,acceptVoteRequest)
    else:
        voteRequestAcceptedBy(myId)
    refreshElectionTimeout()

def voteRequestAcceptedBy(this):
    global acceptedHosts
    global currentElectionRound
    acceptedHosts.add(this)
    if len(acceptedHosts)> ((len(otherHosts)+1)/2):
        if currentElectionRound > maxCrashes:
            becomeLeader()
        else:
            startNewElectionRound()

def heartBeatResponseReceivedFrom(this):
    respondedToHeartBeat.add(this)    

def actOnHeartBeatReceivedFrom(this):
    sendLog("received heartbeat",0)
    refreshElectionTimeout()
    setCurrentStateTo(follower)
    if currentLeader != this:
        setCurrentLeaderTo(this)
    sendHeartBeatResponseTo(this)

def actOnVoteRequestFrom(this):
    if votedForThisTerm or currentState == candidate:
        if votedForThisTerm and votedFor == this:
            sendTo(this,acceptVoteRequest)
            return
        sendTo(this,rejectVoteRequest)
    else:
        voteFor(this)

def actOnMsg(sendersId, sendersTerm, sendersValue):
    if sendersValue == heartBeatResponse:
        heartBeatResponseReceivedFrom(sendersId)
        return
    if sendersValue >= diedSuffix:
        died(sendersValue - diedSuffix)
        return
    if currentTerm>sendersTerm:
        return
    elif currentTerm == sendersTerm:
        if sendersValue == heartBeat:
            actOnHeartBeatReceivedFrom(sendersId)
        elif sendersValue == voteRequest:
            actOnVoteRequestFrom(sendersId)
        elif sendersValue == acceptVoteRequest:
            voteRequestAcceptedBy(sendersId)
    else:
        setCurrentTermTo(sendersTerm)
        setCurrentStateTo(follower)
        if sendersValue == heartBeat:
            actOnHeartBeatReceivedFrom(sendersId)
        elif sendersValue == voteRequest:
            actOnVoteRequestFrom(sendersId)

def becomeLeader():
    if currentState == leader:
        return
    setCurrentElectionRoundTo(0)
    setCurrentStateTo(leader)
    setCurrentLeaderTo(myId)
    sendLog("node "+str(currentLeader)+" is elected as new leader",2)
    fillRespondedToHeartBeat()
    sendHeartBeatToAll()

def initiateElection():
    sendLog("begin another leader election",2)
    setCurrentTermTo(currentTerm + 1)
    setCurrentElectionRoundTo(0)
    setCurrentStateTo(candidate)
    startNewElectionRound()

def startNewElectionRound():
    global acceptedHosts
    setCurrentElectionRoundTo(currentElectionRound+1)
    acceptedHosts = Set([])
    voteFor(myId)
    sendVoteRequestToAll()

if __name__ == "__main__":
        # formatting global parameters
    setUpCommonParameters()
        # making udp socket to listen
    listner = socket(AF_INET, SOCK_DGRAM)
    listner.bind((myName,lPort))
        # sleeping to ensure that every one gets binded before anyone starts sending
    time.sleep(2*len(otherHosts)+15)
    refreshElectionTimeout()
    refreshHeartBeatTimeout()
    timeout = (timeoutRangeMin/10)*.001
    timeoutAt = time.time()+40*60
        # entering into long listening loop
    while time.time()<timeoutAt:
        reader, writer, excep = select([listner],[],[],timeout)
        if reader:
            recvMsg(reader[0])
        if electionTimeout<=int(round(time.time()*1000)) and currentState != leader and not contestingElection():
            if currentLeader != emptyVal:
                diedDetected(currentLeader)
                currentLeaderDied()
            initiateElection()
        if currentState == leader and heartBeatTimeout<=int(round(time.time()*1000)):
            sendHeartBeatToAll()
