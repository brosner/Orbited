+----------+
| CONTENTS |
+----------+

README.txt              this file
OrbitedClass.php        the orbited PHP5 client class
chat.php                client for handling chat actions
users.txt               blank text file for reading and writing users
orbit.html              front end for chat room
chat.js                 javascript used by orbit.html
chat.css                styling for orbit.html
orbit.cfg               orbited configuration


+-------+
| USAGE |
+-------+

1. Unpack archive to the root of your web directory.
2. Make sure users.txt is writable.
3. Start orbited with orbit.cfg configuration (run 'orbited' in the same directory as orbit.cfg).
4. Open 2 windows. The first should point to: http://localhost:8000/orbit.html and the second should point to http://127.0.0.1:8000/orbit.html
5. Enter a nickname and click 'Join' to join the room. The 2 windows should be able to chat with each other. 
    