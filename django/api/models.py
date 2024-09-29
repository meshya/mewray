class SubscriptionDto:
    UserId:str
    ViewId:str
    StartedAt:float
    EnableUntil:float
    MaxConnectionCount:int
    MaxTraffic:str
    UsedTraffic:str
    def __init__(self, **kw):
        for name, val in  kw.items():
            setattr(self, name, val)

class ResponseDto:
    status:int
    data:SubscriptionDto
    def __init__(self, **kw):
        for name, val in  kw.items():
            setattr(self, name, val)        