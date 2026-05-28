from django.db import models
from django.contrib.auth.models import User

class Hra(models.Model):
    uzivatel = models.ForeignKey(User, on_delete=models.CASCADE)
    nazev = models.CharField(max_length=200)
    steam_id = models.CharField(max_length=50, blank=True, null=True)
    odehrany_cas = models.IntegerField(default=0)  # V databázi stále držíme minuty ze Steamu
    
    # Stav hry (Dohráno / Nedohráno / nehrat)
    STAV_CHOICES = [
        ('nedohrano', 'Nedohráno'),
        ('dohrano', 'Dohráno'),
        ('nehrat', 'Nebudu hrát'),
    ]
    stav = models.CharField(max_length=20, choices=STAV_CHOICES, default='nedohrano')
    
    # Priorita na dohrání
    PRIORITA_CHOICES = [
        ('vysoka', '🔥 Vysoká'),
        ('stredni', '⏳ Střední'),
        ('nizka', '💤 Nízká'),
    ]
    priorita = models.CharField(max_length=10, choices=PRIORITA_CHOICES, default='stredni')
    
    # Sloupce pro ukládání počtu achievementů
    achievementy_odemceno = models.IntegerField(default=0)
    achievementy_celkem = models.IntegerField(default=0)

    # NOVÁ POLE PRO KROK 2 A KROK 3:
    hodnoceni = models.IntegerField(default=0)  # 0 až 5 hvězdiček
    poznamka = models.TextField(blank=True, null=True)  # textová recenze hry
    hltb_cas = models.IntegerField(default=0)  # odhadovaný čas na hlavní příběh v hodinách (HLTB)

    @property
    def odehrane_hodiny(self):
        """Přepočítá minuty z databáze na hodiny zaokrouhlené na 1 desetinné místo"""
        return round(self.odehrany_cas / 60, 1)

    def __str__(self):
        return f"{self.uzivatel.username} - {self.nazev} ({self.get_stav_display()})"