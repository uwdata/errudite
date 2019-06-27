
class ConfigurationError(Exception):
    """
    The exception raised by any AllenNLP object when it's misconfigured
    (e.g. missing properties, invalid properties, unknown properties).
    """

    def __init__(self, message):
        super(ConfigurationError, self).__init__()
        self.message = message
        self.args = message

    def __str__(self):
        return repr(self.message)

class DSLParseError(Exception):
    """
    The exception raised by DSL parser when the parsing is wrong.
    """

    def __init__(self, message):
        super(DSLParseError, self).__init__()
        self.message = message
        self.args = message

    def __str__(self):
        return repr(self.message)

class DSLValueError(Exception):
    """
    The exception raised by DSL computation when the value of an 
    instance cannot be correctly computed
    """

    def __init__(self, message):
        super(DSLValueError, self).__init__()
        self.message = message
        self.args = message

    def __str__(self):
        return repr(self.message)

