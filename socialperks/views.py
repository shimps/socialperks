from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.core.context_processors import csrf
from campaign.models import Campaign,Category, CashOffer, ProductOffer, DiscountOffer, Proposal, FinalProposal, Message,PaymentJob
from userprofile.models import Influencer, Brand, Profile,SocialAccount
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from notifications.models import Notification
from admincontact.models import AdminMessage
import tweepy
import stripe
from settings import PAYPAL_RECEIVER_EMAIL,TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, PRELAUNCH, DEBUG, LOCAL_BASE_URL
from settings import PAYMENT_STANDARD_MONTHLY,PAYMENT_STANDARD_6MONTH,PAYMENT_STANDARD_YEAR,PAYMENT_GOLD_MONTHLY,PAYMENT_GOLD_6MONTH,PAYMENT_GOLD_YEAR
from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.ipn.forms import PayPalIPNForm
from paypal.standard.ipn.models import PayPalIPN
import paypal_signal

from django.views.decorators.csrf import csrf_exempt

def prelaunch(user):
    allowedUsers=['smutangama','testuser','shimps']
    
    if user.username in allowedUsers:
        pass
    else: 
        if PRELAUNCH==True:
            return HttpResponseRedirect('/thanks/')
        
#Implement views
def message(backend, user, response, *args, **kwargs):
    if backend.name == 'twitter':
        try:
            Profile.objects.create(user=user,influencer=True,firstName='',lastName='',description='',companyName='',
                                   phone='',address='',website='',postcode='',city='',country='')
            print"\n Done creating profile \n"
        except:
            print "\nEmail: %s\n"%user.email

def charge_stripe(request):

    if request.POST:
        stripe.api_key = "sk_test_tXPfWi4uWQhVG529QrRbwZ6t"

        # Get the credit card details submitted by the form
        token = request.POST['stripeToken']

        print "\nThis is the name: %s\n"%request.POST['name']
    else:
        pass


    args={}
    args.update(csrf(request))
    return render_to_response('charge_stripe.html',args)

def youtube_oauth_callback(request):
    
    from settings import YOUTUBE_CLIENT_ID,YOUTUBE_CLIENT_SECRET,YOUTUBE_CALLBACK_URL
    import json
    import requests

    YOUTUBE_AUTH_URL='https://accounts.google.com/o/oauth2/token'
    
    if request.GET.get('code') is not None:
        code =request.GET['code']

        headers={
            'Content-Type':'application/x-www-form-urlencoded'
            }
        data={}
        

        data['code']=code
        data['client_id']=YOUTUBE_CLIENT_ID
        data['client_secret']=YOUTUBE_CLIENT_SECRET
        data['redirect_uri']=YOUTUBE_CALLBACK_URL
        data['grant_type']='authorization_code'

        #full_data = json.dumps(data,ensure_ascii=False)
        response = requests.post(YOUTUBE_AUTH_URL,headers=headers,data=data)
        
        YOUTUBE_ACCESS_TOKEN = response.json()['access_token']
        YOUTUBE_TOKEN_TYPE = response.json()['token_type']
        #YOUTUBE_REFRESH_TOKEN=response.json()['refresh_token']

        header={
            'Authorization': 'Bearer %s'%YOUTUBE_ACCESS_TOKEN
            }
        YOUTUBE_CHANNEL_DATA_URL='https://www.googleapis.com/youtube/v3/channels?part=statistics&mine=true'
        YOUTUBE_CHANNEL_BRANDING_URL='https://www.googleapis.com/youtube/v3/channels?part=brandingSettings&mine=true'
        channel_data = requests.get(YOUTUBE_CHANNEL_DATA_URL,headers=header)
        channel_branding = requests.get(YOUTUBE_CHANNEL_BRANDING_URL,headers=header)

        channelTitle = channel_branding.json()['items'][0]['brandingSettings']['channel']['title']
        #print "\n Branding: %s \n"%channelTitle
        
        channels = channel_data.json()['items']

        for channel in channels:
            youtube_id = channel['id']
            subscriberCount = int(channel['statistics']['subscriberCount'])
            viewCount = int(channel['statistics']['viewCount'])
            videoCount = int(channel['statistics']['videoCount'])
            try:
                averageViews = viewCount/videoCount
            except:
                averageViews = 0
            try:
                engagement = ((float(viewCount)/videoCount)/subscriberCount)*100
            except:
                engagement=0

            try:
                socialAccount = SocialAccount.objects.get(platform='YOU',user=request.user,username=youtube_id)
                socialAccount.followers = subscriberCount
                socialAccount.reactions = averageViews
                socialAccount.channel_title = channelTitle
                socialAccount.engagement = engagement
                socialAccount.save()
            except:
                SocialAccount.objects.create(platform='YOU',username=youtube_id,channel_title=channelTitle,
                                             followers=subscriberCount,reactions=averageViews,engagement=engagement,
                                             user=request.user)
                profile = request.user.profile
                profile.youtube=True
                profile.save()

        return HttpResponseRedirect('/profile/%s'%request.user.username)
                                             
   
    else:
        return HttpResponse('Failed to authenicate your Youtube Account :(')

    return HttpResponse('Success')

def generate_youtube_account_data():

    return HttpResponse('success')

def generate_twitter_account_data(username):
    
    atoken='462365026-K2jJRlVdXwrUxw8hF3tvxV9e0cvPH5vTWm2PPopO'
    asecret='5638hO4zsQZD21Mm2ecTqq7u6520cBMbwDVFg3pichiYO'
    auth=tweepy.OAuthHandler(TWITTER_CONSUMER_KEY,TWITTER_CONSUMER_SECRET)
    auth.set_access_token(atoken, asecret)
    api=tweepy.API(auth)

    user = api.get_user(username)
    followers = user.followers_count
    
    statuses = api.user_timeline(screen_name=username,count='10')
    
    total_reactions = 0
    
    for status in statuses:
        total_reactions = total_reactions + status.retweet_count + status.favorite_count

    averageReactions = (total_reactions/len(statuses))
    engagement = (float(averageReactions)/float(followers))*100
    
    userData = [followers,averageReactions,engagement]
        
    return userData

def generate_instagram_account_data(ACCESS_TOKEN,followers):

    from urllib import urlopen
    import json

    url = 'https://api.instagram.com/v1/users/self/media/recent/?access_token=%s&count=10'%ACCESS_TOKEN

    response =  urlopen(url)
    json_bytes = json.load(response)

    total_reactions = 0

    for status in json_bytes['data']:
        total_reactions = total_reactions + status['comments']['count']+status['likes']['count']

    averageReactions = float(total_reactions)/len(json_bytes['data'])
    engagement = (averageReactions/followers)*100

    userData = [averageReactions,engagement]
    
    return userData

def extract_account_username(backend, user,response,*args,**kwargs):

    if backend.name == 'twitter':
        print ("\nTwitter username is: %s and %s followers.\n"%(response.get('screen_name'),response.get('followers_count')))
        try:
            socialAccount = SocialAccount.objects.get(platform='TWI',username=response.get('screen_name'),user=user)
            followers,averageReactions,engagement = generate_twitter_account_data(response.get('screen_name'))
            socialAccount.reactions = averageReactions
            socialAccount.engagement = engagement
            socialAccount.followers=followers
            socialAccount.save()
            profile = user.profile
            profile.twitter = True
            profile.save()
        except:
            followers,averageReactions,engagement = generate_twitter_account_data(response.get('screen_name'))
            socialAccount = SocialAccount.objects.create(platform='TWI',username=response.get('screen_name'),user=user,
                                                         followers=followers,reactions=averageReactions,engagement=engagement)
            profile = user.profile
            profile.twitter = True
            profile.save()
            
    elif backend.name == 'instagram':
        
        accessToken = response['access_token']
        username = response['data']['username']
        followers = response['data']['counts']['followed_by']

        
        try:
            socialAccount = SocialAccount.objects.get(platform='INS',username=username,user=user)
            averageReactions, engagement = generate_instagram_account_data(accessToken,followers)
            socialAccount.reactions = averageReactions
            socialAccount.engagement = engagement
            socialAccount.followers = followers
            socialAccount.save()
            profile = user.profile
            profile.instagram = True
            profile.save
        except:
            averageReactions, engagement = generate_instagram_account_data(accessToken,followers)
            socialAccount = SocialAccount.objects.create(platform='INS',username=username,user=user,followers=followers,
                                                         reactions=averageReactions,engagement=engagement)
            profile = user.profile
            profile.instagram = True
            profile.save

def set_redirect_flag(request):

    profile = request.user.profile
    profile.temp_flag = True
    profile.save()
    
    return HttpResponse("set")

def temporary_redirect(request):
    return HttpResponseRedirect('/profile/%s'%request.user)

def disconnect_social_account(request,social_id):

    socialAccount = SocialAccount.objects.get(id=social_id)
    profile = request.user.profile
    
    if socialAccount.user == request.user:
        
        if socialAccount.platform == 'INS':
            profile.instagram = False
            profile.save()
        elif socialAccount.platform == 'TWI':
            profile.twitter = False
            profile.save()
        elif socialAccount.platform == 'YOU':
            profile.youtube = False
            profile.save()
            
        socialAccount.delete()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        return HttpResponse('Not Allowed')
    
    

def must_be_active(user):
    if user.profile.active==False:
        return False
    else:
        return True

def check_if_prelaunch(user):
    allowedUsers=['smutangama','testuser','shimps']
    
    if user.username in allowedUsers:
        return True
    else: 
        if PRELAUNCH==True:
            return False
        else:
            return True

def home(request):
    
    try:
        profile = request.user.profile
        
        if profile.temp_flag == True:
            profile.temp_flag=False
            profile.save()
            return HttpResponseRedirect("/profile/%s"%profile.user.username)
        else:
            pass
        
    except:
        pass


    args={}
    args.update(csrf(request))

    if request.GET.get('ref') is not None:
        referer = request.GET['ref']
        args['referer'] = referer
    
    return render_to_response('firstpage.html',args)

def leaderboard(request):

    leaderboard = Profile.objects.filter(influencer=True)
    args={}
    args.update(csrf(request))
    args['loggedUser']=request.user
    args['leaderboard']=leaderboard
    return render_to_response('leaderboard.html',args)

def process_payment_dict(user_id,PAYMENT_AMOUNT,PAYMENT_PLAN,PAYMENT_DURATION):

    if DEBUG == False:
        paypal_dict = {
            "cmd":"_xclick-subscriptions",
            "business":""+PAYPAL_RECEIVER_EMAIL,
            "a3":""+str(PAYMENT_AMOUNT),
            "currency_code":"GBP",
            "p3":PAYMENT_DURATION,
            "t3":"M",
            "src":"1",
            "sra":"1",
            "no_note":"1",
            "item_name":""+PAYMENT_PLAN,
            "notify_url":"http://www.socialperks.co/paypal-ipn-location/",
            "return_url":"http://www/socialperks.co/payment_return/",
            "cancel_return":"http://www.socialperk.co/payment_cancel/",
            "custom":""+str(user_id),
            }
    else:
        paypal_dict = {
            "cmd":"_xclick-subscriptions",
            "business":""+PAYPAL_RECEIVER_EMAIL,
            "a3":""+str(PAYMENT_AMOUNT),
            "currency_code":"GBP",
            "p3":PAYMENT_DURATION,
            "t3":"M",
            "src":"1",
            "sra":"1",
            "no_note":"1",
            "item_name":""+PAYMENT_PLAN,
            "notify_url":"%s/paypal-ipn-location/"%(LOCAL_BASE_URL),
            "return_url":"%s/payment_return/"%(LOCAL_BASE_URL),
            "cancel_return":"%s/payment_cancel/"%(LOCAL_BASE_URL),
            "custom":""+str(user_id),
            }

    return paypal_dict

def view_prices(request):

    paypal_dict=process_payment_dict(request.user.id,PAYMENT_STANDARD_MONTHLY,'Standard 1 Month',1)
    form = PayPalPaymentsForm(initial=paypal_dict,button_type="subscribe")
    
    paypal_dict2=process_payment_dict(request.user.id,PAYMENT_STANDARD_6MONTH,'Standard 6 Month',6)
    form2 = PayPalPaymentsForm(initial=paypal_dict2,button_type="subscribe")
    
    paypal_dict3=process_payment_dict(request.user.id,PAYMENT_STANDARD_YEAR,'Standard 12 Month',12)
    form3 = PayPalPaymentsForm(initial=paypal_dict3,button_type="subscribe")
    
    paypal_dict4=process_payment_dict(request.user.id,PAYMENT_GOLD_MONTHLY,'Gold 1 Month',1)
    form4 = PayPalPaymentsForm(initial=paypal_dict4,button_type="subscribe")
    
    paypal_dict5=process_payment_dict(request.user.id,PAYMENT_GOLD_6MONTH,'Gold 6 Month',6)
    form5 = PayPalPaymentsForm(initial=paypal_dict5,button_type="subscribe")
    
    paypal_dict6=process_payment_dict(request.user.id,PAYMENT_GOLD_YEAR,'Gold 12 Month',12)
    form6 = PayPalPaymentsForm(initial=paypal_dict6,button_type="subscribe")
    
        

    args={}
    args.update(csrf(request))
    args['loggedUser']=request.user
    args['s_monthly']=form
    args['s_6month']=form2
    args['s_12month']=form3
    args['g_monthly']=form4
    args['g_6month']=form5
    args['g_12month']=form6
    

    return render_to_response('price_list.html',args)

@login_required
@user_passes_test(must_be_active,login_url='/create_profile/')
@user_passes_test(check_if_prelaunch,login_url='/thanks/')
def settings(request):

    args={}
    args.update(csrf(request))
    args['loggedUser'] = request.user
    
    return render_to_response('settings.html',args)

@csrf_exempt
def payment_return(request):


    return HttpResponseRedirect('/settings/')

def payment_cancel(request):

    print"\n Payment Cancelled. \n"
    return HttpResponseRedirect('/settings/')

@csrf_exempt
def paypal_ipn_location(request,item_check_callable=None):
    
    flag = None

    ipn_obj = None

    form = PayPalIPNForm(request.POST)
        
    if form.is_valid():

        try:
            
            ipn_obj = form.save(commit=False)

            if(ipn_obj.txn_type=='subscr_cancel'):
                
                user = User.objects.get(id=int(ipn_obj.custom))
                #print "\n %s just cancelled subscription \n"%(user.username)
                profile = user.profile
                profile.paid=False

                if(ipn_obj.item_name=='Standard 1 Month'):
                    profile.s_monthly=False
                elif(ipn_obj.item_name=='Standard 6 Month'):
                    profile.s_6month=False
                elif(ipn_obj.item_name=='Standard 12 Month'):
                    profile.s_12month=False
                elif(ipn_obj.item_name=='Gold 1 Month'):
                    profile.g_monthly=False
                elif(ipn_obj.item_name=='Gold 6 Month'):
                    profile.g_6month=False
                elif(ipn_obj.item_name=='Gold 12 Month'):
                    profile.g_12month=False
                    
                profile.save()
                
                
            elif(ipn_obj.txn_type=='subscr_signup'):
                
                user = User.objects.get(id=int(ipn_obj.custom))
                #print "\n %s just Subscribed. %s\n"%(user.username,ipn_obj.item_name)
                profile = user.profile
                profile.paid=True

                if(ipn_obj.item_name=='Standard 1 Month'):
                    profile.s_monthly=True
                elif(ipn_obj.item_name=='Standard 6 Month'):
                    profile.s_6month=True
                elif(ipn_obj.item_name=='Standard 12 Month'):
                    profile.s_12month=True
                elif(ipn_obj.item_name=='Gold 1 Month'):
                    profile.g_monthly=True
                elif(ipn_obj.item_name=='Gold 6 Month'):
                    profile.g_6month=True
                elif(ipn_obj.item_name=='Gold 12 Month'):
                    profile.g_12month=True
                
                profile.save()
                
            elif(ipn_obj.txn_type=='web_accept' and ipn_obj.item_name=='SocialPerks Campaign Payment'):
                campaign = Campaign.objects.get(id=int(ipn_obj.custom))
                campaign.paid=True
                campaign.save()
                
                

        except Exception, e:

            flag = "Exception while processing. (%s)" % e
    else:
        
        flag = "Invalid form. (%s)" % form.errors

    if ipn_obj is None:
        
        ipn_obj = PayPalIPN()

    ipn_obj.initialize(request)
    
    if flag is not None:
        ipn_obj.set_flag(flag)

    else:
        # Secrets should only be used over SSL.
        if request.is_secure() and 'secret' in request.GET:
            ipn_obj.verify_secret(form, request.GET['secret'])
        else:

            try:

                ipn_obj.verify(item_check_callable)

            except Exception, e:

                flag = "Exception while processing. (%s)" % e
    
    ipn_obj.save()

    return HttpResponse("OKAY")


def change_paypal_account(request):

    if request.POST:
        email = request.POST['email']
        profile = request.user.profile
        profile.paypal_email=email
        profile.save()

        return HttpResponseRedirect('/settings/')

    return HttpResponse('Something went wrong... :(')

def contact(request):

    if request.POST:
        message = request.POST['message']
        AdminMessage.objects.create(message=message,user=request.user)
        return HttpResponse('sent')
    else:
        return HttpResponse('Something went wrong.')
        

def changePassword(request):
    if request.POST:
        oldPassword = request.POST['oldPassword']
        newPassword = request.POST['newPassword']

        user = auth.authenticate(username=request.user.username,password=oldPassword)

        if user is not None:
            
            user.set_password(newPassword)
            user.save()
            auth.update_session_auth_hash(request,user)
            
            return HttpResponse('match')
        else:
            return HttpResponse('no match')
    else:
        return HttpResponse('Something went wrong :(')
    
def changeEmail(request):
    
    if request.POST:
        newEmail = request.POST['email']
        user = request.user
        user.email=newEmail
        user.save()
        return HttpResponse('changed')
    else:
        return HttpResponse('Something went wrong :(')
    

def terms(request):

    

    args={}
    args.update(csrf(request))
    args['loggedUser']=request.user
    return render_to_response('terms.html',args)

@login_required
@user_passes_test(must_be_active,login_url='/create_profile/')
@user_passes_test(check_if_prelaunch,login_url='/thanks/')
def search(request):

    if request.GET.get('search') is not None:
        search=request.GET['search']
        searchResults = Campaign.objects.filter(Q(title__icontains=search)|Q(perk__icontains=search))
    else:
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    args={}
    args.update(csrf(request))
    args['loggedUser']=request.user
    args['searchResults']=searchResults
    return render_to_response('search_results.html',args)


def createUserProfile(request):
    if request.POST:
        
        profile = Profile.objects.get(user=request.user)
        
        firstName = request.POST['firstName']
        lastName = request.POST['lastName']
        
        if request.POST.get('companyName') is not None:
            companyName = request.POST['companyName']
        else:
            companyName = None

        description = request.POST['description']
        
        phone = request.POST['phone']
        address = request.POST['address']
        postcode = request.POST['postcode']
        city = request.POST['city']
        country = request.POST['country']
        website = request.POST['website']
        
        if request.FILES.get('image') is not None:
            image=request.FILES['image']
            if image.content_type in ['image/jpeg','image/png','image/bmp']:   
                profile.image=image
            else:
                image=None
        else:
            image=None


        
        profile.firstName=firstName
        profile.lastName=lastName
        profile.website=website
        profile.companyName=companyName
        profile.description=description
        profile.phone=phone
        profile.address=address
        profile.city=city
        profile.country=country
        profile.postcode=postcode
        profile.active=True

        profile.save()
        
        if 'settings' in request.META.get('HTTP_REFERER'):
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            return HttpResponseRedirect('/perkboard/')
    else:
            
        args={}
        args.update(csrf(request))
        args['loggedUser']=request.user
        return render_to_response('create_profile.html',args)

def wait_message(request):
    args={}
    args['loggedUser']=request.user
    return render_to_response('wait_message.html',args)
    
@login_required
@user_passes_test(must_be_active,login_url='/create_profile/')
@user_passes_test(check_if_prelaunch,login_url='/thanks/')
def perkBoard(request):

    allowedUsers=['smutangama','testuser','shimps']
    if request.user.username in allowedUsers:
        pass
    else: 
        if PRELAUNCH==True:
            return HttpResponseRedirect('/thanks/')

    args={}
    args.update(csrf(request))
    args['loggedUser']=request.user
    args['perkboard']=Campaign.objects.all().order_by('-id')
    args['categories']=Category.objects.all()
    return render_to_response('perkboard.html',args)

def filterPerks(request):
    args = {}
    
    if request.POST:
        
        category_id = request.POST['categoryChoice']
        timeChoice = request.POST['timeChoice']
        
        if category_id=='all':
            
            if timeChoice=='oldest':
                perkboard = Campaign.objects.all().order_by('id')
            else:
                perkboard = Campaign.objects.all().order_by('-id')
        else:
            category = Category.objects.get(id=category_id)
            
            if timeChoice=='oldest':
                perkboard = Campaign.objects.filter(category=category).order_by('id')
            else:
                perkboard = Campaign.objects.filter(category=category).order_by('-id')

        args['perkboard']=perkboard
        return render_to_response('perk_filter_feed.html',args)
    else:
        return HttpResponse('Something went wrong :(')
        

def createNewCampaign(request):

    if request.POST:
        title = request.POST['campaignTitle']
        description = request.POST['description']
        #startDate = request.POST['startDate']
        endDate = request.POST['endDate']
        perk = request.POST['perkDescription']
        #requirement = request.POST['requirement']
        slots = request.POST['slots']
        
        category_id = request.POST['categoryOption']
        category = Category.objects.get(id=category_id)
        
        if request.FILES.get('image') is not None:
            image = request.FILES['image']
            if image.content_type in ['image/jpeg','image/png','image/bmp']:   
                pass
            else:
                image=None
        else:
            image=None
            
        campaign = Campaign(title=title,description=description,slots=slots,
                            perk=perk,category=category,
                            endDate=endDate,image=image,user=request.user)
        
        if request.POST['offerType']=='cash':
            campaign.cash = True
        elif request.POST['offerType']=='product':
            campaign.product = True
        elif request.POST['offerType']=='discount':
            campaign.discount = True

        platforms = request.POST.getlist('platform')
        print platforms

        for platform in platforms:
            if platform == 'twitter':
                campaign.twitter=True
            elif platform == 'instagram':
                campaign.instagram=True
            elif platform =='youtube':
                campaign.youtube=True
        
            
        campaign.save()

        return HttpResponseRedirect('/campaign/%s'%campaign.slug)
    else:
        args={}
        args.update(csrf(request))
        return render_to_response('new_campaign.html',args)

def editCampaign(request,campaign_id):
    campaign = Campaign.objects.get(id=campaign_id)

    if request.POST:
        title = request.POST['campaignTitle']
        description = request.POST['description']
        #startDate = request.POST['startDate']
        #requirement = request.POST['requirement']
        endDate = request.POST['endDate']
        perk = request.POST['perkDescription']
        category_id = request.POST['categoryOption']
        category = Category.objects.get(id=category_id)
        
        #niche=request.POST['niche']
        
        if request.FILES.get('image') is not None:
            image = request.FILES['image']
            if image.content_type in ['image/jpeg','image/png','image/bmp']:   
                campaign.image=image
            else:
                image=None
             
            
        campaign.title=title
        campaign.description=description
        #campaign.startDate=startDate
        campaign.perk=perk
        campaign.category = category
        campaign.endDate=endDate
        #campaign.requirement = requirement

        platforms = request.POST.getlist('platform')

        for platform in platforms:
            if platform == 'twitter':
                campaign.twitter=True
            elif platform == 'instagram':
                campaign.instagram=True
            elif platform =='youtube':
                campaign.youtube=True
            
        campaign.save()
        
        return HttpResponseRedirect('/campaign/'+campaign.slug)
    else:
        return HttpResponse('Something went wrong :(')

@login_required
@user_passes_test(must_be_active,login_url='/create_profile/')
@user_passes_test(check_if_prelaunch,login_url='/thanks/')
def viewCampaign(request,slug):


    args={}
    args.update(csrf(request))
    campaign=Campaign.objects.get(slug=slug)
    args['campaign']=campaign
    args['categories']=Category.objects.all()
    args['loggedUser']=request.user
    return render_to_response('perkpage.html',args)

def send_campaign_invitation(request):

    if request.POST:
        campaign_id = int(request.POST['campaign_id'])
        user_id = int(request.POST['user_id'])

        campaign = Campaign.objects.get(id=campaign_id)
        user = User.objects.get(id=user_id)

        Notification.objects.create(action='CI',campaign=campaign,sender=request.user,receiver=user)
        return HttpResponse('success')

    else:
        return HttpResponse('Something went wrong... :(')

    return HttpResponse('Success')

def read_notification(request,notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
        notification.read=True
        notification.save()
    except:
        return HttpRsponse('Something went wrong.')
    
    return HttpResponse('success')

@login_required
@user_passes_test(must_be_active,login_url='/create_profile/')
@user_passes_test(check_if_prelaunch,login_url='/thanks/')
def myCampaigns(request):
    args={}
    args.update(csrf(request))
    args['campaigns']=Campaign.objects.filter(user=request.user).order_by('-id')
    args['categories']=Category.objects.all()
    args['loggedUser']=request.user
    return render_to_response('my_campaigns2.html',args)


@login_required
@user_passes_test(must_be_active,login_url='/create_profile/')
@user_passes_test(check_if_prelaunch,login_url='/thanks/')
def myProposals(request):

    args={}
    args['proposals']=Proposal.objects.filter(user=request.user).order_by('-id')
    args['loggedUser']=request.user
    return render_to_response('my_proposals_page.html',args)

def final_proposal_edit(request,proposal_id):
    proposal = Proposal.objects.get(id=proposal_id)
        
    if request.POST:
        amount=request.POST['amount']
        proposal.cashAmount = amount
        proposal.save()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        
        
    return HttpResponse("Something went wrong.. :(")

def postProposal(request,campaign_id):
    
    campaign = Campaign.objects.get(id=campaign_id)
    
    if request.POST.get('proposalMessage') is not None:
        proposalMessage = request.POST['proposalMessage']
    else:
        proposalMessage = None
        
    if request.POST.get('cashProposal') is not None:
        cashProposal = request.POST['cashProposal']
    else:
        cashProposal = None

    if campaign.cash == True:
        proposal = Proposal.objects.create(cash=True,cashAmount=cashProposal,description=proposalMessage,
                                user=request.user,campaign=campaign)
    elif campaign.product == True:
        proposal = Proposal.objects.create(product=True,description=proposalMessage,user=request.user,
                                campaign=campaign)
    else:
        proposal = Proposal.objects.create(discount=True,description=proposalMessage,user=request.user,
                                campaign=campaign)
    Notification.objects.create(action='PR',proposal=proposal,sender=request.user,receiver=campaign.user)
    
    return HttpResponseRedirect('/proposal/%s'%proposal.id)

@login_required
@user_passes_test(must_be_active,login_url='/create_profile/')
@user_passes_test(check_if_prelaunch,login_url='/thanks/')
def viewProposal(request,proposal_id):

    proposal = Proposal.objects.get(id=proposal_id)

    notifications = Notification.objects.filter(receiver=request.user,read=False,proposal=proposal)
    
    try:
        notifications.update(read=True)
    except:
        pass
    
    args={}
    args.update(csrf(request))
    args['proposal']=proposal
    args['loggedUser']=request.user

    try:
        finalProposal = FinalProposal.objects.filter(Q(user=request.user)|Q(campaign__user=request.user),campaign=proposal.campaign)[0]
        args['finalProposal'] = finalProposal

        #Adds some paypal integration
        if DEBUG == False:
            
            paypal_dict = {
                "business": "smutangama1@gmail.com",
                "amount": ""+str(finalProposal.cashAmount),
                "item_name": "Influencer Payout",
                "currency_code":"GBP",
                #"invoice": "socialperks-influencer-payout",
                "notify_url":"http://www.socialperks.co/paypal-ipn-location/",
                "return_url":"http://www/socialperks.co/payment_return/",
                "cancel_return":"http://www.socialperk.co/payment_cancel/",
                "custom": "Upgrade all users!",
            }
        else:
            paypal_dict = {
                "business": ""+PAYPAL_RECEIVER_EMAIL,
                "amount": ""+str(finalProposal.cashAmount),
                "item_name": "Influencer Payout",
                "currency_code":"GBP",
                #"invoice": "socialperks-influencer-payout",
                "notify_url":"%s/paypal-ipn-location/"%(LOCAL_BASE_URL),
                "return_url":"%s/payment_return/"%(LOCAL_BASE_URL),
                "cancel_return":"%s/payment_cancel/"%(LOCAL_BASE_URL),
                "custom": "Upgrade all users!",
            }

        form = PayPalPaymentsForm(initial=paypal_dict)

        args['paypalForm']=form
        #print "\n Paypal Dict: %s\n"%form.render()

    except:
        
        print"\nDoesn't exist.\n"
        pass
    
    return render_to_response('proposal_page.html',args)

def check_proposal_submitted(request):

    if request.GET:
        campaign_id=request.GET['campaign_id']
        campaign = Campaign.objects.get(id=campaign_id)

        count = Proposal.objects.filter(campaign=campaign,user=request.user).count()

        if count>0:
            return HttpResponse('1')
        else:
            return HttpResponse('0')
    else:
        return HttpResponse('Something went wrong :(')

def cost_of_products(amount):

    if amount<10:
        return 10
    else:
        remainder = amount-10
        fives = remainder/5
        extras = remainder%5
        
        if extras==0:
            return 10+(fives*5)
        else:
            return 10+(fives*5)+5
        
def create_product_payment(request):

    campaign_id = int(request.GET['campaign_id'])
    
    campaign = Campaign.objects.get(id=campaign_id)
    user = request.user

    if campaign.user==request.user:

        paypal_dict = {}

        args={}
        args.update(csrf(request))

        if request.GET.get('numberOfSlots') is not None:
            slots = int(request.GET['numberOfSlots'])
            price = cost_of_products(slots)
            #title = request.GET['title']
            
            
        
        if DEBUG == False:
            
            paypal_dict = {
                "business": ""+PAYPAL_RECEIVER_EMAIL,
                "amount": ""+str(price),
                "item_name": "SocialPerks Campaign Payment",
                "currency_code":"GBP",
                #"invoice": "socialperks-influencer-payout",
                "notify_url":"http://www.socialperks.co/paypal-ipn-location/",
                "return_url":"http://www/socialperks.co/payment_return/",
                "cancel_return":"http://www.socialperk.co/payment_cancel/",
                "custom": ""+str(campaign_id),
            }
        else:
            paypal_dict = {
                "business": ""+PAYPAL_RECEIVER_EMAIL,
                "amount": ""+str(price),
                "item_name": "SocialPerks Campaign Payment",
                "currency_code":"GBP",
                #"invoice": "socialperks-influencer-payout",
                "notify_url":"%s/paypal-ipn-location/"%(LOCAL_BASE_URL),
                "return_url":"%s/payment_return/"%(LOCAL_BASE_URL),
                "cancel_return":"%s/payment_cancel/"%(LOCAL_BASE_URL),
                "custom": ""+str(campaign_id),
            }
        
        form = PayPalPaymentsForm(initial=paypal_dict)
        args['paypalForm']=form
        args['price']=price
        args['slots']=slots

        return render_to_response('product_paypal_form.html',args)
    else:
        return HttpResponse('Something went wrong. :(')

    return HttpResponse('Something went wrong :(')

    

def postProposalMessage(request,proposal_id):
    
    proposal = Proposal.objects.get(id=proposal_id)
    
    if request.POST:

        message = request.POST['message']
        if request.FILES.get('attachment') is not None:  
            attachment = request.FILES['attachment']
        else:
            attachment = None

        message = Message.objects.create(message=message,attachment=attachment,user=request.user,proposal=proposal)

        if message.user == message.proposal.campaign.user:
            Notification.objects.create(action='MR',proposal=proposal,sender=request.user,receiver=proposal.user)
        else:
            Notification.objects.create(action='MR',proposal=proposal,sender=request.user,receiver=message.proposal.campaign.user)
                                    
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))       
    else:
        return HttpResponse('Something went wrong! Contact Admin.')
    
def acceptProposal(request,proposal_id):

    proposal = Proposal.objects.get(id=proposal_id)
    
    if proposal.declined==True:
        proposal.declined=False
        
    if proposal.accepted==True:
        proposal.accepted=False
    else:
        proposal.accepted=True
    proposal.save()
    Notification.objects.create(action='PA',proposal=proposal,sender=request.user,receiver=proposal.user)
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def declineProposal(request,proposal_id):

    proposal = Proposal.objects.get(id=proposal_id)
    
    if proposal.accepted==True:
        proposal.accepted=False

    if proposal.declined==True:
        proposal.declined=False
    else:
        proposal.declined=True
    proposal.save()
    Notification.objects.create(action='PD',proposal=proposal,sender=request.user,receiver=proposal.user)
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def editProposal(request,proposal_id):
    
    proposal = Proposal.objects.get(id=proposal_id)
    if request.POST:
        description = request.POST['description']
        proposal.description = description
        
        if request.POST.get('cashAmount'):
            cashAmount = request.POST['cashAmount']
            proposal.cashAmount = cashAmount

        proposal.save()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    else:
        return HttpResponse('Something went wrong :(')

        

def loadProposal(request,campaign_id):

    campaign = Campaign.objects.get(id=campaign_id)
    args={}
    args['proposals']=campaign.proposals.all().order_by('id')
    args['campaign'] = campaign
    return render_to_response('proposal_feed.html',args)

def completeProposal(request,proposal_id):

    proposal = Proposal.objects.get(id=proposal_id)
    proposal.completed = True
    proposal.save()
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def load_notifications(request):

    notifications = Notification.objects.filter(receiver=request.user,read=False)

    args={}
    args['notifications']=notifications
    return render_to_response('notifications.html',args)

def load_notification_count(request):

    notificationCount = Notification.objects.filter(receiver=request.user,read=False).count()
    return HttpResponse("%s"%notificationCount)


def post_final_proposal(request,campaign_id):

    if request.POST:
        
        date = request.POST['endDate']
        description = request.POST['description']
        cashAmount = request.POST['cashAmount']
        numberOfPosts = request.POST['postNumber']
        campaign = Campaign.objects.get(id=campaign_id)
        
        FinalProposal.objects.create(cashAmount=cashAmount,description=description,date=date,
                                     numberOfPosts=numberOfPosts,campaign=campaign,user=request.user)
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    else:
        return HttpResponse('Something went wrong.. :(')

def accept_final_proposal(request,final_proposal_id):
    from datetime import timedelta

    finalProposal = FinalProposal.objects.get(id=final_proposal_id)

    if request.user == finalProposal.campaign.user:
        
        fullAmount = finalProposal.cashAmount
        
        payout = finalProposal.cashAmount *0.80
        date = finalProposal.date + timedelta(days=7)
        campaign = finalProposal.campaign
        sender = finalProposal.campaign.user
        receiver = finalProposal.user
        
        
        PaymentJob.objects.create(payout=payout,date=date,campaign=campaign,sender=sender,receiver=receiver)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        return HttpResponse('You are not allowed to do this!')

#Users
@login_required
@user_passes_test(must_be_active,login_url='/create_profile/')
@user_passes_test(check_if_prelaunch,login_url='/thanks/')
def viewProfile(request,username):
    from settings import YOUTUBE_CLIENT_ID,YOUTUBE_CALLBACK_URL
    args={}
    args.update(csrf(request))
    user=User.objects.get(username=username)
    args['profile']=user.profile
    args['loggedUser']=request.user
    args['youtube_client_id']=YOUTUBE_CLIENT_ID
    args['callback_url']=YOUTUBE_CALLBACK_URL
    return render_to_response('user_profile_page.html',args)

def register(request):

    
    args={}
    args.update(csrf(request))

    if request.POST:
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        accountType = request.POST['accountType']

        user = User.objects.create_user(username=username,email=email,password=password)
        profile = Profile(user=user)

        if request.POST.get('ref') is not None:
            ref = request.POST['ref']
            userReferer = User.objects.get(username=ref)
            userRefererProfile = userReferer.profile
            userRefererProfile.members_referred+=1
            userRefererProfile.save()
        else:
            pass
        
        if accountType == 'influencer':
            profile.influencer = True
        elif accountType == 'brand':
            profile.brand = True

        profile.save()

        user = auth.authenticate(username=username,password=password)
        if user is not None:
            auth.login(request,user)
            return HttpResponseRedirect('/perkboard/')
        else:
            return HttpResponse('Wrong account details')

        return HttpResponseRedirect('/perkboard/')
    else:
          
        return HttpResponse('Something went wrong!')

def registerInfluencer(request):

    if request.POST:
        firstName = request.POST['firstName']
        lastName = request.POST['lastName']
        phone = request.POST['phone']
        address = request.POST['address']
        postcode = request.POST['postcode']
        city = request.POST['city']
        country = request.POST['country']

        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        
        if request.FILES.get('profilePic') is not None:
            image=request.FILES['proilePic']
        else:
            image=None
            
        user = User.objects.create_user(username=username,password=password,email=email)        
        Influencer.objects.create(firstName=firstName,lastName=lastName,phone=phone,address=address,
                                  postcode=postcode,city=city,country=country,user=user)

        return HttpResponseRedirect("/profile/%s"%user.username)
    else:
        return HttpResponse('Something went wrong, contact the Admins.')

    return HttpResponse('Registered User')

def registerBrand(request):

    if request.POST:
        firstName = request.POST['firstName']
        lastName = request.POST['lastName']
        companyName = request.POST['companyName']
        phone = request.POST['phone']
        address = request.POST['address']
        postcode = request.POST['postcode']
        city = request.POST['city']
        country = request.POST['country']

        username = request.POST['username']
        password = request.POST['password']
        email=request.POST['email']
        
        if request.FILES.get('profilePic') is not None:
            image=request.FILES['profilePic']
        else:
            image=None

        user = User.objects.create_user(username=username,password=password,email=email)
        Brand.objects.create(firstName=firstName,lastName=lastName,company=companyName,
                             phone=phone,address=address,postcode=postcode,city=city,
                             country=country,user=user)

        return HttpResponseRedirect("/profile/%s"%user.username)
    else:
        return HttpResponse('Something went wrong, contact the Admins')

    return HttpReponse('Registered Brand')

def logout(request):

    auth.logout(request)
    
    return HttpResponseRedirect('/')

def super_secret_login_link(request):

    username = 'testuser'
    password = 'password'

    user = auth.authenticate(username=username,password=password)

    if user is not None:
        auth.login(request,user)
        return HttpResponseRedirect('/perkboard/')
    else:
        return HttpResponse('There\'s something wrong with your link')



def login(request):
    
    if request.POST:

        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username,password=password)
        if user is not None:
            auth.login(request,user)

            if request.GET.get('ajax') is not None:
                return HttpResponse('success')

            if PRELAUNCH==True:
                args={}
                args['loggedUser']=request.user
                return render_to_response('wait_message.html',args)
            
            return HttpResponseRedirect('/perkboard/')
        else:
            if request.GET.get('ajax') is not None:
                return HttpResponse('failure')

            return HttpResponse('Wrong account details')

    else:
        args={}
        args.update(csrf(request))
        return render_to_response('login.html',args)
