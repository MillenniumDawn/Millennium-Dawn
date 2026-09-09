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
