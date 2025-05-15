import json
from datetime import datetime
from django.shortcuts import render
from geopy.distance import geodesic

from .models import Products2
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db import connection
from django.utils import timezone
from django.db.models import F
from django.db.models import Case, When, DecimalField
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegisterForm
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ShoppingList, ShoppingListItem
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import ShoppingList, ShoppingListItem, Products2
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from main.models import User
from .utils.similarity import get_similar_products
from .utils.similarity import get_similar_products
from django.db.models import F
from django.db.models.functions import Lower, Trim
from django.shortcuts import render, get_object_or_404
from django.shortcuts import render
from django.db.models import Q
from datetime import datetime, time
from difflib import get_close_matches
from django.shortcuts import render
from geopy.distance import geodesic





# Create your views here.

# sega kreirame funkcija koja ke pretstavuva nas prv view
# def index(response):
#     return HttpResponse("<h1>Tech with Tim!</h1>")
# def v1(response):
#     return HttpResponse("<h1>View 1!</h1>")
# #testiranje na connekcija do db
# def test_db_connection(request):
#     try:
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT VERSION();")
#             db_version = cursor.fetchone()
#         return HttpResponse(f"Connected to MySQL, version: {db_version[0]}")
#     except Exception as e:
#         return HttpResponse(f"Database connection failed: {str(e)}")

def index(response):
    return render(response, "main/base.html")


from django.db.models import Q, F, Count
from django.db.models.functions import Lower

from django.utils import timezone
from django.db.models import Q


def home(response):
    categories = Products2.objects.exclude(
        Q(category__isnull=True) | Q(category__exact='')
    ).values_list('category', flat=True).distinct()

    discounted_products = Products2.objects.filter(
        popust=True
    ).filter(
        Q(popust_date__gte=timezone.now().date()) | Q(popust_date__isnull=True)
    ).order_by('-price')[:12]

    CATEGORY_EMOJIS = {
        "Млеко": "🥛",
        "Хлеб": "🍞",
        "Овошје": "🍎",
        "Зеленчук": "🥦",
        "Месо": "🍖",
        "Козметика": "🧴",
        "Слатки": "🍫",
        "Јајца": "🥚",
        "Масло": "🛢️",
        "Брашно": "🌾",
    }

    discounted_products = Products2.objects.filter(
        popust=True
    ).order_by('-price')[:12]  # Removed the date filter here

    stores = Products2.objects.filter(popust=True).values_list('store', flat=True).distinct()

    stores_with_products = []
    for store in stores:
        cleaned = store.strip()

        # Debugging step: break down the query into parts to inspect the data
        store_filtered = Products2.objects.filter(store__iexact=cleaned)
        popust_filtered = store_filtered.filter(popust=True)

        # Debugging output: Check the number of products for each store
        print(f"Store: {cleaned}")
        print(f"Products after store filter: {store_filtered.count()}")
        print(f"Products after popust filter: {popust_filtered.count()}")

        # Fetch products for the store
        products = popust_filtered.order_by('-price')[:3]  # No date filter here

        # Debugging output: Check the actual products being fetched
        if not products:
            print(f"No discounted products for {cleaned}")
        else:
            print(f"Found {len(products)} products for {cleaned}")

        stores_with_products.append({
            'name': cleaned,
            'products': list(products),  # <--- Important!
            'count': products.count()
        })

    context = {
        'categories': categories,
        'discounted_products': discounted_products,
        'category_emojis': CATEGORY_EMOJIS,
        'stores_with_products': stores_with_products
    }

    return render(response, 'main/base.html', context)

# def base(response):
#     return render(response, "main/base.html")
def product_list(request):
    products = Products2.objects.all()
    query = request.GET.get("q")
    products = Products2.objects.all()

    if query:
        products = products.filter(name__icontains=query)

    # Search by name only
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(name__icontains=search_query)

    # Category filter
    selected_categories = request.GET.getlist('category')
    if selected_categories:
        products = products.filter(category__in=selected_categories)

    show_active_discounts = request.GET.get('active_discounts')
    if show_active_discounts:
        products = products.filter(
            popust=True,
            popust_date__gte=timezone.now().date()
        )

    max_price = request.GET.get('max_price')
    if max_price and max_price.isdigit():
        products = products.filter(
            Q(popust=True, actual_price__lte=int(max_price)) |
            Q(popust=False, price__lte=int(max_price))
        )

    # Store filter
    selected_stores = request.GET.getlist('store')
    if selected_stores:
        products = products.filter(store__in=selected_stores)

    sort = request.GET.get('sort', '')
    if sort == 'price_asc':
        products = products.annotate(
            effective_price=Case(
                When(popust=True, then='actual_price'),
                default='price',
                output_field=DecimalField()
            )
        ).order_by('effective_price')
    elif sort == 'price_desc':
        products = products.annotate(
            effective_price=Case(
                When(popust=True, then='actual_price'),
                default='price',
                output_field=DecimalField()
            )
        ).order_by('-effective_price')
    elif sort == 'name_asc':
        products = products.order_by('name')
    elif sort == 'name_desc':
        products = products.order_by('-name')
    elif sort == 'popular':
        products = products.order_by('-popularity')  # Assuming you have a popularity field
    elif sort == 'newest':
        products = products.order_by('-created_at')  # Assuming you have a created_at field

    show_discounted = request.GET.get('discounted')
    if show_discounted:
        products = products.filter(popust=True)

    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': Products2.objects.values_list('category', flat=True).distinct(),
        'selected_categories': selected_categories,
        'selected_max_price': max_price,
        'selected_stores': selected_stores,
        'selected_sort': sort,
        'search_query': search_query,
    }
    return render(request, 'main/product_list.html', context)


def product_catalog(request):
    products = Products2.objects.all()

    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query)
        )

    context = {
        'products': products,
        # your other context variables
    }
    return render(request, 'main/product_list.html', context)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # Redirect to your homepage
    else:
        form = RegisterForm()
    return render(request, 'main/register.html', {'form': form})


def custom_logout(request):
    logout(request)

    # Get the same context data as your home view
    categories = Products2.objects.exclude(
        Q(category__isnull=True) | Q(category__exact='')
    ).values_list('category', flat=True).distinct()

    discounted_products = Products2.objects.filter(
        popust=True
    ).filter(
        Q(popust_date__gte=timezone.now().date()) | Q(popust_date__isnull=True)
    ).order_by('-price')[:12]

    context = {
        'categories': categories,
        'discounted_products': discounted_products
    }

    return render(request, 'main/base.html', context)


@login_required
def view_lists(request):
    user_lists = ShoppingList.objects.filter(user=request.user)
    return render(request, 'main/lists.html', {'user_lists': user_lists})


@login_required
def create_list(request):
    if request.method == 'POST':
        list_name = request.POST.get('list_name')
        if list_name:
            ShoppingList.objects.create(user=request.user, name=list_name)
            return redirect('view_lists')
    return redirect('view_lists')



@login_required
def view_list(request, list_id):
    shopping_list = get_object_or_404(ShoppingList, id=list_id, user=request.user)
    items = ShoppingListItem.objects.filter(shopping_list=shopping_list)

    # Debugging: Log the items being passed to the template
    print(f"Items in list {shopping_list.name}: {items}")

    return render(request, 'main/list_detail.html', {'shopping_list': shopping_list, 'items': items})

@login_required
def delete_list(request, list_id):
    shopping_list = get_object_or_404(ShoppingList, id=list_id, user=request.user)
    if request.method == 'POST':
        shopping_list.delete()
    return redirect('view_lists')


@login_required
@require_POST
def remove_from_list(request, item_id):
    list_item = get_object_or_404(ShoppingListItem, id=item_id, list__user=request.user)
    list_item.delete()
    return redirect('view_list', list_id=list_item.list.id)


@login_required
@csrf_exempt
def toggle_list_item(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        completed = request.POST.get('completed') == 'true'

        list_item = get_object_or_404(ShoppingListItem, id=item_id, list__user=request.user)
        list_item.completed = completed
        list_item.save()

        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


# @csrf_exempt
# @require_POST
# def add_to_list(request):
#     product_id = request.POST.get('product_id')
#     list_id = request.POST.get('list_id')
#
#     try:
#         # Get or create the list item
#         item, created = ShoppingListItem.objects.get_or_create(
#             list_id=list_id,
#             product_id=product_id,
#             defaults={'quantity': 1}
#         )
#
#         if not created:
#             item.quantity += 1
#             item.save()
#
#         return JsonResponse({'success': True, 'message': 'Product added to list'})
#
#     except Exception as e:
#         return JsonResponse({'success': False, 'message': str(e)}, status=400)

@csrf_exempt
@require_POST
@login_required
def add_to_list(request):
    try:
        # Extract data from POST request
        data = json.loads(request.body)
        product_id = data.get('product_id')
        list_id = data.get('list_id')

        # Debugging: Log received values
        print(f"Product ID: {product_id}, List ID: {list_id}, User: {request.user}")

        # Validate inputs
        if not product_id or not list_id:
            return JsonResponse({'success': False, 'message': 'Missing product or list ID'}, status=400)

        # Fetch shopping list and product
        shopping_list = get_object_or_404(ShoppingList, id=list_id, user=request.user)
        product = get_object_or_404(Products2, id=product_id)

        # Debugging: Confirm the product and list are found
        print(f"Shopping List: {shopping_list}, Product: {product}")

        # Get or create the list item
        item, created = ShoppingListItem.objects.get_or_create(
            shopping_list=shopping_list,
            product=product,
            defaults={'quantity': 1}
        )

        # Check if item is created or updated
        if not created:
            item.quantity += 1
            item.save()

        # Debugging: Confirm the item was saved
        print(f"Item: {item}, Created: {created}")

        return JsonResponse({'success': True, 'message': 'Product added to list'})

    except Exception as e:
        print(f"Error: {e}")  # Log error details
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

def get_user_lists(request):
    if not request.user.is_authenticated:
        return JsonResponse({'lists': []})

    lists = ShoppingList.objects.filter(user=request.user).values('id', 'name')
    return JsonResponse({'lists': list(lists)})


def product_detail(request, product_id):
    product = get_object_or_404(Products2, id=product_id)

    # You can call your get_similar_products function here
    similar_products = get_similar_products(product.name, product.category)

    return render(request, 'main/product_detail.html', {
        'product': product,
        'similar_products': similar_products
    })
@login_required
@require_POST
@csrf_exempt  # Add this if you're still having CSRF issues during testing
def remove_from_list(request, item_id):
    try:
        list_item = get_object_or_404(ShoppingListItem, id=item_id, shopping_list__user=request.user)
        list_item.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def get_store_products(request):
    store = request.GET.get('store')
    if not store:
        return JsonResponse({'error': 'Store parameter missing'}, status=400)

    products = Products2.objects.filter(
        store=store,
        popust=True
    )

    products_data = [
        {
            'name': p.name,
            'price': str(p.price),
            'actual_price': str(p.actual_price),
            'image_url': p.image_url
        }
        for p in products
    ]

    return JsonResponse({'products': products_data})


from difflib import SequenceMatcher
from django.db import connection

from difflib import get_close_matches
from django.db import connection


def stats_view(request):
    store = request.GET.get('store', '').strip()
    query = request.GET.get('query', '').strip()
    selected_product = request.GET.get('selected_product', '').strip()

    # Get date range parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Validate and parse dates
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
    except (ValueError, TypeError):
        start_date_obj = None
        end_date_obj = None

    chart_data = []
    matched_name = None
    similar_products = []
    exact_match = False

    if store and query:
        with connection.cursor() as cursor:
            # 1. First try exact match
            cursor.execute("""
                SELECT DISTINCT name 
                FROM product_history2 
                WHERE store LIKE %s AND name = %s
                LIMIT 1
            """, ['%' + store + '%', query])
            exact_match_result = cursor.fetchone()

            if exact_match_result:
                matched_name = exact_match_result[0]
                exact_match = True
            else:
                # 2. Get all product names from this store
                cursor.execute("""
                    SELECT DISTINCT name FROM product_history2 
                    WHERE store LIKE %s
                """, ['%' + store + '%'])
                all_store_products = [row[0] for row in cursor.fetchall()]

                # 3. Find similar products using multiple approaches
                similar_products = []

                # Approach 1: Close string matches
                string_matches = get_close_matches(
                    query,
                    all_store_products,
                    n=10,
                    cutoff=0.3
                )

                # Approach 2: Products containing the search term
                query_lower = query.lower()
                contains_matches = [
                                       p for p in all_store_products
                                       if query_lower in p.lower()
                                   ][:10]

                all_matches = list(set(string_matches + contains_matches))

                if len(all_matches) < 5:
                    all_matches.extend([
                                           p for p in all_store_products
                                           if p not in all_matches
                                       ][:10 - len(all_matches)])

                similar_products = [(p, 1.0) for p in all_matches[:10]]

        if selected_product:
            matched_name = selected_product

        if matched_name:
            base_sql = """
                SELECT scraped_date, price 
                FROM product_history2 
                WHERE name = %s AND store LIKE %s
            """
            params = [matched_name, '%' + store + '%']

            # Add date range conditions if provided
            if start_date_obj and end_date_obj:
                base_sql += " AND scraped_date BETWEEN %s AND %s"
                params.extend([start_date_obj, end_date_obj])
            elif start_date_obj:
                base_sql += " AND scraped_date >= %s"
                params.append(start_date_obj)
            elif end_date_obj:
                base_sql += " AND scraped_date <= %s"
                params.append(end_date_obj)

            base_sql += " ORDER BY scraped_date ASC"

            with connection.cursor() as cursor:
                cursor.execute(base_sql, params)
                result = cursor.fetchall()
                chart_data = [{
                    'date': row[0].isoformat(),
                    'price': float(row[1])
                } for row in result]

    return render(request, 'main/stats.html', {
        'chart_data': chart_data,
        'matched_name': matched_name,
        'query': query,
        'store': store,
        'similar_products': similar_products,
        'exact_match': exact_match,
        'start_date': start_date,
        'end_date': end_date,
    })


STORE_LOCATIONS = {
    'Reptil': [
        {'name': 'Reptil 1', 'lat': 42.002, 'lon': 21.400},
        {'name': 'Reptil 2', 'lat': 42.005, 'lon': 21.410},
        {'name': 'Reptil 3', 'lat': 42.010, 'lon': 21.420},
    ],
    'Vero': [
        {'name': 'Vero 1', 'lat': 41.998, 'lon': 21.435},
        {'name': 'Vero 2', 'lat': 42.012, 'lon': 21.395},
    ],
    'Ramstore': [
        {'name': 'Ramstore 1', 'lat': 42.007, 'lon': 21.408},
        {'name': 'Ramstore 2', 'lat': 42.015, 'lon': 21.420},
    ]
}

def nearby_stores_view(request):
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    fuel_usage = request.GET.get('fuel_usage')
    selected_store = request.GET.get('store')

    if not latitude or not longitude or not fuel_usage or not selected_store:
        return render(request, 'main/nearby_stores.html', {'error': 'Missing parameters'})

    try:
        user_location = (float(latitude), float(longitude))
        fuel_usage = float(fuel_usage)
    except ValueError:
        return render(request, 'main/nearby_stores.html', {'error': 'Invalid input'})

    stores = [
        {'name': 'Reptil 1', 'lat': 42.003, 'lon': 21.406},
        {'name': 'Reptil 2', 'lat': 42.010, 'lon': 21.420},
        {'name': 'Reptil 3', 'lat': 42.005, 'lon': 21.400},
        {'name': 'Vero 1', 'lat': 42.007, 'lon': 21.410},
    ]

    nearby_stores = []
    for store in stores:
        print(f"Checking store: {store['name']}")
        if selected_store.lower() in store['name'].lower():
            store_location = (store['lat'], store['lon'])
            distance_km = geodesic(user_location, store_location).km
            fuel_needed = (fuel_usage / 100) * distance_km
            nearby_stores.append({
                'name': store['name'],
                'distance': distance_km,
                'fuel': fuel_needed
            })

    nearby_stores.sort(key=lambda x: x['distance'])

    context = {
        'nearby_stores': nearby_stores,
        'latitude': latitude,
        'longitude': longitude,
        'fuel_usage': fuel_usage,
        'selected_store': selected_store,
    }

    return render(request, 'main/nearby_stores.html', context)
