from django.db import models
from django.contrib.auth.models import AbstractUser

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

    class Meta:
        db_table = 'products2'

    def __str__(self):
        return self.name

class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    saved_products = models.ManyToManyField('Products2', blank=True)


class ShoppingList(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_lists'
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ShoppingListItem(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE)
    product = models.ForeignKey('Products2', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)