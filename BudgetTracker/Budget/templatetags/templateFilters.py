from django import template
from django.template.defaultfilters import register

register = template.Library()

@register.filter
def get_obj_attr(obj, attr):
    return getattr(obj, attr)

@register.filter(name='dict_key')
def dict_key(d, k):
    return d[k]
