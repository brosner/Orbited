<?php
if (!@include 'Net/Socket.php') die("Net_Socket not found - you need to install the Net_Socket package using:\n\tpear install Net_Socket\n");

class Orbited_User_Key {
    private $location;
    private $username;
    private $session_key;

    function __construct($location, $username, $session_key) {
        $this->location    = $location;
        $this->username    = $username;
        $this->session_key = $session_key;
    }
    
    function __tostring() {
        return $this->location . ', ' . $this->username . ', ' . $this->session_key;
    }
}

class Orbited_Client {
    const VERSION = 'Orbit 1.0';
    private $addr;
    private $port;
    private $socket;
    private $id;
    private $connected;

    function __construct($addr = 'localhost', $port = 9000) {
        $this->addr      = $addr;
        $this->port      = $port;
        $this->socket    = null;
        $this->id        = 0;
        $this->connected = false;
    }

    function connect() {
        $this->connected = true;
        if ($this->socket) {
            return;
        }
        $this->socket = new Net_Socket;
        $this->socket->connect($this->addr, $this->port);
        $this->socket->setBlocking(true);
    }

    function disconnect() {
        $this->connected = false;
        $this->socket->disconnect();
        $this->socket = null;
    }

    function reconnect() {
        $this->disconnect();
        $this->connect();
    }

    function sendLine($line = '') {
        $this->socket->writeLine($line);
    }

    function event($recipients, $body, $retry = true) {
        if (!$this->connected) {
            $this->connect();
        }
        try {
            if (!is_array($recipients)) {
                $recipients = array($recipients);
            }
            if (!$this->socket) {
                throw new Exception('Connection Lost');
            }
            try {
                $this->id++;
                $this->sendLine(self::VERSION);
                $this->sendLine('Event');
                $this->sendLine('id: ' . $this->id);
                foreach ($recipients as $recipient) {
                    if (is_object($recipient)) {
                        $recipient = $recipient->__tostring();
                    }
                    $this->sendLine("recipient: $recipient");
                }
                $this->sendLine('length: ' . strlen($body));
                $this->sendLine();
                $this->socket->write($body);
                return $this->read_response();
            } catch (Exception $e) {
                $this->disconnect();
                throw new Exception('Connection Lost');
            }
        } catch (Exception $e) {
            if ($retry) {
                $this->reconnect();
                $this->event($recipients, $body, false);
            } else {
                throw new Exception('Send Failed');
            }
        }
    }

    // This method is copied from Net_Socket::readLine() since
    // Net_Socket doesn't offer a method to read up to a specified string!?
    function read_response() {
        $line = '';
        $timeout = time() + $this->socket->timeout;
        while (!feof($this->socket->fp) && (!$this->socket->timeout || time() < $timeout)) {
            $line .= @fgets($this->socket->fp, $this->socket->lineLength);
            if (substr($line, -4) == "\r\n\r\n") {
                return rtrim($line, "\r\n");
            }
        }
        return $line;
    }
}

$client = new Orbited_Client;
$user_key = new Orbited_User_Key("user", 0, "/demo");
$client->event( $user_key, "Hello from PHP!<br>", false);
?>