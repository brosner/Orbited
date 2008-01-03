require 'ruby-orbited'

client = SimpleOrbit::Client.new('127.0.0.1', 9000)
client.connect()

puts client.event(['user, 0, /demo'], 'Hello World!<br>', false).to_s
