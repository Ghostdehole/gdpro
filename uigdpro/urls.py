from django.urls import path
from . import views

app_name = 'uigdpro' 

urlpatterns = [

    path('', views.generator_view, name='generator'),
）
    path('check/', views.check_for_file, name='check_for_file'),

    path('download/', views.download, name='download'),

    path('png/', views.get_png, name='get_png'),

    path('update_gh_run/', views.update_github_run, name='update_gh_run'),

    path('save_custom_client/', views.save_custom_client, name='save_custom_client'),

    path('startgh/', views.startgh, name='startgh'),
]
