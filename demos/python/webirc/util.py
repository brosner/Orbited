def expose(func):
    def func2(self, request):
        print "inside of func2"
        try:
            func(request)
        except Exception, e:
            print "error!"
            print dir(func)
            print dir(func2)
            func2.im_self.error(e, request, func)
    func2.exposed = True
    return func2
