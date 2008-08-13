# Created by Noah Kantrowitz on 2007-07-16.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from trac.core import *

from themeengine.api import ThemeBase

class Orbited(ThemeBase):
    """A theme for Trac based on http://www.oswd.org/design/information/id/3465."""
    template = True
    htdocs = True
    css = True
#    screenshot = True
#    template = htdocs = css = screenshot = True
    
