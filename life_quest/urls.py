"""
URL configuration for life_quest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path,include
from django.contrib.auth import views as auth_views
from core import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    #Action URLs
    path('add-task/',views.add_task, name='add_task'),
    path('complete/<int:task_id>/', views.complete_task, name='complete_task'),
    path('delete/<int:task_id>/', views.delete_task, name='delete_task'),
    path('uncomplete_task/<int:task_id>/', views.uncomplete_task, name='uncomplete_task'),
    path('extend-deadline/<int:task_id>/', views.extend_deadline, name='extend_deadline'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('completed/', views.completed_quests_view, name='completed_quests'),

    # Password reset (disabled — uncomment to re-enable)
    # path('forgot-password/', views.forgot_password, name='forgot_password'),
    # path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    # path('reset-password/done/', views.reset_password_done, name='reset_password_done'),

    # Redirect allauth's "Login Cancelled" page back to our login page
    path('accounts/3rdparty/login/cancelled/', views.social_login_cancelled, name='socialaccount_login_cancelled'),

    path('accounts/', include('allauth.urls')),

]
