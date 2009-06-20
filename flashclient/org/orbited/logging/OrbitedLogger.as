package org.orbited.logging {

    public class OrbitedLogger {
        public var name:String;
        public function OrbitedLogger(_name:String) {
            name = _name;
        }
        public function debug(... arguments):void {        
            trace("DEBUG " + name + " " + (new Date()).toString() + ": " + arguments.join(" "))
        }
        public function log(... arguments):void {        
            trace("LOG " + name + " " + (new Date()).toString() + ": " + arguments.join(" "))
        }
        public function warn(... arguments):void {        
            trace("WARN " + name + " " + (new Date()).toString() + ": " + arguments.join(" "))
        }
    }
}
