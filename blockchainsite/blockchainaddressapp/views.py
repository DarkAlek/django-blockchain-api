import json
import urllib3
import datetime
import pytz
import base64
import qrcode
from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic import ListView
from django.db.models import Sum
from .models import Address, Transaction

# Create your views here.

MAX_SITES_COUNT = 101

class IndexView(TemplateView):
    template_name = "index.html"

class AddressView(ListView):
    template_name = "address.html"
    context_object_name = 'transactions'
    model = Transaction

    def get_context_data(self, **kwargs):
        context = super(AddressView, self).get_context_data(**kwargs)
        if context['transactions'] is not None:
            context['count'] = context['transactions'].count()
            context['sum'] = context['transactions'].aggregate(Sum('value'))['value__sum']
            positive_sum = context['transactions'].filter(value__gt=0).aggregate(Sum('value'))['value__sum']
            negative_sum = context['transactions'].filter(value__lt=0).aggregate(Sum('value'))['value__sum']
            print(positive_sum, negative_sum)
            if positive_sum is not None and negative_sum is not None:
                context['total_value'] = positive_sum - negative_sum
            elif positive_sum is not None:
                context['total_value'] = positive_sum
            elif negative_sum is not None:
                context['total_value'] = -negative_sum
            else:
                context['total_value'] = 0
            return context

    def get_queryset(self):
        address_param = self.kwargs['address_id']
        datetime_start = None
        datetime_end = None
        start_date = self.request.GET.get('start', None)
        end_date = self.request.GET.get('end', None)
        if start_date is not None:
            try:
                datetime_start = datetime.date(*(int(x) for x in start_date.split('-')))
            except ValueError:
                datetime_start = None
        if end_date is not None:
            try:
                datetime_end = datetime.date(*(int(x) for x in end_date.split('-'))) + datetime.timedelta(days=1)
            except ValueError:
                datetime_end = None
        #print(start_date.split('-'), end_date.split('-'))
        queryset = Transaction.objects.filter(address__address=address_param)
        if len(queryset) != 0:
            queryset = self.filter_date(queryset, datetime_start, datetime_end)
            return queryset
        else:
            queryset = self.get_transactions(address_param)
            queryset = self.filter_date(queryset, datetime_start, datetime_end)
            return queryset

    def get_transactions(self, address):
        db_address = Address(address=address)
        db_address.save()
        http = urllib3.PoolManager()
        r = http.request('GET', 'https://blockchain.info/rawaddr/' + address)
        if r.status!=200:
            return
        transactions = json.loads(r.data.decode('utf-8'))['txs']
        it = 0
        for site in range(1, MAX_SITES_COUNT):
            it += 1
            if r.status==200 and len(transactions)!=0:
                #here calculations
                for t in transactions:
                    hash_id = t['hash']
                    date = datetime.datetime.utcfromtimestamp(t['time'])
                    value = self.count_value(t, address)
                    db_transaction = Transaction(address=db_address, hash_id=hash_id, value=value, date=date)
                    db_transaction.save()
                    print(hash_id, date, value/100000000)
                url =  'https://blockchain.info/rawaddr/' + address + '?offset=' + str(site*50)
                print(url)
                if len(transactions) < 50:
                    break
                r = http.request('GET', url)
                transactions = json.loads(r.data.decode('utf-8'))['txs']
            else:
                break 
        return Transaction.objects.filter(address__address=address)

    def count_value(self, transaction, address):
        inputs = transaction['inputs']
        out = transaction['out']
        address_inputs = [x['prev_out']['addr'] for x in inputs]

        if address in address_inputs:
            amount = sum([x['value'] for x in out if x['value'] != 0 and x['addr'] != address])
            total_input = sum([x['prev_out']['value'] for x in inputs]) 
            total_output  = sum([x['value'] for x in out])
            value = -(amount + total_input - total_output)
        else:
            amount = sum([x['value'] for x in out if x['value'] != 0 and x['addr'] == address])
            value = amount   
        return value
    
    def filter_date(self, queryset, start_date, end_date):
        if start_date is not None or end_date is not None:
            if start_date is not None and end_date is not None:
                return queryset.filter(date__range=[start_date, end_date])
            elif start_date is not None:
                return queryset.filter(date__gte=start_date)
            else:
                return queryset.filter(date__lte=end_date)
        else:
            return queryset
        

class QrCodeView(TemplateView):
    template_name = "qrcode.html"

    def get_context_data(self, **kwargs):
        context = super(QrCodeView, self).get_context_data(**kwargs)
        address = self.request.GET.get('address', None)
        if address is not None:
            img = qrcode.make(address)
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue())
            context['qrcode'] =  img_str.decode('utf-8')
            return context
