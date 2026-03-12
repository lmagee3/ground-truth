# Approved Authoritative Sources

Ground Truth only cites sources from this list. Any domain not listed here will be flagged by the verification pipeline.

## US Government

| Domain | Source | Data Type |
|--------|--------|-----------|
| loc.gov | Library of Congress | Historical documents, maps, congressional records, digital collections |
| archives.gov | National Archives (NARA) | Declassified intelligence, diplomatic cables, presidential records |
| cia.gov | CIA World Factbook | Country profiles (260 countries, 200+ fields) |
| state.gov | State Department (FRUS) | 350+ volumes of US diplomatic history since 1861 |
| congress.gov | Congressional Research Service | Non-partisan policy analysis |
| foreignassistance.gov | USAID | US foreign aid disbursements by country/sector |
| usitc.gov | International Trade Commission | Tariff schedules, bilateral trade flows |
| fbi.gov | FBI Crime Data Explorer | Crime statistics, threat assessments |
| treasury.gov | US Treasury | Sanctions lists (OFAC), economic data |
| defense.gov | Department of Defense | Official statements, posture reports |
| fas.org | Federation of American Scientists | Weapons systems, nuclear arsenals, intelligence policy |
| dni.gov | Director of National Intelligence | Threat assessments, intelligence community reports |
| cbo.gov | Congressional Budget Office | Defense spending analysis, budget projections |

## International Institutions

| Domain | Source | Data Type |
|--------|--------|-----------|
| data.worldbank.org | World Bank | 16,000+ development indicators, 50+ year history |
| gdeltproject.org | GDELT Project | 250M+ global events, 300+ categories, real-time |
| acleddata.com | ACLED | 1.3M+ conflict events, 200+ countries |
| ucdp.uu.se | Uppsala Conflict Data Program | 500+ variables, 18 conflict datasets since 1946 |
| data.humdata.org | UN Humanitarian Data Exchange | 18,110+ humanitarian datasets |
| unscr.com | UN Security Council Resolutions | 2,802 resolutions since 1946 |
| comtrade.un.org | UN Comtrade | Bilateral trade data, 170+ countries |
| sipri.org | SIPRI | Arms transfers, military spending, arms industry data |
| transparency.org | Transparency International | Corruption Perceptions Index |
| icj-cij.org | International Court of Justice | Legal rulings, advisory opinions |
| icc-cpi.int | International Criminal Court | Case law, legal findings |

## Allied Government Archives

| Domain | Source | Data Type |
|--------|--------|-----------|
| nationalarchives.gov.uk | UK National Archives | 32M+ records, declassified MI5/MI6 |
| archives.nato.int | NATO Archives | 76 years of alliance documents |
| naa.gov.au | National Archives of Australia | Government records |
| aspi.org.au | Australian Strategic Policy Institute | Defense/security analysis |

## Academic / Research (Peer-Reviewed Only)

| Domain | Source | Data Type |
|--------|--------|-----------|
| doi.org | Digital Object Identifier | DOI-resolved peer-reviewed papers |
| jstor.org | JSTOR | Peer-reviewed academic journals |
| zenodo.org | Zenodo | Open-access research datasets |

## Geographic Data

| Domain | Source | Data Type |
|--------|--------|-----------|
| geonames.org | GeoNames | 11M+ placenames, boundaries |
| naturalearthdata.com | Natural Earth | Public domain map data |

---

## EXPLICITLY NOT APPROVED

These domains are **never** used as sources, regardless of context:

- **wikipedia.org** — Editable by anyone, subject to edit wars on geopolitical topics
- **Any news outlet** (nytimes.com, bbc.com, reuters.com, aljazeera.com, etc.) — Editorial voice, narrative framing
- **Any social media** (twitter.com, reddit.com, facebook.com, telegram.org) — Unverified, manipulable
- **Any blog or opinion site** — Subjective, unverifiable

## Adding New Sources

To propose a new approved source:
1. Open a GitHub Issue with the `source-proposal` label
2. Include: domain, organization name, data type, why it's authoritative
3. Must be: government, international institution, or peer-reviewed academic
4. Antigravity reviews and approves/rejects
