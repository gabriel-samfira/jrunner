import json

class BaseCallback(object):

    def __init__(self, message):
        self.message        = message
        self.message_body   = json.loads(self.message.body)
        self.action         = self.message_body['action']
            
        action              = getattr(self, str(self.action))
        action()
