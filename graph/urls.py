from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/graph/', views.graph_data, name='graph_data'),
]
