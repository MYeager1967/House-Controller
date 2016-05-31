/*** HeatIndex Z-Way Home Automation module ***********************************

 Version: 1.0

 ------------------------------------------------------------------------------
 Author: Michael Yeager
 Description: Uses temperature and humidity data from sensors to calculate the
			  current heat index. Creates an element and dummy sensor deviceId
			  for the Home Automation interface.
			  
		***** Uses Celsius temperature input *****
		
		***** Output to display in Fahrenheit *****

******************************************************************************/

// ----------------------------------------------------------------------------
// --- Class definition, inheritance and setup
// ----------------------------------------------------------------------------

function HeatIndex (id, controller) {
    // Call superconstructor first (AutomationModule)
    HeatIndex.super_.call(this, id, controller);
};

inherits(HeatIndex, AutomationModule);

_module = HeatIndex;

// ----------------------------------------------------------------------------
// --- Module instance initialized
// ----------------------------------------------------------------------------

HeatIndex.prototype.init = function (config) {

    // Call superclass' init (this will process config argument and so on)
    HeatIndex.super_.prototype.init.call(this, config);

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
                title: 'Heat Index ' + this.id
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

HeatIndex.prototype.stop = function () {
    
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
    HeatIndex.super_.prototype.stop.call(this);
};

// ----------------------------------------------------------------------------
// --- Module methods
// ----------------------------------------------------------------------------

HeatIndex.prototype.OnChange = function () {
	var vDevSensor1 = this.controller.devices.get(this.config.sensor1),
        vDevSensor2 = this.controller.devices.get(this.config.sensor2),
        vDev = this.vDev;

    var tempC = vDevSensor1.get('metrics:level');
	var humid = vDevSensor2.get('metrics:level');
	var temp  = Math.round((tempC*9/5+32)*100)/100;
	console.log("HeatIndex: Temperature -> "+ temp);	
	console.log("HeatIndex: Humidity    -> "+ humid);
	var heatIndex = temp;
	if ((temp > 80) && (humid > 40)) {
		var c1 = -42.38
		var c2 = 2.049
		var c3 = 10.14
		var c4 = -0.2248
		var c5 = -6.838e-3
		var c6 = -5.482e-2
		var c7 = 1.228e-3
		var c8 = 8.528e-4
		var c9 =- 1.99e-6 
		var T  = temp
		var R  = humid
		var T2 = T*T
		var R2 = R*R
		var TR = T*R
	
		var heatIndex = Math.round((c1 + c2*T + c3*R + c4*T*R + c5*T2 + c6*R2 + c7*T*TR + c8*TR*R + c9*T2*R2)*100)/100
	};
	console.log("HeatIndex: Heat Index  -> "+ heatIndex);
	vDev.set('metrics:level', heatIndex);
}