import datetime as dt
from collections import defaultdict

from django.http import HttpResponse
from pytz import timezone

from backend import settings


def rename_with_date(instance, filename):
    now = (dt.datetime.now(tz=timezone(settings.TIME_ZONE))
           .strftime(r'%Y_%m_%d-%H_%M_%S'))
    name, extension = filename.split('.')
    filename = name + f'_{now}.' + extension
    return f'recipes/{filename}'


def form_shop_list(queryset):
    to_buy_list = defaultdict(int)
    for note in queryset:
        to_buy_list[(note.ingredient.name,
                    note.ingredient.measurements_unit)] += note.amount
    final_string = ''
    for ingredient, amount in to_buy_list.items():
        final_string += f'{ingredient[0]} - {amount}({ingredient[1]})\n'
    return final_string


def add_file_to_response(data, content_type):
    response = HttpResponse(data, content_type=content_type)
    response['Content-Disposition'] = ('attachment;'
                                       ' filename="shop_list.txt"')
    return response
