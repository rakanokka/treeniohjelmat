# XFit-sovellus

XFit on kuntoilijoille suunnattu sovellus, jossa käyttäjät voivat luoda ja jakaa harjoituskertoja tai harjoitusohjelmia sekä tarkastella harjoituksiin liittyvää kehitystä. Lisäksi käyttäjä voi ottaa käyttöön muiden käyttäjien harjoituksia tai harjoitusohjelmia sekä tarkastella ja kommentoida niitä.

## Sovelluksen käyttäminen

### Tunnuksen luominen ja sisään kirjautuminen

Uusi käyttäjä voi luoda järjestelmään henkilökohtaisen käyttäjätilin **Rekisteröidy**-sivulla syöttämällä uniikin käyttäjänimen sekä salasanan. Rekisteröitymisen yhteydessä salasana tiivistetään turvallisesti tietokantaan ennen tallennusta.

Rekisteröitymisen jälkeen sovellukseen kirjaudutaan sisään **Kirjaudu**-sivulla omilla tunnuksilla. Sisäänkirjautumisesta luodaan turvallinen käyttäjäistunto (`session`), joka pitää käyttäjän kirjautuneena ja mahdollistaa omien treenitietojen hallinnan. Sovelluksesta voi kirjautua ulos milloin tahansa ylävalikon **Kirjaudu ulos** -painikkeesta.

Sovellukseen on myös ladattavissa valmista testidataa alustusskriptin avulla, jolloin voit kirjautua sisään valmiilla testitunnuksilla.

### Treenien ja harjoitusten hallinnointi

Sovelluksessa treenien rakenne pohjautuu uudelleenkäytettäviin treenipohjiin (*workout template*) ja harjoituspohjiin (*exercise template*) sekä niiden toteutuksiin eli varsinaisiin treeneihin (*workout log*) ja harjoituksiin (*exercise log*).

#### Treenien ja harjoitusten lisääminen ja näyttäminen

Yksittäisiä harjoituksia ei voi tarkastella suoraan lisäämättä niitä treeniin. Ainoastaan treeni- ja harjoituspohjia voi tarkastella sellaisenaan. Jotta harjoitukset saadaan näkymään harjoituksien listassa, toimi seuraavasti:

1. **Luo treenipohja:** Siirry luomaan uusi treenipohja, lisää siihen haluamasi harjoitukset ja tallenna pohja.
2. **Luo treeni:** Mene treenipohjien näkymään ja luo/aloita treeni kyseisen pohjan pohjalta.
3. **Lisää liikkeet:** Siirry omiin treeneihin, avaa kyseinen treeni tarkasteluun ja lisää tarvittavat liikkeet.

Tämän jälkeen liike päivittyy näkyviin harjoituksien listaan.

#### Treenien ja harjoitusten muokkaaminen ja poistaminen

Pohjiin (treeni- ja harjoituspohjat) tehdyt päivitykset ja poistot vaikuttavat vain tuleviin treeneihin. Kun muokkaat treeni- tai harjoituspohjaa, muutokset tallentuvat pohjaan eivätkä muuta jo luotujen, historiassa olevien treenien sisältöä. Samoin pohjan poistaminen poistaa sen valittavien pohjien listalta ja treenilokit säilyvät ennallaan. Treenejä voi muokata pohjan poistamisen jälkeen, mutta siihen ei voi lisätä uusia harjoituksia pohjan poistamisen jälkeen.[^1] 

Sovellus käyttää pohjissa versiointia, jolla varmistetaan, etteivät muutokset tai poistot riko muiden käyttäjien treeni- tai harjoituspohjia. Muokattaessa treeni- tai harjoituspohjaa sovellus luo pohjasta uuden version. Jos toinen käyttäjä on jo ottanut pohjan käyttöön, hänen näkymissään säilyy se versio pohjasta, joka oli voimassa käyttöönottohetkellä. Sovellus ilmoittaa käyttäjälle, kun pohjalle löytyy uusi versio, ja käyttäjä voi päivittää pohjan halutessaan viimeisimpään versioon.

Pohja voidaan poistaa kahdella eri tavalla:
* **Viimeisimmän version poisto:** Jos pohjasta poistetaan vain sen viimeisin versio, pohja palautuu automaattisesti edelliseen versioonsa. Tällöin myös kyseistä pohjaa käyttävien muiden käyttäjien näkymät päivittyvät käyttämään tätä edellistä versiota.
* **Koko pohjan poisto:** Koko pohjan poistaminen poistaa pohjan tietokannasta eikä sille voi sen jälkeen luoda treenejä tai harjoituksia. Tällöin pohja poistetaan myös muiden käyttäjien näkymästä, joilla oli pohja käytössä.

### Käyttäjäsivut

Jokaisella rekisteröityneellä käyttäjällä on oma käyttäjäprofiilisivu. Käyttäjäsivulta näkee yhdellä silmäyksellä yhteenvedon käyttäjän aktiivisuudesta.

1. **Aktiivisuus- ja tilastoyhteenveto:**
   * Näyttää luotujen sekä käyttöön otettujen treeni- ja liikepohjien määrät.
   * Näyttää suoritettujen treenien ja yksittäisten toteutuneiden liikkeiden kokonaismäärät.

2. **Omat treenipohjat:**
   * Lista käyttäjän omista ja käyttöön ottamista treenipohjista. Jos pohjia ei vielä ole lisätty, osio ilmoittaa tästä selkeästi.

3. **Suoritetut treenit:**
   * Aikajärjestyksessä oleva lista suoritetuista treeneistä. Jokaisesta treenistä näytetään sen nimi, liikkeiden ja suoritettujen sarjojen kokonaismäärät sekä tarkka suoritusajankohta.

4. **Liikepohjat harjoitusryhmittäin:**
   * Käyttäjän luomat liikepohjat on ryhmitelty esimerkiksi lihasryhmän tai muun kategorian mukaan (esim. *Rinta*, *Selkä*). 
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

> **Huom.** Skriptit on ajettava tässä järjestyksessä tyhjään tietokantaan. Jälkimmäinen skripti edellyttää, että tietokannassa on vähintään kolme käyttäjää avaimilla 1, 2 ja 3. Testidata sisältää käyttäjät `pekka`, `matti` ja `teppo`, joiden kaikkien salasanaksi on määritetty merkkijono `hello1234`.

Kun riippuvuudet on asennettu, sovelluksen voi käynnistää ajamalla

```
flask run
```

Sovellus käynnistyy osoitteessa http://localhost:5000.

---

[^1]: Harjoitusten lisääminen sallitaan sellaisissa treeneissä, jotka perustuvat toisen käyttäjän luomaan pohjaan, jota ei ole poistettu. Jos esimerkiksi poistat käyttöön otetun treenipohjan omalta tililtä, voit edelleen lisätä treeniin kyseiseen pohjaan kuuluvia liikkeitä.

