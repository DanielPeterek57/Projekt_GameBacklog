from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.db.models import Sum
import requests
from howlongtobeatpy import HowLongToBeat  # Reálné HLTB API
from .models import Hra

# Tady je tvůj API klíč
STEAM_API_KEY = '48C0275D77A1200C689D8B77CED7DBD9'


def seznam_her(request):
    """Rozdělí hry na sekce a spočítá celkové herní statistiky pro dashboard"""
    if request.user.is_authenticated:
        # Načtení her podle stavu
        hry_nedohrano = Hra.objects.filter(uzivatel=request.user, stav='nedohrano')
        hry_dohrano = Hra.objects.filter(uzivatel=request.user, stav='dohrano')
        hry_odpad = Hra.objects.filter(uzivatel=request.user, stav='nehrat')
        
        # VÝPOČET STATISTIK
        vsechny_hry = Hra.objects.filter(uzivatel=request.user)
        pocet_vsech = vsechny_hry.count()
        pocet_nedohrano = hry_nedohrano.count()
        pocet_dohrano = hry_dohrano.count()
        
        # Sečteme minuty všech her a přepočítáme na hodiny
        celkovy_cas_minuty = vsechny_hry.aggregate(Sum('odehrany_cas'))['odehrany_cas__sum'] or 0
        celkove_hodiny = round(celkovy_cas_minuty / 60, 1)
        
        # Spočítáme celkový zbývající HLTB čas v backlogu
        celkovy_hltb_backlog = hry_nedohrano.aggregate(Sum('hltb_cas'))['hltb_cas__sum'] or 0
        
        # Spočítáme procentuální úspěšnost dokončení her
        procento_dokonceno = round((pocet_dohrano / pocet_vsech * 100), 1) if pocet_vsech > 0 else 0
        
        # OPRAVA: Cesta změněna na malá písmena 'hry/...' kvůli Linuxu
        return render(request, 'hry/seznam_her.html', {
            'hry_nedohrano': hry_nedohrano,
            'hry_dohrano': hry_dohrano,
            'hry_odpad': hry_odpad,
            'stat_hodiny': celkove_hodiny,
            'stat_backlog': pocet_nedohrano,
            'stat_dohrano': pocet_dohrano,
            'stat_procento': procento_dokonceno,
            'stat_hltb': celkovy_hltb_backlog,  # Posíláme HLTB sumu do frontendu
        })
    else:
        # OPRAVA: Cesta změněna na malá písmena 'hry/...' kvůli Linuxu
        return render(request, 'hry/seznam_her.html', {
            'hry_nedohrano': None, 'hry_dohrano': None, 'hry_odpad': None,
            'stat_hodiny': 0, 'stat_backlog': 0, 'stat_dohrano': 0, 'stat_procento': 0, 'stat_hltb': 0
        })


@login_required
def upravit_hru(request, hra_id):
    """Zpracuje kliknutí na tlačítka a zjištění achievementů pro JEDNU hru"""
    if request.method == "POST":
        hra = Hra.objects.get(steam_id=hra_id, uzivatel=request.user)
        akce = request.POST.get('akce')
        
        if akce == 'prepni_stav':
            hra.stav = 'dohrano' if hra.stav == 'nedohrano' else 'nedohrano'
            
        elif akce == 'nebudu_hrat':
            hra.stav = 'nehrat'
            
        elif akce == 'vrat_do_backlogu':
            hra.stav = 'nedohrano'
            
        elif akce == 'zmen_prioritu':
            vybrana_priorita = request.POST.get('nova_priorita')
            if vybrana_priorita in ['nizka', 'stredni', 'vysoka']:
                hra.priorita = vybrana_priorita
                
        # Uložení hvězdiček a recenze ze Síně Slávy
        elif akce == 'uloz_recenzi':
            hra.hodnoceni = int(request.POST.get('hodnoceni', 0))
            hra.poznamka = request.POST.get('poznamka', '')
                
        elif akce == 'nacti_achievementy':
            DYNAMICKE_STEAM_ID = request.user.username
            url_ach = f"http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/?appid={hra_id}&key={STEAM_API_KEY}&steamid={DYNAMICKE_STEAM_ID}"
            odpoved_ach = requests.get(url_ach)
            
            if odpoved_ach.status_code == 200 and odpoved_ach.text.strip():
                try:
                    data_ach = odpoved_ach.json()
                    list_achieved = data_ach.get('playerstats', {}).get('achievements', [])
                    hra.achievementy_celkem = len(list_achieved)
                    hra.achievementy_odemceno = sum(1 for a in list_achieved if a.get('achieved') == 1)
                except Exception:
                    pass
                
        hra.save()
        
    return redirect(f'/moje-hry/#hra-{hra_id}')


@login_required
def nacist_ze_steam(request):
    """BLESKOVÝ import her ze Steamu bez čekání na HLTB (odvrácení timeoutu)"""
    DYNAMICKE_STEAM_ID = request.user.username
    ciste_id = "".join(filter(str.isdigit, str(DYNAMICKE_STEAM_ID)))
    
    if not ciste_id:
        return HttpResponse("🚨 Chyba: Tvoje přihlašovací jméno neobsahuje platné číselné SteamID64.")

    url_hry = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={STEAM_API_KEY}&steamid={ciste_id}&format=json&include_appinfo=true"
    
    try:
        odpoved_hry = requests.get(url_hry)
    except Exception as e:
        return HttpResponse(f"🚨 Chyba sítě: Selhalo připojení ke Steamu. Detail: {e}")

    if odpoved_hry.status_code != 200:
        return HttpResponse(f"🚨 Ochrana: Steam API odmítlo požadavek se status kódem {odpoved_hry.status_code}.")

    try:
        data_hry = odpoved_hry.json()
    except ValueError:
        return HttpResponse("🚨 Chyba: Steam nevrátil JSON data.")

    if 'games' in data_hry.get('response', {}):
        hry_ze_steam = data_hry['response']['games']

        for g in hry_ze_steam:
            id_hry = str(g['appid'])
            nazev_hry = g['name']
            cas_v_minutach = g.get('playtime_forever', 0)

            # Pokud hra už v databázi existuje, zachováme její starý HLTB čas, jinak nastavíme 0
            hra_v_db = Hra.objects.filter(steam_id=id_hry, uzivatel=request.user).first()
            stary_hltb_cas = hra_v_db.hltb_cas if hra_v_db else 0

            Hra.objects.update_or_create(
                steam_id=id_hry,
                uzivatel=request.user,
                defaults={
                    'nazev': nazev_hry,
                    'odehrany_cas': cas_v_minutach,
                    'priorita': 'stredni',
                    'stav': 'nedohrano',
                    'hltb_cas': stary_hltb_cas,
                }
            )
        return redirect('/moje-hry/')
    else:
        return HttpResponse(f"🚨 Úspěšně připojeno k ID {ciste_id}, ale Steam nevrátil žádné hry.")


@login_required
@csrf_protect
def aktualizuj_hltb_hry(request):
    """
    AJAX endpoint volaný z JavaScriptu na pozadí stránky.
    Zjišťuje HLTB čas pro jednu hru s opravenými atributy knihovny.
    """
    if request.method == "POST":
        steam_id = request.POST.get('steam_id')
        nazev_hry = request.POST.get('nazev')
        
        if not steam_id or not nazev_hry:
            return JsonResponse({'success': False, 'error': 'Chybí parametry'}, status=400)
            
        try:
            hra = Hra.objects.get(steam_id=steam_id, uzivatel=request.user)
            realny_cas = 0
            
            # Vyhledávání na HLTB
            results = HowLongToBeat().search(nazev_hry)
            if results:
                nejlepsi_shoda = max(results, key=lambda element: element.similarity)
                
                # OPRAVA: Mapování podle aktuální verze howlongtobeatpy
                if hasattr(nejlepsi_shoda, 'main_extra') and nejlepsi_shoda.main_extra > 0:
                    realny_cas = int(nejlepsi_shoda.main_extra)
                elif hasattr(nejlepsi_shoda, 'main_story') and nejlepsi_shoda.main_story > 0:
                    realny_cas = int(nejlepsi_shoda.main_story)
                elif hasattr(nejlepsi_shoda, 'completionist') and nejlepsi_shoda.completionist > 0:
                    realny_cas = int(nejlepsi_shoda.completionist)

            # Uložíme čas do databáze
            hra.hltb_cas = realny_cas
            hra.save()
            
            print(f"✅ HLTB doplněno na pozadí: {nazev_hry} -> {realny_cas}h")
            return JsonResponse({'success': True, 'hltb_cas': realny_cas})
            
        except Hra.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Hra nenalezena v DB'}, status=404)
        except Exception as e:
            print(f"❌ Chyba na pozadí u hry '{nazev_hry}': {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
            
    return JsonResponse({'success': False, 'error': 'Pouze POST požadavky'}, status=400)


def steam_login(request):
    """Generuje Steam OpenID URL dynamicky pro lokál i server"""
    # Zjistíme, jestli jedeme na PythonAnywhere nebo na localu
    domena = request.build_absolute_uri('/')
    
    steam_openid_url = 'https://steamcommunity.com/openid/login'
    params = {
        'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.mode': 'checkid_setup',
        'openid.return_to': f'{domena}steam/callback/',
        'openid.realm': domena,
        'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
    }
    pripraveny_odkaz = requests.Request('GET', steam_openid_url, params=params).prepare()
    return redirect(pripraveny_odkaz.url)


def steam_callback(request):
    vsechny_parametry = request.GET.dict()
    vsechny_parametry['openid.mode'] = 'check_authentication'
    potvrzeni = requests.post('https://steamcommunity.com/openid/login', data=vsechny_parametry)
    
    if 'is_valid:true' in potvrzeni.text:
        claimed_id = request.GET.get('openid.claimed_id', '')
        vlastni_steam_id = claimed_id.split('/')[-1]
        uzivatel, vytvoren = User.objects.get_or_create(username=vlastni_steam_id)
        login(request, uzivatel)
        return redirect('/import/')
    else:
        return HttpResponse("🚨 Chyba: Autentizace přes Steam selhala.")


def steam_logout(request):
    logout(request)
    return redirect('/moje-hry/')