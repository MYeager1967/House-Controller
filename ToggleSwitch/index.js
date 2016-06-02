/* Version 1.0 2016-06-02
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 *
 */

// ----------------------------------------------------------------------------
// --- Class definition, inheritance and setup
// ----------------------------------------------------------------------------

function ToggleSwitch (id, controller) {
    // Call superconstructor first (AutomationModule)
    ToggleSwitch.super_.call(this, id, controller);
}

inherits(ToggleSwitch, AutomationModule);

_module = ToggleSwitch;

// ----------------------------------------------------------------------------
// --- Module instance initialized
// ----------------------------------------------------------------------------

ToggleSwitch.prototype.init = function (config) {
    ToggleSwitch.super_.prototype.init.call(this, config);

    // define global handler for HTTP requests
    Toggle = function(url, request) {
        var params = url.split("/");
        params.shift(); // shift empty string before first /
        var deviceID = params.shift();
		vDev = this.controller.devices.get(deviceID)
		vDevType = vDev.get('deviceType')
        switch(vDevType) {
            
			case "switchBinary":
				vDev.performCommand(vDev.get("metrics:level") === "on" ? "off":"on");
                return "OK";
				
			case "switchMultilevel":
				vDev.performCommand(vDev.get("metrics:level") === 0 ? "on":"off");
                return "OK";
				
 //           case "SetMetrics":
               // All three parameters (N,I,S) are compulsory
 //              var S = params.shift();
 //              attrib = "metrics:" + I;
 //              this.controller.devices.get(N).set(attrib,S);
 //              return S;

// Your "case" statements may go after this line, but before keyword default:  !
				
            default:
               return "Error: " + deviceID  + " is not supported by ToggleSwitch";
        }
    };
    ws.allowExternalAccess("Toggle", this.controller.auth.ROLE.USER); // login required
};

ToggleSwitch.prototype.stop = function () {
    ToggleSwitch.super_.prototype.stop.call(this);
	
	ws.revokeExternalAccess("Toggle");
    Toggle = null;
};

// ----------------------------------------------------------------------------
// --- Module methods
// ----------------------------------------------------------------------------


