from django import template
import datetime

register = template.Library()

@register.filter
def format_date(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.strftime('%d/%m/%Y - %H:%M')
    return value


@register.filter
def add_years(value, years):
    try:
        if isinstance(value, str):
            value = datetime.strptime(value, "%Y-%m-%d").date()
        return value + relativedelta(years=int(years))
    except (ValueError, TypeError):
        return value
