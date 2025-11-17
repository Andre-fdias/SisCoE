from django import template
import datetime
from dateutil.relativedelta import relativedelta

register = template.Library()


@register.filter
def format_date(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.strftime("%d/%m/%Y - %H:%M")
    return value


@register.filter
def add_years(value, years):
    try:
        if isinstance(value, str):
            value = datetime.datetime.strptime(value, "%Y-%m-%d").date()
        return value + relativedelta(years=int(years))
    except (ValueError, TypeError):
        return value


@register.simple_tag
def get_restricao_fields():
    return [
        field
        for field in CatEfetivo._meta.get_fields()
        if field.name.startswith("restricao_")
    ]


@register.filter
def first_active(categorias):
    return categorias.filter(ativo=True).first()


@register.filter
def map_attr(items, attr_name):
    return [getattr(item, attr_name) for item in items]


@register.filter(name="filter_prontidao")
def filter_prontidao(queryset, value):
    return queryset.filter(detalhassituacao__prontidao=value)
