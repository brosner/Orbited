"""
Select a JSON library from any of several known libraries.
"""

try:
    import cjson
    encode = cjson.encode
    decode = cjson.decode
except ImportError:
    try:
        import simplejson
        encode = simplejson.dumps
        decode = simplejson.loads
    except ImportError:
        try:
            import demjson
            encode = demjson.encode
            decode = demjson.decode
        except ImportError:
            raise ImportError, "could not load one of: cjson, simplejson, demjson"
        