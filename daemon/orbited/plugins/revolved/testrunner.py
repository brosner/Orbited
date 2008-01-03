import event
from scratch2 import *
from errors import AuthError

def is_valid_session(session_id, conn_type):
    if conn_type == 'lurk':
        return len(session_id) == 6
    return len(session_id) == 8

class TestRequest(object):
    def __init__(self, **kwargs): self.__dict__.update(kwargs)

class TestResponse(object):
    def __init__(self): self.headers = {}
    def __getitem__(self, key): return self.headers[key]
    def __setitem__(self, key, val): self.headers[key] = val

class Test(object):
    def __repr__(self):
        return str(self)

    def __init__(self, runner):
        self.authenticator = Authenticator(self)
        self.sessions = {}
        self.runner = runner

    def complete(self):
        self.runner.complete(self)

class Test1(Test):
    def __str__(self):
        return "<Test1: lurker login>"

    def run(self):
        request = TestRequest(
            form = { },
            cookies = { },
        )
        response = TestResponse()
        self.authenticator.connect(request, response)

    def connect_response(self, request, response, value=None, error=None):
        assert value is not None, "Unexpected error: %s" % (error,)
        assert len(value) == 4, "bad return value %s" % (error,)
        assert len(value[0]) == 6, "Not a proper lurker session: %s" %(value[0],)
        assert value[1] == None, \
               "Wrong username: %s, expected None" % value[1]
        assert value[2] == "lurk", \
               "Unexpected conn_type: %s. expected: 'lurk'" % (value[2],)
        assert value[3] == None, \
               "Unexpected resource: %s. expected: None" % (value[3],)
        self.complete()

class Test2(Test):
    def __str__(self):
        return "<Test2: anonymous login>"

    def run(self):
        self.sessions = { '123456': (None, 'lurk', None) }
        request = TestRequest(
            form = {
                'session': '123456',
                'userid': 'test_guy',
                'resource': 'test_resource',
            },
            cookies = {
            }
        )
        response = TestResponse()
        self.authenticator.authenticate(request, response)

    def authenticate_response(self, request, response, value=None, error=None):
        assert value is not None, "Unexpected error: %s" % (error,)
        assert len(value) == 4, "bad return value %s" % (value,)
        assert len(value[0]) == 8, "Not a proper pez session: %s" %(value[0],)
        assert value[1] == 'test_guy', \
               "Wrong username: %s, expected 'test_guy'" % value[1]
        assert value[2] == "anon", \
               "Unexpected conn_type: %s. expected: 'anon'" % (value[2],)
        assert value[3] == "test_resource", \
               "Unexpected resource: %s. expected: 'test_resource'" % (value[3],)
        assert 'Set-Cookie' in response.headers, "Missing Set-Cookie header"
        assert response.headers['Set-Cookie'] == "_chatne_sess_id=%s; path=/;" % value[0]
        self.complete()

class Test3(Test):
    def __str__(self):
        return "<Test3: authenticated login - wrong pass>"

    def run(self):
        self.sessions = { '123456': (None, 'lurk', None) }
        request = TestRequest(
            form = {
                'session': '123456',
                'userid': 'anand',
                'token': 'wrong',
                'resource': 'test_resource',
            },
            cookies = {
            }
        )
        response = TestResponse()
        self.authenticator.authenticate(request, response)
    def authenticate_response(self, request, response, value=None, error=None):
        assert value is None, "Unexpected value (None expected): %s" % (value,)
        assert error is not None, "Unexpected value for error: None"
        assert len(error) == 2, "Unexpected value for error: %s" % (error,)
        exc, msg = error
        assert exc is AuthError, \
               "Unexpected exception (expected AuthError): %s" % (exc,)
        assert msg == "Invalid password", "Unepxected error message: %s" % (msg,)
        self.complete()

class Test4(Test):
    def __str__(self):
        return "<Test4: authenticated login - correct pass>"

    def run(self):
        self.sessions = { '432165': (None, 'lurk', None) }
        request = TestRequest(
            form = {
                'session': '432165',
                'userid': 'jacob',
                'token': 'yohoho',
                'resource': 'test_resource',
            },
            cookies = {
            }
        )
        response = TestResponse()
        self.authenticator.authenticate(request, response)

    def authenticate_response(self, request, response, value=None, error=None):
        assert value is not None, "Unexpected error: %s" % (error,)
        assert len(value) == 4, "bad return value %s" % (value,)
        assert len(value[0]) == 8, "Not a proper pez session: %s" %(value[0],)
        assert value[1] == 'jacob', \
               "Wrong username: %s, expected 'jacob'" % value[1]
        assert value[2] == "auth", \
               "Unexpected conn_type: %s. expected: 'auth'" % (value[2],)
        assert value[3] == "test_resource", \
               "Unexpected resource: %s. expected: 'test_resource'" % (value[3],)
        assert 'Set-Cookie' in response.headers, "Missing Set-Cookie header"
        assert response.headers['Set-Cookie'] == "_chatne_sess_id=%s; path=/;" % value[0]
        self.runner._test4_session = value[0]
        self.complete()

class Test5(Test):
    def __str__(self):
        return "<Test5: connect - authenticated cookie>"

    def run(self):
        request = TestRequest(
            form = {
            },
            cookies = {
                '_chatne_sess_id': self.runner._test4_session
            }
        )
        del self.runner._test4_session
        response = TestResponse()
        self.authenticator.connect(request, response)

    def connect_response(self, request, response, value=None, error=None):
        assert value is not None, "Unexpected error: %s" % (error,)
        assert len(value) == 4, "bad return value %s" % (value,)
        assert len(value[0]) == 8, "Not a proper pez session: %s" %(value[0],)
        assert value[1] == 'jacob', \
               "Wrong username: %s, expected 'jacob'" % value[1]
        assert value[2] == "auth", \
               "Unexpected conn_type: %s. expected: 'auth'" % (value[2],)
        assert value[3] == "test_resource", \
               "Unexpected resource: %s. expected: 'test_resource'" % (value[3],)
        self.complete()

tests = [ t for t in globals().values() if isinstance(t,type) and issubclass(t, Test) and t is not Test]

class Runner(object):
    def __init__(self):
        self.index = 0
        self.tests = []
        for test in sorted(tests):
            self.tests.append(test(self))

    def main(self):
        self.run_next()
        event.dispatch()

    def run_next(self):
        if self.index == len(self.tests):
            return event.abort()
        test = self.tests[self.index]
        print "\n", test, "running."
        test.run()

    def complete(self, test):
        print test, "complete."
        self.index += 1
        self.run_next()

def main():
    r = Runner()
    print r.tests
    r.main()

if __name__ == "__main__":
    main()