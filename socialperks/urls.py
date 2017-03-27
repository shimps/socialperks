"""socialperks URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('social_auth.urls')),
    #Campaign Related
    url(r'^perkboard/filter/$','socialperks.views.filterPerks'),
    url(r'^perkboard/$','socialperks.views.perkBoard'),
    url(r'^campaign/create_new/$','socialperks.views.createNewCampaign'),
    url(r'^campaign/my/$','socialperks.views.myCampaigns'),
    url(r'^campaign/edit/(?P<campaign_id>\d+)/$','socialperks.views.editCampaign'),
    url(r'^campaign/(?P<slug>.*)/$','socialperks.views.viewCampaign'),
    url(r'^proposal/my/$','socialperks.views.myProposals'),
    url(r'^proposal/post/(?P<campaign_id>\d+)/$','socialperks.views.postProposal'),
    url(r'^proposal/edit/(?P<proposal_id>\d+)/$','socialperks.views.editProposal'),
    url(r'^proposal/message/(?P<proposal_id>\d+)/$','socialperks.views.postProposalMessage'),
    url(r'^proposal/(?P<proposal_id>\d+)/$','socialperks.views.viewProposal'),
    url(r'^proposal/accept/(?P<proposal_id>\d+)/$','socialperks.views.acceptProposal'),
    url(r'^proposal/decline/(?P<proposal_id>\d+)/$','socialperks.views.declineProposal'),
    url(r'^proposal/load/(?P<campaign_id>\d+)/$','socialperks.views.loadProposal'),
    url(r'^proposal/complete/(?P<proposal_id>\d+)/$','socialperks.views.completeProposal'),
    url(r'^proposal/post_final_proposal/(?P<campaign_id>\d+)/$','socialperks.views.post_final_proposal'),
    url(r'^proposal/accept_final_proposal/(?P<final_proposal_id>\d+)/$','socialperks.views.accept_final_proposal'),
    url(r'^send_campaign_invitation/$','socialperks.views.send_campaign_invitation'),
    #User Related
    url(r'^profile/(?P<username>.*)/$','socialperks.views.viewProfile'),
    url(r'^register/influencer/$','socialperks.views.registerInfluencer'),
    url(r'^register/brand/$','socialperks.views.registerBrand'),
    url(r'^register/$','socialperks.views.register'),
    url(r'^logout/$','socialperks.views.logout'),
    url(r'^login/$','socialperks.views.login'),
    url(r'^create_profile/$','socialperks.views.createUserProfile'),
    #Funny Pages
    url(r'^super-secret-login-link/$','socialperks.views.super_secret_login_link'),
    #Support Pages
    url(r'^read_notification/(?P<notification_id>\d+)/$','socialperks.views.read_notification'),
    url(r'^leaderboard/$','socialperks.views.leaderboard'),
    url(r'^oauth_callback/$','socialperks.views.oauth_callback'),
    url(r'^plans/$','socialperks.views.view_prices'),
    url(r'^create_product_payment/$','socialperks.views.create_product_payment'),
    url(r'^paypal/',include('paypal.standard.ipn.urls')),
    url(r'^paypal-ipn-location','socialperks.views.paypal_ipn_location'),
    url(r'^payment_return/$','socialperks.views.payment_return'),
    url(r'^payment_cancel/$','socialperks.views.payment_cancel'),
    url(r'^change_paypal_account/$','socialperks.views.change_paypal_account'),
    url(r'^contact/$','socialperks.views.contact'),
    url(r'^thanks/$','socialperks.views.wait_message'),
    url(r'^disconnect_social_account/(?P<social_id>\d+)/$','socialperks.views.disconnect_social_account'),
    url(r'^set_redirect_flag/$','socialperks.views.set_redirect_flag'),
    url(r'^settings/$','socialperks.views.settings'),
    url(r'^check_proposal_submitted/$','socialperks.views.check_proposal_submitted'),
    url(r'^change_password/$','socialperks.views.changePassword'),
    url(r'^change_email/$','socialperks.views.changeEmail'),
    url(r'^load_notification_count/$','socialperks.views.load_notification_count'),
    url(r'^load_notifications/$','socialperks.views.load_notifications'),
    url(r'^search/$','socialperks.views.search'),
    url(r'^terms/$','socialperks.views.terms'),
    url(r'^charge_stripe/$','socialperks.views.charge_stripe'),
    #
    url(r'^$','socialperks.views.home'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
