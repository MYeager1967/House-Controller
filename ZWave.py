
from apscheduler.schedulers.background import BackgroundScheduler
from math import *                           # Not typically recommended
from datetime import timedelta
from threading import Thread
from requests.auth import HTTPBasicAuth

import requests

import commands
import datetime
import json
import logging
import email                   # Needed for EMail
import mimetypes               # Needed for EMail
import email.mime.application  # Needed for EMail
import os
import shlex
import signal
import smtplib                 # Needed for EMail
import sqlite3
import sys
import sysv_ipc
import time

# These variables will be retrieved from the database...
gmail_user = ''
gmail_pwd  = ''
userName = ''
password = ''

DATABASE = '/home/pi/DataBase/Aspenwood.db'

webHeader = 'http://127.0.0.1:8083/ZWaveAPI/Run/devices['

#global christmasLightsOn
global diningOutletOn
global frontPorchOn
global kitchenOn
global solarOutletOn

autoChristmasSceneID    = "DummyDevice_32"
autoEntrySceneID        = "DummyDevice_15"
autoFrontLockSceneID    = "DummyDevice_38"
autoPatioLockSceneID    = "DummyDevice_37"
christmasSceneActiveID  = "DummyDevice_52"
dewPointID              = "DummyTempSensor_51"
#frontSensorID           = 
frontDoorID             = "ZWayVDev_zway_6-0-98"
frontMultiHumidSensorID = "ZWayVDev_zway_14-0-49-5"
heatIndexID             = "DummyTempSensor_50"
masterBedDimID          = "ZWayVDev_zway_20-0-38"
outsideTempID           = "DummyTempSensor_49"
patioDoorID             = "ZWayVDev_zway_7-0-98"
patioSensorID           = "Multiline_31"
patioSceneID            = "DummyDevice_33"
diningOutletID          = "ZWayVDev_zway_10-0-37"
solarOutletID           = "ZWayVDev_zway_11-0-37"
kitchenLightID          = "ZWayVDev_zway_12-0-37"
frontLightID            = "ZWayVDev_zway_13-0-37"
#frontMotionID   = 14
patioLightID            = "ZWayVDev_zway_15-2-37"
poolLightID             = "ZWayVDev_zway_19-1-37"
poolColorWheelID        = "ZWayVDev_zway_19-2-37"
poolTempSensorID        = "ZWayVDev_zway_17-2-49-1" 

frontDoorLocked     = False
patioDoorLocked     = False

christmasEnabled    = False
entryEnabled        = False

diningOutletOn      = False
frontPorchOn        = False
kitchenOn           = False
poolDeckOn          = False
solarOutletOn       = False
mBedLightOn         = False

christmasScene      = False
christmasActive     = False

OutsideTemp     = 0;
DayOutMaxTemp   = 0;
DayOutMinTemp   = 0;
OutsideHumidity = 1; # Prevent error on startup
OutsideDewpoint = 0;

when = ""

#christmasLightsAuto = True

tempF = 70

timeStamp = 0
timeStamp2 = 0

def BatteryPolling():

    try:
        command = requests.get(webHeader +str(frontDoorID)+'].Battery.Get()', auth=HTTPBasicAuth(userName.password))
        command = requests.get(webHeader +str(patioDoorID)+'].Battery.Get()', auth=HTTPBasicAuth(userName,password))
        command = requests.get (webHeader +str(poolSensorID)+'].Battery.Get()', auth=HTTPBasicAuth(userName,password))
        command = requests.get (webHeader +str(patioSensorID)+'].Battery.Get()', auth=HTTPBasicAuth(userName,password))
    except:
        pass

def BatteryReport():

    print('Checking device batteries...\n')
    try:
        sendemail = 0
        message = ""
        command = requests.get(webHeader +str(frontDoorID)+'].Battery.data.last.value', auth=HTTPBasicAuth(userName,password))
        batt = command.content
        print('Front Door Battery at '+str(batt)+'%')
        #if batt <= 30:
        message = message + 'Front Door Battery at '+str(batt)+'%\n'
        sendemail = 1
        bcommand = requests.get(webHeader +str(patioDoorID)+'].Battery.data.last.value', auth=HTTPBasicAuth(userName,password))
        batt = command.content
        print('Patio Door Battery at '+str(batt)+'%')
        #if batt <= 30:
        message = message + 'Patio Door Battery at '+str(batt)+'%\n'
        sendemail = 1
        command = requests.get(webHeader +str(poolSensorID)+'].Battery.data.last.value', auth=HTTPBasicAuth(userName,password))
        batt = command.content
        print('Pool Temp Sensor Battery at '+str(batt)+'%')
        #if batt <= 30:
        message = message + 'Front Sensor Battery at '+str(batt)+'%\n'
        sendemail = 1
        command = requests.get(webHeader +str(patioSensorID)+'].Battery.data.last.value', auth=HTTPBasicAuth(userName,password))
        batt = command.content
        print('Patio Door Sensor Battery at '+str(batt)+'%')
        #if batt <= 30:
        message = message + 'Patio Sensor Battery at '+str(batt)+'%\n'
        sendemail = 1
        #if sendemail != 0:
        SendMail (gmail_user,"Battery Report",message)
    except:
        pass

# -------------------------------------------------------------------------
#                   Reset high and low temperatures
# -------------------------------------------------------------------------
def ResetTemps():
    global DayMaxTemp, DayMinTemp
    DayMaxTemp = OutsideTemp
    DayMinTemp = OutsideTemp

def DoorLock(dnum,whichone):
    
    try:
        command = requests.get(webHeader + str(dnum) + '].DoorLock.Set(255)', auth=HTTPBasicAuth(userName,password))
    except:
        pass

def DoorLockSetUsers():

    try:
        command = requests.get(webHeader + str(dnum) + '].Usercode.Set(user,"code",operation)', auth=HTTPBasicAuth(userName,password))
    except:
        pass

def DoorLockStatus(whichone, alarm, user): #Lock Status Info (Kwikset Locks)

    global frontDoorLocked
    global patioDoorLocked
    
    when = time.strftime(" at %H:%M:%S")

    if(alarm == 18 or alarm == 21 or alarm == 24 or alarm == 27 or alarm == 255):
        status = 255
        user = 0
        #if(whichone == 'Front' and frontDoorLocked == False or whichone == 'Patio' and patioDoorLocked == False):
        print('\n'+whichone+' Door was Locked'+when)
        if (whichone == 'Front'):
            frontDoorLocked = True
        if (whichone == 'Patio'):
            patioDoorLocked = True
        UpdateDataBase('Doors',whichone,'User',user)
        UpdateDataBase('Doors',whichone,'Status',status)

    elif(alarm ==  19 or alarm == 22 or alarm == 25 or alarm == 0):
        #print(whichone)
            #patioDoorLockTime = timestamp + 30
        status = 0
        #if(whichone == 'Front' and frontDoorLocked or whichone == 'Patio' and patioDoorLocked):
        if(alarm == 19):
            print('\n'+whichone+' Door was Unlocked by User ('+str(user)+')'+when)
        else:
            user = 0  
        print ('\n'+whichone+' Door was Unlocked'+when)
        if (whichone == 'Front'):
            frontDoorLocked = False
        if (whichone == 'Patio'):
            patioDoorLocked = False
        UpdateDataBase('Doors',whichone,'User',user)
        UpdateDataBase('Doors',whichone,'Status',status)
        
    elif(alarm == 17 or alarm == 23 or alarm == 26):
        print('\n'+whichone+' Door Lock Error'+when)
    elif(alarm == 33 or alarm == 112):
        print('\n'+whichone+' Door - User Code Modified - User ('+str(user)+')'+when)
    elif(alarm == 161):
        print('\n'+whichone+' Door - Three Failed Attempts at User Code Entry'+when)
    elif(alarm == 162):
        print('\n'+whichone+' Door - Invalid Schedule for User ('+str(user)+')'+when)
    elif(alarm == 167):
        print('\n'+whichone+' Door Low Battery'+when)
    elif(alarm == 168):
        print('\n'+whichone+' Door Battery Critical'+when)
    elif(alarm == 169):
        print('\n'+whichone+' Door Inoperable due to Low Battery Condition'+when)  
    else:
        print('\nUnknown Door Alarm Status ('+str(alarm)+') occurred'+when)

def GetData():

    global OutsideTemp, DayMaxTemp, DayMinTemp, OutsideHumidity, OutsideDewpoint, HeatIndex, Lux
    global timeStamp
    #global timestamp2

    try:
    #    command = requests.get('http://127.0.0.1:8083/ZWaveAPI/Data/'+ str(timeStamp), auth=HTTPBasicAuth('admin','89Bmw325i'))
    #    content = command.content
    #    data = json.loads(content)
        
    #    timeStamp = data['updateTime']
    #    when = time.strftime(" at %H:%M:%S")

#-------------------------------------------
#   Front Door Startup
#-------------------------------------------
    #    try:
    #        alarmType = data['devices'][str(frontDoorID)]['instances']['0']['commandClasses']['113']['data']['V1event']['alarmType']['value']
    #        user = data['devices'][str(frontDoorID)]['instances']['0']['commandClasses']['113']['data']['V1event']['level']['value']
            #print("alarmType - "),
            #print(alarmType)
    #        DoorLockStatus('Front',alarmType,user)
    #    except:
    #        pass
#-------------------------------------------
#   Patio Door Startup
#-------------------------------------------
    #    try:
    #        alarmType = data['devices'][str(patioDoorID)]['instances']['0']['commandClasses']['113']['data']['V1event']['alarmType']['value']
    #        user = data['devices'][str(patioDoorID)]['instances']['0']['commandClasses']['113']['data']['V1event']['level']['value']
    #        #print("alarmType - "),
    #        #print(alarmType)
    #        #print("Patio Start")
    #        DoorLockStatus('Patio',alarmType,user)
    #    except:
    #        pass
#-------------------------------------------
#   Front Door Monitor
#-------------------------------------------
    #   try:
    #        status = data['devices.'+str(frontDoorID)+'.instances.0.commandClasses.98.data.mode']['value']
    #        user = 0
    #        DoorLockStatus('Front',status,user)
            #print "Reset Front Door Status"
    #    except:
    #        pass
    #    try:
    #        alarmType = data['devices.'+str(frontDoorID)+'.instances.0.commandClasses.113.data.V1event']['alarmType']['value']
    #        user = data['devices.'+str(frontDoorID)+'.instances.0.commandClasses.113.data.V1event']['level']['value']
    #        DoorLockStatus('Front',alarmType,user)
    #    except:
    #        pass
#-------------------------------------------
#   Patio Door Monitor
#-------------------------------------------
    #   try:
    #        status = data['devices.'+str(patioDoorID)+'.instances.0.commandClasses.98.data.mode']['value']
    #        user = 0
    #        DoorLockStatus('Patio',status,user)
            #print "Reset Patio Door Status"
    #    except:
    #        pass
    #    try:
    #        alarmType = data['devices.'+str(patioDoorID)+'.instances.0.commandClasses.113.data.V1event']['alarmType']['value']
    #        user = data['devices.'+str(patioDoorID)+'.instances.0.commandClasses.113.data.V1event']['level']['value']
            #print "Patio Monitor"
    #        DoorLockStatus('Patio',alarmType,user)
    #    except:
    #        pass   

################################
#
#     Read ZAutomation Devices
#
################################

        global frontDoorLocked
        global patioDoorLocked

        global christmasEnabled
        global diningOutletOn
        global entryEnabled
        global frontPorchOn
        global kitchenOn
        global poolDeckOn
        global solarOutletOn
        global mBedLightOn

        global timeStamp2

        global OutsideTemp, DayOutMaxTemp, DayOutMinTemp, OutsideHumidity
        #global HeatIndex

        if timeStamp2 > 0: when = time.strftime(" at %H:%M:%S")
        else: when = " at Monitor Startup"
        
        try:
            command = requests.get('http://127.0.0.1:8083/ZAutomation/api/v1/devices?since='+str(timeStamp2), auth=HTTPBasicAuth(userName,password))
            content = command.content
            data = json.loads(content)
            timeStamp2 = data['data']['updateTime']
            deviceList = data['data']['devices']
            i = 0
            for x in deviceList:

                    #### Multisensor Temperature Monitor
                if deviceList[i]['id'] == outsideTempID:
                    OutsideTemp = data['data']['devices'][i]['metrics']['level']
                    UpdateDataBase2('OutsideConditions','Temperature',OutsideTemp)
                    DayOutMaxTemp = max(float(DayOutMaxTemp), float(OutsideTemp))
                    DayOutMinTemp = min(float(DayOutMinTemp), float(OutsideTemp))
                    UpdateDataBase2('OutsideConditions','DayTempMax',DayOutMaxTemp)
                    UpdateDataBase2('OutsideConditions','DayTempMin',DayOutMinTemp)

                    #### Multisensor Dewpoint Monitor
                elif deviceList[i]['id'] == dewPointID:
                    OutsideDewpoint = data['data']['devices'][i]['metrics']['level']
                    UpdateDataBase2('OutsideConditions','Dewpoint',OutsideDewpoint)

                    #### Multisensor Heat Index Monitor
                elif deviceList[i]['id'] == heatIndexID:
                    HeatIndex = data['data']['devices'][i]['metrics']['level']
                    UpdateDataBase2('OutsideConditions','HeatIndex',HeatIndex)

                    #### Multisensor Humidity Monitor
                elif deviceList[i]['id'] == frontMultiHumidSensorID:
                    OutsideHumidity = data['data']['devices'][i]['metrics']['level']
                    UpdateDataBase2('OutsideConditions','Humidity',OutsideHumidity)
                    UpdateDataBase2('OutsideConditions','Updated',time.strftime("%A, %B, %d at %H:%M:%S"))

                    #### Automatic Entry Light Scene Monitor
                elif deviceList[i]['id'] == autoEntrySceneID:
                    status = data['data']['devices'][i]['metrics']['level'].capitalize()
                    UpdateDataBase('Scenes','AutoEntry','Enabled',status)

                    #### Automatic Christmas Lights Scene Monitor                
                elif deviceList[i]['id'] == autoChristmasSceneID:
                    status = data['data']['devices'][i]['metrics']['level'].capitalize()
                    if status == 'Off': christmasEnabled = False
                    else: christmasEnabled = True
                    UpdateDataBase('Scenes','Christmas','Enabled',status)


                    #### Christmas Lights Monitor
                elif deviceList[i]['id'] == christmasSceneActiveID:
                    status = data['data']['devices'][i]['metrics']['level'].capitalize()
                    if status == 'Off': christmasActive = False
                    else: christmasActive = True
                    UpdateDataBase('Scenes','Christmas','Active',status)

                    #### Automatic Front Door Lock Scene Monitor                
                elif deviceList[i]['id'] == autoFrontLockSceneID:
                    status = data['data']['devices'][i]['metrics']['level'].capitalize()
                    UpdateDataBase('Doors','Front','Auto',status)

                    #### Automatic Patio Door Lock Scene Monitor                
                elif deviceList[i]['id'] == autoPatioLockSceneID:
                    status = data['data']['devices'][i]['metrics']['level'].capitalize()
                    UpdateDataBase('Doors','Patio','Auto',status)

                    #### Dimmer (Master Bedroom) Monitor
                elif deviceList[i]['id'] == masterBedDimID:
                    level = data['data']['devices'][i]['metrics']['level']
                    if level != 0:
                        status = "On"
                        mBedLightOn = True
                    else:
                        status = "Off"
                        mBedLightOn = False
                    UpdateDataBase('Lights','Master Bedroom','Status',status)
                    #### Dining Room Outlet Monitor
                elif deviceList[i]['id'] == diningOutletID:
                    status = data['data']['devices'][i]['metrics']['level'].capitalize()
                    if status == 'Off': diningOutletOn = False
                    else: diningOutletOn = True
                    UpdateDataBase('Devices','Dining Outlet','Status',status)

                    #### Front Door Lock Monitor
                elif deviceList[i]['id'] == frontDoorID:
                    status = data['data']['devices'][i]['metrics']['level'].capitalize()
                    if status == "Close":
                        status = "Locked"
                        value = 255
                    else:
                        status = "Unlocked"
                        value = 0
                    UpdateDataBase('Doors','Front','Status',value)
                    print "\nFront Door is " + status + "" + when
                    
                    #### Front Door Sensor Monitor
#                elif deviceList[i]['id'] == "Multiline_17": ### Update when sensor acquired
#                    status = data['data']['devices'][i]['metrics']['level'].capitalize()
#                    UpdateDataBase('Doors','Front','Sensor',status)

                    #### Front Porch Light Switch Monitor
                elif deviceList[i]['id'] == frontLightID:
                    status = data['data']['devices'][i]['metrics']['level'].capitalize()
                    if status == 'Off': frontPorchOn = False
                    else: frontPorchOn = True
                    UpdateDataBase('Lights','Front Porch','Status',status)
                    print "\nFront Porch Light is " + status + "" + when

                    #### Kitchen Light Switch Monitor
                elif deviceList[i]['id'] == kitchenLightID:
                    status = data['data']['devices'][i]['metrics']['level'].capitalize()
                    if status == "Off": kitchenOn = False
                    else: kitchenOn = True
                    UpdateDataBase('Lights','Kitchen','Status',status)
                    print "\nKitchen Light is " + status + "" + when

                    #### Patio Door Lock Monitor
                elif deviceList[i]['id'] == patioDoorID:
                    status = data['data']['devices'][i]['metrics']['level'].capitalize()
                    if status == "Close":
                        status = "Locked"
                        value = 255
                    else:
                        status = "Unlocked"
                        value = 0
                    UpdateDataBase('Doors','Patio','Status',value)
                    print "\nPatio Door is " + status + when

                    #### Patio Door Sensor Monitor
                elif deviceList[i]['id'] == patioSensorID:
                    status = data['data']['devices'][i]['metrics']['level'].capitalize()
                    UpdateDataBase('Doors','Patio','Sensor',status)

                    #### Patio Light Switch Monitor
                elif deviceList[i]['id'] == patioLightID:
                    status = data['data']['devices'][i]['metrics']['level'].capitalize()
                    UpdateDataBase('Lights','Pool Deck','Status',status)

                    #### Pool Light Switch Monitor
                elif deviceList[i]['id'] == poolLightID:
                    status = data['data']['devices'][i]['metrics']['level'].capitalize()
                    UpdateDataBase('Lights','Pool Light','Status',status)

                    #### Pool Light Color Wheel Switch Monitor
                elif deviceList[i]['id'] == "ZWayVDev_zway_19-2-37":
                    status = data['data']['devices'][i]['metrics']['level'].capitalize()
                    UpdateDataBase('Lights','Color Wheel','Status',status)

                    #### Pool Scene Switch Monitor
#                elif deviceList[i]['id'] == "DummyDevice_33":
#                    status = data['data']['devices'][i]['metrics']['level'].capitalize()
#                    UpdateDataBase('Scenes','Patio','Active',status)
                    
                    #### Pool Temp Sensor Monitor
                elif deviceList[i]['id'] == poolTempSensorID:
                    tempC = data['data']['devices'][i]['metrics']['level']
                    PoolTemp = round(tempC*9/5+32, 2)
                    UpdateDataBase2('PoolStatus','PoolTemp',PoolTemp)

                    #### Solar Water Outlet Monitor
                elif deviceList[i]['id'] == solarOutletID:
                    status = data['data']['devices'][i]['metrics']['level'].capitalize()
                    if status == "Off": solarOutletOn = False
                    else: solarOutletOn = True
                    UpdateDataBase('Devices','Solar Outlet','Status',status)

                i=i+1
                
        except:
            print deviceList[i]["id"]
            #pass

        #try:
        #    patioAlarmType = data['devices'][str(patioDoorID)]['instances']['0']['commandClasses']['113']['data']['V1event']['alarmType']['value']
        #    patioUser = data['devices'][str(patioDoorID)]['instances']['0']['commandClasses']['113']['data']['V1event']['level']['value']
        #    print"startup"
        #except:
        #    pass
        #try:
        #    patioAlarmType = data['devices.'+str(patioDoorID)+'.instances.0.commandClasses.113.data.V1event']['alarmType']['value']
        #    patioUser = data['devices.'+str(patioDoorID)+'.instances.0.commandClasses.113.data.V1event']['level']['value']
        #    print "monitor"
        #except:
        #    pass
        #print patioAlarmType
        #print patioUser   
    #### Patio Door Monitor
#            command = requests.get('http://127.0.0.1:8083/OpenRemote/metrics/ZWayVDev_zway_7-0-98/level', auth=HTTPBasicAuth('admin','89Bmw325i'))
#            content = command.content
#            data = content[1:(len(content)-1)].capitalize()
#            if data == 'Open' and patioDoorLocked == True:
#                print patioAlarmType
#                print patioUser
#                DoorLockStatus('Patio',patioAlarmType,patioUser)
#            elif data == 'Closed' and  patioDoorLocked == False:
#                print patioAlarmType
#                print patioUser
#                DoorLockStatus('Patio',patioAlarmType,patioUser)
#            else:
#                print "nope"
            



        
    except:
        print('Data acquisition error...')

def getFltfromString(data):
    
    temp = data
    temp2 = temp[1:]
    temp3 = temp2.split(",")
    return temp3[0]

def HandleCommand(command):

    global frontLightID
    global kitchenLightID
    global christmasActive
    global christmasEnabled
    global entryEnabled
    global diningOutletOn
    
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

    # Handle Z-Wave Commands from Web
    
    if cmd == 'LockFrontDoor':
        command = requests.get('http://127.0.0.1:8083/ZAutomation/api/v1/devices/'+autoFrontLockSceneID+'/command/toggle', auth=HTTPBasicAuth(userName,password)) #Reads the ZAutomation data...
    elif cmd == 'LockPatioDoor':
        command = requests.get('http://127.0.0.1:8083/ZAutomation/api/v1/devices/'+autoPatioLockSceneID+'/command/toggle', auth=HTTPBasicAuth(userName,password)) #Reads the ZAutomation data...
    elif cmd == 'SecureAll':
        command = requests.get('http://127.0.0.1:8083/ZAutomation/api/v1/devices/'+patioSceneID+'/command/off', auth=HTTPBasicAuth(userName,password))
        command = requests.get('http://127.0.0.1:8083/ZAutomation/api/v1/devices/'+autoFrontLockSceneID+'/command/on', auth=HTTPBasicAuth(userName,password)) # Front Door
        command = requests.get('http://127.0.0.1:8083/ZAutomation/api/v1/devices/'+autoPatioLockSceneID+'/command/on', auth=HTTPBasicAuth(userName,password)) # Patio Door
    elif cmd == 'KitchenToggle':
        if kitchenOn == True:
            command = requests.get('http://127.0.0.1:8083/ZAutomation/api/v1/devices/'+kitchenLightID+'/command/off', auth=HTTPBasicAuth(userName,password))
        else:
            command = requests.get('http://127.0.0.1:8083/ZAutomation/api/v1/devices/'+kitchenLightID+'/command/on', auth=HTTPBasicAuth(userName,password))
    elif cmd == 'DiningToggle':
        if diningOutletOn == True:
            command = requests.get('http://127.0.0.1:8083/ZAutomation/api/v1/devices/'+diningOutletID+'/command/off', auth=HTTPBasicAuth(userName,password))
        else:
            command = requests.get('http://127.0.0.1:8083/ZAutomation/api/v1/devices/'+diningOutletID+'/command/on', auth=HTTPBasicAuth(userName,password))
    elif cmd == 'MBedToggle':
        if mBedLightOn == True:
            command = requests.get('http://127.0.0.1:8083/ZAutomation/api/v1/devices/'+masterBedDimID+'/command/off', auth=HTTPBasicAuth(userName,password))
        else:
            command = requests.get('http://127.0.0.1:8083/ZAutomation/api/v1/devices/'+masterBedDimID+'/command/on', auth=HTTPBasicAuth(userName,password))
    elif cmd == 'PorchToggle':
        if frontPorchOn == True:
            command = requests.get('http://127.0.0.1:8083/ZAutomation/api/v1/devices/'+frontLightID+'/command/off', auth=HTTPBasicAuth(userName,password))
        else:
            command = requests.get('http://127.0.0.1:8083/ZAutomation/api/v1/devices/'+frontLightID+'/command/on', auth=HTTPBasicAuth(userName,password))

### Dummy Devices can be Toggled...
    elif cmd == 'ChristmasToggle':
        command = requests.get('http://127.0.0.1:8083/ZAutomation/api/v1/devices/'+autoChristmasSceneID+'/command/toggle', auth=HTTPBasicAuth(userName,password)) #Reads the ZAutomation data...
    elif cmd == 'EntryToggle':
        command = requests.get('http://127.0.0.1:8083/ZAutomation/api/v1/devices/'+autoEntrySceneID+'/command/toggle', auth=HTTPBasicAuth(userName,password)) #Reads the ZAutomation data...
    else:
        print("Invalid Command = " + str(c))

def LogHeader():
    
    print('ZWave Activity Log for '+ time.strftime("%B, %d"))


#def OpenSite(Url):
    
#    try:
#        webHandle = urllib2.urlopen(Url)
#    except urllib2.HTTPError, e:
#            errorDesc = BaseHTTPServer.BaseHTTPRequestHandler.responses[e.code][0]
#            print "Error: cannot retrieve URL: " + str(e.code) + ": " + errorDesc
#            sys.exit(1);
#    except urllib2.URLError, e:
#            print "Error: cannot retrieve URL: " + e.reason[1]
#    except:
#            print "Error: cannot retrieve URL: Unknown error"
#            sys.exit (1)
#    return webHandle


#def ProcessScenes(device, instance, scene):

#    global patioSceneID
#    global patioLightID
#    global poolLightID
#    global patioScene
    
    
#    if(device == patioSceneID and patioScene != scene):
        
#        patioScene = scene
#        UpdateDataBase('Scenes','Patio','Active',patioScene)
#        when = time.strftime(' at %H:%M:%S')

#        print('\nPatio Scene ' + str(patioScene) + ' active' + when)

def ReadDatabase(database, whichone, attrib):
    
    dbconn = sqlite3.connect(DATABASE)
    c = dbconn.cursor()
    c.execute('Select '+ attrib +' from '+ database +' where Name = ?;',(whichone,))
    data = str(c.fetchone())
    dbconn.close()
    return data

#def ReadMulti():
    
#    try:
#        command = requests.get(webHeader + str(frontMotionID) + '].SensorMultilevel.Get()', auth=HTTPBasicAuth('admin','89Bmw325i'))          
#    except:
#        print "Error Reading MultiSensor"

def SendMail(to,subject,text):
  msg = email.mime.Multipart.MIMEMultipart()
  msg['Subject'] = subject
  msg['From'] = 'RPi Home'
  msg['To'] = to
  
  body = email.mime.Text.MIMEText(text)
  msg.attach(body)

  s = smtplib.SMTP('smtp.gmail.com:587')
  s.starttls()
  s.login(gmail_user,gmail_pwd)
  s.sendmail(to,[to],msg.as_string())
  s.quit

def signal_handler(signal,frame):
    
    print (" Exit Signal")
    sys.exit(0)

#def SwitchBinary(dnum, instance, data):
    
#    try:
#        command = requests.get(webHeader + str(dnum) + '].instances[' + str(instance) + '].SwitchBinary.Set(' + str(data) + ')', auth=HTTPBasicAuth(userName,password))
#        time.sleep(1)
#    except:
#        print('Error Setting BinarySwitch')

def UpdateDataBase2(database, attrib, data):

    dbconn = sqlite3.connect(DATABASE)
    c = dbconn.cursor()
    c.execute('update '+ database +' ' 
      'set '+ attrib +' = ?;',
      (data,))
    dbconn.commit()
    dbconn.close()

def UpdateDataBase(database, whichone, attrib, data):
    
    dbconn = sqlite3.connect(DATABASE)
    c = dbconn.cursor()
    c.execute('update '+ database +' ' 
      'set '+ attrib +' = ? where name = ?;',
      (data,whichone))
    dbconn.commit()
    dbconn.close()

if __name__ == '__main__':
    #Catch Control-C input so it isn't ugly
    signal.signal(signal.SIGINT, signal_handler)
    logging.basicConfig(level=logging.ERROR)
    #logging.basicConfig(format='%(levelname)s:%(message)s',level=logging.WARNING)
    #When looking at a log, this will tell me when it is restarted

    print('Restarting Z-Wave Controller')
    # Get User Data from Database
    while (userName == ''):
        try:
            dbconn = sqlite3.connect(DATABASE)
            c = dbconn.cursor()
            c.execute('Select Username from Credentials where Name="Local"')
            temp = getFltfromString(str(c.fetchone()))
            userName = temp[2:(len(temp)-1)]
            c.execute('Select Password from Credentials where Name="Local"')
            temp = getFltfromString(str(c.fetchone()))
            password = temp[2:(len(temp)-1)]
            c.execute('Select Username from Credentials where Name="Email"')
            temp = getFltfromString(str(c.fetchone()))
            gmail_user  = temp[2:(len(temp)-1)]
            c.execute('Select Password from Credentials where Name="Email"')
            temp = getFltfromString(str(c.fetchone()))
            gmail_pwd = temp[2:(len(temp)-1)]
            dbconn.close()
        except:
            pass
        
    serverRunning = False
    while (serverRunning == False):
        output = commands.getoutput('ps -A')
        if 'z-way-server' in output:
            serverRunning = True
        else:
            time.sleep(30)
    print ("\n\nZ-Wave module started at "+time.strftime("%H:%M:%S"))

    # Restore daily high/low temperatures from database
    dbconn = sqlite3.connect(DATABASE)
    c = dbconn.cursor()
    c.execute('Select DayTempMax from OutsideConditions')
    DayOutMaxTemp = getFltfromString(str(c.fetchone()))
    c.execute('Select DayTempMin from OutsideConditions')
    DayOutMinTemp = getFltfromString(str(c.fetchone()))
    dbconn.close()

    GetData()

#    data=getFltfromString(ReadDatabase('Scenes', 'Christmas', 'Enabled'))
#    if data==0:
#        christmasEnabled = False
#    else:
#        christmasEnabled = True
#    data=getFltfromString(ReadDatabase('Scenes', 'Christmas', 'Active'))
#    if data==0:
#        christmasActive = False
#    else:
#        christmasActive = True

#    data=getFltfromString(ReadDatabase('Scenes', 'AutoEntry', 'Enabled'))
#    if data==0:
#        entryEnabled = False
#    else:
#        entryEnabled = True
#        urllib2.urlopen('http://127.0.0.1:8083/ZAutomation/api/v1/devices/DummyDevice_12') #Reads the ZAutomation data...
#        device = OpenSite('http://127.0.0.1:8083/ZAutomation/api/v1/devices/DummyDevice_12')
#        data1 = device.read()
#        print data1

    #time.sleep(5)

    print('\nZ-Wave Active....\n')
    
    #-------------------- Stuff I schedule to happen ----------------------------
    scheditem = BackgroundScheduler()

    # Update Battery Status
#    scheditem.add_job(BatteryPolling, 'cron', day_of_week ='mon-sun', hour=23, minute=30, second=0)

    # Report Battery Status
#    scheditem.add_job(BatteryReport, 'cron', day_of_week ='mon-sun', hour=1, minute=0, second=0)

    # Reset Daily Max/Min Temperatures
    scheditem.add_job(ResetTemps, 'cron', day_of_week ='mon-sun', hour=23, minute=59, second=59)

    # Print Log Header
    scheditem.add_job(LogHeader, 'cron', day_of_week ='mon-sun', hour=0, minute=2, second=0)
    #----------------------------------------------------------------------------

    scheditem.start()
    
    # Create the message queue where commands can be read
    # I just chose an identifier of 14 because the house monitor
    # is using 12.
    Cqueue = sysv_ipc.MessageQueue(14, sysv_ipc.IPC_CREAT,mode=0666)
    firstTime = True
    while True:
        time.sleep(1)
        GetData()
        sys.stdout.flush()
        try:
            if (firstTime):
                while(True):
                    try:
                        # commands could have piled up while this was 
                        # not running.  Clear them out.
                        junk = Cqueue.receive(block=False, type=0)
                        #print "purging leftover commands", str(junk)
                    except sysv_ipc.BusyError:
                        break
                firstTime=False
            newCommand = Cqueue.receive(block=False, type=0)
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
            HandleCommand(newCommand)
        except sysv_ipc.BusyError:
            pass # Only means there wasn't anything there
