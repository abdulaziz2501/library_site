from datetime import date, timedelta
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView, TemplateView, CreateView

from .forms import SignUpForm, ReviewForm
from .models import Book, BookCopy, Borrow


class HomeView(TemplateView):
    template_name = "catalog/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Oxirgi qo‘shilgan 8 ta kitob (UZ: so‘nggi kitoblar)
        ctx["latest_books"] = (
            Book.objects
            .select_related("author")
            .prefetch_related("categories", "copies")
            .order_by("-id")[:8]
        )
        return ctx


class BookListView(ListView):
    model = Book


template_name = "catalog/book_list.html"
context_object_name = "books"
paginate_by = 12  # (UZ: sahifalash)


def get_queryset(self):
    qs = Book.objects.select_related("author").prefetch_related("categories", "copies")
    q = self.request.GET.get("q")
    category = self.request.GET.get("category")
    if q:
        qs = qs.filter(title__icontains=q)
    if category:
        qs = qs.filter(categories__name__iexact=category)
    return qs.distinct()


class BookDetailView(DetailView):
    model = Book
    template_name = "catalog/book_detail.html"
    context_object_name = "book"


def get_context_data(self, **kwargs):
    ctx = super().get_context_data(**kwargs)
    ctx["review_form"] = ReviewForm()
    return ctx


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "registration/signup.html"


    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Welcome! Account created.")
        return redirect("catalog:home")


@login_required
def borrow_copy(request, copy_id):
    copy = get_object_or_404(BookCopy, pk=copy_id)
    if copy.status == BookCopy.BORROWED:
        messages.error(request, "This copy is already borrowed.")
        return redirect(copy.book.get_absolute_url())
    # Simple 14-day loan
    Borrow.objects.create(user=request.user, copy=copy, due_date=date.today() + timedelta(days=14))
    copy.status = BookCopy.BORROWED
    copy.save(update_fields=["status"])
    messages.success(request, "Borrowed successfully. Due in 14 days.")
    return redirect("catalog:profile")


@login_required
def return_copy(request, borrow_id):
    br = get_object_or_404(Borrow, pk=borrow_id, user=request.user, returned_at__isnull=True)
    br.returned_at = date.today()
    br.save(update_fields=["returned_at"])
    copy = br.copy
    copy.status = BookCopy.AVAILABLE
    copy.save(update_fields=["status"])
    messages.success(request, "Returned. Thank you!")
    return redirect("catalog:profile")


@login_required
def profile(request):
    active_loans = Borrow.objects.select_related("copy__book").filter(user=request.user, returned_at__isnull=True)
    history = Borrow.objects.select_related("copy__book").filter(user=request.user, returned_at__isnull=False)[:20]


    # Handle review submit from detail page
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.book_id = int(request.POST.get("book_id"))
            review.save()
            messages.success(request, "Review added.")
            return redirect("catalog:profile")
    return render(request, "catalog/profile.html", {"active_loans": active_loans, "history": history})