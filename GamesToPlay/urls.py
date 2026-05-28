from django.contrib import admin
from django.urls import path
from Hry import views  # Čistý import views z aplikace Hry

urlpatterns = [
    path('admin/', admin.site.urls),
    path('aktualizuj-hltb-hry/', views.aktualizuj_hltb_hry, name='aktualizuj_hltb_hry'),
git init
    # Hlavní stránka tvého herního backlogu
    path('moje-hry/', views.seznam_her, name='seznam_her'),
    path('import/', views.nacist_ze_steam, name='import_her'),
    
    # Směrování akcí z tlačítek
    path('moje-hry/upravit/<str:hra_id>/', views.upravit_hru, name='upravit_hru'),
    
    # Kompletní cesty pro Steam přihlašování
    path('steam/login/', views.steam_login, name='steam_login'),
    path('steam/callback/', views.steam_callback, name='steam_callback'),
    path('steam/logout/', views.steam_logout, name='steam_logout'),
]