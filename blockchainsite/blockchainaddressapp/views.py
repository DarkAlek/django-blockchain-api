import json
import urllib3
import datetime
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic import ListView
from .models import Address, Transaction

# Create your views here.

MAX_SITES_COUNT = 101

class IndexView(TemplateView):
    template_name = "index.html"

class AddressView(ListView):
    template_name = "address.html"
    context_object_name = 'transactions'
    model = Transaction

    def get_queryset(self):
        address_param = self.kwargs['address_id']  
        queryset = Transaction.objects.filter(address__address=address_param)
        if len(queryset) != 0:
            return queryset
        else:
            queryset = self.get_transactions(self.kwargs['address_id'])
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
                    date = datetime.datetime.fromtimestamp(t['time'])
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
            amount = sum([x['value'] for x in out if  x['addr'] != address])
            total_input = sum([x['prev_out']['value'] for x in inputs]) 
            total_output  = sum([x['value'] for x in out])
            value = -(amount + total_input - total_output)
        else:
            amount = sum([x['value'] for x in out if x['addr'] == address])
            value = amount   
        return value