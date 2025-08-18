# ovoj fajl pretstavuva dokument kade se staveni url linkovite koi vodat do view funkciite vo views.py
# sekoja funkcija view vo views.py more da ima link vo tuka url.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

from .views import custom_logout, remove_from_list, get_store_products, stats_view

# from .views import test_db_connection
# prethodnoto znaci deka od momentalniot folder (main) go vnesuvame views.py
urlpatterns = [
    path("", views.home, name="home"),
    # path("v1/",views.v1,name="v1"),
    # path("test-db/",test_db_connection),
    # path("base/", views.base,name="home"),
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
    path('remove-from-list/<int:item_id>/', remove_from_list, name='remove_from_list'),
    path('get-store-products/', get_store_products, name='get_store_products'),
    path('statistics/', stats_view, name='stats'),
    path('nearby-stores/', views.nearby_stores_view, name='nearby_stores'),
    # path("recepies/", views.recipe_generator, name="recipe_generator"),
    path('fridge-recipes/', views.fridge_recipes, name='fridge_recipes'),
    # path('admin/', admin.site.urls),
    path('search-suggestions/', views.search_suggestions, name='search_suggestions'),

    path('header/', views.header, name='header'),
    path('toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', views.favorites_list, name='favorites_list'),
    # path('profile/', views.profile, name='profile'),
    path('get-favorites/', views.get_favorites, name='get_favorites'),

]
# prethodnoto znaci deka koga odime na pocetna strana nema nisto "" i ne nosi na funkcijata
# vo view index imenuvana kako index. Tuka ke se otvori def index(response) i ke pokaze "Tech with tim"
