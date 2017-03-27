from django.db import models
from django.contrib.auth.models import User

class AdminMessage(models.Model):

    message = models.TextField()
    time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return "message from %s"%(self.user.username)

class Crontask(models.Model):

    number = models.IntegerField(default=0)

    def __unicode__(self):
        return "Cron %s"%self.id
