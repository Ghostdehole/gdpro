from django.contrib import admin
from django.urls import path, re_path, include
from uigdpro import views

urlpatterns = [

    path('', views.generator_view, name='generator'),
    path('generator/', views.generator_view, name='generator_alias'), 
    path('check_for_file/', views.check_for_file, name='check_for_file'),
    path('download/', views.download, name='download'), 
    path('creategh/', views.create_github_run, name='creategh'),
    path('updategh/', views.update_github_run, name='updategh'),
    path('startgh/', views.startgh, name='startgh'),
    path('get_png/', views.get_png, name='get_png'),
    path('save_custom_client/', views.save_custom_client, name='save_custom_client'),
   
    # Django Admin
    path('admin/', admin.site.urls),
]
