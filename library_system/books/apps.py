# from django.apps import AppConfig
#
#
# class BooksConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'books'


# books/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Author, Publisher, Book, IncomingBooks, BorrowRecord


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'book_count', 'created_at']
    search_fields = ['name']

    def book_count(self, obj):
        return obj.book_count()

    book_count.short_description = 'Kitoblar soni'


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name']
    search_fields = ['first_name', 'last_name']


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ['name', 'country']
    search_fields = ['name']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'get_authors', 'category', 'inventory_number',
                    'available_copies', 'total_copies', 'status', 'shelf_location']
    list_filter = ['category', 'status', 'language', 'publication_year']
    search_fields = ['title', 'isbn', 'inventory_number', 'authors__first_name', 'authors__last_name']
    filter_horizontal = ['authors']
    readonly_fields = ['added_date', 'updated_date', 'cover_preview']

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('title', 'authors', 'category', 'publisher')
        }),
        ('Qo\'shimcha ma\'lumotlar', {
            'fields': ('isbn', 'publication_year', 'pages', 'language', 'description')
        }),
        ('Muqova', {
            'fields': ('cover_image', 'cover_preview')
        }),
        ('Inventarizatsiya', {
            'fields': ('inventory_number', 'shelf_location', 'total_copies',
                       'available_copies', 'status')
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('added_by', 'added_date', 'updated_date'),
            'classes': ('collapse',)
        }),
    )

    def get_authors(self, obj):
        return obj.get_authors_display()

    get_authors.short_description = 'Mualliflar'

    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" width="150" />', obj.cover_image.url)
        return "Rasm yo'q"

    cover_preview.short_description = 'Muqova'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(IncomingBooks)
class IncomingBooksAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'quantity', 'expected_date',
                    'is_arrived', 'status_badge']
    list_filter = ['is_arrived', 'category', 'expected_date']
    search_fields = ['title', 'supplier']
    date_hierarchy = 'expected_date'

    def status_badge(self, obj):
        if obj.is_arrived:
            return format_html('<span style="color: green;">✓ Keldi</span>')
        elif obj.is_overdue():
            return format_html('<span style="color: red;">⚠ Kechikdi</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Kutilmoqda</span>')

    status_badge.short_description = 'Holat'


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ['book', 'borrower_name', 'borrower_phone', 'borrow_date',
                    'due_date', 'is_returned', 'status_badge']
    list_filter = ['is_returned', 'borrow_date']
    search_fields = ['book__title', 'borrower_name', 'borrower_phone']
    date_hierarchy = 'borrow_date'

    def status_badge(self, obj):
        if obj.is_returned:
            return format_html('<span style="color: green;">✓ Qaytarildi</span>')
        elif obj.is_overdue():
            return format_html('<span style="color: red;">⚠ Muddati o\'tgan</span>')
        else:
            return format_html('<span style="color: blue;">📖 O\'qilmoqda</span>')

    status_badge.short_description = 'Holat'