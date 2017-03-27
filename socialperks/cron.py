from django_cron import CronJobBase, Schedule
from admincontact.models import Crontask

class PrintEveryMinute(CronJobBase):

    RUN_EVERY_MINS = 1
    schedule=Schedule(run_every_mins=RUN_EVERY_MINS)
    code="socialperks.my_cron_job"


    def do(self):

        print"Running"
        
        if Crontask.objects.all().count()==0:
            Crontask.objects.create(number=1)
        else:
            crontask = Crontask.objects.all()[:1].get()
            crontask.number+=1
            crontask.save()
