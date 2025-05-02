import json
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.db.models import Case, When, DecimalField
from django.contrib.auth import login
from .forms import RegisterForm
from django.contrib.auth import logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import ShoppingList, ShoppingListItem, Products2
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from .utils.similarity import get_similar_products



def index(response):
    return render(response, "main/base.html")


def home(response):
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
            'discounted_products': discounted_products,
        }
        return render(response, 'main/base.html', context)

def product_list(request):
    products = Products2.objects.all()
    query = request.GET.get("q")
    products = Products2.objects.all()

    if query:
        products = products.filter(name__icontains=query)

    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(name__icontains=search_query)

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
        products = products.order_by('-popularity')
    elif sort == 'newest':
        products = products.order_by('-created_at')

    show_discounted = request.GET.get('discounted')
    if show_discounted:
        products = products.filter(popust=True)

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

    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query)
        )

    context = {
        'products': products,
    }
    return render(request, 'main/product_list.html', context)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'main/register.html', {'form': form})


def custom_logout(request):
    logout(request)
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
@csrf_exempt
@require_POST
@login_required
def add_to_list(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            list_id = data.get('list_id')
            product_id = data.get('product_id')

            # Get the list and product
            shopping_list = get_object_or_404(ShoppingList, id=list_id, user=request.user)
            product = get_object_or_404(Products2, id=product_id)

            # Check if product already exists in the list
            item, created = ShoppingListItem.objects.get_or_create(
                shopping_list=shopping_list,
                product=product,
                defaults={'quantity': 1}
            )

            return JsonResponse({
                'success': True,
                'message': 'Product added successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

@require_GET
@login_required
def get_user_lists(request):
    if not request.user.is_authenticated:
        return JsonResponse({'lists': []})

    lists = ShoppingList.objects.filter(user=request.user).values('id', 'name')
    return JsonResponse({'lists': list(lists)})


def product_detail(request, product_id):
    product = get_object_or_404(Products2, id=product_id)
    similar_products = get_similar_products(product.name, product.category)
    # Fetch user lists if authenticated
    user_lists = ShoppingList.objects.filter(user=request.user) if request.user.is_authenticated else []

    return render(request, 'main/product_detail.html', {
        'product': product,
        'similar_products': similar_products,
        'user_lists': user_lists
    })


@require_POST
def remove_item(request, item_id):
    try:
        item = ShoppingListItem.objects.get(id=item_id, shopping_list__user=request.user)
        item.delete()
        return JsonResponse({'status': 'success'})
    except ShoppingListItem.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)