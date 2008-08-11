import os
from jsmin import jsmin

f = open(os.path.join('static', 'Orbited.js'), 'r')
data = "\n".join([ l for l in f.readlines() if not l.startswith(';;;') ])
f.close()
f = open(os.path.join('js', 'Orbited.js'), 'w')
f.write(jsmin(data))
f.close()

