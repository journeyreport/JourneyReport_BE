def twilio_message_create(*args, **kwargs):
    class FakeMsg(object):
        def __init__(self):
            self.error_code = None
    return FakeMsg()
