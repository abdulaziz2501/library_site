from django.conf import settings
from django.db import models
from django.urls import reverse


class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)


    class Meta:
        ordering = ["last_name", "first_name"]


    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)


    class Meta:
        ordering = ["name"]


    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.PROTECT)
    categories = models.ManyToManyField(Category, blank=True)
    description = models.TextField(blank=True)
    isbn = models.CharField(max_length=13, blank=True)
    cover = models.ImageField(upload_to="covers/", blank=True, null=True)
    year = models.PositiveIntegerField(blank=True, null=True)


    def __str__(self):
        return self.title


    def get_absolute_url(self):
        return reverse("catalog:book_detail", args=[self.pk])


class BookCopy(models.Model):
    AVAILABLE = "available"
    BORROWED = "borrowed"
    STATUS_CHOICES = [
    (AVAILABLE, "Available"),
    (BORROWED, "Borrowed"),
    ]


    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="copies")
    barcode = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=AVAILABLE)


    def __str__(self):
        return f"{self.book.title} — {self.barcode} ({self.status})"


class Borrow(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    copy = models.ForeignKey(BookCopy, on_delete=models.PROTECT)
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    returned_at = models.DateTimeField(blank=True, null=True)


    class Meta:
        ordering = ["-borrowed_at"]


    def __str__(self):
        return f"{self.user} → {self.copy}"


class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=5)
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ["-created_at"]


    def __str__(self):
        return f"{self.book} — {self.user} ({self.rating})"