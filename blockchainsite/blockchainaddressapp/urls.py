from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    #path('<slug:address_id>/', views.AddressView.as_view(), name='address'),
    re_path(r'^(?P<address_id>[0-9a-zA-Z]{27,34})/$', views.AddressView.as_view(), name='address'),
    path('qrcode/', views.QrCodeView.as_view(), name='qrcode')
]