#! /usr/bin/python

# This is the module that controls the messages sent via XBee to the Arduino Uno attached to the ProLite
# LED sign. It has been modified to send JSON formatted messages with a master key of Prolite and a subkey
# Message containing the Prolite formatted message.

from apscheduler.schedulers.background import BackgroundScheduler
#import subprocess
import logging
#import datetime
import Queue
import time
import sqlite3
import sys
import sysv_ipc

SignPage = 0

Diff = 10
minDiff = 5
setPoint = 86

DATABASE='/home/pi/DataBase/Aspenwood.db'

# The Cqueue is for house commands and Lqueue is for light commands
Cqueue = sysv_ipc.MessageQueue(12, sysv_ipc.IPC_CREAT,mode=0666)
#Lqueue = sysv_ipc.MessageQueue(13, sysv_ipc.IPC_CREAT,mode=0666)

#packets = Queue.Queue() # When I get a packet, I put it on here

#--------Actually send the command to the housemonitor

def sendCommand(message, whichQueue=Cqueue):
    
    try:
        # type 1 messages are for testing, type 2 originate 
        # from the web interface and type 3 originate here
        whichQueue.send(message, block=False, type=3)
    except sysv_ipc.BusyError:
        # I have to think more about what to do with this.
        print "Busy error when sending command", time.strftime("%A, %B, %d at %H:%M:%S")
    sys.stdout.flush()

def handleCommand(command):
    
    #lprint(" " + str(command))
    # the command comes in from php as something like
    # ('s:17:"AcidPump, pumpOff";', 2)
    # so command[0] is 's:17:"AcidPump, pumpOff'
    # then split it at the "  and take the second item
    try:
        c = str(command[0].split('\"')[1]).split(',')
    except IndexError:
        c = str(command[0]).split(' ')    #this is for something I sent from another process
    #lprint(c)
    cmd = c[0]

    
    
    if cmd == 'Toggle':
        if ShowSign:
            SignOff()
        else:
            SignOn()
    
    else:
        print("Invalid Command = " + str(c))

def ReadDatabase2(database, attrib):
    
    dbconn = sqlite3.connect(DATABASE)
    c = dbconn.cursor()
    c.execute('Select '+ attrib +' from '+ database)
    data = str(c.fetchone())
    dbconn.close()
    return data

def ReadDatabase(database, whichone, attrib):
    
    dbconn = sqlite3.connect(DATABASE)
    c = dbconn.cursor()
    c.execute('Select '+ attrib +' from '+ database +' where Name = ?;',(whichone,))
    data = str(c.fetchone())
    dbconn.close()
    return data

def UpdateDatabase(database, whichone, attrib, data):
    
    dbconn = sqlite3.connect(DATABASE)
    c = dbconn.cursor()
    c.execute('update '+ database +' ' 
      'set '+ attrib +' = ? where name = ?;',
      (data,whichone))
    dbconn.commit()
    dbconn.close()
    
def UpdateSign():

    global SignPage

    if (ShowSign):
        #print'+',
        if SignPage == 3:
            #HeatIndex = getFltfromString(ReadDatabase2('OutsideConditions','HeatIndex2'))
            #OutsideTemp = getFltfromString(ReadDatabase2('OutsideConditions','Temp2'))
            HeatIndex = getFltfromString(ReadDatabase2('OutsideConditions','HeatIndex'))
            OutsideTemp = getFltfromString(ReadDatabase2('OutsideConditions','Temperature'))
            if HeatIndex <= '80' or HeatIndex == OutsideTemp:
                SignPage = 4
        if SignPage == 6:
            PoolTemp = getFltfromString(ReadDatabase2('PoolStatus','PoolTemp'))
            if PoolTemp == '50':
                SignPage = 1

        if SignPage == 0:
            print'B',
            message = '{\"Prolite\":{\"Message\":\"<ID01><PA><FD>Booting....\"}}\r<#>'
            sendCommand(message, Cqueue)
        elif SignPage == 1:
            print'T',
            DisplayTime()
        elif SignPage == 2:
            print'O',
            #OutsideTemp = getFltfromString(ReadDatabase2('OutsideConditions','Temp2'))
            OutsideTemp = getFltfromString(ReadDatabase2('OutsideConditions','Temperature'))
            message = '{\"Prolite\":{\"Message\":\"<ID01><PA><FL>Temp '+OutsideTemp+'F\"}}\r<#>'
            sendCommand(message, Cqueue)
        elif SignPage == 3:
            print'I',
            message = '{\"Prolite\":{\"Message\":\"<ID01><PA><FR><CB>Hidx '+str(HeatIndex)+'F\"}}\r<#>'
            sendCommand(message, Cqueue)
        elif SignPage == 4:
            print'H',
            #OutsideHumidity = getFltfromString(ReadDatabase2('OutsideConditions','Humid2'))
            OutsideHumidity = getFltfromString(ReadDatabase2('OutsideConditions','Humidity'))
            message = '{\"Prolite\":{\"Message\":\"<ID01><PA><FL>RH '+str(OutsideHumidity)+'%\"}}\r<#>'
            sendCommand(message, Cqueue)
        elif SignPage == 5:
            print'D',
            #Dewpoint = getFltfromString(ReadDatabase2('OutsideConditions','Dewpoint2'))
            Dewpoint = getFltfromString(ReadDatabase2('OutsideConditions','Dewpoint'))
            message = '{\"Prolite\":{\"Message\":\"<ID01><PA><FL>Dew '+str(Dewpoint)+'F\"}}\r<#>'
            sendCommand(message, Cqueue)
        elif SignPage == 6:
            print'P',
            #PoolTemp = getFltfromString(ReadDatabase2('PoolStatus','PoolTemp'))
            message = '{\"Prolite\":{\"Message\":\"<ID01><PA><FL>Pool '+str(PoolTemp)+'F\"}}\r<#>'
            sendCommand(message, Cqueue)

            SignPage = 0
  
        SignPage = SignPage + 1
    else:
            print'S',

def DisplayTime():
    
    hour = int(time.strftime("%H"))
    if hour == 0:
         hour = 12
    elif hour >= 13:
         hour = hour-12
    message = '{\"Prolite\":{\"Message\":\"<ID01><PA><FL>'+str(hour)+'<SE>:<SA>'+(time.strftime("%M"))+'\"}}\r<#>'
    sendCommand(message, Cqueue)
def SignOn():

    global ShowSign
    UpdateDatabase('Devices','PoolSign','Status','On')
    ShowSign = True

def SignOff():
    
    global ShowSign
    UpdateDatabase('Devices','PoolSign','Status','Off')
    ShowSign = False
    message = '{\"Prolite\":{\"Message\":\"<ID01><PA><FL><FQ>\"}}\r<#>'
    sendCommand(message, Cqueue)
    
def Status():
    
    temp = "\n\nUptime - "+time.strftime("%H:%M:%S\n")
    print temp

def getFltfromString(data):
    
    temp = data
    temp2 = temp[1:]
    temp3 = temp2.split(",")
    return temp3[0]
    #data = str(temp3[0])+'00'
    #print data [0:5]
    #return data[0:5]

#---------------------------------------------------
logging.basicConfig()

#------------------ Stuff I schedule to happen -----
scheditem = BackgroundScheduler()
scheditem.start()

# Update Sign Every 10 Seconds
scheditem.add_job(UpdateSign, 'interval', seconds=10)
# Print Header in Log
scheditem.add_job(Status, 'interval', hours=2, minutes=30)
# Turn Sign On
scheditem.add_job(SignOn, 'cron', day_of_week ='mon-sun', hour=8, minute=30)
# Turn Sign Off
scheditem.add_job(SignOff, 'cron', day_of_week ='mon-sun', hour=23, minute=0)
#---------------------------------------------------

#if(Hour <= 9 or Hour <=22):
#    ShowSign = False

SignOn()

print "\n\nProLite Controller started at ", time.strftime("%A, %B, %d at %H:%M:%S\n")

UpdateSign()

# Now do nothing while the scheduler takes care of things for me

Pqueue = sysv_ipc.MessageQueue(15, sysv_ipc.IPC_CREAT,mode=0666)
firstTime = True
while True:
    time.sleep(0.1)
    sys.stdout.flush()
    try:
        if (firstTime):
            while(True):
                try:
                    # commands could have piled up while this was 
                    # not running.  Clear them out.
                    junk = Pqueue.receive(block=False, type=0)
                    #print "purging leftover commands", str(junk)
                except sysv_ipc.BusyError:
                    break
            firstTime=False
        newCommand = Pqueue.receive(block=False, type=0)
        # type=0 above means suck every message off the
        # queue.  If I used a number above that, I'd
        # have to worry about the type in other ways.
        # note, I'm reserving type 1 messages for 
        # test messages I may send from time to 
        # time.  Type 2 are messages that are
        # sent by the php code in the web interface.
        # Type 3 are from the event handler. This is just like
        # the house monitor code in that respect.
        # I haven't decided on any others yet.
        handleCommand(newCommand)
    except sysv_ipc.BusyError:
        pass # Only means there wasn't anything there
