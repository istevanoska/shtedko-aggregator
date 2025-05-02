from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

from .views import custom_logout

urlpatterns = [
    path("", views.home, name="home"),
    path("home/", views.home, name="home"),
    path("products/", views.product_list, name="product_list"),
    path('login/', auth_views.LoginView.as_view(template_name='main/login.html'), name='login'),
    path('logout/', custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('lists/', views.view_lists, name='view_lists'),
    path('lists/create/', views.create_list, name='create_list'),
    path('lists/<int:list_id>/', views.view_list, name='view_list'),
    path('lists/<int:list_id>/delete/', views.delete_list, name='delete_list'),
    path('list-item/<int:item_id>/remove/', views.remove_from_list, name='remove_from_list'),
    path('toggle-list-item/', views.toggle_list_item, name='toggle_list_item'),
    path('add-to-list/', views.add_to_list, name='add_to_list'),
    path('api/lists/', views.get_user_lists, name='get_user_lists'),
    path('api/lists/add-product/', views.add_to_list, name='add_to_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('remove-item/<int:item_id>/', views.remove_item, name='remove_item'),
    # urls.py
    path('get-user-lists/', views.get_user_lists, name='get_user_lists'),



]
