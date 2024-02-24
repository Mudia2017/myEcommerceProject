import django_filters
from django_filters import CharFilter
from .models import Product


class ProductOverView(django_filters.FilterSet):

    name = CharFilter(field_name='name', lookup_expr='icontains', label='')
    class Meta:
        model = Product
        # fields = ['name','description']
        fields = '__all__'
        exclude = ('price', 'description', 'category', 'brand', 'image', 'mfgDate', 'expDate', 'discount', 'price_after_discount', 'out_of_stock', 'store', 'active')