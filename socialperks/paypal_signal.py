from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received

def money_received(sender, **kwargs):
    print "\nIPN call\n"
    ipn_obj = sender
    if ipn_obj.payment_status==ST_PP_COMPLETED:

        if ipn.obj.receiver_email!="smutangama1-facilitator@gmail.com":
            print "This payment isn't valid\n"
            return

    else:
            pass

valid_ipn_received.connect(money_received)
