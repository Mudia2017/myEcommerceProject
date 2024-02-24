import django_filters
from django_filters import CharFilter
from homePage . models import Product


class OrderFilter(django_filters.FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains', label='')
    class Meta:
        model = Product
        fields = '__all__'
        exclude = ('price', 'new_price', 'description', 'category', 'brand', 'image', 'mfgDate', 'expDate', 'discount', 'out_of_stock', 'store', 'active')