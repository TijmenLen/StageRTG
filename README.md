# StageRTG

**Masterstage M2 Technische Geneeskunde**  
**Radiotherapiegroep Deventer**  
**Tijmen Lensink**  
**2026**


## Automatisering van hart- en longsparende optimalisaties voor slokdarmkanker in RayStation

### Achtergrond

Deze repository bevat alle Python-scripts die zijn ontwikkeld en gebruikt tijdens de masterstage van Tijmen Lensink bij Radiotherapiegroep.

De scripts zijn ontwikkeld binnen de Python-omgeving van RayStation en zijn gebruikt voor:

- Ontwikkeling van hart- en longsparende optimalisatiestrategieën;
- Validatie van verschillende optimalisatieparameters;
- Geautomatiseerde verwerking van een volledig patiëntcohort;
- Extractie van dosimetrische en plangerelateerde gegevens;
- Berekening van NTCP-scores op basis van bestaande modellen;
- Vergelijking van klinische plannen met automatisch gegenereerde alternatieven.

Deze repository wordt toegevoegd als appendix bij het masterstageverslag en dient als technische documentatie van de gebruikte analysemethoden, optimalisatiestrategieën en automatiseringen.

---

## Softwareomgeving

Alle scripts zijn ontwikkeld voor uitvoering binnen:

- RayStation
- Python (ingebouwde RayStation Python-omgeving)

De scripts zijn niet ontworpen als zelfstandige Python-programma's buiten RayStation en maken gebruik van RayStation-specifieke functionaliteit voor planmanipulatie, optimalisatie en data-extractie.

---

## Doel van de repository

Het doel van deze repository is het documenteren van de scripts die zijn gebruikt tijdens de masterstage voor:

1. Het ontwikkelen van hart- en longsparende optimalisatiestrategieën;
2. Het valideren van optimalisatieparameters;
3. Het uitvoeren van geautomatiseerde cohortanalyses;
4. Het exporteren van dosimetrische en plangerelateerde gegevens;
5. Het berekenen van NTCP-scores;
6. Het ondersteunen van de analyses beschreven in het masterstageverslag.

---

# Repositorystructuur

## 1. Optimalisatiestrategieën

Deze scripts implementeren de ontwikkelde optimalisatiestrategieën. Voor ieder script wordt een kopie van het huidige behandelplan gemaakt, waarna aanvullende optimalisatiedoelen worden toegevoegd en de RayStation Fine-Tuner wordt uitgevoerd.

### `Hart_compleet.py`

Voert de hartsparende optimalisatiestrategie uit op het momenteel geopende behandelplan.

**Functionaliteit**
- Maakt een kopie van het actieve behandelplan;
- Voegt aanvullende hartgerichte optimalisatiedoelen toe;
- Voert de RayStation Fine-Tuner uit;
- Genereert automatisch een hartsparende planvariant.

---

### `Long_compleet.py`

Voert de longsparende optimalisatiestrategie uit op het momenteel geopende behandelplan.

**Functionaliteit**
- Maakt een kopie van het actieve behandelplan;
- Voegt aanvullende longgerichte optimalisatiedoelen toe;
- Voert de RayStation Fine-Tuner uit;
- Genereert automatisch een longsparende planvariant.

---

### `Hart+Long.py`

Combineert beide optimalisatiestrategieën binnen één script.

**Functionaliteit**
- Maakt twee kopieën van het oorspronkelijke behandelplan;
- Genereert een hartsparende planvariant;
- Genereert een longsparende planvariant;
- Ondersteunt directe vergelijking van beide strategieën.

---

## 2. Ontwikkeling en validatie van de strategieën

Deze scripts zijn gebruikt tijdens de ontwikkelfase van de optimalisatiestrategieën.

Het doel van deze scripts was het bepalen van geschikte parameterinstellingen voor de uiteindelijke hart- en longsparende strategieën.

### `Validatie_Hart.py`

Genereert meerdere kopieën van een bestaand behandelplan met verschillende parameterinstellingen voor de hartsparende strategie.

**Functionaliteit**
- Maakt meerdere planvarianten;
- Test verschillende optimalisatie-instellingen;
- Exporteert resultaten naar CSV-bestanden;
- Ondersteunt parameteroptimalisatie van de hartsparende strategie.

---

### `Validatie_Long.py`

Genereert meerdere kopieën van een bestaand behandelplan met verschillende parameterinstellingen voor de longsparende strategie.

**Functionaliteit**
- Maakt meerdere planvarianten;
- Test verschillende optimalisatie-instellingen;
- Exporteert resultaten naar CSV-bestanden;
- Ondersteunt parameteroptimalisatie van de longsparende strategie.

---

## 3. Cohortanalyse

Deze scripts zijn gebruikt voor geautomatiseerde verwerking van het volledige patiëntcohort.

### `Cohort.py`

Voert de hart- en longsparende strategieën uit voor alle patiënten binnen het onderzochte cohort.

**Functionaliteit**
- Doorloopt het volledige cohort;
- Voert hart- en longsparende optimalisaties uit;
- Past geen MU-limiet toe;
- Exporteert relevante plan- en dosisgegevens.

---

### `Cohort_MU.py`

Variant van `Cohort.py` waarbij een limiet op het aantal Monitor Units (MU) wordt toegepast.

**Functionaliteit**
- Doorloopt het volledige cohort;
- Voert hart- en longsparende optimalisaties uit;
- Houdt rekening met een vooraf ingestelde MU-limiet;
- Exporteert plan- en dosisgegevens.

---

### `Cohort_declined.py`

Voert dezelfde analyse uit als `Cohort.py`, maar uitsluitend voor patiënten met een declined behandelplan.

**Functionaliteit**
- Selecteert alleen patiënten met een declined plan;
- Voert hart- en longsparende optimalisaties uit;
- Exporteert relevante analysegegevens.

---

### `Cohort data export.py`

Script voor grootschalige data-extractie van alle beschikbare behandelplannen binnen het cohort.

**Geëxporteerde gegevens omvatten onder andere**
- Clinical Goals;
- DVH-gegevens;
- Gemiddelde orgaandoses;
- Monitor Units (MU);
- Plantype;
- Planstatus;
- Overige relevante dosimetrische parameters.

Dit script vormde de basis voor een groot deel van de verdere analyses binnen de masterstage.

---

## 4. NTCP-modellen

Deze scripts zijn gebruikt voor het berekenen van voorspelde toxiciteitsrisico's op basis van bestaande NTCP-modellen.

### `pneumonia_model.py`

Implementatie van het UMCG NTCP-model voor pneumonie.

**Functionaliteit**
- Berekent het voorspelde risico op pneumonie;
- Gebruikt patiënt- en dosimetrische kenmerken als invoer;
- Dient als basis voor cohortbrede NTCP-analyses.

---

### `Cohort NTCP pneumonia.py`

Past het UMCG pneumonie-NTCP-model toe op alle plannen binnen het cohort.

**Functionaliteit**
- Doorloopt alle plannen binnen het cohort;
- Berekent NTCP-scores voor pneumonie;
- Exporteert de resultaten voor verdere analyse.

---

### `Cohort NTCP NIPP.py`

Past het NTCP-model toe dat wordt gebruikt binnen het Nederlandse Indicatie Protocol Protonentherapie (NIPP).

**Functionaliteit**
- Doorloopt alle plannen binnen het cohort;
- Berekent NTCP-scores volgens het NIPP-model;
- Exporteert de resultaten voor verdere analyse en vergelijking.

---

## Workflow

De globale workflow van de masterstage was als volgt:

1. Ontwikkelen van hart- en longsparende optimalisatiestrategieën;
2. Valideren van verschillende parameterinstellingen;
3. Toepassen van de definitieve strategieën op het volledige cohort;
4. Exporteren van dosimetrische en plangerelateerde gegevens;
5. Berekenen van NTCP-scores;
6. Vergelijken van klinische plannen met automatisch gegenereerde alternatieven;
7. Statistische analyse van de resultaten.

---

## Patiëntdata

De scripts in deze repository zijn ontwikkeld voor gebruik binnen een klinische onderzoeksomgeving.

Vanwege privacywetgeving en de AVG zijn geen patiëntgegevens opgenomen in deze repository. Eventuele geëxporteerde datasets, CSV-bestanden of andere onderzoeksresultaten zijn niet inbegrepen.

---

## Relatie met het masterstageverslag

Deze repository bevat de scripts die zijn gebruikt voor de dataverzameling, planoptimalisatie en NTCP-analyses zoals beschreven in het masterstageverslag van Tijmen Lensink.

De repository dient als technische appendix ter ondersteuning van de reproduceerbaarheid, transparantie en documentatie van de uitgevoerde analyses.

---

## Repositorybeschrijving

RayStation Python-scripts ontwikkeld tijdens een masterstage voor hart- en longsparende planoptimalisatie, cohortanalyse en NTCP-modellering bij slokdarmkanker.
