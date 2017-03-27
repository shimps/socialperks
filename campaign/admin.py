from django.contrib import admin
from models import Campaign,Category, FinalProposal,CashOffer, ProductOffer, DiscountOffer, Proposal, Message,PaymentJob

# This class prepopulates the model admin page with a slugfield
class CampaignAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':('title',)}

# Register your models here.
admin.site.register(Campaign)
admin.site.register(CashOffer)
admin.site.register(ProductOffer)
admin.site.register(DiscountOffer)
admin.site.register(Proposal)
admin.site.register(Message)
admin.site.register(Category)
admin.site.register(PaymentJob)
admin.site.register(FinalProposal)
