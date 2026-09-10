---
title: Data Sources
description: Historical data behind Millennium Dawn's starting country values.
---

Sources for players who want to check the numbers behind the mod's starting conditions.
These are starting values, not forecasts. Gameplay changes them after the game begins.

## Starting inflation

The January 2000 start uses **1999 annual-average consumer price inflation** where a reported
figure is available. This is the change in the year's average Consumer Price Index (CPI),
not December-to-December inflation.

- **World Bank:** [Inflation, consumer prices (annual %)](https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG).
  The [1999 data](https://api.worldbank.org/v2/country/all/indicator/FP.CPI.TOTL.ZG?date=1999&format=json&per_page=400)
  supplies 159 country and economy matches. Aruba has a reported figure but no matching mod tag.
- **Argentina:** [IMF Country Report 2000/160, Table 1](https://www.elibrary.imf.org/view/journals/002/2000/160/article-A001-en.xml#A01app01tab01).
  Annual-average CPI fell **1.2%** in 1999. This is the historical Buenos Aires headline series,
  not the **1.8%** end-of-period decline.
- **Taiwan:** [Central Bank, 2006 historical indicators](https://www.cbc.gov.tw/public/data/publications/year2006/06-en-key.pdf).
  The 1999 general CPI entry is **0.17%**. This uses the published historical series in that report.

### How the values are used

- Rates are stored as fractions, rounded to five significant digits. For example, the US rate
  of about **2.188%** becomes `inflation_rate_var = 0.02188`.
- Negative rates remain negative. Countries without a sourced figure receive no historical seed;
  a starting zero is not evidence that their real-world inflation was zero.
- Each country's starting rate fills the four-quarter tracker at startup. Later quarterly
  calculations replace one entry at a time, smoothing the first updates.
- Angola, Belarus, and the Democratic Republic of the Congo have reported rates above **200%**.
  Their historical seeds are retained, but the quarterly calculation clamps inflation to **200%**.
- The World Bank's Serbia series is not copied to Kosovo or Montenegro. Its combined West Bank
  and Gaza series is used for Palestine, not Israel or a separate Gaza tag.

## Starting policy rate

`cb_policy_rate` is the central bank policy rate in whole percentage points. The GUI and the
quarterly AI step it by 1 and clamp it to 0-20. The January 2000 start uses the official policy
rate in force on **2000.1.1** where that instrument is documented. Half-percentage values round
half up (5.50 becomes 6). Rates above 20 are stored as 20.

Euro-area founding members already sat at 3, which matches the ECB main refinancing rate of
**3.00%**. Sweden (3.25%) and Denmark (about 3.3%, euro peg) also round to 3, so those files are
unchanged. Countries without a sourced 2000.1.1 policy rate keep the existing default of 3. That
is a fallback, not a claim that their central bank was at 3%. Formables, rebels, and breakaway
tags are not copied from a parent.

Negative policy rates are out of scope. The clamp still bottoms out at 0.

### Seeded values

| Tag | Seed | Rate in force on 2000.1.1                 |
| --- | ---: | ----------------------------------------- |
| JAP |    0 | BoJ overnight call about 0.03% (ZIRP)     |
| SWI |    2 | SNB 3-month Libor target midpoint 1.75%   |
| SIA |    2 | BOT 14-day RP about 1.5%                  |
| CAN |    5 | Bank of Canada overnight target 4.75%     |
| AST |    5 | RBA cash rate 5.00%                       |
| NZL |    5 | RBNZ OCR 5.00%                            |
| CZE |    5 | CNB 2-week repo 5.25%                     |
| KOR |    5 | BoK overnight call about 4.75%            |
| USA |    6 | Fed funds target 5.50%                    |
| ENG |    6 | BoE Bank Rate 5.50%                       |
| NRY |    6 | Norges Bank deposit rate 5.50%            |
| CHI |    6 | PBOC 1-year lending rate 5.85%            |
| MAY |    6 | BNM intervention rate 5.50%               |
| HKG |    7 | HKMA Base Rate 7.00% (Fed + 150 bp)       |
| RAJ |    8 | RBI Bank Rate 8%                          |
| GRE |   11 | Bank of Greece 14-day intervention 10.75% |
| ISR |   11 | Bank of Israel declared rate 10.7%        |
| SAF |   12 | SARB repo about 12% at end-1999           |
| IND |   13 | Bank Indonesia 30-day SBI about 13%       |
| HUN |   15 | MNB base rate 14.50%                      |
| POL |   17 | NBP reference rate 16.50%                 |
| BRA |   19 | Copom SELIC target 19%                    |
| SOV |   20 | CBR refinancing rate 55% (clamped)        |
| TUR |   20 | CBRT overnight well above 20% (clamped)   |
| UKR |   20 | NBU discount rate 45% (clamped)           |
| ROM |   20 | NBR 1999 policy rates above 20% (clamped) |

Greece had not yet joined the euro. The 10.75% rate is the 14-day intervention rate still in
force on 2000.1.1. The Bank of Greece cut it to 9.75% on 26 January 2000. The Bank of England
raised Bank Rate to 5.75% on 13 January 2000. Both files use the New Year's Day setting.

Thailand adopted inflation targeting and an official 14-day RP policy rate in May 2000. The
seed uses the end-1999 14-day repurchase rate, which was already the money-market signal.
Hong Kong's Base Rate is mechanical under the currency board (US federal funds target plus
150 basis points). Chile is omitted: the 1999 TPM was a real rate, not a nominal policy rate.

### Sources

- **ECB:** [Key ECB interest rates](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/key_ecb_interest_rates/html/index.en.html).
  Main refinancing operations were 3.00% from 5 November 1999 through 3 February 2000.
- **Federal Reserve:** [FOMC statement, 16 November 1999](https://www.federalreserve.gov/boarddocs/press/general/1999/19991116/).
  Funds target 5.50% until 2 February 2000.
- **Bank of England:** [Bank Rate history](https://www.bankofengland.co.uk/boeapps/database/Bank-Rate.asp).
  5.50% from 4 November 1999 until the 13 January 2000 hike.
- **Bank of Japan:** [Monetary Policy Meeting minutes, 1999](https://www.boj.or.jp/en/mopo/mpmsche_minu/minu_1999/g990813.htm).
  Zero interest rate policy. Overnight call around 0.03%.
- **Bank of Canada:** [Monetary Policy Report, November 1999](https://www.bankofcanada.ca/1999/11/17-november-1999/).
  Overnight target 4.75% from 17 November 1999.
- **Bank of Korea:** [Base rate history](https://www.bok.or.kr/portal/singl/baseRate/list.do?menuNo=200643).
  Overnight call target 4.75% from 6 May 1999 until 10 February 2000.
- **RBA:** [Cash rate to 5.0%, 3 November 1999](https://www.rba.gov.au/media-releases/1999/mr-99-11.html).
- **RBNZ:** [OCR decisions](https://www.rbnz.govt.nz/monetary-policy/monetary-policy-decisions).
  OCR 5.0% from 17 November 1999.
- **Norges Bank:** deposit rate 5.50% from 23 September 1999.
  [19 January 2000 decision](https://www.norges-bank.no/en/topics/monetary-policy/Monetary-policy-meetings/Key-policy-rate-decisions-2000/19-January-2000-Introduction/) left it unchanged.
- **CNB:** [2-week repo history](https://www.cnb.cz/en/faq/How-has-the-CNB-two-week-repo-rate-changed-over-time/).
  5.25% from 26 November 1999.
- **NBP:** reference rate 16.50% from 18 November 1999.
- **MNB:** base rate 14.50% from 22 December 1999.
- **PBOC:** [1-year lending rate 5.85% from 10 June 1999](https://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125440/125838/125888/2882344/index.html).
- **RBI:** Bank Rate 8% from 1 March 1999.
- **BNM:** intervention rate 5.50% from 9 August 1999.
- **Bank of Greece:** 14-day intervention rate 10.75% until
  [26 January 2000](https://www.bankofgreece.gr/en/news-and-media/press-office/news-list/news?announcement=fcae9b04-63c1-4815-973d-3481b1447b92).
- **Bank of Russia:** refinancing rate 55% until 24 January 2000.
- **NBU:** [discount rate 45% from 24 May 1999 to 1 February 2000](https://bank.gov.ua/en/monetary/archive-rish).
- **Copom / Banco Central do Brasil:** SELIC target 19% from 22 September 1999 through
  21 March 2000.
- **HKMA:** Base Rate equals the US funds target plus 150 basis points when that floor binds.
- **SARB:** repo near 12% at end-1999 after the daily-auction drift in late 1999.
- **Bank Indonesia:** 30-day SBI about 13% in late 1999 (World Bank January 2000 brief).
- **Bank of Israel:** declared rate 10.7% in December 1999.
- **SNB:** 3-month Libor target range 1.25-2.25% at the start of 2000. Midpoint 1.75%.

The seed sits on the next line after `inflation_rate_var` when that country has a
historical inflation value. New tags and later history files should keep
`cb_policy_rate = 3` unless a 2000.1.1 source exists. Runtime startup still writes 3
when the variable is missing.

## Rail Terminal Placement

Before this pass no state in Millennium Dawn started with a `rail_terminal`, so every real-world freight and passenger
hub began the game at zero. 81 states now start with one. This page records the tier criteria, the sources the
selection was drawn from, and the specific hub behind each state, so a later balance or accuracy pass can argue with
the picks instead of guessing at them.

The values live in `history/states/<id>-<name>.txt` inside the `buildings` block. Modding rules for those files are in
[the state README](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/history/states/README.md).

### Data sources

The selection is a curated list, not a mechanical import of one dataset. There is no single global register of rail
terminal capacity that covers 2000 to today, so each pick is anchored to a documented claim about the facility named
in its entry:

- yard size and throughput: [Bailey Yard](https://en.wikipedia.org/wiki/Bailey_Yard) (~2,850 acres, ~139 trains and
  14,000 cars a day), [Maschen](https://en.wikipedia.org/wiki/Maschen_Marshalling_Yard) (280 ha, largest in Europe and
  second largest in the world), and the [list of rail yards](https://en.wikipedia.org/wiki/List_of_rail_yards) for the
  rest
- station passenger throughput: [Guinness World Records](https://www.guinnessworldrecords.com/world-records/busiest-station)
  for Shinjuku (2.7 million a day) and the
  [list of busiest railway stations in Europe](https://en.wikipedia.org/wiki/List_of_busiest_railway_stations_in_Europe)
  for Gare du Nord and the London terminals
- network share: [Chicago Metropolitan Agency for Planning](https://cmap.illinois.gov/regional-plan/goals/recommendation/maintain-the-regions-status-as-north-americas-freight-hub/)
  for Chicago handling about a quarter of US rail traffic with all six Class I railroads present
- intermodal and inland ports: [Port of Duisburg](https://en.wikipedia.org/wiki/Port_of_Duisburg) (world's largest
  inland container port, over 30% of China to Europe rail freight) and
  [City Deep](https://en.wikipedia.org/wiki/City_Deep,_Gauteng) (Africa's largest dry port)

For the gameplay mechanics, see the [Economy Guide](/player-tutorials/economy-guide/).
