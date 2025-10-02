from django import template


register = template.Library()

@register.filter
def available_count(book):
    return book.copies.filter(status="available").count()