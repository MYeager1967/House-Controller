/*** TempF Z-Way Home Automation module ***********************************

 Version: 1.0

 ------------------------------------------------------------------------------
 Author: Michael Yeager
 Description: Converts system Celsius temperature to Fahrenheit. Creates an
			  element and dummy sensor deviceId for the Home Automation
			  interface.
			  
		***** Uses Celsius temperature input *****
		
		***** Output to display in Fahrenheit *****

******************************************************************************/

// ----------------------------------------------------------------------------
// --- Class definition, inheritance and setup
// ----------------------------------------------------------------------------

function TempF (id, controller) {
    // Call superconstructor first (AutomationModule)
    TempF.super_.call(this, id, controller);
};

inherits(TempF, AutomationModule);

_module = TempF;

// ----------------------------------------------------------------------------
// --- Module instance initialized
// ----------------------------------------------------------------------------

TempF.prototype.init = function (config) {

    // Call superclass' init (this will process config argument and so on)
    TempF.super_.prototype.init.call(this, config);

    // Remember "this" for detached callbacks (such as event listener callbacks)
    var self = this;

	this.vDev = this.controller.devices.create({
        deviceId: "DummyTempSensor_" + this.id,
        defaults: {
            deviceType: "sensorMultilevel",
            metrics: {
                scaleTitle:  this.config.scale === 'C' ? '°C' : '°F',
                level: this.config.scale === 'C' ? 26 : 80,
                min: this.config.scale === 'C' ? -34 : -30,
                max: this.config.scale === 'C' ? 54.4 : 130,
				probeType: 'temperatureF',
				icon: '/ZAutomation/api/v1/load/modulemedia/TempF/icon.png',
                title: 'TempF ' + this.id
            }
        },
        overlay: {},
        handler: function (command, args) {
            self.vDev.set("metrics:level", args.level);
        },
        moduleId: this.id
    });
	
	this.controller.devices.on(this.config.sensor1, 'change:metrics:level', function() {
        self.OnChange();
		});
};

TempF.prototype.stop = function () {
    
	this.controller.devices.off(this.config.sensor1, 'change:metrics:level', function() {
		self.OnChange();
		});
	if (this.vDev) {
        this.controller.devices.remove(this.vDev.id);
        this.vDev = null;
    }
    TempF.super_.prototype.stop.call(this);
};

// ----------------------------------------------------------------------------
// --- Module methods
// ----------------------------------------------------------------------------

TempF.prototype.OnChange = function () {
	var vDevSensor1 = this.controller.devices.get(this.config.sensor1),
    vDev = this.vDev;

    var tempC = vDevSensor1.get('metrics:level');
	var temp  = Math.round((tempC*9/5+32)*100)/100;
	//if (temp < 110 && temp > -30) {
	console.log("TempF: Temperature C -> "+ tempC);	
	console.log("TempF: Temperature F -> "+ temp);
	vDev.set('metrics:level', temp);
	//	}
	//else {
	//	console.log("TempF: Invalid TempC -> "+ tempC);	
	//	}
}