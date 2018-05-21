from datetime import datetime
from django import template

register = template.Library()

@register.filter(name='btc_human_read')
def btc_human_read(value):
    return '%f' % (value/100000000) + ' BTC'

@register.filter(name='data_format')
def data_format(value):
    value = str(value)
    return value[:-6]