from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
_magic_number = 2
_modified_time = 1187751120.0068679
_template_filename='/home/desmaj/python/pylonschat/pylonschat/pylonschat/templates/chat/index.html'
_template_uri='chat/index.html'
_template_cache=cache.Cache(__name__, _modified_time)
_source_encoding=None
_exports = []


def render_body(context,**pageargs):
    context.caller_stack.push_frame()
    try:
        __M_locals = dict(pageargs=pageargs)
        h = context.get('h', UNDEFINED)
        # SOURCE LINE 1
        context.write(u'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"\n  "http://www.w3.org/TR/html4/strict.dtd">\n<html>\n  <head>\n    <meta http-equiv="Content-type" content="text/html; charset=utf-8">\n    <title>PylonsChat</title>\n    ')
        # SOURCE LINE 7
        context.write(unicode(h.stylesheet_link_tag('chat.css')))
        context.write(u'\n    ')
        # SOURCE LINE 8
        context.write(unicode(h.javascript_include_tag('chat.js')))
        context.write(u'\n  </head>\n  <body>\n    <input type="text" id="nickname">\n    <input type="button" value="nickname" name="nickname" onclick="connect();">\n    <div id="box"></div>\n    \n    <input type="text" id="chat">\n    <input type="submit" value="chat" onClick="send_msg();">\n    \n    <iframe id="events"></iframe>\n  </body>\n</html>')
        return ''
    finally:
        context.caller_stack.pop_frame()


