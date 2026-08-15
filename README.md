# Florø Detailing – nettside med booking

Django-nettside for Florø Detailing med online booking av bilvask-timer. Betaling skjer på stedet.

## Funksjonalitet

- Forside med tjenester, priser og "slik fungerer det"
- Bookingflyt i fire steg (som en veiviser, ingen datofelt å skrive i):
  1. Velg tjeneste
  2. Velg dato (bla horisontalt blant kommende dager)
  3. Velg ledig tid (hindrer dobbeltbooking automatisk)
  4. Fyll ut kontaktinfo, bekreft e-postadressen med en engangskode, og bekreft bookingen – betaling skjer på stedet
- E-postverifisering: kunden må taste inn en 6-sifret kode sendt til e-postadressen sin før
  bookingen kan fullføres, slik at vi vet adressen faktisk er ekte og nåbar
- E-postbekreftelse til kunde + varsel til bedriften ved ny booking
- Adminpanel (`/admin/`) for å administrere:
  - Tjenester og priser (`Service`)
  - Åpningstider per ukedag (`BusinessHours`)
  - Stengte datoer/ferier (`ClosedDate`)
  - Bookinger og status
  - E-postverifiseringer (`EmailVerification`, kun til innsyn/support)
  - Nettsideinnstillinger (kontaktinfo, forsidetekst, kapasitet, booking-regler)

## Kom i gang lokalt

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# rediger .env og sett en egen SECRET_KEY

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Åpne http://127.0.0.1:8000 for nettsiden og http://127.0.0.1:8000/admin/ for adminpanelet.

Ved første oppsett er det allerede lagt inn:
- Tjenester: **Lett vask innvendig (500 kr), Grundigvask innvendig med shine (750 kr), Rens av seter (75 kr)**
- Åpningstider: mandag–fredag 08:00–16:00, stengt i helgene
- Kapasitet: 1 bil om gangen

Endre/legg til dette i adminpanelet under **Tjenester**, **Åpningstider** og **Nettsideinnstillinger**.

## Betaling

Kunden betaler på stedet (kort/Vipps/kontant slik dere ønsker) – det finnes ingen betalingsintegrasjon
i nettsiden. Bookingen bekreftes med det samme når kunden fullfører steg 4 i bookingveiviseren, og
kunden får en booking-bekreftelse (ikke en betalingskvittering) på skjerm og e-post.

## E-post

Som standard skrives e-poster til terminalen (nyttig i utvikling) – både bookingbekreftelser og
engangskodene for e-postverifisering.

**Viktig:** `smtp.gmail.com` fungerer fint lokalt, men Google blokkerer/dropper ofte SMTP-
tilkoblinger fra skyservere (Railway, AWS, GCP, DigitalOcean m.fl.) som anti-spam-tiltak – dette
gir en treg, hengende forespørsel i ca. 30 sekunder og til slutt en generisk 500-feil i
produksjon, selv med korrekt app-passord. **Bruk derfor Gmail kun til lokal utvikling, og en
ordentlig transaksjonstjeneste i produksjon** (samme `EMAIL_*`-variabler, bare andre verdier –
ingen kodeendring nødvendig):

- **SendGrid** (anbefalt hvis dere ikke har eget domene ennå): gratis opptil 100 e-poster/dag.
  Under **Settings → Sender Authentication → Verify a Single Sender**, verifiser Gmail-adressen
  dere sender fra (ingen DNS/domene nødvendig – bare et bekreftelseslenke-klikk). Lag så en
  API-nøkkel under **Settings → API Keys**, og sett:
  ```
  EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
  EMAIL_HOST=smtp.sendgrid.net
  EMAIL_PORT=587
  EMAIL_HOST_USER=apikey
  EMAIL_HOST_PASSWORD=<SendGrid API-nøkkel>
  EMAIL_USE_TLS=True
  DEFAULT_FROM_EMAIL=Florø Detailing <den-verifiserte-adressen@gmail.com>
  BUSINESS_NOTIFICATION_EMAIL=den-verifiserte-adressen@gmail.com
  ```
- **Resend** (hvis dere har/skaffer et domene): gratis opptil 3000 e-poster/mnd, men krever
  domeneverifisering (noen DNS-oppføringer) for å sende til andre enn dere selv.

### Lokal utvikling via Gmail (valgfritt)

1. Slå på 2-trinnsbekreftelse på Google-kontoen (`myaccount.google.com/security`).
2. Gå til `myaccount.google.com/apppasswords` og lag et app-passord for "Mail" (16 tegn – bruk
   **dette**, ikke det vanlige kontopassordet).
3. Sett i lokal `.env`:
   ```
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=din-konto@gmail.com
   EMAIL_HOST_PASSWORD=<16-tegns app-passord>
   EMAIL_USE_TLS=True
   ```
4. Restart serveren og test bookingflyten med en ekte e-postadresse.

### E-postverifisering (engangskode)

Når kunden skriver inn e-postadressen sin i steg 4, sender de en 6-sifret kode til seg selv via
"Send kode"-knappen og taster den inn før "Bekreft booking" blir klikkbar. Dette skjer i
`booking/views.py` (`send_verification_code`, `verify_email_code`) og lagres i
`EmailVerification`-modellen:

- Koden er gyldig i 30 minutter og maks 5 forsøk før kunden må be om en ny.
- Kunden kan tidligst be om en ny kode 45 sekunder etter forrige.
- Bookingen kan **ikke** fullføres uten en gyldig, verifisert kode for nøyaktig den
  e-postadressen som er skrevet inn – dette håndheves server-side i `BookingForm.clean()`,
  ikke bare i nettleseren, så det kan ikke omgås ved å skru av JavaScript.

## Deploy / hosting

Prosjektet er hosting-agnostisk og klart for f.eks. PythonAnywhere, Render, Railway eller en
egen VPS/DigitalOcean-instans:

- Statiske filer serveres via WhiteNoise (ingen ekstra oppsett nødvendig)
- Databasen styres via `DATABASE_URL` (SQLite lokalt som standard; sett en Postgres-URL i
  produksjon, f.eks. `postgres://bruker:passord@host:5432/dbnavn`)
- Produksjonsserveren startes med Gunicorn (`Procfile` i rotmappa gjør dette automatisk på
  Railway/Render/Heroku-lignende hosting)
- Husk å sette `DEBUG=False`, en ekte `SECRET_KEY` og `ALLOWED_HOSTS` i produksjon

Før dere går live (gjøres automatisk av `Procfile` på Railway): `python manage.py collectstatic`

### Deploy til Railway

1. Push prosjektet til et GitHub-repo (privat er fint).
2. Gå til [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** →
   velg repoet. Railway kjenner igjen `Procfile`-en automatisk og installerer
   `requirements.txt`.
3. Legg til en database: **+ New** → **Database** → **Add PostgreSQL** i samme prosjekt.
   Railway setter `DATABASE_URL` automatisk på web-tjenesten – ingenting å konfigurere.
4. Åpne web-tjenesten → **Variables** og sett minst:
   ```
   SECRET_KEY=<en lang, tilfeldig streng - ikke gjenbruk dev-verdien>
   DEBUG=False
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=din-konto@gmail.com
   EMAIL_HOST_PASSWORD=<gmail app-passord>
   EMAIL_USE_TLS=True
   DEFAULT_FROM_EMAIL=Florø Detailing <din-konto@gmail.com>
   BUSINESS_NOTIFICATION_EMAIL=din-konto@gmail.com
   ```
   (`ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` trenger dere **ikke** sette selv – appen leser
   Railways `RAILWAY_PUBLIC_DOMAIN`-variabel automatisk.)
5. Under **Settings → Networking**, trykk **Generate Domain** for å få en offentlig URL
   (f.eks. `florodetailing.up.railway.app`). Redeploy trigges automatisk.
6. Opprett en admin-bruker på den kjørende tjenesten: i Railway-dashbordet, åpne
   **web-tjenesten → ⋮ → Command Palette → Run command**, og kjør
   `python manage.py createsuperuser`.
7. Vil dere bruke eget domene i stedet for `*.up.railway.app`: **Settings → Networking →
   Custom Domain**, følg instruksjonene for å peke DNS-en deres dit.

Etter dette redeployer Railway automatisk hver gang dere pusher til GitHub-branchen som er
koblet opp.

## Prosjektstruktur

```
florodetailing/   # Django-innstillinger og hoved-URL-er
booking/          # Hele appen: modeller, views, urls, admin, booking-logikk, e-post
  templates/      # HTML-maler (base.html + booking/*.html)
  migrations/
static/           # CSS/JS
```

Alt av forretningslogikk (tjenester, åpningstider, bookinger) ligger samlet i `booking`-appen,
med egne moduler for hver ting (`models.py`, `views.py`, `forms.py`, `availability.py` for
ledig-tid-logikk, `emails.py` for e-postbekreftelser).
