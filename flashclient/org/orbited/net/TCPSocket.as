package org.orbited.net {
	import flash.display.MovieClip;
	//import flash.errors.*;
	import flash.events.*;
	import flash.utils.*;
	import flash.net.URLRequest;
	import flash.net.URLRequestMethod;
	import flash.net.URLStream;
	import flash.net.URLLoader;

	public class TCPSocket{
		public const READY_STATE_INITIALIZED:uint  = 1;
		public const READY_STATE_OPENING:uint      = 2;
		public const READY_STATE_OPEN:uint         = 3;
		public const READY_STATE_CLOSING:uint      = 4;
		public const READY_STATE_CLOSED:uint       = 5;
		public const RETRY_INTERVAL:uint          = 250;
		public const RETRY_TIMEOUT:uint           = 30000;

		private var sendQueue:Array = [];
		private var lastEventId:uint;
		private var packetCount:uint;
		private var sending:Boolean;
		private var _readyState:uint;
		private var stream:URLStream;
		private var session:String;
		private var buffer:String;
		private var pingTimeout = 15;
		private var pingInterval = 20;
		private var url:String;
		private var timeoutTimer:uint;
		
		//Callbacks
		public var onOpen:Function = function(){}
		public var onClose:Function = function(data:uint){}
		public var onRead:Function = function(data:String){}

		public function TCPSocket():void{
            _readyState = READY_STATE_INITIALIZED;
        }
		
		//Error Codes
    	public const ConnectionTimeout:uint = 101;
    	public const InvalidHandshake:uint = 102;
    	public const UserConnectionReset:uint = 103;
    	public const Unauthorized:uint = 106;
    	public const RemoteConnectionFailed:uint = 108;
    	//Statuses
    	public const ServerClosedConnection:uint = 201;
    	public const SocketControlKilled:uint = 301;
		
		//Base64 Stuff
        private var p = "=";
        private var tab = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        
        public function encode64(ba:String){
            //  summary
            //  Encode a string as a base64-encoded string
            var s=[];
            var l=ba.length;
            var rm=l%3;
            var x=l-rm;
            for (var i=0; i<x;){
            var t=ba.charCodeAt(i++)<<16|ba.charCodeAt(i++)<<8|ba.charCodeAt(i++);
            s.push(tab.charAt((t>>>18)&0x3f));
            s.push(tab.charAt((t>>>12)&0x3f));
            s.push(tab.charAt((t>>>6)&0x3f));
            s.push(tab.charAt(t&0x3f));
            }
            //  deal with trailers, based on patch from Peter Wood.
            switch(rm){
            case 2:
            t=ba.charCodeAt(i++)<<16|ba.charCodeAt(i++)<<8;
            s.push(tab.charAt((t>>>18)&0x3f));
            s.push(tab.charAt((t>>>12)&0x3f));
            s.push(tab.charAt((t>>>6)&0x3f));
            s.push(p);
            break;
            case 1:
            t=ba.charCodeAt(i++)<<16;
            s.push(tab.charAt((t>>>18)&0x3f));
            s.push(tab.charAt((t>>>12)&0x3f));
            s.push(p);
            s.push(p);
            break;
            }
            return s.join("");  //    string
        }
		public function decode64(str:String){
            //  summary
            //  Convert a base64-encoded string to an array of bytes
            var s=str.split("");
            var out=[];
            var l=s.length;
            var tl=0;
            while(s[--l]==p){ ++tl; }   //    strip off trailing padding
            for (var i=0; i<l;){
            var t=tab.indexOf(s[i++])<<18;
            if(i<=l){ t|=tab.indexOf(s[i++])<<12; }
            if(i<=l){ t|=tab.indexOf(s[i++])<<6; }
            if(i<=l){ t|=tab.indexOf(s[i++]); }
            out.push(String.fromCharCode((t>>>16)&0xff));
            out.push(String.fromCharCode((t>>>8)&0xff));
            out.push(String.fromCharCode(t&0xff));
            }
            // strip off trailing padding
            while(tl--){ out.pop(); }
            return out.join(""); //     string
        }
		
		public function encodePackets(queue:Array):Array{
			var output:Array = queue.concat();
			output[output.length-1] = '0'+ output[output.length-1].length + ',' + output[output.length-1];
			for (var i=2; i < output.length+1; ++i){
				output[output.length-i] = '1'+ output[output.length-i].length + ',' + output[output.length-i];
			}
			return [output.join('')];
		}
		var doClose = function(code:uint) {
			if (_readyState == READY_STATE_CLOSED){
				trace("Already Closed...");
			}
			else{
				trace('doClose', code);
            	_readyState = READY_STATE_CLOSED;
				onClose(code);
			}
        }
		public function doPing(): void {
			sendQueue.push(String(++packetCount), "ping");
			if (!sending) {
				doSend();
			}
		}
		public function doOpen(): void {
			send(url+"\n");
			onOpen();
		}
		public function doSend(retries:uint=0): void {
			if (retries*RETRY_INTERVAL >= RETRY_TIMEOUT) {
                doClose(ConnectionTimeout);
				trace("Retry Timed Out");
                sending = false;
				return;
			}
			if (sendQueue.length == 0) {
				trace('sendQueue exhausted');
                sending = false;
                return;
            }
			sending = true;
            var numSent = sendQueue.length;
			
			var loader:URLLoader = new URLLoader();
			var request:URLRequest = new URLRequest("http://localhost:8000/tcp/" + session + "?ack=" + lastEventId);
			request.method = URLRequestMethod.POST;
			request.data = encodePackets(sendQueue);
			request.contentType = "text/plain";
			trace('doSend:',request.data);
			loader.addEventListener(Event.COMPLETE, function (event:Event):void{
				trace(loader.data)
				switch (loader.data){
					case "OK":
						resetTimeout();
                        sendQueue.splice(0, numSent);
                        return doSend();
						break;
					default:
						trace("Retrying");
						setTimeout(doSend, RETRY_INTERVAL, ++retries);
						break;
				}
			});
			try {
                loader.load(request);
            } catch (error:Error) {
                trace("doSend ERROR");	
            }
		}
		public function receivedFrame(frame:Array): void {
            lastEventId = frame[0];
            var type:String = frame[1];
			trace("RECEIVED FRAME:", frame);
            switch(type) {
				case "data":
					//trace('base64 decoding ' + frame.data.length + ' bytes of data');
                    var data:String = decode64(frame[2]);
					trace("decode64:", data);
                    onRead(data);
                    break;
                case "opt":
                    if (type == "pingTimeout") {
                        pingTimeout = parseInt(frame[2]);
                    }
                    if (type == "pingInterval") {
                        pingInterval = parseInt(frame[2]);
                    }
                	break;
                case "open":
                    if (_readyState == READY_STATE_OPENING) {
						_readyState = READY_STATE_OPEN;
                        doOpen();
                    }
					else {
						trace("Invalid readyState", _readyState);
					}
                	break;
                case "close":
                    doClose(ServerClosedConnection);
                    break;
                case "ping":
					if (_readyState == READY_STATE_OPEN) {
                    	doPing();
					}
                    break;
				}
			resetTimeout();
		}
		private var commaPos:int = -1;
		private var argEnd:int = -1;
		private var frame:Array = []
		public function processBuffer():void {
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
		public function streamProgress(event:ProgressEvent): void {
            buffer += stream.readUTFBytes(stream.bytesAvailable)
            processBuffer()
        }
        public function streamComplete(event:Event): void {
            trace('stream Complete', event)
        }
		public function startStream():void {
            stream = new URLStream();
            stream.addEventListener(ProgressEvent.PROGRESS, streamProgress);
            stream.addEventListener(Event.COMPLETE, streamComplete);        
            buffer = "";
			stream.load(new URLRequest("http://localhost:8000/tcp/" + session + "/xhrstream"));
        }
		public function open(hostname:String, port:int, isBinary:Boolean=false):void {
			if (_readyState == READY_STATE_INITIALIZED){
				_readyState = READY_STATE_OPENING;
				var loader:URLLoader = new URLLoader();
    			// TODO: catch error codes
    			loader.addEventListener(Event.COMPLETE, function (event:Event):void{
					session = loader.data;
					startStream();
					trace('Receive Session key:', session);
					});
				trace('Request tcp session key');
				url = hostname+":"+port;
				loader.load(new URLRequest("http://localhost:8000/tcp"));
			}
		}
		public function send(data:String) {
			trace('send', data);
            if (_readyState != READY_STATE_OPEN) {
                trace("Invalid readyState", _readyState);
            }
            data = encode64(data);
            sendQueue.push(String(++packetCount), "data", data);
			trace('sending == ', sending);
            if (!sending) {
				trace('starting send');
                doSend();
            }
        }
		public function hardClose(){
			stream.close();
			var loader:URLLoader = new URLLoader();
			var request:URLRequest = new URLRequest("http://localhost:8000/tcp/" + session);
			request.method = URLRequestMethod.POST;
			request.data = encodePackets([String(++packetCount), "close"]);
			request.contentType = "text/plain";
			trace("hardClose:", request.data);
			loader.addEventListener(Event.COMPLETE, function (event:Event):void{
				trace(loader.data)
			});
			loader.load(request);
        }
		public function close(){
            switch(_readyState) {
                case READY_STATE_CLOSING:
                case READY_STATE_CLOSED:
                    return;
                case READY_STATE_INITIALIZED:
                    _readyState = READY_STATE_CLOSED;
					//onclose()
                    return;
                default:
                    break;
            }
            _readyState = READY_STATE_CLOSING;
            sendQueue.push(String(++packetCount), "close");
            if (!sending) {
                doSend();
            }
        }
		public function reset() {
			trace('reset');
			switch(_readyState){
				case READY_STATE_INITIALIZED:
				case READY_STATE_OPENING:
					doClose(UserConnectionReset);
					break;
				case READY_STATE_OPEN:
				case READY_STATE_CLOSING:
					sendQueue = [];
                    sending = false;
					doClose(UserConnectionReset);
					hardClose();
                    break;
			}
        }
		public function resetTimeout() {
			trace('reset Timeout', pingInterval+pingTimeout+10);
            clearTimeout(timeoutTimer);
            timeoutTimer = setTimeout(timedOut, (pingInterval + pingTimeout + 10)*1000);
        }
        public function timedOut() {
			trace('timed out!');
            doClose(ConnectionTimeout);
        }
	}
}
