from django import template
from django.template.defaultfilters import register

register = template.Library()

@register.filter
def get_obj_attr(obj, attr):
    return getattr(obj, attr)

@register.filter(name='dict_key')
def dict_key(d, k):
    return d[k]

@register.filter(name='money')
def money(value):
    """1234.5 -> '1,234.50'"""
    if value is None or value == '':
        return ''
    return '{:,.2f}'.format(value)

@register.filter(name='signed_money')
def signed_money(value):
    """Like money, but always shows the sign: '+12.00', '-3.50', '0.00'."""
    if value is None or value == '':
        return ''
    if value == 0:
        return '0.00'
    return '{:+,.2f}'.format(value)
