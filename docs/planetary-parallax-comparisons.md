# Planetary parallax and refraction comparisons

Tycho’s records contain a direct observing program for Mars and numerical
diurnal-parallax calculations for Jupiter and Saturn. The tables below hold the
recorded geometry fixed while varying the distance and the refraction rule
independently. For Venus, the last table also varies how the planet’s motion is
removed between the two readings. [Mercury and Venus source analysis](mercury-venus-parallax.md)

## What the outer-planet records contain

- **Mars.** The December 26, 1582 computation adopts Copernicus’s distance of
  721 Earth radii. At 40° altitude the printed 3′39″ is reproduced as 219.15″.
  The printed longitude and latitude corrections are 2′36″ and 2′34″. The
  February 23 and March 10, 1587 records contain direct comparisons at different
  altitudes. A separate reduction for the March 7 opposition uses 3′55″ in
  altitude and adds 3′36″ in latitude. The addition takes 3°34′36″ to 3°38′12″.
  [*Opera Omnia* X, p. 200](https://arsastronomica.com/works/tycho-brahe-thesaurus-observationum-tomus-primus/) · [*Opera Omnia* XI, pp. 181–187](https://arsastronomica.com/works/tycho-brahe-thesaurus-observationum-tomus-secundus/)
- **Jupiter.** The June 29, 1593 opposition reduction subtracts 575 from a
  mean distance of 3,990 Earth radii to get 3,415. This gives 60.4″ of
  horizontal parallax and 59.3″ at 11°, reproducing the printed one minute
  and 59″. The reduction subtracts about 1′ from the 18′ southern latitude
  magnitude after removing refraction. A separate September reduction adopts
  3,042 Earth radii and gives 56″ in altitude at 32⅓°. Direct geometry gives
  57.3″ at the stated upper altitude. The printed longitude and latitude
  components are 22″ and 51″. [*Opera Omnia* XII, pp. 280 and 433](https://arsastronomica.com/works/tycho-brahe-thesaurus-observationum-tomus-tertius/)
- **Saturn.** The March 1599 opposition material adopts 9,400 Earth radii.
  This implies 21.9″ of horizontal parallax. The log adds a computed 18″ in
  ecliptic latitude to 2°48′38″, giving 2°48′56″. Tycho also describes Saturn’s
  small parallax as hard to discern and gives roughly 20″ in the
  *Progymnasmata*. [*Opera Omnia* XIII, pp. 168–169](https://arsastronomica.com/works/tycho-brahe-thesaurus-observationum-tomus-quartus/) · [*Progymnasmata*, p. 414](https://arsastronomica.com/works/tycho-brahe-astronomiae-instauratae-progymnasmata/)

The Jupiter and Saturn reductions establish that the correction was calculated
and used. The cited examples start from model distances. Other passages that
call for testing the “parallax of the orb” concern the annual orbital geometry.
Statements about “parallax of the instrument” concern the observing instrument.
Neither expression supplies a terrestrial-baseline parallax measurement. [Reading and reduction examples](observation-methods.md)

Riccioli tabulated the following horizontal values for the greatest and least
distances in each model. The modern row uses NASA’s approximate distance limits.

| Model | Mars, far to near | Jupiter, far to near | Saturn, far to near |
| --- | ---: | ---: | ---: |
| Ptolemy | 19″–150″ | 11.2″–21.3″ | 7.8″–11.7″ |
| Copernicus | 68″–520″ | 27.7″–44.9″ | 16.5″–22.9″ |
| Tycho | 69″–515″ | 33.2″–60.3″ | 17.0″–28.3″ |
| Longomontanus | 59″–515″ | 24.0″–41.8″ | 14.0″–21.0″ |
| Kepler | 23″–147″ | 9.5″–15.7″ | 5.8″–7.8″ |
| Riccioli | 10″–86″ | 4.3″–7.8″ | 2.3″–3.5″ |
| Modern | 3.3″–24.1″ | 1.36″–2.24″ | 0.79″–1.09″ |

Riccioli’s table covers ten authorities, and [all of them are listed](figures/parallax-model-ranges.csv).
Sources. [Riccioli, *Almagestum Novum* I, p. 700](https://arsastronomica.com/works/giovanni-battista-riccioli-almagestum-novum-tomus-primus-pars-prior/) · NASA fact sheets for [Mars](https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html), [Jupiter](https://nssdc.gsfc.nasa.gov/planetary/factsheet/jupiterfact.html), and [Saturn](https://nssdc.gsfc.nasa.gov/planetary/factsheet/saturnfact.html)

## Outer planets at the recorded altitudes

The historical column uses the distance adopted in the source. For Mars in
1587, the effective 682.1 Earth radii comes from inverting the printed 235″ at
39°. This preserves the historical correction in the comparison. The modern
column takes a dated Earth-to-planet distance from Horizons. The chosen date
anchors the modern range at noon UT, independent of the interpretation of the
source clocks. For Saturn this illustration uses the March 25 meridian altitude
after the logged 35″ instrument adjustment. Its altitude parallax is a separate
quantity from the 18″ ecliptic-latitude correction. [Source clock and projection conventions](mercury-venus-parallax.md#reproducing-the-comparisons)

| Planet and Julian date | Altitude | Historical distance (Earth radii) | Modern range (au) | Historical altitude parallax | Modern altitude parallax |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mars, 1582 Dec 26 | 40° | 721 | 0.64004 | 219.2″ | 10.5″ |
| Mars, 1587 Mar 7 | 39° | 682.1 | 0.65024 | 235.0″ | 10.5″ |
| Jupiter, 1593 Jun 29 | 11° | 3,415 | 4.12913 | 59.3″ | 2.1″ |
| Saturn, 1599 Mar 25 | 35°35′45″ | 9,400 | 8.67392 | 17.8″ | 0.8″ |

### Cross the distance and refraction choices

Use Tycho’s fixed-star table, his solar table as a separate comparison, and
Bennett’s modern apparent-altitude formula under standard conditions (1010 hPa,
10°C). The solar column tests the effect of substituting his solar table for the
stellar one. At Jupiter’s 11° the source uses 5′, which agrees with the stellar
table. At the four altitudes listed above, the stellar corrections are 0″,
0″, 300″, and 0″. The solar corrections are 10″, 15″, 570″, and 32.0″, with
linear interpolation for Saturn. The modern corrections are 71.1″, 73.7″,
295.6″, and 83.3″. [Tycho’s solar and fixed-star tables](https://arsastronomica.com/works/tycho-brahe-astronomiae-instauratae-progymnasmata/) · [Bennett’s refraction formula](https://doi.org/10.1017/S0373463300022037)

Each entry below is **the net change to the indicated altitude** in arcseconds,
treating it as apparent for the comparison. Negative values lower it. Remove
refraction first, then add parallax at the unrefracted topocentric altitude. These
are scenario calculations on the shared input. Applying them to a source’s
published coordinate requires checking what the original reduction already did.

| Case | Distance basis | Tycho stellar | Tycho solar | Bennett standard |
| --- | --- | ---: | ---: | ---: |
| Mars 1582 | Historical | +219.2 | +209.2 | +148.1 |
| Mars 1582 | Horizons | +10.5 | +0.5 | −60.6 |
| Mars 1587 | Historical | +235.0 | +220.0 | +161.4 |
| Mars 1587 | Horizons | +10.5 | −4.5 | −63.1 |
| Jupiter 1593 | Historical | −240.7 | −510.7 | −236.3 |
| Jupiter 1593 | Horizons | −297.9 | −567.9 | −293.5 |
| Saturn 1599 | Historical | +17.8 | −14.2 | −65.4 |
| Saturn 1599 | Horizons | +0.8 | −31.2 | −82.4 |

For apparent altitude `h` in degrees and refraction `R` in arcseconds, set
`u = h − R/3600`. The net change is `asin(cos(u)/n)` converted to arcseconds
minus `R`, with distance `n` in Earth radii. Bennett gives `R = 60 cot(h +
7.31/(h + 4.4))` in arcseconds with the cotangent’s argument in degrees. Get the
DE441 ranges with Horizons observer table quantity `20`, center `500@399`,
targets `4`, `5`, and `6` (planetary barycenters), `TIME_TYPE=UT`, and
`TLIST_TYPE=JD`. The respective Julian dates are `2299243`, `2300775`, `2303081`,
and `2305176`. [Horizons API](https://ssd-api.jpl.nasa.gov/doc/horizons.html)

## Mercury and Venus on the same basis

For Mercury on March 24, 1589 the quantity is **declination**. The three
refraction choices are the printed 480″ declination correction, Tycho’s 600″
stellar *altitude* correction projected into declination (502.2″), and Bennett
projected the same way (496.3″). The parallax corrections are +180″ in the
historical reduction and +7.8″ from the modern distance and geometry. The
altitude of about 5° makes the atmosphere assumption particularly important.
One degree of altitude moves the projected refraction by 50″ to 95″. At 4°
the stellar table gives 554.7″ and Bennett 591.8″. At 6° they give 450.2″
and 425.7″. That is more than the columns below differ from one another.
[Mercury reduction and source references](mercury-venus-parallax.md#reproducing-the-historical-corrections)

| Net change in Mercury declination | Printed refraction | Tycho stellar table | Bennett standard |
| --- | ---: | ---: | ---: |
| Historical parallax | −300.0″ | −322.2″ | −316.3″ |
| Modern parallax | −472.2″ | −494.4″ | −488.5″ |

For Venus on March 4, 1590 the quantity is **evening-minus-meridian declination**.
The two motion estimates come from Tycho’s own meridian series using Origanus’s
interpolation method and from the modern ephemeris. The historical parallax
uses the tangent calculation with Tycho’s 3′ solar scale. The three choices for
the difference in projected refraction are **0″** with Tycho’s stellar table,
**+85.8″** with Longomontanus’s mean of Tycho’s stellar and solar tables, and
**+72.1″** with Bennett. The entries are residuals after subtracting motion,
parallax, and refraction from the same +370″ altitude-derived change. [Venus source data, historical geometry, and projection](mercury-venus-parallax.md#the-march-1590-venus-test)

| Motion estimate | Parallax shift | Tycho stellar | Longomontanus mean | Bennett standard |
| --- | --- | ---: | ---: | ---: |
| Log interpolation +310.2″ | Historical −34.6″ | +94.4″ | +8.6″ | +22.3″ |
| Log interpolation +310.2″ | Modern −1.9″ | +61.7″ | −24.1″ | −10.4″ |
| Horizons +295.0″ | Historical −34.6″ | +109.6″ | +23.8″ | +37.5″ |
| Horizons +295.0″ | Modern −1.9″ | +76.9″ | −8.9″ | +4.7″ |

Several combinations leave small residuals on March 4. The armillae give a
change 65″ larger that night. Choosing a distance or refraction model by the
smallest residual would overlook the disagreement between measurement methods.

### All seven Venus pairs

The same residual can be formed for each of the seven pairs, using the modern
motion for every date. Each entry is the mean over the seven pairs, followed by
the scatter from pair to pair.

| Recorded change | Parallax | Tycho stellar | Longomontanus mean | Bennett standard |
| --- | --- | ---: | ---: | ---: |
| From altitudes | Modern | +67″ ± 55″ | +17″ ± 63″ | +13″ ± 58″ |
| From altitudes | 850 Earth radii | +101″ ± 55″ | +50″ ± 63″ | +47″ ± 59″ |
| By armillae | Modern | +53″ ± 80″ | +2″ ± 68″ | −1″ ± 74″ |
| By armillae | 850 Earth radii | +87″ ± 79″ | +36″ ± 67″ | +33″ ± 73″ |

The pairs scatter by 55″ to 80″, more than eight of the twelve March 4
residuals above. If the pairs were independent, the mean of seven would be
uncertain by 21″ to 30″. Adding either refraction rule lowers the mean by
about 50″, roughly twice that uncertainty. Changing the parallax scale moves
it by 34″, one to one and a half times that uncertainty. The pairs therefore
hint at differential refraction and do not constrain the distance. The
scatter also includes a change in the armillae series after March 15. [Summary for every combination](figures/parallax-venus-scenarios.csv) · [Every term for each pair](figures/parallax-venus-pairs.csv)

The out-of-sample comparison requires other dates with established calibration
and correction states. Origanus’s ingested introduction provides sample ephemeris
directions and a way to interpolate them. It supplies no dated distance series
for these examples. The historical range calculations here therefore come from
the historical model distances and geometry stated above. [Origanus, *Ephemerides Brandenburgicae*](https://arsastronomica.com/works/david-origanus-ephemerides-brandenburgicae/)

## Inputs and reproduction

One [script](../examples/planetary_parallax.py) recomputes every table on this
page and on the [Mercury and Venus page](mercury-venus-parallax.md). It runs
offline and needs NumPy.

- **Printed values.** A [selection script](../examples/parallax_select.py) reads
  [Tychonides 1.3.3](https://github.com/sweisman/tychonides/releases/tag/tychonides-1.3.3)
  and writes the [printed inputs](../examples/parallax-inputs.csv), the
  [Venus pairs](../examples/parallax-venus-pairs.csv), and
  [Riccioli’s table](../examples/parallax-riccioli.csv). Of the 58 printed
  inputs, 29 resolve to one catalog entry with an exact value and 12 to one
  entry the catalog has not yet classified. The other 17 share their digits
  with other entries on the cited pages, so the file gives the count and names
  none. A declared value that disagrees with its catalog entry stops the script.
- **Refraction tables.** Tycho’s solar and fixed-star tables come from the
  [refraction study’s selection](../examples/refraction-tables.csv).
- **Modern values.** A [second script](../examples/parallax_ephemeris.py) caches
  the [Horizons declinations and distances](../examples/parallax-ephemeris.csv)
  at each instant the tables use.
- **Outputs.** The [outer-planet table](figures/parallax-outer-planets.csv), the
  [worked examples](figures/parallax-examples.csv), [Mercury](figures/parallax-mercury.csv),
  the [March 4 scenarios](figures/parallax-venus-march-4.csv), and the
  [single numbers quoted in the text](figures/parallax-checks.csv).

```sh
python examples/parallax_select.py downloads/tychonides.sqlite
python examples/parallax_ephemeris.py
python examples/planetary_parallax.py --output docs/figures
```

Only the last command is needed to regenerate the tables.
