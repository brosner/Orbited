package org.orbited.logging {
    
    public function getLogger(name:String):OrbitedLogger {
        if (loggers[name]) {
            return loggers[name]
        }
        loggers[name] = new OrbitedLogger(name)
        return loggers[name]
    }
}