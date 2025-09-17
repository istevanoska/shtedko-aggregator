from datetime import timezone

from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.auth.models import AbstractUser

#definirame modeli i atributi koi treba da odat so modelite
#modelite se nacin kako da gi modelirame informaciite od db
#ni ovozmova polseno da gi zemaem informaciie, da im dodavame atributi na informaciite od bazata
# Create your models here.
#prvo krirame class so imeto na nasiot model i go nasleduvame od models od django
class ToDoList(models.Model):
    name = models.CharField(max_length=200) #

    def __str__(self):
        return self.name
class Item(models.Model):
    todolist = models.ForeignKey(ToDoList, on_delete=models.CASCADE)
    text = models.CharField(max_length=300)
    complete = models.BooleanField()
    def __str__(self):
        return self.text



class Category(models.Model):
    name = models.CharField(max_length=100)
    name_mk = models.CharField(max_length=100) # Macedonian name

    def __str__(self):
        return self.name_mk  # or self.name depending on context

class Subcategory(models.Model):
    name = models.CharField(max_length=100)       # English
    name_mk = models.CharField(max_length=100)    # Macedonian
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.name_mk

#sega odime so komanda python manage.py makemigrations
class Products2(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    actual_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00  # Add this line
    )
    category = models.CharField(max_length=100)
    image_url = models.CharField(max_length=255)
    product_url = models.CharField(max_length=255)
    store = models.CharField(max_length=255)
    popust = models.BooleanField(default=False)
    popust_date = models.DateField(null=True, blank=True)
    embedding = models.BinaryField()
    subcategory = models.ForeignKey(Subcategory, on_delete=models.SET_NULL, null=True, blank=True)


    class Meta:
        db_table = 'products2'

    def __str__(self):
        return self.name

class User(AbstractUser):
    # Add custom fields if needed (optional)
    phone = models.CharField(max_length=20, blank=True)
    saved_products = models.ManyToManyField('Products2', blank=True)

class ShoppingList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    db_collation = 'utf8mb4_unicode_ci'


class ShoppingListItem(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE)
    product = models.ForeignKey('Products2', on_delete=models.CASCADE)  # Assuming you have a Product model
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('shopping_list', 'product')



from django.utils import timezone  # Correct import for timezone.now

User = get_user_model()

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey('main.Products2', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'product')

class ProductHistory(models.Model):
    product = models.ForeignKey(Products2, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()

    class Meta:
        db_table = "product_history2"

    def __str__(self):
        return f"{self.product.name} - {self.price} ({self.date})"
