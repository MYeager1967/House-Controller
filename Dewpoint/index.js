/*** Dewpoint Z-Way Home Automation module ***********************************

 Version: 1.0

 ------------------------------------------------------------------------------
 Author: Michael Yeager
 Description: Uses temperature and humidity data from sensors to calculate the
			  current dew point. Creates an element and dummy sensor deviceId
			  for the Home Automation interface.
			  
		***** Uses Celsius temperature input *****
		
		***** Output to display in Fahrenheit *****

******************************************************************************/

// ----------------------------------------------------------------------------
// --- Class definition, inheritance and setup
// ----------------------------------------------------------------------------

function Dewpoint (id, controller) {
    // Call superconstructor first (AutomationModule)
    Dewpoint.super_.call(this, id, controller);
};

inherits(Dewpoint, AutomationModule);

_module = Dewpoint;

// ----------------------------------------------------------------------------
// --- Module instance initialized
// ----------------------------------------------------------------------------

Dewpoint.prototype.init = function (config) {

    // Call superclass' init (this will process config argument and so on)
    Dewpoint.super_.prototype.init.call(this, config);

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
                icon: 'thermostat',
                title: 'Dewpoint ' + this.id
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
	this.controller.devices.on(this.config.sensor2, 'change:metrics:level', function() {
        self.OnChange();
		});
};

Dewpoint.prototype.stop = function () {
    
	this.controller.devices.off(this.config.sensor1, 'change:metrics:level', function() {
		self.OnChange();
		});
	this.controller.devices.off(this.config.sensor2, 'change:metrics:level', function() {
        self.OnChange();
		});
	if (this.vDev) {
        this.controller.devices.remove(this.vDev.id);
        this.vDev = null;
    }
    Dewpoint.super_.prototype.stop.call(this);
};

// ----------------------------------------------------------------------------
// --- Module methods
// ----------------------------------------------------------------------------

Dewpoint.prototype.OnChange = function () {
	var vDevSensor1 = this.controller.devices.get(this.config.sensor1),
    vDevSensor2 = this.controller.devices.get(this.config.sensor2),
    vDev = this.vDev;

	tempC = vDevSensor1.get('metrics:level');
	humid = vDevSensor2.get('metrics:level');
	temp  = Math.round((tempC*9/5+32)*100)/100;
	console.log("Dewpoint: Temperature -> "+ temp);	
	console.log("Dewpoint: Humidity    -> "+ humid);
	
	tem = -1.0*tempC
	es = 6.112*Math.exp(-1.0*17.67*tem/(243.5 - tem))
	ed = humid/100.0*es
	eln = Math.log(ed/6.112)
	dewpoint = -243.5*eln/(eln - 17.67 )
	dewpoint = Math.round((1.8*dewpoint+32)*100)/100
	console.log("Dewpoint: Dewpoint    -> "+ dewpoint);
	vDev.set('metrics:level', dewpoint);
}