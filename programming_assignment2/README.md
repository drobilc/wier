# Seminar 2 - ekstrakcija podatkov

Navodila naloge se nahajajo [tukaj](https://szitnik.github.io/wier-labs/PA2.html).

## Namestitev

```bash
cd programming_assignment2/extraction

# Create a new virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install required libraries and modules
pip install -r requirements.txt
```

## Uporaba

### Regularni izrazi

```bash
# Overstock - regularni izrazi
python .\run-extraction.py regex-overstock .\data\overstock.com\

# RTV SLO - regularni izrazi
python .\run-extraction.py regex-rtvslo .\data\rtvslo.si\

# Avto.net - regularni izrazi
python .\run-extraction.py regex-avtonet .\data\avto.net\
```

### XPath izrazi

```bash
# Overstock - XPath izrazi
python .\run-extraction.py xpath-overstock .\data\overstock.com\

# RTV SLO - XPath izrazi
python .\run-extraction.py xpath-rtvslo .\data\rtvslo.si\

# Avto.net - XPath izrazi
python .\run-extraction.py xpath-avtonet .\data\avto.net\

# Bolha - XPath izrazi
python .\run-extraction.py xpath-bolha .\data\bolha.com\
```

### Avtomatična ekstrakcija podatkov

```bash
# Overstock - avtomaticna ekstrakcija
python .\run-extraction.py automatic .\data\overstock.com\jewelry01.html .\data\overstock.com\jewelry02.html

# Overstock - avtomaticna ekstrakcija in shranjevanje HTML vsebine v datoteko result.html
python .\run-extraction.py automatic .\data\overstock.com\jewelry01.html .\data\overstock.com\jewelry02.html > result.html
```