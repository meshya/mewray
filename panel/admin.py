from django.contrib import admin
from repo.models import node, plan, subscribe, assign
from apikey.models import access

reg = admin.site.register
reg(node)
reg(plan)
reg(subscribe)
reg(assign)
reg(access)