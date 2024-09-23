from django.contrib import admin
from repo.models import node, plan, subscribe, assign


reg = admin.site.register
reg(node)
reg(plan)
reg(subscribe)
reg(assign)