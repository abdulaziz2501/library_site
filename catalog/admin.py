from django.contrib import admin
from .models import Author, Category, Book, BookCopy, Borrow, Review


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name")
    search_fields = ("first_name", "last_name")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


class BookCopyInline(admin.TabularInline):
    model = BookCopy
    extra = 1


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "year")
    list_filter = ("author", "categories")
    search_fields = ("title", "isbn")
    filter_horizontal = ("categories",)
    inlines = [BookCopyInline]


@admin.register(Borrow)
class BorrowAdmin(admin.ModelAdmin):
    list_display = ("user", "copy", "borrowed_at", "due_date", "returned_at")
    list_filter = ("borrowed_at", "returned_at")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("book", "user", "rating", "created_at")
    list_filter = ("rating",)