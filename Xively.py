#! /home/pi/PythonScripts

# This is the module that updates the Xively feed....

from apscheduler.schedulers.background import BackgroundScheduler

import logging
import datetime
import time
import sqlite3
import sys
import xively

UpdateRunning = False

# The Database where the information is stored
DATABASE='/home/pi/DataBase/Aspenwood.db'

# The Xively feed id and API key are retrieved from the database
FEED_ID = 0 
API_KEY = ''

#-------------------------------------------------
logging.basicConfig(level=logging.ERROR)
#-------------------------------------------------

# This is where the update to Xively happens
def UpdateXively():

    global UpdateRunning

    if(UpdateRunning == False):
        try:
            UpdateRunning = True
            # Read data from database
            dbconn = sqlite3.connect(DATABASE)
            c = dbconn.cursor()
            c.execute('Select PoolPump from PoolStatus')
            PoolPump = getFltfromString(str(c.fetchone()))
            c.execute('Select SolarPump from PoolStatus')
            PoolSolarPump = getFltfromString(str(c.fetchone()))
            c.execute('Select Chlorine from PoolStatus')
            Chlorine = getFltfromString(str(c.fetchone()))
            c.execute('Select SolarDifferential from PoolStatus')
            SolarDifferential = getFltfromString(str(c.fetchone()))
            c.execute('Select TankTemp from DHWController')
            DHW = getFltfromString(str(c.fetchone()))
            dbconn.close()
            
            now = datetime.datetime.utcnow()
            feed.datastreams = [
            xively.Datastream(id='Pool_Pump', current_value=PoolPump, at=now),
            xively.Datastream(id='Pool_Chlor', current_value=Chlorine, at=now),
            xively.Datastream(id='Pool_Solar_Pump', current_value=PoolSolarPump,at=now),
            xively.Datastream(id='Pool_Solar_Diff', current_value=SolarDifferential,at=now),
                
            xively.Datastream(id='Water_Heater', current_value=DHW,at=now)
                
                ]
            feed.update()
            print "X",
        except:
            print "O",	# Xively Update Failed
            
        UpdateRunning = False
    else:
        pass

def Status():
    print "\n\nTime ", time.strftime("- %H:%M:%S\n")

def getFltfromString(data): 
    temp = data
    temp2 = temp[1:]
    temp3 = temp2.split(",")
    return temp3[0]

#---------------------------------------------------
scheditem = BackgroundScheduler()
#------------------ Stuff I schedule to happen -----

scheditem.add_job(UpdateXively, 'interval', seconds=15)
scheditem.add_job(Status, 'interval', hours=2, minutes=30)
#---------------------------------------------------
scheditem.start()

# Get Feed ID and Key from Database
while (FEED_ID == 0):
    try:
        dbconn = sqlite3.connect(DATABASE)
        c = dbconn.cursor()
        c.execute('Select Username from Credentials where Name="Xively"')
        temp = getFltfromString(str(c.fetchone()))
        FEED_ID = temp[2:(len(temp)-1)]
        c.execute('Select Password from Credentials where Name="Xively"')
        temp = getFltfromString(str(c.fetchone()))
        API_KEY = temp[2:(len(temp)-1)]
        dbconn.close()
    except:
        pass

print "\n\nXively Update Process started on", time.strftime("%A, %B, %d at %H:%M:%S\n")

# Initialize api client
api = xively.XivelyAPIClient(API_KEY)
# and get my feed
feed = api.feeds.get(FEED_ID)

# Now do nothing while the scheduler takes care of things for me

while(1):
    time.sleep(1)
    sys.stdout.flush()

