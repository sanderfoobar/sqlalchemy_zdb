class InvalidParameterException(Exception):
    def __init__(self, msg):
        super(InvalidParameterException, self).__init__(msg)
