from django.contrib import admin
from . models import *

from embed_video.admin import AdminVideoMixin
from .models import Video_item
# Register your models here.

class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'brand', 'price', 'discount', 'mfgDate', 'expDate', 'store', 'active')
    readonly_fields = ('new_price',)

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'date_order', 'complete', 'transaction_id', 'paid')

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'order', 'quantity', 'unit_price', 'line_total', 'store_name', 'date_added')

class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'cus_name', 'transaction_id', 'ptd_id', 'product_name')

admin.site.register(Customer)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(ShippingAddress)
admin.site.register(Store)
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Comment)
admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(WishList)
admin.site.register(Payment)
admin.site.register(Slide_image)
admin.site.register(RecentViewItems)




class MyModelAdmin(AdminVideoMixin, admin.ModelAdmin):
    pass

admin.site.register(Video_item, MyModelAdmin)