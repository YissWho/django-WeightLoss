# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('auth/', views.auth_view, name='auth'),
    # 临时加一个首页路由防报错，后面我们再详细写打卡页
    path('', views.home_view, name='home'), 
    path('logout/', views.logout_view, name='logout'),
    # 个人信息编辑页
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('check_in/', views.check_in_view, name='check_in'),
    path('history/', views.history_view, name='history'),
    path('history/edit/<int:record_id>/', views.record_edit_view, name='record_edit'),
    path('history/delete/<int:record_id>/', views.record_delete_view, name='record_delete'),
]