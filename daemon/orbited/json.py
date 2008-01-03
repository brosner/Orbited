class JsonHolder(object):
    pass
json = JsonHolder()
try:
    import cjson
    json.encode = cjson.encode
    json.decode = cjson.decode
except ImportError:
    import simplejson
    json.encode = simplejson.dumps
    json.decode = simplejson.loads
    