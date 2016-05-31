#! /home/pi/PythonScripts
#
# This is the actual house Monitor Module
#
# This code originated with Dave in his Desert Home project
#
# I take the techniques tried in other modules and incorporate them
# to gather data around the house and save it in a database.  The
# data base can be read for presentation in a web page and also  
# forwarded to cloud services for storage and graphing. 
#
# For the XBee network, a new process is forked off to receive XBee
# packets.  This way, the main code can go about doing somthing else.

from xbee import ZigBee
from apscheduler.schedulers.background import BackgroundScheduler
from math import *                           # Not typically recommended

# -----------
import logging
import datetime
import email                   # Needed for EMail
import mimetypes               # Needed for EMail
import email.mime.application  # Needed for EMail
import time
import serial
import Queue
import sqlite3
import smtplib                 # Needed for EMail
import sys
import urllib2
import subprocess
import sysv_ipc
import shlex
import ephem                   # Sunrise / Sunset
import json
import os
# -------------------------------------------------------------------
# Define Email addresses
userName   = ''
password   = ''
gmail_user = ''
gmail_pwd  = ''

#-------------------------------------------------
# the database where I'm storing stuff
DATABASE='/home/pi/DataBase/Aspenwood.db'

home          = ephem.Observer()
home.lon      = str(-81.37722)
home.lat      = str(28.340307)
home.elev     = 79
home.pressure = 0

# on the Raspberry Pi the serial port is ttyAMA0. ttyUSB0 for USB Serial
XBEEPORT = '/dev/ttyUSB0' 
XBEEBAUD_RATE = 9600

# The XBee addresses I'm dealing with
BROADCAST = '\x00\x00\x00\x00\x00\x00\xff\xff'
SPARE1    = '\x00\x13\xa2\x00\x40\x70\x3e\xef' # XBee Pro
SPARE2    = '\x00\x13\xa2\x00\x40\xc1\xaf\x19'
SPARE3    = '\x00\x13\xa2\x00\x40\x31\x55\xe9'
POOLCTRL  = '\x00\x13\xa2\x00\x40\xad\x75\x14'
LEDSIGN   = '\x00\x13\xa2\x00\x40\x32\x18\x73'

UNKNOWN   = '\xff\xfe'   # This is the 'I don't know' 16 bit address

# Global items that I want to keep track of
CurrentPower = 0
DayMaxPower = 0
DayMinPower = 50000
# Pool Data Variables
PoolTemp = 0
PoolPump = 0
PoolSolarPump = 0
SolarDifferential = 0
pH = 0
# Outside Weather Variables
OutsideTemp = 0
OutsideHumidity = 0
HeatIndex = 0
DayOutMaxTemp =  -10.00
DayOutMinTemp = 200

#-------------------------------------------------
logging.basicConfig(level=logging.ERROR)
#-------------------------------------------------
def openSite(Url):
#print Url
 try:
  webHandle = urllib2.urlopen(Url)
 except urllib2.HTTPError, e:
  errorDesc = BaseHTTPServer.BaseHTTPRequestHandler.responses[e.code][0]
  print "Error: cannot retrieve URL: " + str(e.code) + ": " + errorDesc
  sys.exit(1);
 except urllib2.URLError, e:
  print "Error: cannot retrieve URL: " + e.reason[1]
 except:
  print "Error: cannot retrieve URL: Unknown error"
  sys.exit (1)
 return webHandle
#-----------------------------------------------
#def controlThermo(whichOne, command):
# dbconn = sqlite3.connect(DATABASE)
# c = dbconn.cursor()
# c.execute("select address from thermostats "
# "where location=?; ", (whichOne,))
# thermoIp = c.fetchone()
# website = openSite("HTTP://" + thermoIp[0] + "/" + command)
# websiteHtml = website.read()
# return  websiteHtml

#def getThermoStatus(whichOne):
# website = openSite("HTTP://" + whichOne[0] + "/status")
 # now read the status that came back from it
# websiteHtml = website.read()
 # After getting the status from the little web server on
 # the arduino thermostat, strip off the trailing cr,lf
 # and separate the values into a list that can
 # be used to tell what is going on
# return  websiteHtml.rstrip().split(",")

#def ThermostatStatus():
 # The scheduler will run this as a separate thread
 # so I have to open and close the database within
 # this routine
 #print(time.strftime("%A, %B %d at %H:%M:%S"))
 # open the database and set up the cursor (I don't have a
 # clue why a cursor is needed)
# dbconn = sqlite3.connect(DATABASE)
# c = dbconn.cursor()
# for whichOne in ['North', 'South']:
#  c.execute("select address from thermostats "
# "where location=?; ", (whichOne,))
# thermoIp = c.fetchone()
# status = getThermoStatus(thermoIp)
 #print whichOne + " reports: " + str(status)
# c.execute("update thermostats set 'temp-reading' = ?, "
#  "status = ?, "
#  "'s-temp' = ?, "
#  "'s-mode' = ?, "
#  "'s-fan' = ?, "
#  "peak = ?,"
#  "utime = ?"
#  "where location = ?;",
#  (status[0],status[1],
#  status[2],status[3],
#  status[4],status[5],
#  time.strftime("%A, %B %d at %H:%M:%S"),
#  whichOne))
# dbconn.commit()
# dbconn.close()

#------------ XBee Stuff -------------------------
packets = Queue.Queue() # When I get a packet, I put it on here

# Open serial port for use by the XBee
ser = serial.Serial(XBEEPORT, XBEEBAUD_RATE)

def message_received(data):
 # this is a call back function.  When a message
 # comes in this function will get the data
 packets.put(data, block=False)

def sendPacket(where, what):
# I'm only going to send the absolute minimum. 
        zb.send('tx',
                dest_addr_long = where,
                # I always use the 'unknown' value for the 16 bit
                # address as it's too much trouble to keep track of
                # two addresses for the device
                dest_addr = UNKNOWN,
                data = what)
        time.sleep(0.25) # Keep multiple packets from choking devices

def sendQueryPacket():
 # In my house network sending a '?\r' (question mark, carriage
 # return) causes the controller to send a packet with some status
 # information in it as a broadcast.  As a test, I'll send it and 
 # the receive above should catch the response.
    
 # I'm broadcasting this message only
 # because it makes it easier for a monitoring
 # XBee to see the packet.  This allows me to monitor
 # some of the traffic with a regular XBee and not
 # load up the network unnecessarily.
 #print 'sending query packet'
 sendPacket(BROADCAST, '?\r')

#-------- Send the command / data to another process
def sendCommand(message, whichQueue):
   try:
      # type 1 messages are for testing, type 2 originate 
      # from the web interface and type 3 originate here
      whichQueue.send(message, block=False, type=3)
   except sysv_ipc.BusyError:
      # I have to think more about what to do with this.
      print "Busy error when sending command", time.strftime("%A, %B, %d at %H:%M:%S")
      sys.stdout.flush()

def SunInfo():
    global Sunrise, Sunset
    home.date = datetime.datetime.now()
    home.horizon = '-0:34'
    t = ephem.localtime(home.next_rising(ephem.Sun()))
    Sunrise = FixSunTime(t,0)
    t = ephem.localtime(home.next_setting(ephem.Sun()))
    Sunset = FixSunTime(t,12)
    home.horizon = '-6' # -6 Civilian -12 Nautical -18 Astronomical
    t = ephem.localtime(home.next_rising(ephem.Sun(), use_center=True))
    BeginTwilight = FixSunTime(t,0)
    t = ephem.localtime(home.next_setting(ephem.Sun(), use_center=True))
    EndTwilight = FixSunTime(t,12)
    try:
        dbconn = sqlite3.connect(DATABASE)
        c = dbconn.cursor()
        c.execute("update SunInfo set BeginTwilight = ?, "
        "Sunrise = ?,"
        "Sunset = ?,"         
        "EndTwilight = ?,"
        "Updated = ?;",
        (str(BeginTwilight), str(Sunrise), str(Sunset), str(EndTwilight),
        time.strftime("%A, %B, %d at %H:%M:%S")))
        dbconn.commit()
        dbconn.close()
    except:
        pass

def FixSunTime(t,x):
 temp = '0'+str(t.minute)
 temp2 = '%s:%s'%((t.hour)-x,temp[-2:])
 return temp2

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
                                                    
 # This routine does nothing more than strip the extra characters
 # from data retrieved from the database so that I can pull float
 # values from it.
 
def getFltfromString(data): 
  temp = data
  temp2 = temp[1:]
  temp3 = temp2.split(",")
  return temp3[0]

 # OK, another thread has caught the packet from the XBee network,
 # put it on a queue, this process has taken it off the queue and 
 # passed it to this routine, now we can take it apart and see
 # what is going on ... whew!
def handlePacket(data):
  global CurrentPower, DayMaxPower, DayMinPower
  global OutsideTemp, DayOutMaxTemp, DayOutMinTemp, OutsideHumidity, OutsideDewpoint
  global HeatIndex
  global PoolTemp, SolarDifferential, PoolpH
  global PoolPump, PoolSolarPump

  #print data # for debugging so you can see things
  # this packet is returned every time you do a transmit
  # (can be configured out), to tell you that the XBee
  # actually send the darn thing
  if data['id'] == 'tx_status':
   if ord(data['deliver_status']) != 0:
    #print 'Transmit error = ',
    #print data['deliver_status'].encode('hex'),
    pass
   pass
 # The receive packet is the workhorse, all the good stuff
 # happens with this packet.
  elif data['id'] == 'rx':
      rfdata = data['rf_data']
      #print rfdata
      try:
          data = json.loads(data['rf_data']);
      except:
          print '\nInvalid JSON packet...'
# -------------------------------------------------------------------------
#                    Pool Controller
# -------------------------------------------------------------------------          
   
      if 'Pool' in data:
          # ---------------------------------------------------------------
          #          Pool Data and Outside Conditions
          # ---------------------------------------------------------------  
          try:
            SolarDifferential = data['Pool']['SolarDiff']
            PoolPump = data['Pool']['PoolPump']
            Speed = data['Pool']['Speed']
            Chlor = data['Pool']['Chlor']
            PoolSolarPump = data['Pool']['SolarPump']
            PoolpH = data['Pool']['pH']
            #OutsideTemp = data['Pool']['Outside']
            #OutsideHumidity = data['Pool']['Humidity']
            #OutsideDewpoint = round(CalcDewpoint(),2)
            #if (OutsideTemp > 80.00) and (OutsideHumidity > 40.00):
            #    HeatIndex = round(CalcHeatIndex(),2)
            #else:
            #    HeatIndex = OutsideTemp
            Version = data['Pool']['Version']
            print'P',
  
            dbconn = sqlite3.connect(DATABASE)
            c = dbconn.cursor()
            c.execute("update PoolStatus set SolarDifferential = ?,"
            "PoolPump = ?,"
            "Speed = ?,"
            "Chlorine = ?,"
            "SolarPump = ?,"
            "pH = ?,"
            "ControlVersion = ?,"
            "Updated = ?;",
            (SolarDifferential, PoolPump, Speed, Chlor, PoolSolarPump, PoolpH,
            Version, time.strftime("%A, %B, %d at %H:%M:%S")))
            #if (OutsideTemp > 0):
            #  c.execute("update OutsideConditions "        
            #   "set Temperature = ?,"
            #   "DayTempMax = ?,"
            #   "DayTempMin = ?,"
            #   "Humidity = ?,"
            #   "Dewpoint = ?,"
            #   "HeatIndex = ?,"
            #   "Updated = ?;",
            # (OutsideTemp, float(DayOutMaxTemp), float(DayOutMinTemp), OutsideHumidity,
            #  OutsideDewpoint, HeatIndex, time.strftime("%A, %B, %d at %H:%M:%S")))        
            dbconn.commit()
            dbconn.close()
          except KeyError:
            pass
          except sqlite3.OperationalError:
            pass
# ---------------------------------------------------------------
#               Pool Controller Mode Update
# ---------------------------------------------------------------
      elif 'PoolSettings' in data:

          print 'PC',
          try:
            dbconn = sqlite3.connect(DATABASE)
            c = dbconn.cursor()
            c.execute('Select Mode from PoolStatus')
            temp = getFltfromString(str(c.fetchone()))
            poolMode = int(temp)
            c.execute('Select SetTemp from PoolStatus')
            temp = getFltfromString(str(c.fetchone()))
            poolSetP = int(temp)
            c.execute('Select SetDiff from PoolStatus')
            temp = getFltfromString(str(c.fetchone()))
            poolDiff = int(temp)
            c.execute('Select TimeOn from PoolTimers where name="Clean"')
            temp = str(c.fetchone())
            cleanOn = temp[3:8]
            c.execute('Select TimeOff from PoolTimers where name="Clean"')
            temp = str(c.fetchone())
            cleanOff = temp[3:8]
            c.execute('Select TimeOn from PoolTimers where name="Chlorinator"')
            temp = str(c.fetchone())
            chlorOn = temp[3:8]
            c.execute('Select TimeOff from PoolTimers where name="Chlorinator"')
            temp = str(c.fetchone())
            chlorOff = temp[3:8]
            c.execute('Select TimeOn from PoolTimers where name="High"')
            temp = str(c.fetchone())
            HighOn = temp[3:8]
            c.execute('Select TimeOff from PoolTimers where name="High"')
            temp = str(c.fetchone())
            HighOff = temp[3:8]
            c.execute('Select TimeOn from PoolTimers where name="Med"')
            temp = str(c.fetchone())
            MedOn = temp[3:8]
            c.execute('Select TimeOff from PoolTimers where name="Med"')
            temp = str(c.fetchone())
            MedOff = temp[3:8]
            c.execute('Select TimeOn from PoolTimers where name="Low"')
            temp = str(c.fetchone())
            LowOn = temp[3:8]
            c.execute('Select TimeOff from PoolTimers where name="Low"')
            temp = str(c.fetchone())
            LowOff = temp[3:8]
            dbconn.close()

            try:
              temp = data['PoolSettings']['Mode']
              if(temp != poolMode):
                jsonMessage = '{\"SetPool\":{\"Mode\":'+str(poolMode)+'}}\r'
                sendPacket(POOLCTRL,jsonMessage)
                print '+',
            except:
              pass
            try:
              temp = data['PoolSettings']['Setpoint']
              if(temp != poolSetP):
                jsonMessage = '{\"SetPool\":{\"Setpoint\":'+str(poolSetP)+'}}\r'
                sendPacket(POOLCTRL,jsonMessage)
                print '+',
            except:
              pass
            try:
              temp = data['PoolSettings']['SetDiff']
              if(temp != poolDiff):
                jsonMessage = '{\"SetPool\":{\"SetDiff\":'+str(poolDiff)+'}}\r'
                sendPacket(POOLCTRL,jsonMessage)
                print '+',
            except:
              pass
            try:
              temp = data['PoolSettings']['CleanOn']
              if(temp != cleanOn):
                jsonMessage = '{\"SetPool\":{\"CleanOn\":\"'+cleanOn+'\"}}\r'
                sendPacket(POOLCTRL,jsonMessage)
                print '+',
            except:
              pass
            try:
              temp=data['PoolSettings']['CleanOff']
              if(temp != cleanOff):
                jsonMessage = '{\"SetPool\":{\"CleanOff\":\"'+cleanOff+'\"}}\r'
                sendPacket(POOLCTRL,jsonMessage)
                print '+',
            except:
              pass
            try:
              temp = data['PoolSettings']['ChlorOn']
              if(temp != chlorOn):
                jsonMessage = '{\"SetPool\":{\"ChlorOn\":\"'+chlorOn+'\"}}\r'
                sendPacket(POOLCTRL,jsonMessage)
                print '+',
            except:
              pass
            try:
              temp=data['PoolSettings']['ChlorOff']
              if(temp != chlorOff):
                jsonMessage = '{\"SetPool\":{\"ChlorOff\":\"'+chlorOff+'\"}}\r'
                sendPacket(POOLCTRL,jsonMessage)
                print '+',
            except:
              pass
            try:
              temp = data['PoolSettings']['PoolHighOn']
              if(temp != HighOn):
                jsonMessage = '{\"SetPool\":{\"PoolHighOn\":\"'+HighOn+'\"}}\r'
                sendPacket(POOLCTRL,jsonMessage)
                print '+',
            except:
              pass
            try:
              temp = data['PoolSettings']['PoolHighOff']
              if(temp != HighOff):
                jsonMessage = '{\"SetPool\":{\"PoolHighOff\":\"'+HighOff+'\"}}\r'
                sendPacket(POOLCTRL,jsonMessage)
                print '+',
            except:
              pass
            try:
              temp = data['PoolSettings']['PoolMedOn']
              if(temp != MedOn):
                jsonMessage = '{\"SetPool\":{\"PoolMedOn\":\"'+MedOn+'\"}}\r'
                sendPacket(POOLCTRL,jsonMessage)
                print '+',
            except:
              pass
            try:
              temp = data['PoolSettings']['PoolMedOff']
              if(temp != MedOff):
                jsonMessage = '{\"SetPool\":{\"PoolMedOff\":\"'+MedOff+'\"}}\r'
                sendPacket(POOLCTRL,jsonMessage)
                print '+',
            except:
              pass
            try:
              temp = data['PoolSettings']['PoolLowOn']
              if(temp != LowOn):
                jsonMessage = '{\"SetPool\":{\"PoolLowOn\":\"'+LowOn+'\"}}\r'
                sendPacket(POOLCTRL,jsonMessage)
                print '+',
            except:
              pass
            try:
              temp = data['PoolSettings']['PoolLowOff']
              if(temp != LowOff):
                jsonMessage = '{\"SetPool\":{\"PoolLowOff\":\"'+LowOff+'\"}}\r'
                sendPacket(POOLCTRL,jsonMessage)
                print '+',
            except:
              pass
            
              
          except:
            pass
      elif 'PoolTest' in data:
          print 'X',
      elif 'XMitTest' in data:
          pass
# -------------------------------------------------------------------------
#          Catch and process Sensor packets
# -------------------------------------------------------------------------
      elif 'Sensors' in data:
          try:
              if data['Sensors']['PoolTemp']:
                  print 'SE',
          except:
              pass
# -------------------------------------------------------------------------
#          Catch and process time packet from Pool controller
# -------------------------------------------------------------------------
      elif 'Time' in data:
          print 'T',
          temp1 = time.time()
          temp2 = data['Time']['UTC']
          temp3 = int((temp1-temp2)/60)
#          if(temp3 != 240 and temp3 != 300):
#              if (temp3 > 230 and temp3 < 250):
#                  print '('+str(temp3-240)+')',
#              print str(temp1)+'/'+str(temp3 - 240 + temp1),
              #print str(temp1)+" / "+str(temp2)+"|"+str(temp3),
          if (temp3 > 220 and temp3 < 235 or temp3 > 245 and temp3 < 260):
              print "**TS**",
              temp4 = (temp3 - 240 + temp1)
              subprocess.call(["sudo", "date", "-s", "@"+str(temp4)])
          if (temp3 > 280 and temp3 < 295 or temp3 > 305 and temp3 < 320):
              print "**TS**",
              temp4 = (temp3 - 300 + temp1)
              subprocess.call(["sudo", "date", "-s", "@"+str(temp4)])      
                         
              #print '**TS**',
              #subprocess.call(["sudo", "service", "ntp", "restart", "/dev/null"])
              #subprocess.call(["sudo", "date", "-s", "@"+str(temp2)])
      elif 'BTime' in data:
          print 'BT',
      elif 'Reboot' in data:
          print data['Reboot']['Device'],
      elif 'SolarDHW' in data:
          print 'W',
          try:
            HWTankTemp = data['SolarDHW']['TankTemp']
            HWCollector = data['SolarDHW']['CollectorTemp']
            HWSolarPump = data['SolarDHW']['SolarPump']
            HWElecHeat = data['SolarDHW']['ElecHeat']
            Version = data['SolarDHW']['Version']
            dbconn = sqlite3.connect(DATABASE)
            c = dbconn.cursor()
            c.execute("update DHWController set TankTemp = ?, "
            "CollectorTemp = ?,"
            "SolarPump = ?,"
            "ElecHeatOn = ?,"
            "ControlVersion = ?,"
            "Updated = ?;",
            (HWTankTemp, HWCollector, HWSolarPump, HWElecHeat,
            Version, time.strftime("%A, %B, %d at %H:%M:%S")))       
            dbconn.commit()
            dbconn.close()
          except KeyError:
            pass
          
      elif 'DHWSettings' in data:
          print 'WC',
          dbconn = sqlite3.connect(DATABASE)
          c = dbconn.cursor()
          c.execute('Select Mode from DHWController')
          temp = getFltfromString(str(c.fetchone()))
          Mode = int(temp)
          c.execute('Select Setpoint from DHWController')
          temp = getFltfromString(str(c.fetchone()))
          Setpoint = int(temp)
          c.execute('Select ElectricHeatSetpoint from DHWController')
          temp = getFltfromString(str(c.fetchone()))
          ESetpoint = int(temp)
          c.execute('Select Timer1On from DHWController')
          temp = str(c.fetchone())
          Timer1On = temp[3:8]
          c.execute('Select Timer1Off from DHWController')
          temp = str(c.fetchone())
          Timer1Off = temp[3:8]
          c.execute('Select Timer2On from DHWController')
          temp = str(c.fetchone())
          Timer2On = temp[3:8]
          c.execute('Select Timer2Off from DHWController')
          temp = str(c.fetchone())
          Timer2Off = temp[3:8]
          dbconn.close()

          try:
            temp = data['DHWSettings']['Mode']
            if(temp != Mode):
              jsonMessage = '{\"SetDHW\":{\"Mode\":'+str(Mode)+'}}\r'
              sendPacket(SPARE1,jsonMessage)
              print '+',
          except:
            pass
          try:
            temp = data['DHWSettings']['Setpoint']
            if(temp != Setpoint):
              jsonMessage = '{\"SetDHW\":{\"Setpoint\":'+str(Setpoint)+'}}\r'
              sendPacket(SPARE1,jsonMessage)
              print '+',
          except:
            pass
          try:
            temp = data['DHWSettings']['ESetpoint']
            if(temp != ESetpoint):
              jsonMessage = '{\"SetDHW\":{\"ESetpoint\":'+str(ESetpoint)+'}}\r'
              sendPacket(SPARE1,jsonMessage)
              print '+',
          except:
            pass
          try:
            temp = data['DHWSettings']['Timer1On']
            if(temp != Timer1On):
              jsonMessage = '{\"SetDHW\":{\"Timer1On\":\"'+Timer1On+'\"}}\r'
              sendPacket(SPARE1,jsonMessage)
              print '+',
          except:
            pass
          try:
            temp = data['DHWSettings']['Timer1Off']
            if(temp != Timer1Off):
              jsonMessage = '{\"SetDHW\":{\"Timer1Off\":\"'+Timer1Off+'\"}}\r'
              sendPacket(SPARE1,jsonMessage)
              print '+',
          except:
            pass
          try:
            temp = data['DHWSettings']['Timer2On']
            if(temp != Timer2On):
              jsonMessage = '{\"SetDHW\":{\"Timer2On\":\"'+Timer2On+'\"}}\r'
              sendPacket(SPARE1,jsonMessage)
              print '+',
          except:
            pass
          try:
            temp = data['DHWSettings']['Timer2Off']
            if(temp != Timer2Off):
              jsonMessage = '{\"SetDHW\":{\"Timer2Off\":\"'+Timer2Off+'\"}}\r'
              sendPacket(SPARE1,jsonMessage)
              print '+',
          except:
            pass

            #jsonMessage  = '{\"SetDHW\":{'     # First Line!!!
            #jsonMessage += '\"Mode\":'+str(DHWMode)+','
            #jsonMessage += '\"Setpoint\":'+str(DHWSetP)+','
            #jsonMessage += '\"ElecSetpoint\":'+str(ElecSetpoint)+','
            #jsonMessage += '\"Timer1On\":\"'+Timer1On+'\",'
            #jsonMessage += '\"Timer1Off\":\"'+Timer1Off+'\",'
            #jsonMessage += '\"Timer2On\":\"'+Timer2On+'\",'
            #jsonMessage += '\"Timer2Off\":\"'+Timer2Off+'\"}}\r'     # Last line!!!

            #print '+',
            
            #sendPacket(SPARE1,jsonMessage)
            
          #except KeyError:
            #pass
              

      else:
          print '\n' + rfdata;


#          temp1 = data['Pool']['Outside'];
#          temp2 = data['Pool']['PoolTemp'];
#    
#          print 'PoolTemp - ' + temp2;
#      except:
#          pass

##   print data['rf_data'];
##   rxList = data['rf_data'].split(',')
   #print rxList[0],
##   if rxList[0] == 'Status': #This is the status send by the old controller
##    pass
    # remember, it's sent as a string by the XBees
#    tmp = int(rxList[1]) # index 1 is current power
#    if tmp > 0:  # Things can happen to cause this
     # and I don't want to record a zero
#     CurrentPower = tmp
#     DayMaxPower = max(DayMaxPower,tmp)
#     DayMinPower = min(DayMinPower,tmp)
#     tmp = int(rxList[3]) # index 3 is outside temp
#     CurrentOutTemp = tmp
#     DayOutMaxTemp = max(DayOutMaxTemp, tmp)
#     DayOutMinTemp = min(DayOutMinTemp, tmp)
#     dbconn = sqlite3.connect(DATABASE)
#     c = dbconn.cursor()
     # do database stuff
#     c.execute("update housestatus " 
#      "set curentpower = ?, "
#      "daymaxpower = ?,"
#      "dayminpower = ?,"
#      "currentouttemp = ?,"
#      "dayoutmaxtemp = ?,"
#      "dayoutmintemp = ?,"
#      "utime = ?;",
#      (CurrentPower, DayMaxPower, DayMinPower,
#      CurrentOutTemp, DayOutMaxTemp,
#      DayOutMinTemp,
#      time.strftime("%A, %B, %d at %H:%M:%S")))
#     dbconn.commit()
#     dbconn.close()
# -------------------------------------------------------------------------
#          Catch error messages from devices and send email
# -------------------------------------------------------------------------
##   elif rxList[0] == 'Error':
##    print 'Error '+rxList[1],
##    message = 'Error: '+rxList[1]+time.strftime("%A, %d %B, ")
##    SendMail ("myeager1967@gmail.com","Status: Error",message)
    #print(rxList)
#          
# -------------------------------------------------------------------------
##   elif rxList[0] == 'AcidPump':
    # This is the Acid Pump Status packet
    # it has 'AcidPump,time_t,status,level,#times_sent_message
    # I only want to save status, level, and the last
    # time it reported in to the database for now
##    dbconn = sqlite3.connect(DATABASE)
##    c = dbconn.cursor()
##    c.execute("update acidpump set status = ?, "
##    "'level' = ?,"
##    "utime = ?;",
##    (rxList[2], rxList[3],
##    time.strftime("%A, %B, %d at %H:%M:%S")))
##    dbconn.commit()
##    dbconn.close()
# -------------------------------------------------------------------------
#          
# -------------------------------------------------------------------------    
##   elif rxList[0] == '?\r': #incoming request for a house status message
    # Status message that is broadcast to all devices consists of:
    # power,time_t,outsidetemp,insidetemp,poolmotor  ---more to come someday
    # all fields are ascii with poolmotor being {Low,High,Off}
##    dbconn = sqlite3.connect(DATABASE)
##    c = dbconn.cursor()
##    spower = int(float(c.execute("select rpower from power").fetchone()[0]))
##    stime = int((time.time() - (7*3600)))
##    sotemp = int(c.execute("select currenttemp from xbeetemp").fetchone()[0])
##    sitemp = int(c.execute("select avg(\"temp-reading\") from thermostats").fetchone()[0])
##    spoolm = c.execute("select motor from pool").fetchone()[0]
##    dbconn.close()
##    sstring = "Status,%d,%d,%d,%d,%s" %(spower,stime,sotemp,sitemp,spoolm)
##    print sstring.encode('ascii','ignore')
##    sendPacket(BROADCAST, sstring.encode('ascii','ignore'))
# -------------------------------------------------------------------------
#          Catch and process time packet from Pool controller
# -------------------------------------------------------------------------
##   elif rxList[0] == 'Time':
    #print(rxList)
##    print 'T',
##    dbconn = sqlite3.connect(DATABASE)
##    c = dbconn.cursor()
##    c.execute("update Time "
##    "set UTC = ?,"
##    "Updated = ?;",
##    (rxList[1],
##    time.strftime("%A, %B, %d at %H:%M:%S")))
##    dbconn.commit()
##    dbconn.close()
# -------------------------------------------------------------------------
#          
# -------------------------------------------------------------------------    
##   elif rxList[0] == 'Garage':
##    #print("Got Garage Packet")
##    #print(rxList)
##    if len(rxList) > 2: #this means it's a status from the garage
     # not a command to the garage
     #print "updating garage in database"
     # Now stick it in the database
##     dbconn = sqlite3.connect(DATABASE)
##     c = dbconn.cursor()
##     c.execute("update garage set door1 = ?, "
##     "door2 = ?,"
##     "waterh = ?,"
##     "utime = ?;",
##     (rxList[1], rxList[2],rxList[3].rstrip(),
##     time.strftime("%A, %B, %d at %H:%M:%S")))
##     dbconn.commit()
##     dbconn.close()

#          
# -------------------------------------------------------------------------
#  elif rxList[0] == 'Power':
   #print("Got Power Packet")
   #print(rxList)
   # I didn't really need to put these into variables, 
   # I could have used the strings directly, but when
   # I came back in a year or two to this code, I 
   # wouldn't have a clue what was going on.  By 
   # putting them in variables (less efficient), I 
   # make my life easier in the future.
#   rpower = float(rxList[1])
#   CurrentPower = rpower
#   DayMaxPower = max(DayMaxPower,CurrentPower)
#   DayMinPower = min(DayMinPower,CurrentPower)
#   apower = float(rxList[2])
#   pfactor = float(rxList[3])
#   voltage = float(rxList[4])
#   current = float(rxList[5])
#   frequency = float(rxList[6].rstrip())
   #print ('rpower %s, apower %s, pfactor %s, voltage %s, current %s, frequency %s' 
   # %(rpower, apower, pfactor, voltage, current, frequency))
#   try:
#    dbconn = sqlite3.connect(DATABASE)
#    c = dbconn.cursor()
#    c.execute("update power set rpower = ?, "
#     "apower = ?,"
#     "pfactor = ?,"
#     "voltage = ?,"
#     "current = ?,"
#     "frequency = ?,"
#     "utime = ?;",
#     (rpower, apower, pfactor, voltage, current, 
#     frequency, time.strftime("%A, %B, %d at %H:%M:%S")))
#    dbconn.commit()
#   except:
#    print "Error: Database error"
#   dbconn.close()
# -------------------------------------------------------------------------
#          Handle unsupported command
# -------------------------------------------------------------------------
##  else:
   #print ("Error: can\'t handle " + rxList[0] + ' yet')
##   print ("."),
# -------------------------------------------------------------------------
#          
# -------------------------------------------------------------------------
# elif data['id'] == 'rx_io_data_long_addr':
  #print ('data from thermostat')
#  tmp = data['samples'][0]['adc-1']
  # Don't even ask about the calculation below
  # it was a real pain in the butt to figure out
#  otemp = (((tmp * 1200.0) / 1024.0) / 10.0) * 2.0
#  CurrentOutTemp = otemp
#  DayOutMaxTemp = max(DayOutMaxTemp, CurrentOutTemp)
#  DayOutMinTemp = min(DayOutMinTemp, CurrentOutTemp)
#  dbconn = sqlite3.connect(DATABASE)
#  c = dbconn.cursor()
#  c.execute("update xbeetemp set 'currenttemp' = ?, "
#   "utime = ?;",
#   (int(otemp),
#   time.strftime("%A, %B, %d at %H:%M:%S")))
#  dbconn.commit()
#  dbconn.close()
# else:
#  print ('Error: Unimplemented XBee frame type' + data['id'])

#-------------------------------------------------

# This little status routine gets run by scheduler
def printHouseData():
  print("\nOutside Temp: Current %s, Min %s, Max %s - "
  %(OutsideTemp, DayOutMinTemp, DayOutMaxTemp)+time.strftime("%B, %d at %H:%M:%S"))
  
def Test():
    uxtime = 1427200500
    jsonMessage = '{\"RXTest\":{\"String\":\"This is a test...\"}}\r'
    #sendPacket(POOLCTRL,jsonMessage)
    #print 'TEST',
    sendPacket(SPARE1,jsonMessage)
    jsonMessage = '{\"RXTest1\":{\"Number\":'+str(uxtime)+'}}\r'
    sendPacket(SPARE1,jsonMessage)
def handleCommand(command):
    try:
        data = str(command)
        #data = data[1:(len(data)-4)]
        #print(data)
        data = str(command[0]).split("<#>")
        data = json.loads(data[0])
        jsonMessage = json.dumps(data)

        if data.has_key("Prolite"):
            sendPacket (LEDSIGN, jsonMessage)
            
    except:
        # the command comes in from php as something like
        # ('s:17:"AcidPump, pumpOff";', 2)
        # so command[0] is 's:17:"AcidPump, pumpOff'
        # then split it at the "  and take the second item
        # inter language stuff is a real pain sometimes
        #print command

        try:
            c = str(command[0].split('\"')[1]).split(',')
        except IndexError:
            c = str(command[0]).split(' ')    #this is for something I sent from another process
        #print c
        device = c[0]
        todo = c[1].strip(' ')
        # now I have a list like ['device', 'command']
        #print c[0]

        # ----- Process Devices -----
        
        #if device == 'Pool':
            #c=str(command[0]).split('ProLite ')
            #message = command[0]
            #sendPacket (SPARE1, message)  # Change Later!!!!

# Beginning of Pool command code
  
        if device == 'Pool':
            if (todo[0:8] == "setmode="):
                poolMode = int(todo[-1])
                message = '{\"SetPool\":{\"Mode\":'+str(poolMode)+'}}\r'
                sendPacket(POOLCTRL, message)
                UpdateDatabase('PoolStatus','Mode',poolMode)
            elif (todo[0:6] == "speed="):
                speed = int(todo[-1])
                message = '{\"SetPool\":{\"Speed\":'+str(speed)+'}}\r'
                sendPacket(POOLCTRL, message)
            elif (todo[0:8] == "settemp="):
                poolSetP = int(todo[-2:])
                message = '{\"SetPool\":{\"Setpoint\":'+str(poolSetP)+'}}\r'
                sendPacket(POOLCTRL, message)
                UpdateDatabase('PoolStatus','SetTemp',poolSetP)
            elif (todo[0:8] == "setdiff="):
                poolDiff = int(todo[-2:])
                message = '{\"SetPool\":{\"SetDiff\":'+str(poolDiff)+'}}\r'
                sendPacket(POOLCTRL, message)
                UpdateDatabase('PoolStatus','SetDiff',poolDiff)
            elif (todo[0:8] == "cleanon="):
                data = todo[-5:]
                message = '{\"SetPool\":{\"CleanOn\":\"'+data+'\"}}\r'
                sendPacket(POOLCTRL, message)
                UpdateDatabase2('PoolTimers','Clean','TimeOn',data)
            elif (todo[0:9] == "cleanoff="):
                data = todo[-5:]
                message = '{\"SetPool\":{\"CleanOff\":\"'+data+'\"}}\r'
                sendPacket(POOLCTRL, message)
                UpdateDatabase2('PoolTimers','Clean','TimeOff',data)
            elif (todo[0:8] == "chloron="):
                data = todo[-5:]
                message = '{\"SetPool\":{\"ChlorOn\":\"'+data+'\"}}\r'
                sendPacket(POOLCTRL, message)
                UpdateDatabase2('PoolTimers','Chlorinator','TimeOn',data)
            elif (todo[0:9] == "chloroff="):
                data = todo[-5:]
                message = '{\"SetPool\":{\"ChlorOff\":\"'+data+'\"}}\r'
                sendPacket(POOLCTRL, message)
                UpdateDatabase2('PoolTimers','Chlorinator','TimeOff',data)
            elif (todo[0:11] == "pumphighon="):
                data = todo[-5:]
                message = '{\"SetPool\":{\"PumpHighOn\":\"'+data+'\"}}\r'
                sendPacket(POOLCTRL, message)
                UpdateDatabase2('PoolTimers','High','TimeOn',data)
            elif (todo[0:12] == "pumphighoff="):
                data = todo[-5:]
                message = '{\"SetPool\":{\"PumpHighOff\":\"'+data+'\"}}\r'
                sendPacket(POOLCTRL, message)
                UpdateDatabase2('PoolTimers','High','TimeOff',data)
            elif (todo[0:10] == "pumpmedon="):
                data = todo[-5:]
                message = '{\"SetPool\":{\"PumpMedOn\":\"'+data+'\"}}\r'
                sendPacket(POOLCTRL, message)
                UpdateDatabase2('PoolTimers','Med','TimeOn',data)
            elif (todo[0:11] == "pumpmedoff="):
                data = todo[-5:]
                message = '{\"SetPool\":{\"PumpMedOff\":\"'+data+'\"}}\r'
                sendPacket(POOLCTRL, message)
                UpdateDatabase2('PoolTimers','Med','TimeOff',data)
            elif (todo[0:10] == "pumplowon="):
                data = todo[-5:]
                message = '{\"SetPool\":{\"PumpLowOn\":\"'+data+'\"}}\r'
                sendPacket(POOLCTRL, message)
                UpdateDatabase2('PoolTimers','Low','TimeOn',data)
            elif (todo[0:11] == "pumplowoff="):
                data = todo[-5:]
                message = '{\"SetPool\":{\"PumpLowOff\":\"'+data+'\"}}\r'
                sendPacket(POOLCTRL, message)
                UpdateDatabase2('PoolTimers','Low','TimeOff',data)
            else:
                print "\nHaven't done this yet", device, todo
                
# Beginning of DHW command code

        elif device == 'DHW':
            if (todo[0:8] == "setmode="):
                data = int(todo[-1])
                message = '{\"SetDHW\":{\"Mode\":'+str(data)+'}}\r'
                #print('SM'),
                sendPacket(SPARE1, message)
                UpdateDatabase('DHWController','Mode',data)            
            elif (todo[0:8] == "settemp="):
                data = int(todo[-3:])
                message = '{\"SetDHW\":{\"Setpoint\":'+str(data)+'}}\r'
                #print('SP'),
                sendPacket(SPARE1, message)
                UpdateDatabase('DHWController','Setpoint',data)
            elif (todo[0:8] == "eheatsp="):
                data = int(todo[-3:])
                message = '{\"SetDHW\":{\"ElecSetpoint\":'+str(data)+'}}\r'
                #print("SD"),
                sendPacket(SPARE1, message)
                UpdateDatabase('DHWController','ElectricHeatSetpoint',data)
            elif (todo[0:9] == "timer1on="):
                data = todo[-5:]
                message = '{\"SetDHW\":{\"Timer1On\":\"'+data+'\"}}\r'
                #print('Timer'),
                sendPacket(SPARE1, message)
                UpdateDatabase('DHWController','Timer1On',data)
            elif (todo[0:10] == "timer1off="):
                data = todo[-5:]
                message = '{\"SetDHW\":{\"Timer1Off\":\"'+data+'\"}}\r'
                #print('Timer'),
                sendPacket(SPARE1, message)
                UpdateDatabase('DHWController','Timer1Off',data)
            elif (todo[0:9] == "timer2on="):
                data = todo[-5:]
                message = '{\"SetDHW\":{\"Timer2On\":\"'+data+'\"}}\r'
                #print('Timer'),
                sendPacket(SPARE1, message)
                UpdateDatabase('DHWController','Timer2On',data)
            elif (todo[0:10] == "timer2off="):
                data = todo[-5:]
                message = '{\"SetDHW\":{\"Timer2Off\":\"'+data+'\"}}\r'
                #print('Timer'),
                sendPacket(SPARE1, message)
                UpdateDatabase('DHWController','Timer2Off',data)
            else:
                print "\nHaven't done this yet", device, todo


                
        elif device == 'Garage':
            print "Garage command", todo
            if (todo == 'waterhon'):
                sendPacket(BROADCAST, "Garage,waterheateron\r")
            elif (todo == 'waterhoff'):
                sendPacket(BROADCAST, "Garage,waterheateroff\r")
            elif (todo == 'door1open'):
                sendPacket(BROADCAST, "Garage,door1\r")
            elif (todo == 'door1close'):
                sendPacket(BROADCAST, "Garage,door1\r")
            elif (todo == 'door2open'):
                sendPacket(BROADCAST, "Garage,door2\r")
            elif (todo == 'door2close'):
                sendPacket(BROADCAST, "Garage,door2\r")
            else:
                print "haven't done this yet"


                
        elif device == "preset":
            if (todo == "test"): # This is only to test the interaction
                print "got a preset test command"
            elif (todo =='acoff'):
                controlThermo("North", "off")
                controlThermo("South", "off")
                controlThermo("North", "fan=auto")
                controlThermo("South", "fan=auto")
            elif (todo == 'recirc'):
                controlThermo("North", "fan=recirc")
                controlThermo("South", "fan=recirc")
            elif (todo == 'auto'):
                controlThermo("North", "fan=auto")
                controlThermo("South", "fan=auto")
            elif (todo == 'temp98'):
                controlThermo("North", "temp=98")
                controlThermo("South", "temp=98")
                controlThermo("North", "fan=auto")
                controlThermo("South", "fan=auto")
            elif (todo == 'summernight'):
                controlThermo("North", "temp=78")
                controlThermo("South", "temp=79")
                controlThermo("North", "fan=recirc")
                controlThermo("South", "fan=recirc")
                controlThermo("North", "cool")
                controlThermo("South", "cool")
            elif (todo == 'winternight'):
                controlThermo("North", "temp=73")
                controlThermo("South", "temp=72")
                controlThermo("North", "fan=recirc")
                controlThermo("South", "fan=recirc")
                controlThermo("North", "heat")
                controlThermo("South", "heat")
            elif (todo == 'peakno'):
                controlThermo("North", "peakoff")
                controlThermo("South", "peakoff")
            elif (todo == 'peakyes'):
                controlThermo("North", "peakon")
                controlThermo("South", "peakon")
            else:
                print "haven't done this yet"
        else:
            print "command not implemented: ", str(c)
# -------------------------------------------------------------------------
#          NOAA Dewpoint Calculation
# -------------------------------------------------------------------------
def CalcDewpoint():
 try:
  outside = float(OutsideTemp)
  humid = float(OutsideHumidity)
  Celcius = (outside-32)*5/9
  A0 = 373.15/(273.15+Celcius)
  Sum = -7.90298*(A0-1)
  Sum += 5.02808*log10(A0)
  Sum += -1.3816e-7*(pow(10,(11.344*(1-1/A0)))-1)
  Sum += 8.1328e-3*(pow(10,(-3.49149*(A0-1)))-1)
  Sum += log10(1013.246)
  VP = pow(10, Sum-3)*humid
  T = log(VP/0.61078)
  dewpoint = (241.88*T)/(17.558-T)
  dewpoint = (1.8*dewpoint+32)
  return dewpoint
 except:
  return 0
# -------------------------------------------------------------------------
#          NOAA Heat Index Calculation
# -------------------------------------------------------------------------
def CalcHeatIndex():
 c1 = -42.38
 c2 = 2.049
 c3 = 10.14
 c4 = -0.2248
 c5 = -6.838e-3
 c6 = -5.482e-2
 c7 = 1.228e-3
 c8 = 8.528e-4
 c9 =- 1.99e-6 
 T = float(OutsideTemp)       #Your outside Temp sensor reading
 R = float(OutsideHumidity)   #Your Outside Humidity sensor reading
 T2 = T*T
 R2 = R*R
 TR = T*R
 rv = c1 + c2*T + c3*R + c4*T*R + c5*T2 + c6*R2 + c7*T*TR + c8*TR*R + c9*T2*R2
 return rv
# -------------------------------------------------------------------------
#                   Reset high and low temperatures
# -------------------------------------------------------------------------
def ResetTemps():
 global DayOutMaxTemp, DayOutMinTemp # Needed to keep from giving local variable errors...
 message = 'Temperatures for '+time.strftime("%A, %d %B, ")+' were '+str(DayOutMaxTemp)+'F / '+str(DayOutMinTemp)+'F\n\n'
 message = message + 'Temperatures reset for next day...'
 SendMail ("myeager1967@gmail.com","Status Update",message)
 DayOutMaxTemp = OutsideTemp
 DayOutMinTemp = OutsideTemp

# -------------------------------------------------------------------------
#                   Email pool temperature
# -------------------------------------------------------------------------
def EmailPoolTemp():
    dbconn = sqlite3.connect(DATABASE)
    c = dbconn.cursor()
    c.execute('Select PoolTemp from PoolStatus')
    PoolTemp = getFltfromString(str(c.fetchone()))
    dbconn.close()
    message = 'Pool Temperature is '+str(PoolTemp)+'F\n\n'
    SendMail ("myeager1967@gmail.com","Pool Temperature",message)
    SendMail ("lyeager1967@gmail.com","Pool Temperature",message)

def UpdateDatabase(database, attrib, data):
    dbconn = sqlite3.connect(DATABASE)
    c = dbconn.cursor()
    c.execute('update '+ database +' ' 
     'set '+ attrib +' = ?;',
     (data,))
    dbconn.commit()
    dbconn.close()

def UpdateDatabase2(database, whichone, attrib, data):    
    dbconn = sqlite3.connect(DATABASE)
    c = dbconn.cursor()
    c.execute('update '+ database +' ' 
      'set '+ attrib +' = ? where name = ?;',
      (data,whichone))
    dbconn.commit()
    dbconn.close()

def PoolTest():
    message = '{\"SetPool\":{\"Test\":\"0000\"}}\r'
    sendPacket(POOLCTRL, message)

# ------------------------------------------------------------------------------
#                        Catch EXIT signal...
# ------------------------------------------------------------------------------

def signal_handler(signal,frame):
 print time.strftime("\n\n%A, %B, %d at %H:%M:%S -- Exit Signal!!!")
 sys.stdout.flush()
 sys.exit(0)

#Catch Control-C input so it isn't ugly
##signal.signal(signal.SIGINT, signal_handler)
#logging.basicConfig(format='%(levelname)s:%(message)s',level=logging.WARNING)

# Send Restart Status Email...
#message = 'House controller restarted -- '+time.strftime("%B, %d at %H:%M:%S")
#SendMail ("myeager1967@gmail.com","Status Update",message)

print ("\n\nRestarted Module at "+time.strftime("%B, %d at %H:%M:%S"))

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

SunInfo()
print '\nSunrise at -> ',Sunrise
print 'Sunset at  -> ',Sunset,'\n'

# ------------------------------------------------------------------------------
#                        Scheduled events
# ------------------------------------------------------------------------------
scheditem = BackgroundScheduler()

# Print a status message
scheditem.add_job(printHouseData, 'interval', minutes=3)
# Print a status message
#scheditem.add_interval_job(PoolTest, seconds=15)
# Email Pool Temperature
scheditem.add_job(EmailPoolTemp, 'cron', day_of_week ='mon-sun', hour=16, minute=30)
# Get Sunrise / Sunset Times
scheditem.add_job(SunInfo, 'cron', day_of_week ='mon-sun', hour=0, minute=0, second=15)
#-----------------------------------------------------------------
#scheditem.start()

# This is the main thread.  Since most of the real work is done by 
# scheduled tasks, this code checks to see if packets have been 
# captured and calls the packet decoder

# This process also handles commands sent over the XBee network 
# to the various devices.  I want to keep the information on the
# exact commands behind the firewall, so they'll come in as 
# things like 'AcidPump, on', 'Garage, dooropen'
# since this is a multiprocess environment, I'm going to use 
# system v message queues to pass the commands to this process

# Create the message queue where commands can be read
# I just chose an identifier of 12.  It's my machine and I'm
# the only one using it so all that crap about unique ids is
# totally useless.  12 is the number of eggs in a normal carton.
Cqueue = sysv_ipc.MessageQueue(12, sysv_ipc.IPC_CREAT,mode=0666)
#Pqueue = sysv_ipc.MessageQueue(14, sysv_ipc.IPC_CREAT,mode=0666) # Queue to send data to sign process

firstTime = True;
#print "started on", time.strftime("%A, %B, %d at %H:%M:%S")

while True:

 try:
  time.sleep(0.1)
  sys.stdout.flush()
  if packets.qsize() > 0:
   # got a packet from recv thread
   # See, the receive thread gets them
   # puts them on a queue and here is
   # where I pick them off to use
   newPacket = packets.get_nowait()
   # now go dismantle the packet
   # and use it.
   handlePacket(newPacket)
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
    
    # Now that things are clear, start scheduler...
    scheditem.start()
    print('\nScheduler Started...')
    # Create XBee library API object, which spawns a new thread
    zb = ZigBee(ser, callback=message_received)
    print '\nZigBee Module started...'
    
    print('\nEntering Processing Loop....\n---------------------------')
   newCommand = Cqueue.receive(block=False, type=0)
   # type=0 above means suck every message off the
   # queue.  If I used a number above that, I'd
   # have to worry about the type in other ways.
   # note, I'm reserving type 1 messages for 
   # test messages I may send from time to 
   # time.  Type 2 are messages that are
   # sent by the php code in the web interface.
   # Type 3 are from the event handler.
   # I haven't decided on any others yet.
   handleCommand(newCommand)
  except sysv_ipc.BusyError:
   pass # Only means there wasn't anything there

 except KeyboardInterrupt:
         break
        
# halt() must be called before closing the serial
# port in order to ensure proper thread shutdown
zb.halt()
ser.close()
