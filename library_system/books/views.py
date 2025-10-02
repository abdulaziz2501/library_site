# books/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Book, Category, Author, IncomingBooks, BorrowRecord


def home(self):
    """Bosh sahifa"""
    # Statistika
    total_books = Book.objects.count()
    total_categories = Category.objects.count()
    available_books = Book.objects.filter(status='available').count()
    borrowed_books = BorrowRecord.objects.filter(is_returned=False).count()

    # Eng ko'p kitoblar bo'lgan kategoriyalar
    top_categories = Category.objects.annotate(
        book_count=Count('book')
    ).order_by('-book_count')[:6]

    # Yangi qo'shilgan kitoblar
    recent_books = Book.objects.all()[:8]

    # Keladigan kitoblar
    upcoming_books = IncomingBooks.objects.filter(
        is_arrived=False,
        expected_date__gte=timezone.now().date()
    ).order_by('expected_date')[:5]

    context = {
        'total_books': total_books,
        'total_categories': total_categories,
        'available_books': available_books,
        'borrowed_books': borrowed_books,
        'top_categories': top_categories,
        'recent_books': recent_books,
        'upcoming_books': upcoming_books,
    }
    return render(request, 'books/home.html', context)


def book_list(request):
    """Barcha kitoblar ro'yxati"""
    books = Book.objects.all()
    categories = Category.objects.all()

    # Qidiruv
    search_query = request.GET.get('search', '')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(authors__first_name__icontains=search_query) |
            Q(authors__last_name__icontains=search_query) |
            Q(isbn__icontains=search_query)
        ).distinct()

    # Kategoriya bo'yicha filter
    category_id = request.GET.get('category')
    if category_id:
        books = books.filter(category_id=category_id)

    # Holat bo'yicha filter
    status = request.GET.get('status')
    if status:
        books = books.filter(status=status)

    # Til bo'yicha filter
    language = request.GET.get('language')
    if language:
        books = books.filter(language=language)

    # Saralash
    sort_by = request.GET.get('sort', '-added_date')
    books = books.order_by(sort_by)

    context = {
        'books': books,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_status': status,
        'selected_language': language,
    }
    return render(request, 'books/book_list.html', context)


def book_detail(request, pk):
    """Kitob tafsilotlari"""
    book = get_object_or_404(Book, pk=pk)

    # O'xshash kitoblar
    related_books = Book.objects.filter(
        category=book.category
    ).exclude(pk=book.pk)[:4]

    # Olish tarixi
    borrow_history = BorrowRecord.objects.filter(
        book=book
    ).order_by('-borrow_date')[:5]

    context = {
        'book': book,
        'related_books': related_books,
        'borrow_history': borrow_history,
    }
    return render(request, 'books/book_detail.html', context)


def category_list(request):
    """Kategoriyalar ro'yxati"""
    categories = Category.objects.annotate(
        book_count=Count('book')
    ).order_by('name')

    context = {
        'categories': categories,
    }
    return render(request, 'books/category_list.html', context)


def category_detail(request, pk):
    """Kategoriya tafsilotlari"""
    category = get_object_or_404(Category, pk=pk)
    books = Book.objects.filter(category=category)

    # Saralash
    sort_by = request.GET.get('sort', 'title')
    books = books.order_by(sort_by)

    context = {
        'category': category,
        'books': books,
    }
    return render(request, 'books/category_detail.html', context)


def author_list(request):
    """Mualliflar ro'yxati"""
    authors = Author.objects.annotate(
        book_count=Count('book')
    ).order_by('last_name', 'first_name')

    context = {
        'authors': authors,
    }
    return render(request, 'books/author_list.html', context)


def author_detail(request, pk):
    """Muallif tafsilotlari"""
    author = get_object_or_404(Author, pk=pk)
    books = Book.objects.filter(authors=author)

    context = {
        'author': author,
        'books': books,
    }
    return render(request, 'books/author_detail.html', context)


def incoming_books(request):
    """Keladigan kitoblar"""
    # Kelgan kitoblar
    arrived_books = IncomingBooks.objects.filter(
        is_arrived=True
    ).order_by('-arrived_date')[:10]

    # Kutilayotgan kitoblar
    pending_books = IncomingBooks.objects.filter(
        is_arrived=False
    ).order_by('expected_date')

    # Kechikkan kitoblar
    overdue_books = pending_books.filter(
        expected_date__lt=timezone.now().date()
    )

    context = {
        'arrived_books': arrived_books,
        'pending_books': pending_books,
        'overdue_books': overdue_books,
    }
    return render(request, 'books/incoming_books.html', context)


def statistics(request):
    """Statistika sahifasi"""
    # Umumiy statistika
    stats = {
        'total_books': Book.objects.count(),
        'total_authors': Author.objects.count(),
        'total_categories': Category.objects.count(),
        'available_books': Book.objects.filter(status='available').count(),
        'borrowed_books': BorrowRecord.objects.filter(is_returned=False).count(),
        'overdue_books': BorrowRecord.objects.filter(
            is_returned=False,
            due_date__lt=timezone.now().date()
        ).count(),
    }

    # Kategoriya bo'yicha kitoblar
    category_stats = Category.objects.annotate(
        book_count=Count('book')
    ).order_by('-book_count')

    # Til bo'yicha kitoblar
    language_stats = Book.objects.values('language').annotate(
        count=Count('id')
    ).order_by('-count')

    # Oxirgi 30 kunda qo'shilgan kitoblar
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_additions = Book.objects.filter(
        added_date__gte=thirty_days_ago
    ).count()

    context = {
        'stats': stats,
        'category_stats': category_stats,
        'language_stats': language_stats,
        'recent_additions': recent_additions,
    }
    return render(request, 'books/statistics.html', context)


@login_required
def borrow_book(request, pk):
    """Kitob olish"""
    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        if book.available_copies > 0:
            borrower_name = request.POST.get('borrower_name')
            borrower_phone = request.POST.get('borrower_phone')
            borrower_id = request.POST.get('borrower_id')
            due_date = request.POST.get('due_date')
            notes = request.POST.get('notes', '')

            # Kitob olish yozuvi yaratish
            BorrowRecord.objects.create(
                book=book,
                borrower_name=borrower_name,
                borrower_phone=borrower_phone,
                borrower_id=borrower_id,
                due_date=due_date,
                notes=notes,
            )

            # Mavjud nusxalarni kamaytirish
            book.available_copies -= 1
            if book.available_copies == 0:
                book.status = 'borrowed'
            book.save()

            messages.success(request, f'"{book.title}" kitobi muvaffaqiyatli berildi!')
            return redirect('book_detail', pk=book.pk)
        else:
            messages.error(request, 'Bu kitob hozir mavjud emas!')

    context = {
        'book': book,
        'default_due_date': (timezone.now() + timedelta(days=14)).date(),
    }
    return render(request, 'books/borrow_book.html', context)


@login_required
def return_book(request, record_id):
    """Kitobni qaytarish"""
    record = get_object_or_404(BorrowRecord, pk=record_id)

    if not record.is_returned:
        record.is_returned = True
        record.return_date = timezone.now().date()
        record.save()

        # Mavjud nusxalarni oshirish
        book = record.book
        book.available_copies += 1
        if book.available_copies > 0:
            book.status = 'available'
        book.save()

        messages.success(request, f'"{book.title}" kitobi qaytarildi!')

    return redirect('book_detail', pk=record.book.pk)


def borrow_history(request):
    """Olish tarixi"""
    # Hozir olingan kitoblar
    current_borrows = BorrowRecord.objects.filter(
        is_returned=False
    ).order_by('due_date')

    # Muddati o'tgan kitoblar
    overdue_borrows = current_borrows.filter(
        due_date__lt=timezone.now().date()
    )

    # Qaytarilgan kitoblar
    returned_borrows = BorrowRecord.objects.filter(
        is_returned=True
    ).order_by('-return_date')[:20]

    context = {
        'current_borrows': current_borrows,
        'overdue_borrows': overdue_borrows,
        'returned_borrows': returned_borrows,
    }
    return render(request, 'books/borrow_history.html', context)

