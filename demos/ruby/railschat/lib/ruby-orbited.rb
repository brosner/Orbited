require 'socket'
include Socket::Constants
require 'json'

BUFFER_SIZE = 4096
LINE_END = "\r\n"

module SimpleOrbit
end

class SimpleOrbit::Client
  @@version = 'Orbit 1.0'
  def initialize(addr="127.0.0.1", port=9000)
    @addr = addr
    @port = port
    @socket = nil
    @id = 0
    @connected = false
  end
  def connect()
    @connected = true
    if @socket
      # already connected
      return
    end
    @socket = TCPSocket.new(@addr, @port)
  end
  def disconnect()
    if @connected
      @connected = false
      @socket.close()
      @socket = nil
    end
  end
  def reconnect()
    disconnect()
    connect()
  end
  def sendline(line='')
    @socket.write(line.to_s + LINE_END)
    # puts line.to_s
  end
  def event(recipients, body, json=true, try_again=true)
    if not @connected
      connect()
    end
    begin
      if json
        body = JSON.generate(body)
      end
      if not @socket
        raise ## **Connection-lost**
      end
      begin
        @id = @id + 1
        sendline(@@version.to_s)
        sendline('Event')
        sendline('id: ' + @id.to_s)
        for recipient in recipients
          sendline('recipient: ' + recipient.to_s)
        end
        sendline('length: ' + body.length.to_s)
        sendline()
        @socket.write(body)
        # puts body.to_s
        return read_response()
      rescue
        disconnect()
        raise
      end
    rescue
      if try_again
          reconnect()
          event(recipients, body, json, false)
      else
          raise
      end
    end
  end
  def read_response()
#    return @socket.recvfrom(BUFFER_SIZE)
  end
end