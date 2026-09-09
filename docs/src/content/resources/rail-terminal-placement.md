---
title: "Rail Terminal Placement"
description: "Why 81 states start with a rail terminal, how the two tiers are defined, and the source behind every pick."
---

Before this pass no state in Millennium Dawn started with a `rail_terminal`, so every real-world freight and passenger
hub began the game at zero. 81 states now start with one. This page records the tier criteria, the sources the
selection was drawn from, and the specific hub behind each state, so a later balance or accuracy pass can argue with
the picks instead of guessing at them.

The values live in `history/states/<id>-<name>.txt` inside the `buildings` block. Modding rules for those files are in
[the state README](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/history/states/README.md).

## Data sources

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

## Level 2 states

- **785 Nebraska** - Bailey Yard at North Platte, the largest classification yard in the world.
- **778 Illinois** - Chicago, the largest rail hub in North America. Roughly a quarter of all US rail traffic and the
  only city where all six Class I railroads meet.
- **567 Henan** - Zhengzhou North, the largest marshalling yard in Asia, on the crossing of the Beijing to Guangzhou
  and Longhai trunk lines, with more than 500 trains a day.
- **652 Moscow** - the Moscow junction: nine main-line terminals and the Bekasovo yard, the busiest node of the
  Russian network.
- **615 Kanto** - Tokyo, where Shinjuku is the busiest railway station in the world at about 2.7 million passengers a
  day.
- **56 Ile de France** - Paris, where Gare du Nord is the busiest station in Europe at roughly 700,000 passengers a
  day.
- **1080 Hamburg** - Maschen, the largest marshalling yard in Europe and second largest in the world, feeding the
  Hamburg and Bremerhaven port traffic and the Scandinavian corridor.
- **39 Nordrhein-Westfalen** - Duisburg, the largest inland port in the world and the European end of most China to
  Europe rail freight, alongside the Ruhr yards.
- **13 Greater London** - the densest rail node in Britain. Clapham Junction alone sees about 2,000 train movements a
  day, more than any other station in Europe.
- **431 Haryana** - Delhi, the busiest junction group on Indian Railways and the northern container gateway at ICD
  Tughlakabad.
- **275 Gauteng** - Johannesburg, with City Deep, the largest dry port in Africa, and the Sentrarand yard on the
  Transnet network.

## Level 1 states

### Europe

- **41 Hessen** - Frankfurt, the busiest long-distance station in Germany and the centre of the north to south
  corridor.
- **43 Bayern** - Munich and the Nuremberg yard, the southern German hub.
- **45 Berlin** - the Berlin terminals with the Seddin yard, eastern Germany's freight node.
- **46 West-Nederland** - Rotterdam, and the Betuweroute dedicated freight line to the Ruhr.
- **50 Vlaanderen** - Antwerp port rail and Antwerp-Noord, the largest yard in Belgium.
- **62 Rhone-Alpes** - Lyon and the Sibelin yard on the French north to south freight axis.
- **74 Swiss Plateau** - Basel and Zurich, the northern gate of the Gotthard and Loetschberg transalpine corridors.
- **76 Austria Proper** - Vienna, with Kledering, the largest yard in Austria.
- **80 Lombardia** - Milan and the Smistamento yard, Italy's northern rail gateway.
- **91 Madrid** - the Madrid terminals and the Abronigal container terminal at the centre of the radial Spanish
  network.
- **114 Masovia** - Warsaw, the junction of the Polish network.
- **115 Silesia** - Upper Silesia, the heaviest freight region in Poland, and the Slawkow broad-gauge terminus.
- **117 Bohemia** - Prague and the Ceska Trebova junction.
- **121 Northern Hungary** - Budapest and the Ferencvaros yard, the hub of the Hungarian network.
- **1093 Brest** - the break-of-gauge exchange between 1520 mm and 1435 mm track on the Moscow to Warsaw corridor.
- **698 Kyiv** - the hub of Ukrainian Railways with the Darnytsia yard.
- **644 Leningrad** - Saint Petersburg, the Baltic port rail complex.
- **1244 Istanbul** - Halkali, the European freight terminal of the Turkish network and the Marmaray crossing.

### Russia, Central Asia and Iran

- **676 Sverdlovsk** - Yekaterinburg, the Trans-Siberian hub of the Urals.
- **680 Novosibirsk** - Inskaya, one of the largest yards on the Russian network.
- **682 Krasnoyarsk** - the Trans-Siberian crossing of the Yenisei.
- **692 Primorye** - Vladivostok, the eastern terminus of the Trans-Siberian and its port rail.
- **719 Almaty** - the main junction of the Kazakh network toward the Dostyk border crossing.
- **725 Fergana** - the Fergana valley junctions, the busiest section of the Uzbek network.
- **405 Tehran** - the hub of Iranian Railways where the north to south and Mashhad corridors meet.

### South, East and Southeast Asia

- **426 Sindh** - Karachi port rail, the southern terminus of Pakistan's ML-1 main line.
- **444 Awadh** - the Kanpur and Lucknow junctions on the Delhi to Howrah trunk.
- **452 West Bengal** - Kolkata, with Howrah and Sealdah among the busiest terminals in India, plus Haldia port rail.
- **462 Tamil Nadu** - Chennai, the hub of southern India and its port rail.
- **471 Mumbai** - the Mumbai network and the JNPT port rail, India's largest container flow.
- **508 Central Thailand** - Bangkok, the hub of the State Railway of Thailand.
- **532 Pearl River Delta** - Guangzhou and the Shenzhen port rail.
- **540 Shanghai** - the Shanghai terminals and the Yangshan and Waigaoqiao port rail.
- **547 Beijing** - the capital terminal group with the Fengtai yard.
- **552 Liaoning** - Shenyang and the Dalian port rail, the hub of the Manchurian network.
- **559 Shaanxi** - Xi'an, the assembly point for China to Europe block trains.
- **570 Hubei** - Wuhan, where the Beijing to Guangzhou trunk crosses the Yangtze.
- **592 Xinjiang** - Urumqi, and the Alashankou and Khorgos border crossings into Kazakhstan.
- **604 Gyeonggi** - Seoul and the Uiwang container base.
- **612 Kansai** - Osaka and Kobe with the Suita yard, the western Japanese hub.
- **631 Western Java** - Jakarta, the hub of the Javanese network and Tanjung Priok port rail.

### Africa and North Africa

- **215 Cairo** - Ramses station, the hub of Egyptian National Railways.
- **386 Algerois** - Algiers, the hub of the SNTF network.
- **377 Casablanca-Settat** - Casablanca, the ONCF freight and phosphate hub.
- **334 Lagos** - Apapa port rail, the southern terminus of the Lagos to Kano line.
- **241 Kenyan Coast** - Mombasa, the port terminus of the Kenyan main line.
- **242 Central Kenya** - Nairobi, the junction of the Kenyan network.
- **257 Tanzanian Central Coast** - Dar es Salaam, the terminus of TAZARA and the Central Line.
- **293 Copperbelt** - the Ndola and Kitwe copper railheads.
- **306 Katanga** - Lubumbashi, the Katanga copper railhead toward Zambia and Angola.
- **279 Kwazulu-Natal** - Durban port rail, the busiest container corridor in Africa.
- **281 Western Cape** - Cape Town and the Belcon container terminal.

### Americas

- **763 Ontario** - Toronto and MacMillan Yard, the largest yard on CN.
- **1159 Western Quebec** - Montreal, the eastern hub of both Canadian railways.
- **757 Manitoba** - Winnipeg and Symington Yard, CN's largest in western Canada.
- **754 British Columbia** - Vancouver port rail, Canada's Pacific gateway.
- **811 California** - the Los Angeles and Long Beach port rail on the Alameda Corridor.
- **800 Texas** - Houston and Dallas to Fort Worth, the gateway for Mexican traffic.
- **783 Missouri** - Saint Louis and Kansas City, among the largest US hubs by tonnage.
- **792 Georgia** - Atlanta with the Inman and Tilford yards, the southeastern hub.
- **793 Tennessee** - Memphis, a first-rank intermodal hub served by five Class I railroads.
- **832 Nuevo Leon** - Monterrey, the hub of the Laredo cross-border corridor.
- **882 Sao Paulo** - Sao Paulo and the Santos port railway.
- **884 Minas Gerais** - the Vitoria to Minas iron ore railway.
- **891 Para** - the Carajas railway, one of the heaviest iron ore hauls in the world.
- **453 Pampas** - Buenos Aires, the hub of the Argentine network.

### Oceania

- **1221 New South Wales** - Sydney, with Port Botany rail and the Enfield terminal.
- **741 Queensland** - Brisbane and the central Queensland coal network.
- **743 Victoria** - Melbourne, the interstate standard-gauge hub.
- **746 Western Australia** - Perth and Kwinana, plus the Pilbara ore railways.
