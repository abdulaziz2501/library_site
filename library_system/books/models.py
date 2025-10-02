# books/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    """Kitob kategoriyalari"""
    name = models.CharField(max_length=100, verbose_name="Kategoriya nomi")
    description = models.TextField(blank=True, verbose_name="Ta'rif")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ['name']

    def __str__(self):
        return self.name

    def book_count(self):
        """Bu kategoriyadagi kitoblar soni"""
        return self.book_set.count()


class Publisher(models.Model):
    """Nashriyotlar"""
    name = models.CharField(max_length=200, verbose_name="Nashriyot nomi")
    country = models.CharField(max_length=100, blank=True, verbose_name="Mamlakat")

    class Meta:
        verbose_name = "Nashriyot"
        verbose_name_plural = "Nashriyotlar"

    def __str__(self):
        return self.name


class Author(models.Model):
    """Mualliflar"""
    first_name = models.CharField(max_length=100, verbose_name="Ism")
    last_name = models.CharField(max_length=100, verbose_name="Familiya")
    bio = models.TextField(blank=True, verbose_name="Biografiya")

    class Meta:
        verbose_name = "Muallif"
        verbose_name_plural = "Mualliflar"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Book(models.Model):
    """Asosiy kitob modeli"""

    # Kitob holati
    STATUS_CHOICES = [
        ('available', 'Mavjud'),
        ('borrowed', 'Olingan'),
        ('reserved', 'Band qilingan'),
        ('maintenance', 'Ta\'mirda'),
    ]

    # Asosiy ma'lumotlar
    title = models.CharField(max_length=300, verbose_name="Kitob nomi")
    authors = models.ManyToManyField(Author, verbose_name="Mualliflar")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name="Kategoriya")
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Nashriyot")

    # Qo'shimcha ma'lumotlar
    isbn = models.CharField(max_length=13, unique=True, blank=True, null=True, verbose_name="ISBN")
    publication_year = models.IntegerField(verbose_name="Nashr yili")
    pages = models.IntegerField(blank=True, null=True, verbose_name="Sahifalar soni")
    language = models.CharField(max_length=50, default="O'zbek", verbose_name="Til")
    description = models.TextField(blank=True, verbose_name="Tavsif")

    # Rasm
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True, verbose_name="Muqova rasmi")

    # Inventarizatsiya
    inventory_number = models.CharField(max_length=50, unique=True, verbose_name="Inventar raqami")
    shelf_location = models.CharField(max_length=100, verbose_name="Javon joylashuvi")
    total_copies = models.IntegerField(default=1, verbose_name="Jami nusxalar")
    available_copies = models.IntegerField(default=1, verbose_name="Mavjud nusxalar")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name="Holat")

    # Sanalar
    added_date = models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan sana")
    updated_date = models.DateTimeField(auto_now=True, verbose_name="Yangilangan sana")
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Qo'shgan")

    class Meta:
        verbose_name = "Kitob"
        verbose_name_plural = "Kitoblar"
        ordering = ['-added_date']

    def __str__(self):
        return self.title

    def is_available(self):
        """Kitob mavjudligini tekshirish"""
        return self.available_copies > 0

    def get_authors_display(self):
        """Barcha mualliflarni ko'rsatish"""
        return ", ".join([str(author) for author in self.authors.all()])


class IncomingBooks(models.Model):
    """Yangi keladigan kitoblar"""
    title = models.CharField(max_length=300, verbose_name="Kitob nomi")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name="Kategoriya")
    quantity = models.IntegerField(verbose_name="Miqdori")
    expected_date = models.DateField(verbose_name="Kutilayotgan sana")
    supplier = models.CharField(max_length=200, blank=True, verbose_name="Ta'minotchi")
    notes = models.TextField(blank=True, verbose_name="Izohlar")
    is_arrived = models.BooleanField(default=False, verbose_name="Keldi")
    arrived_date = models.DateField(blank=True, null=True, verbose_name="Kelgan sana")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Keladigan kitob"
        verbose_name_plural = "Keladigan kitoblar"
        ordering = ['expected_date']

    def __str__(self):
        return f"{self.title} - {self.expected_date}"

    def is_overdue(self):
        """Muddati o'tganmi?"""
        return not self.is_arrived and self.expected_date < timezone.now().date()


class BorrowRecord(models.Model):
    """Kitob olish tarixi"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="Kitob")
    borrower_name = models.CharField(max_length=200, verbose_name="Oluvchi ismi")
    borrower_phone = models.CharField(max_length=20, verbose_name="Telefon")
    borrower_id = models.CharField(max_length=50, blank=True, verbose_name="ID/Passport")

    borrow_date = models.DateTimeField(default=timezone.now, verbose_name="Olingan sana")
    due_date = models.DateField(verbose_name="Qaytarish muddati")
    return_date = models.DateField(blank=True, null=True, verbose_name="Qaytarilgan sana")

    is_returned = models.BooleanField(default=False, verbose_name="Qaytarildi")
    notes = models.TextField(blank=True, verbose_name="Izohlar")

    class Meta:
        verbose_name = "Olish tarixi"
        verbose_name_plural = "Olish tarixi"
        ordering = ['-borrow_date']

    def __str__(self):
        return f"{self.borrower_name} - {self.book.title}"

    def is_overdue(self):
        """Muddati o'tganmi?"""
        if not self.is_returned:
            return timezone.now().date() > self.due_date
        return False