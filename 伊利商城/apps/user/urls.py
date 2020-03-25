"""yili URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
# from django.urls import path
from django.conf.urls import url,include
from .views import RegisterView,LoginView,ActiveView,UserInfoView,UserOrderView,UserSiteView

urlpatterns = [
    url('active/(?P<token>.*)/$',ActiveView.as_view(),name='active'),
    url('info/$', UserInfoView.as_view(), name='info'),
    url('order/(?P<page>\d+)$', UserOrderView.as_view(), name='order'),
    url('site/$', UserSiteView.as_view(), name='site'),
]
