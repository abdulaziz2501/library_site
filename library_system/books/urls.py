# books/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Asosiy sahifalar
    path('', views.home, name='home'),
    path('books/', views.book_list, name='book_list'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),

    # Kategoriyalar
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:pk>/', views.category_detail, name='category_detail'),

    # Mualliflar
    path('authors/', views.author_list, name='author_list'),
    path('authors/<int:pk>/', views.author_detail, name='author_detail'),

    # Keladigan kitoblar
    path('incoming/', views.incoming_books, name='incoming_books'),

    # Statistika
    path('statistics/', views.statistics, name='statistics'),

    # Kitob olish/qaytarish
    path('books/<int:pk>/borrow/', views.borrow_book, name='borrow_book'),
    path('borrow/<int:record_id>/return/', views.return_book, name='return_book'),
    path('borrow-history/', views.borrow_history, name='borrow_history'),
]