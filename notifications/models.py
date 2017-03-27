from django.db import models
from django.contrib.auth.models import User
from campaign.models import Proposal,Campaign

# Create your models here.
class Notification(models.Model):
    
    notificationChoices = (('PR','Proposal Received'),('PA','Proposal Accepted'),('PD','Proposal Denied'),('MR','Message Received'),('CI','Campaign Invite'))
    action = models.CharField(max_length=3,choices=notificationChoices,null=True,blank=True)
    read = models.BooleanField(default=False)

    campaign = models.ForeignKey(Campaign,null=True)

    proposal = models.ForeignKey(Proposal,blank=True,null=True)
    #flag = models.BooleanField(default=0)
    #campaign = models.ForeignKey(Campaign,blank=True,null=True)
    
    
    sender = models.ForeignKey(User) 
    receiver = models.ForeignKey(User, related_name='notifications')


    
