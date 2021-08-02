from django.contrib import admin

from .models import Product


class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('product_name',)}
    list_display = ['product_name', 'price', 'stock', 'category', 'modified_date', 'is_available']

# Register your models here.
admin.site.register(Product, ProductAdmin)

