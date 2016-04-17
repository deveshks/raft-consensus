#sendLog(myName+" -exit- "+str(time.time()))
#sendLog(myName+" -entry- "+str(time.time()))
#sendLog(myName+" -first- "+str(time.time()))


count = 5
while(count>0):
    sleep(3)
    sendLog("H: "+str(count)+": "+socket.gethostname())
    count -=1
