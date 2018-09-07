"""pugliaeventi URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path

from recommender_webapp import views
from pugliaeventi import views as main_views
from ajax_select import urls as ajax_select_urls

urlpatterns = [
    url(r'^$', main_views.index, name='index'),
    url(r'^admin/', admin.site.urls),
    url(r'^login/$', views.user_login, name='login'),
    url(r'^logout/$', views.user_logout, name='logout'),
    url(r'^register/$', views.user_signup, name='register'),
    url(r'^profile_configuration/$', views.profile_configuration, name='profile_configuration'),
    url(r'^close_places/$', views.close_places, name='close_places'),
    url(r'^my_places/$', views.my_places, name='my_places'),
    url(r'^my_profile/$', views.user_profile, name='my_profile'),
    path('place/<int:place_id>/', views.place_details, name='place_details'),
    path('event/<int:event_id>/', views.event_details, name='event_details'),
    path('ratings/<int:place_id>/<int:mood>/<int:companionship>/', views.add_rating_config, name='add_rating_conf'),

    # place it at whatever base url you like
    url(r'^ajax_select/', include(ajax_select_urls)),
    #url(r'.*', lambda request: render(request, '404.html'), name='404')

]
