package org.orbited.net {
    import flash.errors.*;
    import flash.events.*;
    import flash.net.URLRequest;
    import flash.net.URLStream;
    import flash.net.URLLoader;
    import org.orbited.logging.*;

    public class TCPSocket {
        static private var logger:OrbitedLogger = getLogger('orbited.net.TCPSocket');
        public const READY_STATE_INITIALIZED:int  = 1;
        public const READY_STATE_OPENING:int      = 2;
        public const READY_STATE_OPEN:int         = 3;
        public const READY_STATE_CLOSING:int      = 4;
        public const READY_STATE_CLOSED:int       = 5;
        private var _readyState:int;
        private var stream:URLStream;
        private var session:String;
        private var buffer:String;
        private var pingTimeout = 30;
        private var pingInterval = 40;

        public function get readyState():int {
            return _readyState;
        }
        
        public function TCPSocket() {
            _readyState = READY_STATE_INITIALIZED;
        }
        
        public function onread(data:String):void {
            logger.debug('onread: ' + data)

        }
        
        public function onopen():void {
            logger.debug('onopen was called');
        }

        public function onclose(code:int):void {
            
        }


        public function open(hostname:String, port:int, isBinary:Boolean=false):void {
            if (_readyState != READY_STATE_INITIALIZED) {
                throw new Error("Invalid readyState");
            }
            var loader:URLLoader = new URLLoader();            
            // TODO: catch error codes
            loader.addEventListener(Event.COMPLETE, function(event:Event):void {
                logger.debug('Receive Session key:', loader.data);
                session = loader.data;
                startStream();
            });

            logger.debug('Request tcp session key');
            loader.load(new URLRequest("http://127.0.0.1:8000/tcp"));
        }
        
        public function send(data:String) {
            if (_readyState != READY_STATE_OPEN) {
                throw new Error("Invalid readyState");
            }
//            sendFrame(

        }

        public function close():void {
            logger.debug('close');
        }

        public function reset():void {
            logger.debug("reset");
        }
        private function sendFrame(frame:Array):void {
            
        }

        private function encodePackets(queue) {
            //TODO: optimize this.
            var output = []
            for (var i =0; i < queue.length; ++i) {
                var frame = queue[i];
                for (var j =0; j < frame.length; ++j) {
                    var arg = frame[j]
                    if (arg == null) {
                        arg = ""
                    }
                    if (j == frame.length-1) {
                        output.push('0')
                    }
                    else {
                        output.push('1')
                    }
                    output.push(arg.toString().length)
                    output.push(',')
                    output.push(arg.toString())
                }
            }
            return output.join("")
        }


        private function doPing():void {

        }
        private function doClose():void {
            
        }

        private function doOpen(): void {
            this.onopen()
        }

        private function receivedFrame(frame:Array): void {
            var id:int = frame[0]
            var type:String = frame[1]
            switch(type) {
                case "opt":
                    if (type == "pingTimeout") {
                        pingTimeout = parseInt(frame[2])
                    }
                    if (type == "pingInterval") {
                        pingInterval = parseInt(frame[2])
                    }
                break;
                case "open":
                    if (_readyState == READY_STATE_INITIALIZED) {
                        doOpen();
                    }
                break;
                case "close":
                    doClose();
                    break;
                case "ping":
                    doPing();
                    break;
            }
            logger.debug("RECEIVED FRAME:", frame);

        }

        private var commaPos:int = -1;
        private var argEnd:int = -1;
        private var frame:Array = []

        private function processBuffer():void {

            // ignore leading whitespace, such as at the start of an xhr stream
            while (buffer.charAt(0) == ' ' || buffer.charAt(0) == 'x') {
                buffer = buffer.slice(1)
            }
            var k:int = 0
            while (true) {
                k += 1
                if (k > 2000) {
                    throw new Error("Borked XHRStream transport");
                    return
                }
                if (commaPos == -1) {
                    commaPos = buffer.indexOf(',')
                }
                if (commaPos == -1) {
                    return
                }
                if (argEnd == -1) {
                    var argSize:int = parseInt(buffer.slice(1,commaPos))
                    argEnd = commaPos + 1 + argSize
                }
                if (buffer.length < argEnd) {
                    return
                }
                var data:String = buffer.slice(commaPos+1, argEnd)
                frame.push(data)
                var isLast:Boolean = (buffer.charAt(0) == '0')
                buffer = buffer.slice(argEnd)
                argEnd = -1;
                commaPos = -1
                if (isLast) {
                    var frameCopy:Array = frame
                    frame = []
                    receivedFrame(frameCopy)                
                }
            } 

        }

        private function startStream():void {
            stream = new URLStream();
            stream.addEventListener(ProgressEvent.PROGRESS, streamProgress);
            stream.addEventListener(Event.COMPLETE, streamComplete);        
            buffer = "";
            stream.load(new URLRequest("http://localhost:8000/tcp/" + session + "/xhrstream"));
        }
        private function streamProgress(event:ProgressEvent): void {
            buffer += stream.readUTFBytes(stream.bytesAvailable)
            processBuffer()
        }
        private function streamComplete(event:Event): void {
            logger.debug('stream Complete', event)
        }
    }

}