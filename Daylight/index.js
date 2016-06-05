/*** Daylight Z-Way HA module *******************************************

Version: 1.0.0
(c) Martijn van der Horst, 2014
-----------------------------------------------------------------------------
Author: Martijn van der Horst <M.G.v.d.Horst@gmail.com>
Description:
    Creates a binary sensor that indicates whether it is daylight (or not)
    the value is based on sunrise/sunset times from a calculation
******************************************************************************/

// ----------------------------------------------------------------------------
// --- Class definition, inheritance and setup
// ----------------------------------------------------------------------------

function Daylight (id, controller) {
    // Call superconstructor first (AutomationModule)
    Daylight.super_.call(this, id, controller);
}

inherits(Daylight, AutomationModule);

_module = Daylight;

// ----------------------------------------------------------------------------
// --- Module instance initialized
// ----------------------------------------------------------------------------

Daylight.prototype.init = function (config) {
    Daylight.super_.prototype.init.call(this, config);

    var self = this;

    // Setup device
    this.vDev = this.controller.devices.create({
        deviceId: "Daylight_" + this.id,
        defaults: {
            deviceType: 'sensorBinary',
            metrics: {
                level: 'off',
				icon: '/ZAutomation/api/v1/load/modulemedia/Daylight/icon.png',
                title: 'Daylight ' + this.id
            }
        },
        overlay: {
            deviceType: 'sensorBinary'
        },
        moduleId: this.id
    });

    this.do_update_state = function () {
        self.update_state();
    };
    this.do_update_schedule = function () {
        self.update_schedule();
    };

    // Setup event listeners
    this.controller.on("daylight.sunrise", this.do_update_state);
    this.controller.on("daylight.sunset", this.do_update_state);
    this.controller.on("daylight.newdate", this.do_update_schedule);
    
    // Add cron schedule for updating the sunrise and sunset times
    // This is done at 03:01 to ensure the schedule is updated after any switch to or from daylight savings time 
    this.controller.emit("cron.addTask", "daylight.newdate", {
        minute: 1,
        hour: 3,
        weekDay: null,
        day: null,
        month: null
    });


    // Setup sunrise and sunset events and current state
    self.update_state();

};

Daylight.prototype.stop = function () {
    // Remove cron tasks
    this.controller.emit("cron.removeTask", "daylight.sunrise");
    this.controller.emit("cron.removeTask", "daylight.sunset");
    this.controller.emit("cron.removeTask", "daylight.newdate");

    // Remove event listeners
    this.controller.off("daylight.sunrise", this.do_update_state);
    this.controller.off("daylight.sunset", this.do_update_state);
    this.controller.off("daylight.newdate", this.do_update_schedule);

    // Remove device
    if (this.vDev) {
        this.controller.devices.remove(this.vDev.id);
        this.vDev = null;
    }
    
    Daylight.super_.prototype.stop.call(this);
};

// ----------------------------------------------------------------------------
// --- Module methods
// ----------------------------------------------------------------------------

Daylight.prototype.update_schedule = function () {
    var self = this;
    var now = new Date(Date.now());
    var latitude = this.config.latitude;
    var longitude = this.config.longitude;
    var zenith = this.config.zenith;
    var sunrise = self.sunrise_sunset_algorithm(now, "sunrise", latitude, longitude, zenith);
    var sunset = self.sunrise_sunset_algorithm(now, "sunset", latitude, longitude, zenith);
    var thour;
    var tminute;
	var dtime;

    debugPrint("Daylight: Schedule update executed");

    // Remove existing cron tasks for sunrise/sunset
    this.controller.emit("cron.removeTask", "daylight.sunrise");
    this.controller.emit("cron.removeTask", "daylight.sunset");

    // Add cron schedule for sunrise
    debugPrint("Daylight: Sunrise in local time: " + sunrise.toString())
    debugPrint("Daylight: Sunrise in UTC time  : " + sunrise.toUTCString())
	thour = sunrise.getHours();
    tminute = sunrise.getMinutes();
    //sunrise.setMinutes(sunrise.getMinutes() + 1); // +1 to ensure update_state is executed after sunrise
	if (thour > 12) { sunrise_short = (thour -12) + ":" + ((tminute < 10) ? "0"+tminute : tminute) + " pm"; }
	else { sunrise_short = thour + ":" + ((tminute < 10) ? "0"+tminute : tminute) + " am"; }
    //sunrise_short = thour + ":" + ((tminute < 10) ? "0"+tminute : tminute); 
    debugPrint("Daylight: Sunrise event scheduled for " + sunrise_short);
    self.vDev.set("metrics:sunrise", sunrise_short);
    this.controller.emit("cron.addTask", "daylight.sunrise", {
        minute: tminute,
        hour: thour,
        weekDay: null,
        day: null,
        month: null
    });

    // Add cron schedule for sunset
    debugPrint("Daylight: Sunset in local time: " + sunset.toString())
    debugPrint("Daylight: Sunset in UTC time  : " + sunset.toUTCString())
	thour = sunset.getHours();
    tminute = sunset.getMinutes();
    //sunset.setMinutes(sunset.getMinutes() + 1); // +1 to ensure update_state is executed after sunset
	if (thour > 12) { sunset_short = (thour - 12) + ":" + ((tminute < 10) ? "0"+tminute : tminute) + " pm"; }
	else { sunset_short = thour + ":" + ((tminute < 10) ? "0"+tminute : tminute) + " am"; }
    //sunset_short = thour + ":" + ((tminute < 10) ? "0"+tminute : tminute);
    debugPrint("Daylight: Sunset event scheduled for " + sunset_short);
    self.vDev.set("metrics:sunset", sunset_short);
    this.controller.emit("cron.addTask", "daylight.sunset", {
        minute: tminute,
        hour: thour,
        weekDay: null,
        day: null,
        month: null
    });
}

Daylight.prototype.update_state = function () {
    var self = this;
    var now = new Date(Date.now());
    var latitude = this.config.latitude;
    var longitude = this.config.longitude;
    var zenith = this.config.zenith;
    var sunrise = self.sunrise_sunset_algorithm(now, "sunrise", latitude, longitude, zenith);
    var sunset = self.sunrise_sunset_algorithm(now, "sunset", latitude, longitude, zenith);
    var current_level = self.vDev.get("metrics:level");
	
	//self.vDev.set('metrics:icon',self.imagePath+'/icon.png');
    
    debugPrint("Daylight: Status update executed");
    debugPrint("Daylight: current local time: " + (new Date(Date.now())).toString())
    debugPrint("Daylight: current UTC time  : " + (new Date(Date.now())).toUTCString())
    debugPrint("Daylight: Sunrise in local time: " + sunrise.toString())
    debugPrint("Daylight: Sunrise in UTC time  : " + sunrise.toUTCString())
    debugPrint("Daylight: Sunset in local time: " + sunset.toString())
    debugPrint("Daylight: Sunset in UTC time  : " + sunset.toUTCString())

    if ((now>sunrise) && (now<sunset)) {
        debugPrint("Daylight: Conclusion is that sensor should be on");
        if (current_level !== "on") {
            self.vDev.set("metrics:level", "on");
            debugPrint("Daylight: Sensor switched to on");
        } else {
            debugPrint("Daylight: Sensor already on, nothing changed");
        }
    } else {
        debugPrint("Daylight: Conclusion is that sensor should be off");
        if (current_level !== "off") {
            self.vDev.set("metrics:level", "off");
            debugPrint("Daylight: Sensor switched to off");
        } else {
            debugPrint("Daylight: Sensor already off, nothing changed");
        }
    }

    self.update_schedule();
}

Daylight.prototype.sunrise_sunset_algorithm = function(date, setorrise, latitude, longitude, zenith_name) {
    /*
    Sunrise/Sunset Algorithm

    Source:
            Almanac for Computers, 1990
            published by Nautical Almanac Office
            United States Naval Observatory
            Washington, DC 20392

    Implemented by:
            Martijn van der Horst

    Inputs:
            date:                  date for sunrise/sunset calculation
            setorrise:             whether to calculate sunset or sunrise time
              'sunset'
              'sunrise'
            latitude, longitude:   location for sunrise/sunset in degrees
            zenith_name:           Sun's zenith for sunrise/sunset
              'offical'      = 90 degrees 50'
              'civil'        = 96 degrees
              'nautical'     = 102 degrees
              'astronomical' = 108 degrees

            NOTE: longitude is positive for East and negative for West

    Returns:
            A new Date object indicating the time at which the sun rises or sets

    */
    var zenith = 90.8333333;
    if (zenith_name === 'civil') {
        zenith = 96;
    } else if (zenith_name === 'nautical') {
        zenith = 102;
    } else if (zenith_name === 'astronomical') {
        zenith = 108;
    }

    /* 1. first calculate the day of the year (N) */
    var start_of_year = new Date(date);
    start_of_year.setUTCFullYear(date.getUTCFullYear(), 0, 1);
    var N = Math.floor((date.getTime()-start_of_year.getTime())/(24 * 60 * 60 * 1000));

    /* 2. convert the longitude to hour value (lngHour) and calculate an approximate time (t) */
    var lngHour = longitude / 15;
    var t = N + ((6 - lngHour) / 24);
    if (setorrise === 'sunset') {
        t = N + ((18 - lngHour) / 24);
    }

    /* 3. calculate the Sun's mean anomaly (M) */
    var M = (0.9856 * t) - 3.289;

    /* 4. calculate the Sun's true longitude (L) */
    var L = M + (1.916 * Math.sin(M * (Math.PI/180))) + (0.020 * Math.sin(2 * M * (Math.PI/180))) + 282.634;
    while (L < 0) {
        L += 360;
    };
    while (L >= 360) {
        L -= 360;
    }

    /* 5a. calculate the Sun's right ascension (RA) */
    var RA = Math.atan(0.91764 * Math.tan(L * (Math.PI/180))) * (180/Math.PI);
    while (RA < 0) {
        RA += 360;
    };
    while (RA >= 360) {
        RA -= 360;
    }

    /* 5b. right ascension value needs to be in the same quadrant as L */
    var Lquadrant  = (Math.floor( L/90)) * 90;
    var RAquadrant = (Math.floor(RA/90)) * 90;
    RA = RA + (Lquadrant - RAquadrant);

    /* 5c. right ascension value needs to be converted into hours */
    RA = RA / 15;

    /* 6. calculate the Sun's declination */
    var sinDec = 0.39782 * Math.sin(L * (Math.PI/180));
    var cosDec = Math.cos(Math.asin(sinDec))

    /* 7a. calculate the Sun's local hour angle */
    var cosH = (Math.cos(zenith * (Math.PI/180)) - (sinDec * Math.sin(latitude * (Math.PI/180)))) / (cosDec * Math.cos(latitude * (Math.PI/180)));
    if (cosH >  1) {
        /* the sun never rises on this location (on the specified date) */
        return null;
    }
    if (cosH < -1) {
        /* the sun never sets on this location (on the specified date) */
        return null;
    }

    /* 7b. finish calculating H and convert into hours */
    var H = 360 - (Math.acos(cosH)*(180/Math.PI));
    if (setorrise === 'sunset') {
        H = Math.acos(cosH)*(180/Math.PI);
    }
    H = H / 15;

    /* 8. calculate local mean time of rising/setting (T) */
    var T = H + RA - (0.06571 * t) - 6.622

    /* 9. adjust back to UTC */
    var UT = T - lngHour
    while (UT < 0) {
        UT += 24;
    };
    while (UT >= 24) {
        UT -= 24;
    }

    /* 10. convert UT value to local time zone */
    var UTChours = Math.floor(UT);
    UT = (UT - UTChours) * 60;
    var UTCminutes = Math.floor(UT);
    UT = (UT - UTCminutes) * 60;
    var UTCseconds = Math.floor(UT);
    UT = (UT - UTCseconds) * 1000;
    var UTCms = Math.floor(UT);
    
    var result = new Date(date);
    result.setUTCHours(UTChours, UTCminutes, UTCseconds, UTCms);
    
    // UTC to local timezone conversion could have changed the date, ensure that the result is on the requested date:
    result.setFullYear(date.getFullYear(), date.getMonth(), date.getDate());

    return result;
}
