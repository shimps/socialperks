from django.db import models
from django.contrib.auth.models import User
from time import time
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill,Transpose, SmartResize

# A Helper Function for uploaded images
def get_upload_file_name(instance,filename):
    return "uploads/%s_%s"%(str(time()).replace('.','_'),filename)

def get_upload_file_name_attachment(instance,filename):
    return "uploads/attachments/%s_%s"%(str(time()).replace('.','_'),filename)

# Create your models here.

class Category(models.Model):

    title = models.CharField(max_length=200)
    description = models.TextField()


    def __unicode__(self):
        return self.title
    
class Campaign(models.Model):
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True,blank=True,null=True)
    perk = models.CharField(max_length=200,blank=True,null=True)
    niche = models.CharField(max_length=200,blank=True,null=True)
    requirement = models.IntegerField(default=0)
    description = models.TextField()
    category = models.ForeignKey(Category,related_name='campaigns',blank=True,null=True)
    slots = models.IntegerField(default=0)

    
    image = models.FileField(upload_to=get_upload_file_name,null=True,blank=True)
    image_thumbnail250= ImageSpecField(source='image',
                                       processors=[Transpose(),SmartResize(250,250)],
                                       format='JPEG',
                                       options={'quality':80})
    image_thumbnail80= ImageSpecField(source='image',
                                       processors=[Transpose(),SmartResize(80,80)],
                                       format='JPEG',
                                       options={'quality':80})
    
    postDate = models.DateTimeField(auto_now_add=True)
    startDate = models.DateField(blank=True,null=True)
    endDate = models.DateField(blank=True,null=True)

    product = models.BooleanField(default=False)
    discount = models.BooleanField(default=False)
    cash = models.BooleanField(default=False)

    twitter = models.BooleanField(default=False)
    facebook = models.BooleanField(default=False)
    instagram = models.BooleanField(default=False)
    youtube = models.BooleanField(default=False)
    vine = models.BooleanField(default=False)
    snapchat = models.BooleanField(default=False)

    paid = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    user = models.ForeignKey(User, related_name='campaigns',null=True,blank=True)

    def __unicode__(self):
        return self.title

    def save(self, **kwargs):
        #This overwrites the save function and makes sure the slug is unique.
        #Note slug is a separate file slug.py with the unique_slugify function.
        from slug import unique_slugify
        slug_str="%s"%self.title
        unique_slugify(self, slug_str)
        super(Campaign, self).save()


    

    
#These Offers are created with the the Campaign        
class CashOffer(models.Model):

    minimum = models.IntegerField(default=100)
    maximum = models.IntegerField(default=250)
    description = models.TextField()
    stock = models.IntegerField(default=0)
    
    campaign = models.OneToOneField(Campaign, related_name='cashOffer')

class ProductOffer(models.Model):

    image = models.FileField(upload_to=get_upload_file_name,null=True,blank=True)
    description = models.TextField(null=True, blank=True)
    stock = models.IntegerField(default=0)
    
    campaign = models.OneToOneField(Campaign, related_name='productOffer')

class DiscountOffer(models.Model):

    image = models.FileField(upload_to=get_upload_file_name,null=True,blank=True)
    description = models.TextField()
    discount = models.IntegerField(default=0)
    stock = models.IntegerField(default=0)
    
    campaign = models.OneToOneField(Campaign, related_name='discountOffer')

#These proposals are made by the Influencers
class Proposal(models.Model):

    cash = models.BooleanField(default=False)
    discount = models.BooleanField(default=False)
    product = models.BooleanField(default=False)
    cashAmount = models.FloatField(default=0)
    description = models.TextField(null=True, blank=True)
    accepted = models.BooleanField(default=False)
    declined = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    
    user = models.ForeignKey(User,related_name='proposals')
    campaign = models.ForeignKey(Campaign, related_name='proposals')

#This stores the final proposal

class FinalProposal(models.Model):

    cashAmount = models.FloatField(default=0)
    numberOfPosts = models.IntegerField(default=0)
    description = models.TextField(null=True,blank=True)
    date = models.DateField(null=True,blank=True)
    
    user = models.ForeignKey(User,related_name='final_proposals',null=True,blank=True)
    campaign = models.ForeignKey(Campaign, related_name='final_proposals',null=True,blank=True)
    
    
#This stores the message board for the Proposals
class Message(models.Model):

    message = models.TextField()
    attachment = models.FileField(upload_to=get_upload_file_name_attachment,null=True,blank=True)
    date = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    
    proposal = models.ForeignKey(Proposal,related_name='messages')
    user = models.ForeignKey(User,related_name='messages')

#Scheduled Payments

class PaymentJob(models.Model):

    payout = models.FloatField(default=0)
    campaign = models.ForeignKey(Campaign,related_name="payouts",null=True,blank=True)
    date = models.DateField()
    sender = models.ForeignKey(User,related_name='payments_sent')
    receiver = models.ForeignKey(User,related_name='payments_received')
    complete=models.BooleanField(default=False)

    def __unicode__(self):
        return "Payment from %s to %s"%(self.sender,self.receiver)

