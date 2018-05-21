from django.urls import path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<slug:address_id>/', views.AddressView.as_view(), name='address')
]