let aktualniPriorita = 'all';
let vzestupneNazev = true;
let vzestupneCas = true;
let aktivniFormularProPrioritu = null;

document.addEventListener('DOMContentLoaded', function() {
    // Inicializace vyhledávání
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', provestFiltraci);
    }

    // Inicializace filtrů priorit
    const filtrTlacitka = document.querySelectorAll('.filter-buttons .btn-filter');
    filtrTlacitka.forEach(tlacitko => {
        tlacitko.addEventListener('click', function(event) {
            const vybranyFiltr = event.target.getAttribute('data-filter');
            aktualniPriorita = vybranyFiltr;

            filtrTlacitka.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            provestFiltraci();
        });
    });

    // Načtení a aplikace uloženého řazení z localStorage
    const zalohovaneRazeni = localStorage.getItem('games_sort_type');
    if (zalohovaneRazeni) {
        vzestupneNazev = localStorage.getItem('games_sort_nazev') === 'true';
        vzestupneCas = localStorage.getItem('games_sort_cas') === 'true';
        
        if (zalohovaneRazeni === 'nazev') {
            vzestupneNazev = !vzestupneNazev;
            seradTabulku(0);
        } else if (zalohovaneRazeni === 'cas') {
            vzestupneCas = !vzestupneCas;
            seradTabulku(1);
        }
    }

    // ================= ASYNCHRONNÍ MAPOVÁNÍ HLTB NA POZADÍ =================
    spustAsynchronniHltbNaPozadi();
});

function provestFiltraci() {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;

    const hledanyText = searchInput.value.toLowerCase().trim();
    const radky = document.querySelectorAll('#backlog-body tr:not(.no-games-row)');

    radky.forEach(radek => {
        const nazevHry = radek.getAttribute('data-nazev');
        const prioritaHry = radek.getAttribute('data-priorita');

        const odpovidaText = nazevHry.includes(hledanyText);
        const odpovidaPriorita = (aktualniPriorita === 'all' || prioritaHry === aktualniPriorita);

        if (odpovidaText && odpovidaPriorita) {
            radek.style.display = '';
        } else {
            radek.style.display = 'none';
        }
    });
}

function seradTabulku(sloupecIndex) {
    const tbody = document.getElementById('backlog-body');
    if (!tbody) return;
    
    const radky = Array.from(tbody.querySelectorAll('tr:not(.no-games-row)'));
    const sipkaNazev = document.getElementById('sipka-nazev');
    const sipkaCas = document.getElementById('sipka-cas');

    if (sloupecIndex === 0) {
        vzestupneNazev = !vzestupneNazev;
        radky.sort((a, b) => {
            const jmenoA = a.getAttribute('data-nazev');
            const jmenoB = b.getAttribute('data-nazev');
            return vzestupneNazev ? jmenoA.localeCompare(jmenoB) : jmenoB.localeCompare(jmenoA);
        });
        if(sipkaNazev) sipkaNazev.textContent = vzestupneNazev ? '🔽' : '🔼';
        if(sipkaCas) sipkaCas.textContent = '🔼';
        localStorage.setItem('games_sort_type', 'nazev');
        localStorage.setItem('games_sort_nazev', vzestupneNazev);
    } else if (sloupecIndex === 1) {
        vzestupneCas = !vzestupneCas;
        radky.sort((a, b) => {
            const casA = parseInt(a.getAttribute('data-rawcas')) || 0;
            const casB = parseInt(b.getAttribute('data-rawcas')) || 0;
            return vzestupneCas ? casA - casB : casB - casA;
        });
        if(sipkaCas) sipkaCas.textContent = vzestupneCas ? '🔽' : '🔼';
        if(sipkaNazev) sipkaNazev.textContent = '🔼';
        localStorage.setItem('games_sort_type', 'cas');
        localStorage.setItem('games_sort_cas', vzestupneCas);
    }
    radky.forEach(radek => tbody.appendChild(radek));
}

function otevriOknoPriority(event, steamId) {
    event.stopPropagation();
    const tlacitko = event.target;
    aktivniFormularProPrioritu = tlacitko.closest('form');
    const modal = document.getElementById('priority-custom-modal');
    if (!modal) return;
    const rect = tlacitko.getBoundingClientRect();
    modal.style.left = (window.scrollX + rect.left) + "px";
    modal.style.top = (window.scrollY + rect.bottom + 5) + "px";
    modal.style.display = "flex";
}

function vyberPriorituZOkna(novaHodnota) {
    if (!aktivniFormularProPrioritu) return;
    const hiddenInput = aktivniFormularProPrioritu.querySelector('.hidden-priorita-input');
    if (hiddenInput) {
        hiddenInput.value = novaHodnota;
        aktivniFormularProPrioritu.submit();
    }
    zavriOknoPriority();
}

function zavriOknoPriority() {
    const modal = document.getElementById('priority-custom-modal');
    if (modal) modal.style.display = "none";
    aktivniFormularProPrioritu = null;
}

document.addEventListener('click', function(event) {
    const modal = document.getElementById('priority-custom-modal');
    if (modal && modal.style.display === "flex") {
        if (!event.target.closest('.priority-popup') && !event.target.closest('.priorita-button')) {
            zavriOknoPriority();
        }
    }
});

// ================= CYBER RANDOMIZER =================
function spustRandomizer() {
    const vsechnyRadky = Array.from(document.querySelectorAll('#backlog-body tr:not(.no-games-row)'));
    const viditelneRadky = vsechnyRadky.filter(r => r.style.display !== 'none');

    if (viditelneRadky.length === 0) {
        alert("🚨 Žádné viditelné hry k losování!");
        return;
    }

    vsechnyRadky.forEach(r => r.classList.remove('randomizer-winner-glow'));

    let cykly = 0;
    const maximalniCykly = 20; 
    const rychlostBlikani = 90; 

    const interval = setInterval(() => {
        const nahodnyIndex = Math.floor(Math.random() * viditelneRadky.length);
        
        viditelneRadky.forEach(r => r.style.backgroundColor = '');
        viditelneRadky[nahodnyIndex].style.backgroundColor = 'rgba(0, 243, 255, 0.15)';

        cykly++;

        if (cykly >= maximalniCykly) {
            clearInterval(interval);
            viditelneRadky.forEach(r => r.style.backgroundColor = '');

            const finalniIndex = Math.floor(Math.random() * viditelneRadky.length);
            const vybranyRadek = viditelneRadky[finalniIndex];

            vybranyRadek.classList.add('randomizer-winner-glow');
            vybranyRadek.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, rychlostBlikani);
}

// ================= NOVÉ: LOGIKA PRO ASYNCHRONNÍ DOPLŇOVÁNÍ HLTB =================
function spustAsynchronniHltbNaPozadi() {
    // Vybere všechny řádky her v backlogu, které mají atribut data-hltb rovný 0
    const hryKNacteni = Array.from(document.querySelectorAll('#backlog-body tr[data-hltb="0"]'));
    
    if (hryKNacteni.length === 0) return;

    console.log(`📡 Spouštím doplňování HLTB časů na pozadí pro ${hryKNacteni.length} her.`);
    
    let index = 0;

    function nactiDalsiHru() {
        if (index >= hryKNacteni.length) {
            console.log("🏁 Všechny chybějící HLTB časy byly úspěšně zkontrolovány.");
            return;
        }

        const radek = hryKNacteni[index];
        const steamId = radek.getAttribute('data-steam-id'); // Ujisti se, že máš tr s tímto atributem
        const nazevHry = radek.getAttribute('data-nazev');

        // Cyberpunkový detail: Jemné oranžové blikání buňky, která se právě stahuje
        const hltbBunka = radek.querySelector('.hltb-cas-hodnota');
        if (hltbBunka) {
            hltbBunka.style.color = '#ff9d00';
            hltbBunka.textContent = '⚡...';
        }

        // Posíláme fetch na náš nový Django endpoint
        fetch(`/aktualizuj-hltb-hry/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken') // Bezpečné Django CSRF
            },
            body: new URLSearchParams({
                'steam_id': steamId,
                'nazev': nazevHry
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.hltb_cas > 0) {
                // Přepíšeme atribut na řádku, aby se nehledal příště a fungovalo řazení
                radek.setAttribute('data-hltb', data.hltb_cas);
                
                // Aktualizujeme frontend hodnotu s neonovým efektem
                if (hltbBunka) {
                    hltbBunka.style.color = '#00f3ff'; // Zpět na cyan neon
                    hltbBunka.textContent = `${data.hltb_cas} h`;
                }

                // Přepočítáme celkový HLTB čas na páté kartě dashboardu v reálném čase
                aktualizujCelkovyHltbDashboard(data.hltb_cas);
            } else {
                // Pokud HLTB hru nenašlo, necháme tam 0 (nebo text '-' / 'N/A')
                if (hltbBunka) {
                    hltbBunka.style.color = '#ff0055'; // Růžový neon pro neznámý čas
                    hltbBunka.textContent = '--';
                }
                radek.setAttribute('data-hltb', '-1'); // Označíme, ať se nezkouší pořád dokola
            }
        })
        .catch(err => console.error("Chyba při stahování HLTB:", err))
        .finally(() => {
            index++;
            // Bezpečný rozestup 1.5 sekundy mezi požadavky proti zablokování IP adresy
            setTimeout(nactiDalsiHru, 1500);
        });
    }

    // Odstartujeme smyčku
    nactiDalsiHru();
}

function aktualizujCelkovyHltbDashboard(pridanyCas) {
    const dashboardHltbPrvku = document.getElementById('dashboard-hltb-suma');
    if (dashboardHltbPrvku) {
        let aktualniSuma = parseInt(dashboardHltbPrvku.textContent) || 0;
        dashboardHltbPrvku.textContent = aktualniSuma + pridanyCas;
    }
}

// Pomocná funkce pro získání CSRF tokenu z cookies (Django standard)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}