# Seminar 1 - spletni pajek

Navodila naloge se nahajajo [tukaj](https://szitnik.github.io/wier-labs/PA1.html).

## Namestitev

```bash
cd programming_assignment1/crawler

# Create a new virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install required libraries and modules
pip install -r requirements.txt

# Copy and edit crawler configuration
cp example_configuration.yaml configuration.yaml
```

Pajka poženemo tako, da mu podamo zastavico s potjo do konfiguracijske datoteke.

```bash
python .\main.py --configuration .\configuration.yaml
```

## TODO

* [ ] Spoznavni sestanek
* [ ] Razdelitev dela
* [ ] Poimenovanje skupine