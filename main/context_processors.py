from .models import ShoppingList

def user_lists(request):
    if request.user.is_authenticated:
        return {'user_lists': ShoppingList.objects.filter(user=request.user)}
    return {'user_lists': []}