#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
# from catalog.models import *
#
#
# a = Author.objects.create(first_name="George", last_name="Orwell")
# c = Category.objects.create(name="Dystopia")
# b = Book.objects.create(title="1984", author=a, description="Classic novel", isbn="9780451524935", year=1949)
# b.categories.add(c)
# BookCopy.objects.create(book=b, barcode="C1984-001")
# BookCopy.objects.create(book=b, barcode="C1984-002")

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_site.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
