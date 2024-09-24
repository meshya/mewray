from repo import models

class SubscriptionService:
    def __init__(self, sub:models.subscribe):
        self.dbObj = sub
    
    @classmethod
    def create(self, userId, planId):
        ...