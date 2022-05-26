# Seminar 3 - implementacija preprostega indeksa

Navodila naloge se nahajajo [tukaj](https://szitnik.github.io/wier-labs/PA3.html).

## Namestitev

```bash
cd programming_assignment3/implementation-indexing

# Create a new virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install required libraries and modules
pip install -r requirements.txt
```

## Uporaba

### Kreiranje podatkovne baze

```bash
#pot do datotek HTML je lahko aboslutna ali relativna
python createBase.py --path pot_do_datotek
```

### Iskanje po bazi

```bash
# argument --dbpath je opcijski
# če arguemnt ni podan, program bazo z imenom inverted-index.db išče v imeniku, kjer poženemo program
python run-sqlite-search.py --query "besede ločene s presledkom" [--dbpath pot do obsoječe baze]
```

### Iskanje po HTML datotekah

```bash
#pot do datotek HTML je lahko aboslutna ali relativna
python run-basic-search.py --query "besede ločene s presledkom" --path pot_do_datotek
```

### Že kreirana baza podatkov
Bazo podatkov, narejeno s createBase.py, lahko snamete na [povezavi](https://drive.google.com/file/d/1CDF1kLlZ_72cYs-poq0AkLnbQV0hOQz2/view?usp=sharing).