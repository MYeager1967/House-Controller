/*** LightScene Z-Way HA module *******************************************

Version: 1.0.2
(c) Z-Wave.Me, 2014
-----------------------------------------------------------------------------
Author: Poltorak Serguei <ps@z-wave.me>
Description:
    Implements light scene based on virtual devices of type dimmer, switch or anothe scene
******************************************************************************/

// ----------------------------------------------------------------------------
// --- Class definition, inheritance and setup
// ----------------------------------------------------------------------------

function LightScene (id, controller) {
    // Call superconstructor first (AutomationModule)
    LightScene.super_.call(this, id, controller);
}

inherits(LightScene, AutomationModule);

_module = LightScene;

// ----------------------------------------------------------------------------
// --- Module instance initialized
// ----------------------------------------------------------------------------

LightScene.prototype.init = function (config) {
    LightScene.super_.prototype.init.call(this, config);

    var self = this;
//	self.imagePath  = '/ZAutomation/api/v1/load/modulemedia/'+self.constructor.name;

    this.vDev = this.controller.devices.create({
        deviceId: "LightScene_" + this.id,
        defaults: {
            deviceType: "toggleButton",
            metrics: {
                level: 'on', // it is always on, but useful to allow bind
                icon: '/ZAutomation/api/v1/load/modulemedia/LightScene/icon.png',
                title: 'Light Scene ' + this.id
            }
        },
        overlay: {},
        handler: function () {
            self.config.switches.forEach(function(devState) {
                var vDev = self.controller.devices.get(devState.device);
                if (vDev) {
                    if (!devState.sendAction || (devState.sendAction && vDev.get("metrics:level") != devState.status)) {
                        vDev.performCommand(devState.status);
                    }
                }
            });
            self.config.thermostats.forEach(function(devState) {
                var vDev = self.controller.devices.get(devState.device);
                if (vDev) {
                    if (!devState.sendAction || (devState.sendAction && vDev.get("metrics:level") != devState.status)) {
                        vDev.performCommand("exact", { level: devState.status });
                    }
                }
            });
            self.config.dimmers.forEach(function(devState) {
                var vDev = self.controller.devices.get(devState.device);
                if (vDev) {
                    if (!devState.sendAction || (devState.sendAction && vDev.get("metrics:level") != devState.status)) {
                        vDev.performCommand("exact", { level: devState.status });
                    }
                }
            });
            self.config.locks.forEach(function(devState) {
                var vDev = self.controller.devices.get(devState.device);
                if (vDev) {
                    if (!devState.sendAction || (devState.sendAction && vDev.get("metrics:level") != devState.status)) {
                        vDev.performCommand(devState.status);
                    }
                }
            });
            self.config.scenes.forEach(function(scene) {
                var vDev = self.controller.devices.get(scene);
                if (vDev) {
                    vDev.performCommand("on");
                }
            });
			//self.vDev.set('metrics:icon','/ZAutomation/api/v1/load/modulemedia/LightScene/icon.png');
            self.vDev.set("metrics:level", "on"); // update on ourself to allow catch this event
        },
        moduleId: this.id
    });
};

LightScene.prototype.stop = function () {
    if (this.vDev) {
        this.controller.devices.remove(this.vDev.id);
        this.vDev = null;
    }

    LightScene.super_.prototype.stop.call(this);
};

// ----------------------------------------------------------------------------
// --- Module methods
// ----------------------------------------------------------------------------


//this.set('metrics:icon',self.imagePath+'/'+type+'_'+command+'.png');