import re
from werkzeug.routing import BaseConverter
from ..targets.interfaces import UNREWRITTEN_RID, InstanceKey

SPLIT_SIGN = ":::"

class StrConverter(BaseConverter):
    @classmethod
    def to_python(self, value):
        if value == "None" or value == "null":
            return None
        else:
            return value
class IntConverter(BaseConverter):
    @classmethod
    def to_python(self, value):
        if value == "None" or value == "null":
            return None
        else:
            try:
                return int(value)
            except:
                return -1
class BoolConverter(BaseConverter):
    @classmethod
    def to_python(self, value):
        if value == "None" or value == "null":
            return None
        elif value.lower().strip() == "true":
            return True
        else:
            return False

class InstanceKeyConverter(BaseConverter):
    @classmethod
    def to_python(self, value):
        p = r"^qid:(?P<qid>\w+)\-vid:(?P<vid>\w+)(\-rid:(?P<rid>\w+))*$"
        pattern = re.compile(p)
        try:
            g = pattern.match(value)
            print(g)
            if g:
                return InstanceKey(qid=g['qid'], vid=int(g['vid']))
            else:
                return InstanceKey(qid='', vid=0)
        except:
            return InstanceKey(qid='', vid=0)
    
    @classmethod
    def to_url(self, value):
        return f'qid:{value.qid}-vid:{value.vid}'

class InstanceKeyListConverter(BaseConverter):
    @classmethod
    def to_python(self, value):
        print(value.split(SPLIT_SIGN))
        return [ InstanceKeyConverter.to_python(i) for i in value.split(SPLIT_SIGN) ]
    @classmethod
    def to_url(self, values):
        return SPLIT_SIGN.join(InstanceKeyConverter.to_url(value) for value in values) # pylint: disable=E1120


class ListConverter(BaseConverter):
    @classmethod
    def to_python(self, value):
        try:
            #value = value.strip()
            if value == "None" or value == "null":
                return None
            elif value == "":
                return []
            return [StrConverter.to_python(i) for i in value.split(SPLIT_SIGN)]
        except:
            return ['' for i in value.split(SPLIT_SIGN)]
    @classmethod
    def to_url(self, values):
        return SPLIT_SIGN.join(StrConverter.to_url(value) for value in values) # pylint: disable=E1120

class IntListConverter(ListConverter):
    @classmethod
    def to_python(self, value):
        try:
            #value = value.strip()
            if value == "None" or value == "null":
                return None
            elif value == "":
                return []
            return [BoolConverter.to_python(i) for i in value.split(SPLIT_SIGN)]
        except:
            return [-1 for i in value.split(SPLIT_SIGN)]