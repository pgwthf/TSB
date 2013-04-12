from django.core.management.base import NoArgsCommand, make_option

from pricemanager.models import Stock, Price

#from optparse import make_option

class Command(NoArgsCommand):

    help = "Whatever you want to print here"

    option_list = NoArgsCommand.option_list + (make_option('--verbose', 
            action='store_true'),)

    def handle_noargs(self, **options):
        
#TODO: verbose option on (any) function that can be called
# options for downloading yahoo, retry=true/false

        Price.download_prices_today(currency=Stock.US_DOLLAR, num_retries=0)
