
class BuzzAuthorizationException(Exception):

    def __init__(self, msg):
        Exception.__init__(self, msg)
        self._msg = msg

    def __str__(self):
        return self._msg


class BuzzOperationException(Exception):
    def __init__(self, msg):
            Exception.__init__(self, msg)
            self._msg = msg

    def __str__(self):
        return self._msg


class BuzzOauthException(Exception):

    def __init__(self, msg):
        Exception.__init__(self, msg)
        self._msg = msg

    def __str__(self):
        return self._msg

class BuzzYahooOauthException(BuzzOauthException):

    def __init__(self, msg):
        BuzzOauthException.__init__(self, msg)
