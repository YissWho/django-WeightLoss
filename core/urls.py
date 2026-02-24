# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('auth/', views.auth_view, name='auth'),
    # 临时加一个首页路由防报错，后面我们再详细写打卡页
    path('', views.home_view, name='home'), 
    path('logout/', views.logout_view, name='logout'),
]