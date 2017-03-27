from django.db import models
from django.contrib.auth.models import User
from time import time
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill,Transpose, SmartResize

    
#A Helper function to help with uploads.Generates a filename through a time string
def get_upload_file_name(instance,filename):
    return "uploads/profile_pictures/%s_%s"%(str(time()).replace('.','_'),filename)

# Create your models here.

class Profile(models.Model):

    firstName = models.CharField(max_length=200,null=True,blank=True)
    lastName = models.CharField(max_length=200,null=True,blank=True)
    description = models.TextField(blank=True, null=True)
    companyName = models.CharField(max_length=200,null=True,blank=True)

    image = models.FileField(upload_to=get_upload_file_name,null=True,blank=True)
    image_thumbnail250= ImageSpecField(source='image',
                                       processors=[Transpose(),SmartResize(250,250)],
                                       format='JPEG',
                                       options={'quality':80})

    phone = models.CharField(max_length=100,null=True,blank=True)
    address = models.CharField(max_length=200,null=True,blank=True)
    website = models.CharField(max_length=200,null=True,blank=True)
    postcode = models.CharField(max_length=100,null=True,blank=True)
    city = models.CharField(max_length=100,null=True,blank=True)
    country = models.CharField(max_length=100,null=True,blank=True)

    paypal_email = models.CharField(max_length=200,null=True,blank=True)
    
    members_referred = models.IntegerField(default=0)
    
    active = models.BooleanField(default=False)
    influencer = models.BooleanField(default=False)
    brand = models.BooleanField(default=False)
    
    paid = models.BooleanField(default=False)
    s_monthly=models.BooleanField(default=False)
    s_6month=models.BooleanField(default=False)
    s_12month=models.BooleanField(default=False)
    g_monthly=models.BooleanField(default=False)
    g_6month=models.BooleanField(default=False)
    g_12month=models.BooleanField(default=False)

    twitter = models.BooleanField(default=False)
    facebook = models.BooleanField(default=False)
    vine = models.BooleanField(default=False)
    instagram = models.BooleanField(default=False)
    youtube = models.BooleanField(default=False)
    snapchat = models.BooleanField(default=False)

    temp_flag = models.BooleanField(default=False)

    
    user = models.OneToOneField(User, related_name='profile')

    def __unicode__(self):
        return "%s's profile"%self.user.username
    

class SocialAccount(models.Model):
    
    platformChoices = (('TWI','Twitter'),('FAC','Facebook'),('INS','Instagram'),('VIN','Vine'),('YOU','Youtube'),('SNA','Snapchat'))
    platform = models.CharField(max_length=3,choices=platformChoices,null=True,blank=True)
    username = models.CharField(max_length=200, null=True,blank=True)
    channel_title = models.CharField(max_length=200,null=True, blank=True)
    followers = models.IntegerField(default=0)
    reactions = models.IntegerField(default=0)
    engagement = models.FloatField(default=0)
    
    user = models.ForeignKey(User,related_name='socialAccounts')

    def __unicode__(self):
        return "%s's %s Account"%(self.user.username,self.platform)
    
class Influencer(models.Model):

    firstName = models.CharField(max_length=200)
    lastName = models.CharField(max_length=200)
    image = models.FileField(upload_to=get_upload_file_name,null=True,blank=True)
    phone = models.CharField(max_length=100)
    address=models.CharField(max_length=200)
    postcode=models.CharField(max_length=100)
    city=models.CharField(max_length=100)
    country=models.CharField(max_length=100)
    
    user = models.OneToOneField(User,related_name="influencer")

class Brand(models.Model):

    firstName = models.CharField(max_length=200)
    lastName = models.CharField(max_length=200)
    image = models.FileField(upload_to=get_upload_file_name,null=True,blank=True)
    company = models.CharField(max_length=200)
    phone = models.CharField(max_length=100)
    address=models.CharField(max_length=200)
    postcode=models.CharField(max_length=100)
    city=models.CharField(max_length=100)
    country=models.CharField(max_length=100)
    
    user = models.OneToOneField(User,related_name="brand")


from paypal.standard.ipn.signals import payment_was_successful

def show_me_the_money(sender, **kwargs):



    ipn_obj = sender



    # Undertake some action depending upon `ipn_obj`.


    if ipn_obj.custom == "Upgrade all users!":

        print"\n User has paid. \n"

    print __file__,1, 'This works'        

payment_was_successful.connect(show_me_the_money)   
