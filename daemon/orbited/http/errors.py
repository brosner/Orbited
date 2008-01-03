from orbited.util import formatBlock

unknown = formatBlock("""
    HTTP/1.0 500 Error
    Content-Type: text/html
      
    An Unknown Error occurred.
    """)
    
protocol = formatBlock("""
    HTTP/1.0 500 Protocol Error
    Content-Type: text/html
    
    This server did not understand the request protocol.<br>
    Error: <b>%s</b>
    """)


orbited = formatBlock("""
    HTTP/1.0 500 Orbited Error
    Content-Type: text/html
    
    Orbited Error:<b>%s</b>
    """)
