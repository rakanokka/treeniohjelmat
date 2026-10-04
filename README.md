# XFit-sovellus

XFit on kuntoilijoille suunnattu sovellus, jossa käyttäjät voivat luoda ja jakaa harjoituskertoja tai harjoitusohjelmia sekä tarkastella harjoituksiin liittyvää kehitystä. Lisäksi käyttäjä voi ottaa käyttöön muiden käyttäjien harjoituksia tai harjoitusohjelmia sekä tarkastella ja kommentoida niitä.

## Sovelluksen käyttäminen

### Tunnuksen luominen ja sisään kirjautuminen

Uusi käyttäjä voi luoda järjestelmään henkilökohtaisen käyttäjätilin **Rekisteröidy**-sivulla syöttämällä uniikin käyttäjänimen sekä salasanan. Rekisteröitymisen yhteydessä salasana tiivistetään turvallisesti tietokantaan ennen tallennusta.

Rekisteröitymisen jälkeen sovellukseen kirjaudutaan sisään **Kirjaudu**-sivulla omilla tunnuksilla. Sisäänkirjautumisesta luodaan turvallinen käyttäjäistunto (`session`), joka pitää käyttäjän kirjautuneena ja mahdollistaa omien treenitietojen hallinnan. Sovelluksesta voi kirjautua ulos milloin tahansa sivupalkin tai ylävalikon **Kirjaudu ulos** -painikkeesta.

Sovellukseen on myös ladattavissa valmista testidataa alustusskriptin avulla, jolloin voit kirjautua sisään valmiilla testitunnuksilla.

### Treeni- ja harjoituspohjien hallinnointi

Sovelluksessa treenien rakenne pohjautuu uudelleenkäytettäviin treenipohjiin (*workout template*) ja harjoituspohjiin (*exercise template*). Voit hallinnoida niitä seuraavasti:

1. **Uuden treenipohjan luominen:**
   * Luo uusi treenipohja syöttämällä sille nimi, kuvaus sekä valitsemalla siihen kuuluvat harjoitukset tavoitesarjoineen ja -toistoineen (esim. Kyykky 3 x 8).
   * Harjoituksia voi lisätä treenipohjaan kaikista itse luoduista tai muiden luomista ja omalle tilille käyttöön otetuista harjoituspohjista.
   * Voit liittää treeniin luokitusta helpottavia tägejä (esim. `Voima`, `Yläkeho`, `Koti`). Syötetyt tägit kytketään automaattisesti treenipohjaan.

2. **Muiden käyttäjien treenipohjien selaaminen ja haku:**
   * Voit selata kaikkia järjestelmään luotuja julkisia treenipohjia sekä ryhmitellä niitä tägien perusteella klikkaamalla mitä tahansa tägilinkkiä.
   * Tällä hetkellä muiden käyttäjien treenipohjia voi ottaa käyttöön omalle treenilistalle hakusivun kautta nimellä hakemalla (käyttöönotto tägisuodatuksen kautta ei ole vielä tuettu).

3. **Muokkaaminen ja poistaminen:**
   * Voit muokata ja päivittää itse luomiasi treenipohjia sekä niiden harjoituksia ja tägejä milloin tahansa.
   * Voit poistaa itse luomasi treenipohjan järjestelmästä tai poistaa toisen käyttäjän luoman pohjan omalta omien treenien listaltasi.
   * **Huom.** Tällä hetkellä treeni- tai harjoituspohjan muokkaaminen tai poistaminen luojan toimesta vaikuttaa suoraan myös kaikkien niiden käyttäjien näkymiin, jotka ovat ottaneet kyseisen pohjan käyttöön. Tämä on väliaikainen toteutustapa.

4. **Treenin luominen treenipohjasta:**
   * Voit aloittaa uuden treenisuorituksen suoraan treenipohjaan liitetyn **Tee treeni** -painikkeen kautta (löytyy sekä itse luoduista että käyttöön otetuista treenipohjista).
   * Sovellus luo pohjan perusteella valmiin runko-osion, johon voit kirjata todelliset suoritetut sarjat, toistot ja käytetyt painot treenin.
   * Valmiin treenin tallentaminen luo järjestelmään pysyvän treenilokin (*workout log*), jota ei enää muuteta, vaikka alkuperäistä treenipohjaa muokattaisiin myöhemmin.

### Käyttäjäsivut

Jokaisella rekisteröityneellä käyttäjällä on oma käyttäjäprofiilisivu, joka toimii tilastojen ja omien sisältöjen keskuksena. Käyttäjäsivulta näkee yhdellä silmäyksellä yhteenvedon käyttäjän aktiivisuudesta sekä linkit kaikkiin hänen luomiinsa tai käyttöön ottamiinsa kokonaisuuksiin.

Profiilisivulta löytyvät seuraavat tiedot ja osiot:

1. **Aktiivisuus- ja tilastoyhteenveto:**
   * Näyttää luotujen sekä käyttöön otettujen treeni- ja liikepohjien määrät.
   * Näyttää suoritettujen treenien ja yksittäisten toteutuneiden liikkeiden kokonaismäärät.

2. **Omat treenipohjat:**
   * Lista käyttäjän omista ja käyttöön ottamista treenipohjista. Jos pohjia ei vielä ole lisätty, osio ilmoittaa tästä selkeästi.

3. **Suoritetut treenit:**
   * Aikajärjestyksessä oleva lista suoritetuista treeneistä. Jokaisesta treenistä näytetään sen nimi, liikkeiden ja suoritettujen sarjojen kokonaismäärät sekä tarkka suoritusajankohta.

4. **Liikepohjat harjoitusryhmittäin:**
   * Käyttäjän luomat liikepohjat on ryhmitelty lihasryhmän/kategorian mukaan (esim. *Rinta*, *Selkä*).
   * Kategoriakohtaisesti näytetään luotujen liikepohjien määrä sekä se, kuinka moneen treenipohjaan kyseisen kategorian liikkeitä on liitetty.

### Kommentointi

Sovelluksessa käyttäjät voivat viestiä keskenään ja antaa palautetta treeni- ja harjoituspohjista. Treeni- tai harjoituspohjan sivulla näkyvät kaikki siihen liitetyt kommentit aikajärjestyksessä.

## Sovelluksen asennus ja käynnistäminen

Sovellus on suunniteltu suoritettavaksi Linux- tai macOS-ympäristössä. Sovelluksen ajaminen Windowsilla edellyttää WSL-ympäristöä (Windows Subsystem for Linux). 

> **Huom.** WSL ei kuitenkaan kaikin puolin vastaa natiivia Linux-ympäristöä, joten suositeltava alusta on Linux tai macOS.

Varmista ennen aloittamista, että koneellesi on asennetuina seuraavat työkalut:
* **Git**
* **Python 3.10+** (mukaan lukien `pip` ja `venv`)
* **SQLite3**

> **Huom.** Projektin Python-koodissa käytetään runsaasti tyyppivihjeitä, jotka otettiin käyttöön versiossa 3.5. Versio 3.5 ei välttämättä tunnista kaikkia tyyppivihjeitä. Siten suositeltavaa on käyttää Python 3.10+. 

Kloonaa projekti paikallisesti koneellesi ja siirry projektin juurihakemistoon:

```bash
git clone git@github.com:rakanokka/treeniohjelmat.git xfit
cd xfit
```

Suositeltava tapa on suorittaa sovellusta Python-virtuaaliympäristössä ja asentaa sinne tarvittavat riippuvuudet:

```bash
python3 -m venv venv
source venv/bin/activate
pip install flask
```

Sovelluksen käyttö edellyttää olemassa olevaa tietokantaa. Luo tietokanta suorittamalla

```bash 
sqlite3 xfit_dev.db < schema.sql
```

> **Huom.** Sovellus ei luo tyhjää tietokantaa eikä käynnisty, jos se ei löydä tiedostossa `config.py` määritettyä polkua tietokantaan. 

Mikäli haluat käyttää sovellusta valmiiksi syötetyllä testidatalla, voit lisätä tiedot tietokantaan suorittamalla

```bash 
sqlite3 xfit_dev.db < seed_users.sql
sqlite3 xfit_dev.db < seed_workouts.sql
```

> **Huom.** Skriptit on ajettava tässä järjestyksessä tyhjään tietokantaan. Jälkimmäinen skripti edellyttää, että tietokannassa on vähintään kolme käyttäjää avaimilla 1, 2 ja 3. Testidata sisältää käyttäjät `pekka`, `matti` ja `teppo`, joiden kaikkien salasanaksi on määritetty merkkijono `hello`.

Kun riippuvuudet on asennettu, sovelluksen voi käynnistää ajamalla

```
flask run
```

Sovellus käynnistyy osoitteessa http://localhost:5000.
