from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from catalog.models import Author, Category, Book, BookCopy, Review

class Command(BaseCommand):
    help = "Seed a few demo books, copies, and a demo user."

    def handle(self, *args, **kwargs):
        User = get_user_model()
        u, _ = User.objects.get_or_create(username="abdulaziz", defaults={"email":"demo@example.com"})
        if not u.has_usable_password():
            u.set_password("0940418a"); u.save()

        fiction,_ = Category.objects.get_or_create(name="Fiction")
        dystopia,_ = Category.objects.get_or_create(name="Dystopia")
        cs,_ = Category.objects.get_or_create(name="Computer Science")

        orwell,_ = Author.objects.get_or_create(first_name="George", last_name="Orwell", defaults={"bio": "English novelist and essayist."})
        lee,_ = Author.objects.get_or_create(first_name="Harper", last_name="Lee", defaults={"bio": "American novelist."})
        pressman,_ = Author.objects.get_or_create(first_name="Roger S.", last_name="Pressman", defaults={"bio": "Software engineering author."})

        b1,_ = Book.objects.get_or_create(title="1984", author=orwell, defaults={"description":"A dystopian social science fiction novel.", "isbn":"9780451524935", "year":1949})
        b1.categories.add(fiction, dystopia)

        b2,_ = Book.objects.get_or_create(title="To Kill a Mockingbird", author=lee, defaults={"description":"Classic novel on justice and moral growth.", "isbn":"9780061120084", "year":1960})
        b2.categories.add(fiction)

        b3,_ = Book.objects.get_or_create(title="Software Engineering: A Practitioner's Approach", author=pressman, defaults={"description":"Foundational text on software engineering.", "isbn":"9780078022128", "year":2014})
        b3.categories.add(cs)

        for book, codes in [(b1, ["C1984-001","C1984-002"]), (b2, ["C-MOCK-001"]), (b3, ["C-SE-001","C-SE-002","C-SE-003"])]:
            for code in codes:
                BookCopy.objects.get_or_create(book=book, barcode=code)

        Review.objects.get_or_create(book=b1, user=u, rating=5, text="Chilling and timeless.")
        Review.objects.get_or_create(book=b2, user=u, rating=4, text="Powerful story and characters.")

        self.stdout.write(self.style.SUCCESS("Demo data seeded. Login: demo / demo12345"))
