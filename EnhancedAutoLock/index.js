/*** EnhancedAutoLock Z-Way Home Automation module ****************************************

 Version: 1.0

 -----------------------------------------------------------------------------
 Modified By: Michael Yeager based on code by Yurkin Vitaliy <aivs@z-wave.me>
 Description: Allows automatic (delayed) locking of a door after the door is closed in
			  conjunction with a binary device to turn it on and off.

*******************************************************************************************/

// ----------------------------------------------------------------------------
// --- Class definition, inheritance and setup
// ----------------------------------------------------------------------------
function EnhancedAutoLock (id, controller) {
    // Call superconstructor first (AutomationModule)
    EnhancedAutoLock.super_.call(this, id, controller);

    // Create instance variables
    this.timer = null;
};

inherits(EnhancedAutoLock, AutomationModule);
_module = EnhancedAutoLock;

// ----------------------------------------------------------------------------
// --- Module instance initialized
// ----------------------------------------------------------------------------
EnhancedAutoLock.prototype.init = function (config) {
    // Call superclass' init (this will process config argument and so on)
    EnhancedAutoLock.super_.prototype.init.call(this, config);

    var self = this;
    
    // init value at start
    var lastSensorStatus = "on";
	
	// handler1 - Catches status change on BinarySwitch1
    this.handler1 = function (vDev) {
		var nowSwitch1Status = vDev.get("metrics:level");
		var nowSwitch2Status = controller.devices.get(self.config.BinarySwitch2).get('metrics:level');
		var nowSensorStatus  = controller.devices.get(self.config.BinarySensor).get('metrics:level');
		var nowLockStatus 	 = controller.devices.get(self.config.DoorLock).get('metrics:level');
		console.log("------------------- Enhanced AutoLock: Running");

		if (nowSwitch1Status === "on") {
			if (nowSwitch2Status === "off") {
				if (nowSensorStatus === "off") {
					if (nowLockStatus === "open") {
						// Close lock 
						self.controller.devices.get(self.config.DoorLock).performCommand("close");
						console.log("------------------- Enhanced AutoLock: Close lock");
					};
				
				};
			};
		};
		// And clearing out this.timer variable
		self.timer = null;
		console.log("------------------- Enhanced AutoLock: Clear timer");
	};
	
	// handler2 - Catches status change on BinarySwitch1
    this.handler2 = function (vDev) {
		var nowSwitch2Status = vDev.get("metrics:level");
		var nowSwitch1Status = controller.devices.get(self.config.BinarySwitch1).get('metrics:level');
		var nowSensorStatus = controller.devices.get(self.config.BinarySensor).get('metrics:level');
		var nowLockStatus 	= controller.devices.get(self.config.DoorLock).get('metrics:level');
		console.log("------------------- Enhanced AutoLock: Running");
		//console.log("------------------- Enhanced AutoLock: ", self.config.BinarySwitch1, "=", nowSwitch1Status);
		//console.log("------------------- Enhanced AutoLock: ", self.config.BinarySwitch2, "=", nowSwitch2Status);
		//console.log("------------------- Enhanced AutoLock: ", self.config.BinarySensor, "=", nowSensorStatus);
		//console.log("------------------- Enhanced AutoLock: ", self.config.DoorLock, "=", nowLockStatus);
		
		if (nowSwitch1Status === "on") {
			if (nowSwitch2Status === "off") {
				if (nowSensorStatus === "off") {
					if (nowLockStatus === "open") {
						// Close lock 
						self.controller.devices.get(self.config.DoorLock).performCommand("close");
						console.log("------------------- Enhanced AutoLock: Close lock");
					};
				};
			};
		};
		// And clearing out this.timer variable
		self.timer = null;
		console.log("------------------- Enhanced AutoLock: Clear timer");
	};

	// handler3 - Catches status change on BinarySensor
	this.handler3 = function (vDev) {
		var nowSensorStatus  = vDev.get("metrics:level");
		var nowSwitch1Status = controller.devices.get(self.config.BinarySwitch1).get('metrics:level');
		var nowSwitch2Status = controller.devices.get(self.config.BinarySwitch2).get('metrics:level');
		var nowLockStatus 	 = controller.devices.get(self.config.DoorLock).get('metrics:level');

		// Check if feature switch is set
		if (nowSwitch1Status === "on") {
			if (nowSwitch2Status === "off") {
				// Check if sensor is triggered
				if (lastSensorStatus !== nowSensorStatus) {
					console.log("------------------- Enhanced AutoLock: Running");

					// Clear delay if door opened
					if (nowSensorStatus === "on") {
						console.log("------------------- Enhanced AutoLock: Clear delay - Door opened");
						clearTimeout(self.timer);
					};
					// Close lock if sensor false
					if (nowSensorStatus === "off") {
						// Start Timer
						console.log("Start delay: ", self.config.delay, "seconds");
						self.timer = setTimeout(function () {
							if (nowLockStatus === "open") {
								// Close lock 
								self.controller.devices.get(self.config.DoorLock).performCommand("close");
								console.log("------------------- Enhanced AutoLock: Close lock");
							};
							// And clearing out this.timer variable
							self.timer = null;
							console.log("------------------- Enhanced AutoLock: Clear timer");
						}, self.config.delay*1000);
					}
					lastSensorStatus = nowSensorStatus;
				};
			};
		};
    };

    // Setup metric update event listener
	this.controller.devices.on(this.config.BinarySwitch1, 'change:metrics:level', this.handler1);
	this.controller.devices.on(this.config.BinarySwitch2, 'change:metrics:level', this.handler2);
	this.controller.devices.on(this.config.BinarySensor, 'change:metrics:level', this.handler3);
};

EnhancedAutoLock.prototype.stop = function () {
    EnhancedAutoLock.super_.prototype.stop.call(this);

    if (this.timer)
		console.log("------------------- Enhanced AutoLock: Stop");
        clearTimeout(this.timer);

    this.controller.devices.off(this.config.BinarySwitch1, 'change:metrics:level', this.handler);
	this.controller.devices.off(this.config.BinarySwitch2, 'change:metrics:level', this.handler);
	this.controller.devices.off(this.config.BinarySensor, 'change:metrics:level', this.handler);
};
