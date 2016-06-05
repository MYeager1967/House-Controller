<?php
define('IS_AJAX', isset($_SERVER['HTTP_X_REQUESTED_WITH']) && strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) == 'xmlhttprequest');

if(!IS_AJAX){
	echo("Bug Off ");
	$ipaddress = $_SERVER["REMOTE_ADDR"];
	echo "Your IP is $ipaddress!";
	die();
}

$db= new SQLite3('/home/pi/DataBase/Aspenwood.db');
/*
Having everything happen on second boundaries can cause the 
database to be busy when all the processes fire at once. So, 
delaying a call when it is busy will keep database errors to 
a minimum.  Actually, the first delay will almost certainly 
assure the rest of them will execute just fine, since the 
second boundary will pass.
*/
function timedQuerySingle($statement){
	global $db;

	if ($db->busyTimeout(150)){
		$result = $db->querySingle($statement);
		}
	else{
		error_log($statement);
		}
	$db->busyTimeout(0);
	return ($result);
	}
# Get the various items out of the data base
# This could be one giant array() statement
# and actually save cpu , but getting them as
# variables first makes debugging and array 
# construction easier.  At least initially.
#$power = $db->querySingle("select rpower from power;");
$mbeddim = timedQuerySingle('select "Status" from "Lights" where name="Master Bedroom";');
$sunrise = timedQuerySingle("select Sunrise from OutsideConditions;");
$sunset = timedQuerySingle("select Sunset from OutsideConditions;");
# Current status of the two thermostats
$ntm = timedQuerySingle(
	'select status from thermostats where location="North";');
$stm = timedQuerySingle(
	'select status from thermostats where location="South";');
$ntt = timedQuerySingle(
	'select "temp-reading" from thermostats where location="North";');
$stt = timedQuerySingle(
	'select "temp-reading" from thermostats where location="South";');
# The North and South Thermostat setting (temp, mode, fan)
$ntms = timedQuerySingle(
	'select "s-mode" from thermostats where location="North";');
$stms = timedQuerySingle(
	'select "s-mode" from thermostats where location="South";');
$ntfs = timedQuerySingle(
	'select "s-fan" from thermostats where location="North";');
$stfs = timedQuerySingle(
	'select "s-fan" from thermostats where location="South";');
$ntts = timedQuerySingle(
	'select "s-temp" from thermostats where location="North";');
$stts = timedQuerySingle(
	'select "s-temp" from thermostats where location="South";');
$poolsign = timedQuerySingle(
	'select "Status" from Devices where Name = "PoolSign";');
$solar = timedQuerySingle(
	'select "Status" from Devices where Name = "Solar Outlet";');
#$apl = timedQuerySingle(
#	'select "level" from PoolSign;');
$patioscene = timedQuerySingle(
	'select "Active" from Scenes where Name = "Patio";');
#$gd2 = timedQuerySingle(
#	'select "door2" from garage;');
#$wh = timedQuerySingle(
#	'select "waterh" from garage;');

# >>>> This is the section where pool and outside data are retrieved
//$outtemp = timedQuerySingle("select Temp2 from OutsideConditions;");
$outtemp = timedQuerySingle("select Temperature from OutsideConditions;");
//$outhumid = timedQuerySingle("select Humid2 from OutsideConditions;");
$outhumid = timedQuerySingle("select Humidity from OutsideConditions;");
$outtempmax = timedQuerySingle("select DayTempMax from OutsideConditions;");
$outtempmin = timedQuerySingle("select DayTempMin from OutsideConditions;");
$tempf = timedQuerySingle("select Temp2 from OutsideConditions;");
$pm = timedQuerySingle('select "PoolPump" from PoolStatus;');
$pmode = timedQuerySingle('select "Mode" from PoolStatus;');
$pspeed = timedQuerySingle('select "Speed" from PoolStatus;');
$poolsetpoint = timedQuerySingle('select "SetTemp" from PoolStatus;');
$setdiff = timedQuerySingle('select "SetDiff" from PoolStatus;');
$solardiff = timedQuerySingle('select "SolarDifferential" from PoolStatus;');

# Read pool timers...
$cleanon = timedQuerySingle('select "TimeOn" from "PoolTimers" where name="Clean";');
$cleanoff = timedQuerySingle('select "TimeOff" from "PoolTimers" where name="Clean";');
$chloron = timedQuerySingle('select "TimeOn" from "PoolTimers" where name="Chlorinator";');
$chloroff = timedQuerySingle('select "TimeOff" from "PoolTimers" where name="Chlorinator";');
$pumplowon = timedQuerySingle('select "TimeOn" from "PoolTimers" where name="Low";');
$pumplowoff = timedQuerySingle('select "TimeOff" from "PoolTimers" where name="Low";');
$pumpmedon = timedQuerySingle('select "TimeOn" from "PoolTimers" where name="Med";');
$pumpmedoff = timedQuerySingle('select "TimeOff" from "PoolTimers" where name="Med";');
$pumphighon = timedQuerySingle('select "TimeOn" from "PoolTimers" where name="High";');
$pumphighoff = timedQuerySingle('select "TimeOff" from "PoolTimers" where name="High";');

$weatherupdated = timedQuerySingle('select "Updated" from OutsideConditions;');
//$weatherupdated = timedQuerySingle('select "Updated2" from OutsideConditions;');

$pw = timedQuerySingle('select "waterfall" from pool;');
$pl = timedQuerySingle('select "light" from pool;');
$pf = timedQuerySingle('select "fountain" from pool;');
$ps = timedQuerySingle('select "SolarPump" from PoolStatus;');
$pt = timedQuerySingle('select "PoolTemp" from PoolStatus;');
$ph = timedQuerySingle('select "pH" from PoolStatus;');

# Stuff for DHW Controller Setting Page
$dhwt = timedQuerySingle('select "TankTemp" from DHWController;');
$dhwsp = timedQuerySingle('select "Setpoint" from DHWController;');
$dhwmode = timedQuerySingle('select "Mode" from DHWController;');
$dhwcoll = timedQuerySingle('select "CollectorTemp" from DHWController;');
$dhwehsp = timedQuerySingle('select "ElectricHeatSetpoint" from DHWController;');
$dhwheat = timedQuerySingle('select "SolarPump" from DHWController;');
$dhweheat = timedQuerySingle('select "ElecHeatOn" from DHWController;');
$dhwtimer1on = timedQuerySingle('select "Timer1On" from DHWController;');
$dhwtimer1off = timedQuerySingle('select "Timer1Off" from DHWController;');
$dhwtimer2on = timedQuerySingle('select "Timer2On" from DHWController;');
$dhwtimer2off = timedQuerySingle('select "Timer2Off" from DHWController;');

# >>>> 
$porchlight = timedQuerySingle(
	'select "Status" from "Lights" where name="Front Porch";');
$kitchenlight = timedQuerySingle(
	'select "status" from "Lights" where name="Kitchen";');
$patiolight = timedQuerySingle(
	'select "Status" from "Lights" where name="Pool Deck";');
$poollight = timedQuerySingle(
	'select "Status" from "Lights" where name="Pool Light";');
$colorwheel = timedQuerySingle(
	'select "Status" from "Lights" where name="Color Wheel";');
$diningoutlet = timedQuerySingle('select "Status" from "Devices" where name="Dining Outlet";');
$fdoorlock = timedQuerySingle ('select "Status" from "Doors" where name="Front";');
$flockauto = timedQuerySingle ('select "Auto" from "Doors" where name="Front";');
$fdoorsensor = timedQuerySingle ('select "Sensor" from "Doors" where name="Front";');
$pdoorlock = timedQuerySingle ('select "Status" from "Doors" where name="Patio";');
$plockauto = timedQuerySingle ('select "Auto" from "Doors" where name="Patio";');
$pdoorsensor = timedQuerySingle ('select "Sensor" from "Doors" where name="Patio";');	
$gdoorstat = timedQuerySingle (
	'select "Open" from "Doors" where name="Garage";');
$xmasenabled = timedQuerySingle(
	'select "Enabled" from "Scenes" where name="Christmas";');
$xmasactive = timedQuerySingle('select "Active" from "Scenes" where name="Christmas";');
$entryenabled = timedQuerySingle('select "Enabled" from "Scenes" where name="AutoEntry";');
$patioactive = timedQuerySingle(
	'select "Active" from "Scenes" where name="Patio";');
$db->close();
# Now, construct an array to use in the  json_encode()
# statement at the bottom.
$giveback = array('mbeddim' => $mbeddim, 'outsidetemp'=>$outtemp, 'ph'=>$ph,
    'outhumid'=>$outhumid, 'poolsetpoint'=>$poolsetpoint, 'setdiff'=>$setdiff, 'solardiff'=>$solardiff, 'weatherupdated'=>$weatherupdated,
	'tempf'=>$tempf, 'outmax'=>$outtempmax, 'outmin'=>$outtempmin,
	'cleanon'=>$cleanon, 'cleanoff'=>$cleanoff, 'chloron'=>$chloron, 'chloroff'=>$chloroff,
	'pumplowon'=>$pumplowon, 'pumplowoff'=>$pumplowoff, 'pumpmedon'=>$pumpmedon, 'pumpmedoff'=>$pumpmedoff, 'pumphighon'=>$pumphighon, 'pumphighoff'=>$pumphighoff,
	'ntm'=>$ntm, 'stm'=>$stm, 'ntt'=>$ntt, 'stt'=>$stt,
	'ntms'=>$ntms, 'stms'=>$stms, 'ntfs'=>$ntfs, 'stfs'=>$stfs,
	'ntts'=>$ntts, 'stts'=>$stts,
	'poolsign'=>$poolsign, 'solar'=>$solar, 'sunrise'=>$sunrise, 'sunset'=>$sunset, #'apl'=>$apl,
	'patioscene'=>$patioscene,
	'flockauto'=>$flockauto, 'plockauto'=>$plockauto,
// Water Heater Variables
	'dhwt'=>$dhwt, 'dhwmode'=>$dhwmode, 'dhwsp'=>$dhwsp, 'dhwehsp'=>$dhwehsp, 'dhwheat'=>$dhwheat, 'dhweheat'=>$dhweheat,
	'dhwtimer1on'=>$dhwtimer1on, 'dhwtimer1off'=>$dhwtimer1off, 'dhwtimer2on'=>$dhwtimer2on, 'dhwtimer2off'=>$dhwtimer2off,
	'dhwcoll'=>$dhwcoll,
	#'gd2'=>$gd2, 'wh'=>$wh,
	'pmode'=>$pmode, 'pspeed'=>$pspeed, 'pm'=>$pm, 'pw'=>$pw, 'pl'=>$pl, 'pf'=>$pf, 'ps'=>$ps, 'pt'=>$pt,
	'poollight'=>$poollight, 'colorwheel'=>$colorwheel, //'patiolight'=>$patiolight, 'diningoutlet'=>$diningoutlet,
	'porchlight'=>$porchlight, 'kitchenlight'=>$kitchenlight, 'patiolight'=>$patiolight, 'diningoutlet'=>$diningoutlet,
	'fdoorlock'=>$fdoorlock, 'fdoorsensor'=>$fdoorsensor, 'pdoorlock'=>$pdoorlock, 'pdoorsensor'=>$pdoorsensor,
	'gdoorstat'=>$gdoorstat, 'xmasenabled'=>$xmasenabled, 'xmasactive'=>$xmasactive, 'patioactive'=>$patioactive,
	'entryenabled'=>$entryenabled); // 'xmasenabled'=>$xmasenabled, 'xmasactive'=>$xmasactive, 'patioactive'=>$patioactive);
# And lastly, send it back to the web page
echo json_encode($giveback);
?>
