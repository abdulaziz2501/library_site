from django.urls import path
from . import views


app_name = "catalog"


urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("books/", views.BookListView.as_view(), name="book_list"),
    path("books/<int:pk>/", views.BookDetailView.as_view(), name="book_detail"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("borrow/<int:copy_id>/", views.borrow_copy, name="borrow_copy"),
    path("return/<int:borrow_id>/", views.return_copy, name="return_copy"),
    path("profile/", views.profile, name="profile"),
]