from ..models import AssignReport
from asgiref.sync import async_to_sync as a2s

backends = []

class baseNodeBackend:
    def __init__(self, address, host, auth, settings):
        self.address = address
        self.host = host
        self.auth = auth
        self.setting = settings
    def getReportBySubscription(self, subpk) -> AssignReport:
        return a2s(self.agetReportBySubscription)(subpk)
    def getAllReport(self):
        return a2s(self.agetAllReport)()
    def getAllAssigns(self):
        return a2s(self.agetAllAssigns)()
    def addSubscription(self, ):
        return a2s(self.aaddSubscription)()
    def deleteSubscription(self, ):
        return a2s(self.adeleteSubscription)()
    def getURL(self, subpk):
        return a2s(self.agetURL)()
    async def agetReportBySubscription(self, subpk) -> AssignReport:
        raise
    async def agetAllReport(self):
        raise
    async def agetAllAssigns(self):
        raise
    async def aaddSubscription(self, uuid):
        raise
    async def adeleteSubscription(self, uuid):
        raise
    async def agetURL(self, uuid, **wargs):
        raise
    def __init_subclass__(cls) -> None:
        backends.append(cls)