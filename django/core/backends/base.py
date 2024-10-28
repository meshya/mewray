from ..models import AssignReport
from asgiref.sync import async_to_sync as a2s
from repo import models

backends = []

class baseNodeBackend:
    def __init__(self, node:models.node):
        self.address = node.address
        self.host = node.host
        self.auth = node.auth
        self.setting = node.settings
        self.dbObj = node
    # def getReportByAssign(self, uuid) -> AssignReport:
    #     return a2s(self.agetReportByAssign)(uuid)
    # def getAllReport(self):
    #     return a2s(self.agetAllReport)()
    # def getAllAssigns(self):
    #     return a2s(self.agetAllAssigns)()
    # def addSubscription(self, ):
    #     return a2s(self.aaddSubscription)()
    # def deleteSubscription(self, ):
    #     return a2s(self.adeleteSubscription)()
    # def getURL(self, subpk):
    #     return a2s(self.agetURL)()

    # async def agetReportByAssign(self, assign) -> AssignReport:
    #     raise
    # async def agetAllReport(self)->list[AssignReport]:
    #     raise
    # async def agetAllAssigns(self)->list[models.assign]:
    #     raise
    # async def aaddSubscription(self, assign, tag=''):
    #     raise
    # async def adeleteSubscription(self, uuid):
    #     raise
    # async def agetURL(self, assign, **wargs):
    #     raise
    # async def aupdate(self, assign:models.assign):
    #     raise
    async def aadd(self, uuid):...
    async def aremove(self, uuid):...
    async def aexists(self, uuid):...
    async def aisEnable(self, uuid):...
    async def aenable(self, uuid):...
    async def adisable(self, uuid):...
    async def atraffic(self, uuid):...
    async def aconfig(self, uuid):...
    async def aall(self):...
    def __init_subclass__(cls) -> None:
        backends.append(cls)

class AssignNotSynced(Exception):
    def __init__(self, uuid, *args: object) -> None:
        self.uuid = uuid
        super().__init__(*args)