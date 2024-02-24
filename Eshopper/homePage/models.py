from django.db import models
from django.contrib.auth.models import User
from .paystack import PayStack

# IMPORTED THESE FOR TOKEN GENERATION
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from embed_video.fields import EmbedVideoField
from mptt.models import MPTTModel, TreeForeignKey
# Create your models here.

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200, null=True)
    full_name = models.CharField(max_length=200, default='', blank=True)
    email = models.EmailField(max_length=200, default='', blank=True)
    mobile = models.CharField(max_length=15, default='', blank=True)
    home_tel = models.CharField(max_length=15, default='', blank=True)
    address = models.CharField(max_length=200, default='', blank=True)
    city = models.CharField(max_length=200, default='', blank=True)
    state = models.CharField(max_length=200, default='', blank=True)

    def __str__(self):
        return self.name

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class Category(MPTTModel):
    category = models.CharField(max_length=200, null=True, blank=True, unique=True, default='')
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', default='')
    image = models.ImageField(null=True, blank=True)
    active = models.BooleanField(default=True, null=True, blank=False)
    
    class MPTTMeta:
        order_insertion_by = ['category']

    def __str__(self):
        return self.category

    @property
    def imgURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url

    

class Brand(models.Model):
    brand = models.CharField(max_length=200, null=True, blank=True)
    
    def __str__(self):
        return self.brand


class Store(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    store_name = models.CharField(max_length=200, null=True, blank=True)
    store_address = models.CharField(max_length=256, null=True, blank=True)
    city = models.CharField(max_length=200, null=True)
    LGA = models.CharField(max_length=200, null=True)
    state = models.CharField(max_length=200, null=True)
    email = models.EmailField(max_length=200, null=True)
    mobile = models.CharField(max_length=15, null=True)
    altMobile = models.CharField(max_length=15, default='', blank=True) 
    verified = models.BooleanField(default=False, null=True, blank=False)
    active = models.BooleanField(default=True, null=True, blank=False)

    def __str__(self):
        return self.store_name


class Product(models.Model):
    name = models.CharField(max_length=200, null=True)
    description = models.TextField(null=True, blank=True)
    category = TreeForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=True, blank=True)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    new_price = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    image = models.ImageField(null=True, blank=True)
    mfgDate = models.DateField(default=None, null=True, blank=True)
    expDate = models.DateField(default=None, null=True, blank=True)
    discount = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    out_of_stock = models.BooleanField(default=False, null=True, blank=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    active = models.BooleanField(default=True, null=True, blank=False)
    
    def __str__(self):
        return self.name

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url

    @property
    def get_unit_price(self):
        if self.discount > 0:
            new_price = round(self.price - ((self.price / 100) * self.discount), 2) 
        else:
            new_price = self.price
        return new_price

    # def delete(self, *args, **kwargs):
    #     self.image.delete()
    #     super().delete(*args, **kwargs)


class Slide_image(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    slide_ptd_image = models.ImageField()

    @property    
    def image_slideURL(self):
        try:
            url = self.slide_ptd_image.url
        except:
            url = ''
        return url


class Video_item(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    video = EmbedVideoField()  # same like models.URLField()

    def __str__(self):
        return self.video


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    date_order = models.DateTimeField(blank=True, null=True)
    complete = models.BooleanField(default=False, null=True, blank=False)
    transaction_id = models.CharField(max_length=200, null=True)
    payment_option = models.CharField(max_length=200, null=True)
    paid = models.BooleanField(default=False, null=True, blank=False)
    paymentReference = models.CharField(null=True, blank=True, max_length=200)
    status = models.CharField(max_length=50, blank=True)
    reason_for_refund = models.CharField(max_length=200, null=True)
    order_private_note = models.TextField(null=True)
    refund_status = models.CharField(max_length=200, null=True, blank=True)
    refund_private_note = models.TextField(null=True)
    acct_activities = models.TextField(null=True)

    def __float__(self):
        return float(self.id)

    @property
    def shipping(self):
        orderitems = self.orderitem_set.all()
        # return shipping 

    @property
    def get_cart_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total for item in orderitems])
        return total
    
    @property
    def get_cart_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    store_name = models.CharField(max_length=256, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    refundAmt = models.DecimalField(max_digits=9, decimal_places=2, default=0)

    @property
    def get_total(self):
        if self.product.discount > 0:
            discounted_price = round(self.product.price - ((self.product.price / 100) * self.product.discount), 2)
            total = discounted_price * self.quantity
        else:
            total = self.product.price * self.quantity
        return total

    @property
    def get_unit_price(self):
        if self.product.discount > 0:
            new_price = round(self.product.price - ((self.product.price / 100) * self.product.discount), 2) 
        else:
            new_price = self.product.price
        return new_price


class CustomerAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    address_type = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=200, null=True)
    address = models.CharField(max_length=200, null=True)
    city = models.CharField(max_length=200, null=True)
    state = models.CharField(max_length=200, null=True)
    zipcode = models.CharField(max_length=200, null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True)
    altMobile = models.CharField(max_length=15, null=True, blank=True)
    default = models.BooleanField(default=False, null=True, blank=False)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, blank=True, null=True)
    address_type = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=200, null=True)
    address = models.CharField(max_length=200, null=True)
    city = models.CharField(max_length=200, null=True)
    state = models.CharField(max_length=200, null=True)
    zipcode = models.CharField(max_length=200, null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True)
    altMobile = models.CharField(max_length=15, null=True, blank=True)
    optional_note = models.TextField(null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address


class ProductReview(models.Model):
    ptd_review_id = models.CharField(max_length=200, null=True)
    cus_name = models.CharField(max_length=200, null=True)
    transaction_id = models.CharField(max_length=200, null=True)
    order_date = models.DateTimeField(blank=True, null=True)
    ptd_id = models.CharField(max_length=200, null=True)
    product_name = models.CharField(max_length=200, null=True)
    product_image = models.CharField(max_length=200, null=True)


class Comment(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    subject = models.CharField(max_length=200, default='', blank=True)
    comment = models.CharField(max_length=256, default='', blank=True)
    rate = models.FloatField(default=1, max_length=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.comment


class WishList(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    store_id = models.CharField(max_length=200, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.product)


class RecentViewItems(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.product)

        
class Payment(models.Model):
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    ref = models.CharField(max_length=200)
    email = models.EmailField()
    channel = models.CharField(max_length=200, null=True, blank=True)
    card_type = models.CharField(max_length=200, null=True, blank=True)
    bank = models.CharField(max_length=200, null=True, blank=True)
    status = models.CharField(max_length=200, null=True, blank=True)
    verified = models.BooleanField(default=False)
    message = models.CharField(max_length=250, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_created',)

    def __str__(self) -> str:
        return f"Payment: {self.amount}"

    # def save(self, *args, **kwargs) -> None:
    #     while not self.ref:
    #         ref = secrets.token_urlsafe(50)
    #         object_with_similar_ref = Payment.objects.filter(ref=ref)
    #         if not object_with_similar_ref:
    #             self.ref = ref
    #     super().save(*args, **kwargs)
    
    # def amount_value(self) -> int:
    #     return self.amount *100

    def verify_payment(self):
        paystack = PayStack()
        status, result = paystack.verify_payment(self.ref, self.amount)
        print('Verification from model start here....')
        print(status)
        print(result)
        print(result['amount'] / 100)
        print(self.amount)
        if status:
            if float (result['amount'] / 100) == float (self.amount):
                self.verified = True
            self.save()
        if self.verified:
            return status, result
        return status, result



