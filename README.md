# XFit-sovellus

XFit on kuntoilijoille suunnattu sovellus, jossa käyttäjät voivat luoda ja jakaa harjoituskertoja tai harjoitusohjelmia sekä tarkastella harjoituksiin liittyvää kehitystä. Lisäksi käyttäjä voi ottaa käyttöön muiden käyttäjien harjoituksia tai harjoitusohjelmia sekä tarkastella ja kommentoida niitä.

## Sovelluksen kuvaus

### Sovelluksen toiminnot

Sovelluksen perustoiminnot ovat seuraavat:

* Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.
* Käyttäjä pystyy lisäämään sovellukseen harjoituskertoja sekä harjoituskerroista koostuvia suunnitelmallisia harjoitusohjelmia.
* Käyttäjä pystyy muokkaamaan ja poistamaan käytössään olevia harjoituskertoja tai -ohjelmia.
* Käyttäjä voi tarkastella käytössään olevia harjoituksia sekä myös muiden harjoituksia.
* Jokaisella harjoituksella on luoja, joka on harjoituksen lisännyt käyttäjä. Käyttäjä voi tarkastella muiden käyttäjien luomia (ja mahdollisesti käyttöön ottamia) harjoituksia.
* Käyttäjä pystyy etsimään harjoituksia hakusanalla, henkilön tai käyttäjän nimellä sekä harjoitusryhmän perusteella (sekä mahdollisesti myös muilla perusteilla).
* Sovelluksessa on käyttäjäsivut, jotka näyttävät käyttäjä- sekä harjoituskohtaisia tietoja ja tilastoja.
* Käyttäjä voi luokitella lisäämänsä harjoitukset erilaisiin ryhmiin, jotka määritetään tietokannassa. Käyttäjä voi valita jokaisen luokittelun kohdalla yhden tai useamman vaihtoehdon.
* Käyttäjä pystyy lisäämään kommentteja ja muistiinpanoja (toissijainen tietokohde) sekä omiin että muiden käyttäjien harjoituskertoihin ja -ohjelmiin.

Tiivistetysti sovellus toimii siten, että käyttäjä voi lisätä tililleen treenejä, jotka koostuvat yksittäisistä harjoituksista (liikkeistä). Treenit ja harjoitukset jaetaan pohjiin ja varsinaisiin toteutuksiin, joista jälkimmäiset toimivat periaatteessa suoritusten lokitietoina. Pohjat ovat sovelluksessa jaettavia, muokattavia ja poistettavia tietokohteita, kun taas toteutuneita treeni- tai harjoitustietoja ei voi jakaa tai muokata.

Nykytoteutuksessa sovelluksella pystyy

* luomaan tunnuksen ja kirjautumaan sisään sovellukseen
* lisäämään omia harjoituspohjia sekä ottamaan käyttöön muiden käyttäjien harjoituspohjia
* tarkastelemaan harjoituspohjia (omia ja käyttöön otettuja) sekä harjoituksia
* muokkaamaan ja poistamaan omia harjoituspohjia sekä poistamaan käyttöön otettuja harjoituspohjia
* etsimään muiden käyttäjien lisäämiä harjoituspohjia harjoituksen nimellä

Nykyinen toteutus sisältää kaksi merkittävää puutetta sovelluksen käyttöön liittyen. Molempien korjaaminen edellyttää hienovaraisempaa suunnittelua tietokannan rakennetta koskien, joten olen päättänyt siirtää niiden lopulliset toteutukset myöhempään vaiheeseen.[^1] Ensinnäkin käyttäjällä on mahdollisuus muokata vain omia harjoituspohjiaan. Toiseksi pohjan muokkaus tai poisto vaikuttaa muiden käyttäjien tietohin, joilla on harjoituspohja käytössä. Toisin sanoen jos luoja muokkaa pohjaa tai poistaa sen, muutetut tiedot näkyvät muilla käyttäjillä tai poistuvat heidän kannastaan. Molemmat rajoitteet perustuvat siihen, että en ole vielä tarkalleen oivaltanut tehokasta keinoa erottaa käyttäjän omia ja käyttöön otettuja harjoituspohjia kopiomatta rivejä tietokannassa. Kuten arvata saattaa, tietojen kopionti johtaisi epätoivottuun tilanteeseen, kun tuhat eri käyttäjää lisää tililleen yhden käyttäjän pohjan: tietokannassa olisi vähintään 1001 lähes identtistä riviä.

Harjoituspohjien poistot ja muokkaukset eivät vaikuta niihin perustuviin harjoituksiin, joita käyttäjä on lisännyt sovellukseen. Lisätyt harjoitukset ovat erillisiä kohteita tietokannassa eikä niiden tarkastelu riipu harjoituspohjasta.[^2] Siten jos käyttäjä esimerkiksi poistaa luodun pohjan tai muokkaa sitä, jolle hän on aikaisemmin lisännyt harjoituksen, hän voi poiston tai muokkauksen jälkeen edelleen tarkastella harjoitusta alun perin lisätyssä muodossa. Toisaalta harjoituksen lisääminen edellyttää, että sille on olemassa harjoituspohja.[^3]

### Sovelluksen käyttäminen

Sovelluksen käyttäminen vaatii sisäänkirjautumista. Jos käytät sovellusta testidatalla, tietokannassa on kolme testikäyttäjää valmiiksi lisättynä (ks. ohjeet alla sovelluksen asennukseen liittyen). Kirjautuneena käyttäjänä voit tarkastella harjoituksia `Harjoitukset`-linkin kautta. Linkki johtaa sivulle, jossa yllä kuvatut toiminnot ovat toteteutettavissa. Sovellus ei vielä tue vastaavia (tai muitakaan) toimintoja `Treenit`-sivustolla. Niihin liittyvät sivut ovat pahasti keskeneräisiä ja niille siirtyminen voi jopa johtaa palvelimen kaatumiseen.

## Sovelluksen asennus ja käynnistäminen

Sovellus on suunniteltu suoritettavaksi Linux- tai macOS-ympäristössä. Sovelluksen ajaminen Windowsilla edellyttää WSL-ympäristöä (Windows Subsystem for Linux). 

> **Huom.** WSL ei kuitenkaan kaikin puolin vastaa natiivia Linux-ympäristöä, joten suositeltava alusta on Linux tai macOS.

Varmista ennen aloittamista, että koneellesi on asennetuina seuraavat työkalut:
* **Git**
* **Python 3.10+** (mukaan lukien `pip` ja `venv`)
* **SQLite3**

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
sqlite3 database/xfit_dev.db < src/db/schema.sql
```

> **Huom.** Sovellus ei luo tyhjää tietokantaa eikä käynnisty, jos se ei läydä tiedostossa `config.py` määritettyä polkua tietokantaan. 

Mikäli haluat käyttää sovellusta valmiiksi syötetyllä testidatalla, voit lisätä tiedot tietokantaan suorittamalla

```bash 
sqlite3 database/xfit_dev.db < src/db/seed_users.sql
sqlite3 database/xfit_dev.db < src/db/seed_workouts.sql
```

tai vaihtoehtoisesti `Flask`-komentorivin kautta

```bash 
flask --app run db-seed-users
flask --app run db-seed-workouts
```

> **Huom.** Skriptit on ajettava tässä järjestyksessä tyhjään tietokantaan. Jälkimmäinen skripti edellyttää, että tietokannassa on vähintään kolme käyttäjää avaimilla 1, 2 ja 3. Testidata sisältää käyttäjät `pekka`, `matti` ja `teppo`, joiden kaikkien salasanaksi on määritetty merkkijono `hello`.

Kun riippuvuudet on asennettu, sovelluksen voi käynnistää ajamalla

```
python3 run.py
```

Sovellus käynnistyy osoitteessa http://localhost:5000.

---

[^1]: Tietokannan rakenne tulee joka tapauksessa muuttumaan projektin aikana, joten nykytoteutus on muutenkin vain väliaikainen.
[^2]: Harjoitus viittaa vierasavaimella harjoituspohjaan, joka on `NULLABLE`. Vierasavain saa arvon `NULL`, jos harjoitukseen liitetty pohja poistetaan taulusta.  
[^3]: Sovelluksen nykyinen tila ei mahdollista harjoitusten lisäämistä ja vaatimus pohjan olemassaolosta toteutetaan todennäköisesti sovellustasolla. Tietokanta mahdollistaa harjoitusten lisäämisen ilman pohjaa, koska vierasavain on `NULLABLE`.
