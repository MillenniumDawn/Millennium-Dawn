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

For the gameplay mechanics, see the [Economy Guide](/player-tutorials/economy-guide/).
