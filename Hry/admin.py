from django.contrib import admin
from .models import Hra  # Importuješ tvou tabulku

admin.site.register(Hra) # Říkáš Djangu: "Zobraz tuhle tabulku v adminu"