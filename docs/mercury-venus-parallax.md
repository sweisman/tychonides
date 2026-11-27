# Mercury and Venus parallax

**In plain terms.** Tycho calculated how far parallax should lower Mercury and
Venus in the sky. In March 1590 he tested it on Venus by comparing readings
taken high and low, and found no drop he could detect. This page reproduces
his numbers and shows what his readings can and cannot decide. The
[plain-language guide](plain-language.md) explains the terms.

Tycho calculated parallax corrections for both Mercury and Venus. For Venus he
also made an observational test. In March 1590 he compared readings near the
meridian with readings farther west and judged the parallax imperceptible. He
expected about 4′ under the Ptolemaic hypothesis. His *Progymnasmata*, p. 414,
discusses the difficulty of testing all three superior planets, explicitly reports
repeated attempts on Mars, and identifies proximity to the Sun as an obstacle to
observing Mercury and Venus when they are closest to Earth. [Thesaurus Observationum III, *Opera Omnia* XII, pp. 52, 60, and 69](https://arsastronomica.com/works/tycho-brahe-thesaurus-observationum-tomus-tertius/) · [Astronomiae Instauratae Progymnasmata](https://arsastronomica.com/works/tycho-brahe-astronomiae-instauratae-progymnasmata/)

## The historical distance scale

Tycho’s nominal 3′ horizontal solar parallax gives a Sun–Earth distance of
1,146 Earth radii. Using the modern equatorial radius to express that distance
in modern units gives 7.31 million km or 4.54 million miles, close to the rounded
4.6 million miles. At one modern astronomical unit the corresponding angle is
8.79″. The historical scale therefore makes the horizontal parallax about 20.5
times greater for the same relative orbital geometry. [Progymnasmata, solar-parallax table and p. 414](https://arsastronomica.com/works/tycho-brahe-astronomiae-instauratae-progymnasmata/) · [JPL equatorial Earth radius](https://ssd.jpl.nasa.gov/planets/phys_par.html) · [JPL value of the astronomical unit](https://ssd.jpl.nasa.gov/astro_par.html)

For distance `n` in Earth radii the horizontal angle is `asin(1/n)`. At apparent
altitude `h` the altitude correction is `asin(cos(h)/n)` on a spherical Earth,
ignoring refraction. Right ascension, declination, and ecliptic components each
require their own projection.

## Reproducing the historical corrections

Tycho used the first three Venus values below to carry positions from daytime
Sun–Venus observations to nighttime Venus–star observations. The historical
recalculation uses the distance and angle printed in each work. Horizons supplies
only the optional comparison column, using its range for the date and the same
printed altitude.

| Source and example | Distance (Earth radii) | Altitude | Printed altitude parallax | Recomputed | Modern comparison |
| --- | ---: | ---: | ---: | ---: | ---: |
| *Progymnasmata*, pp. 157–158, February 26, 1582, 3:35 p.m. | 815 | 48½° | 2′48″ | 167.7″ | 8.3″ |
| *Progymnasmata*, p. 160, March 20, 1582, 2:25 p.m. | 623 | 57° | 3′00″ | 180.3″ | 9.0″ |
| *Progymnasmata*, pp. 161–162, same day, 8:11 p.m. | 623 | 23½° | 5′04″ | 303.6″ | 15.2″ |
| *Thesaurus Observationum* XII, p. 463, February 3–5 reduction | 343 | 12° | 9′20″ | 588.2″ | — |
| *Thesaurus Observationum* XII, p. 468, March reduction | 348 | 3° | 9′52″ | 591.9″ | — |
| Longomontanus, *Astronomia Danica*, p. 185, December 12, 1610 | about 850 | 15½° in the calculation | about 4′ | 233.8″ | — |

The p. 463 Venus example also gives sides 1,112 and 822 with included angle
10° in the triangle used to find the distance. The cosine rule gives 334.5
Earth radii, compared with the printed 343. Even retaining 343 gives 9′48.2″
in the second triangle, 28.2″ above the printed 9′20″. The printed net correction
does reproduce as 9′20″ minus 6′00″ of refraction, or 3′20″. The cause of the
triangle discrepancies remains open. [Progymnasmata](https://arsastronomica.com/works/tycho-brahe-astronomiae-instauratae-progymnasmata/) · [Thesaurus Observationum III](https://arsastronomica.com/works/tycho-brahe-thesaurus-observationum-tomus-tertius/) · [Astronomia Danica](https://arsastronomica.com/works/longomontanus-astronomia-danica/)

For Mercury, Tycho’s March 1589 reductions subtract 8′ for refraction and add
3′ for parallax in declination. On March 24, 14°55′ becomes 14°47′ and then
14°50′. At the logged approximate altitude of 5° and the printed hours of
8:15, 8:09, and 8:15 p.m., the modern declination corrections for March 24, 27,
and 28 are +7.8″, +8.5″, and +8.8″. Holding his
refraction fixed on March 24 and varying only parallax gives 14°47′07.8″. In
another reduction, on February 3, 1592, the printed altitude terms give
8′15″ refraction minus 3′15″ parallax, or 5′. These calculations establish the
corrections used in the reductions. The Mercury passages examined here supply
no independent determination of the planet’s distance. [Thesaurus Observationum II, *Opera Omnia* XI, p. 339](https://arsastronomica.com/works/tycho-brahe-thesaurus-observationum-tomus-secundus/) · [Thesaurus Observationum III, *Opera Omnia* XII, p. 225](https://arsastronomica.com/works/tycho-brahe-thesaurus-observationum-tomus-tertius/) · [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/)

Riccioli’s comparative table supplies a second historical check on the scale.
These are tabulated horizontal parallax ranges over each historical model’s
distance extremes. A particular observation requires its own distance and projection.

| Model as tabulated by Riccioli | Venus, far to near | Mercury, far to near |
| --- | ---: | ---: |
| Ptolemy | 2′25″–18′40″ | 17′15″–62′00″ |
| Copernicus | 1′43″–11′30″ | 2′05″–5′40″ |
| Tycho | 1′40″–11′25″ | 2′04″–5′35″ |
| Longomontanus | 1′35″–11′25″ | 1′50″–5′50″ |
| Kepler | 36″–3′45″ | 42″–2′00″ |
| Riccioli | 16″–1′48″ | 19″–50″ |
| Modern reference from NASA’s minimum and maximum Earth distances | 5.0″–34.4″ | 5.9″–17.0″ |

The modern upper figures are geometric reference values. The nearest approaches
can occur at elongations that make observation difficult. Riccioli’s table
covers ten authorities, and [all of them are listed](figures/parallax-model-ranges.csv). [Almagestum Novum I, p. 700](https://arsastronomica.com/works/giovanni-battista-riccioli-almagestum-novum-tomus-primus-pars-prior/) · [NASA Venus distances](https://nssdc.gsfc.nasa.gov/planetary/factsheet/venusfact.html) · [NASA Mercury distances](https://nssdc.gsfc.nasa.gov/planetary/factsheet/mercuryfact.html)

## The March 1590 Venus test

The recap on *Opera Omnia* XII, p. 69, gives seven complete meridian-to-evening
pairs. For each pair there is a declination derived from altitude and another
read with the armillae. The four later lines lack a meridian value. The table
below subtracts the meridian declination from the evening declination within
each method. The 850-radius column uses Longomontanus’s adopted distance as a
fixed historical scale comparison across the seven pairs, with the recorded
geometry. His distance applies to his 1610 example. The modern columns use
Horizons ranges and declinations for each 1590 date. [Thesaurus Observationum III, *Opera Omnia* XII, p. 69](https://arsastronomica.com/works/tycho-brahe-thesaurus-observationum-tomus-tertius/) · [Astronomia Danica, p. 185](https://arsastronomica.com/works/longomontanus-astronomia-danica/)

| March day (Julian) | Recorded change from altitudes | Recorded change by armillae | Historical parallax shift at 850 Earth radii | Modern orbital change | Modern parallax shift |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4 | +370″ | +435″ | −32.4″ | +295.0″ | −1.9″ |
| 11 | +215″ | +380″ | −35.3″ | +252.2″ | −2.2″ |
| 15 | +255″ | +350″ | −36.5″ | +221.2″ | −2.4″ |
| 18 | +335″ | +195″ | −37.2″ | +198.0″ | −2.6″ |
| 19 | +265″ | +180″ | −37.5″ | +191.0″ | −2.6″ |
| 21 | +255″ | +120″ | −37.9″ | +178.3″ | −2.8″ |
| 26 | +235″ | +170″ | −38.7″ | +141.9″ | −3.0″ |

The catalog keeps each row of the recap together. The study gives the rows the
page’s day labels in order, from the latest meridian clock to the earliest.
Each recorded meridian altitude then lies within 31″ of the value the modern
ephemeris gives for that day. A one-day error would move it by more than 10′.
The catalog dates each row from the day column of the recap, and its seven
dates are the ones the study assigned.
The catalog also does not say which of a row’s two armillae readings is the
evening one. They are ordered like the row’s two altitude-derived
declinations. [Selected pairs with catalog identities](../examples/parallax-venus-pairs.csv) · [Every term for each pair](figures/parallax-venus-pairs.csv)

### A calculation without a modern ephemeris

Origanus demonstrates proportional interpolation on p. 143 of the
*Ephemerides Brandenburgicae*. For January 27, 1596 at his hour 15, the elapsed
fraction is 39/144. Venus goes from 1°02′ to 1°06′ south, giving **1°03′05″ south**.
Mercury goes from 30′ north to 17′ south, giving **17′19″ north**. These
are the values in print. Interpolating the Mercury endpoints directly gives
**17′16.25″ north**, 2.75″ below the printed result. The Venus interpolation
reproduces its printed value exactly. These are ecliptic latitudes.
The daily series begins in 1595, and the ingested introduction contains selected
entries and examples. A latitude alone supplies no geocentric distance. [Ephemerides Brandenburgicae, Part II, chapter IV, p. 143](https://arsastronomica.com/works/david-origanus-ephemerides-brandenburgicae/) · [Ingested edition coverage](historical-books-ingestion.md)

Applying the same proportional rule to Tycho’s near-consecutive meridian
altitudes for March 3–4 gives 1,445″ of change over 23 h 59½ min. The meridian
altitude tracks declination at this site, with a constant latitude term. Project
that local rate over the 5 h 09 min March 4 evening interval and the motion is
**+310.2″**. The altitude-derived observed change is +370″, leaving **+59.8″**
for the combined effects of parallax, refraction, measurement, and the linear
motion approximation. The two independent choices of motion calculation matter
here. The Horizons motion over the same nominal interval is +295.0″, giving
+75.0″ before correction. The historical rate comes from the observations and
can carry changes in their corrections and instrument errors. [Thesaurus Observationum III, *Opera Omnia* XII, pp. 51–52 and 69](https://arsastronomica.com/works/tycho-brahe-thesaurus-observationum-tomus-tertius/)

The March 3 Sun–Venus separation of about 46° gives a historical geometric
check. If Venus is at greatest elongation in a circular model, the tangent
triangle gives `1,146 × cos(46°)` or **796 Earth radii**. Applied to the March 4
pair this gives **−34.6″** of declination change. Under Tycho’s stellar refraction
table the vertical correction is zero at both altitudes. Under Longomontanus’s
alternative of taking the mean of Tycho’s solar and stellar refractions for
Venus, the March 4 evening refraction projects to about **+86″** in declination,
with the meridian term set to zero above the table range. Thus the historical
parallax and these two refraction prescriptions give changes of −34.6″ and about
+51″ beyond orbital motion. The tangent approximation is specific to the
near-elongation geometry. It supplies no distance measurement independent of
the adopted solar scale. [Thesaurus Observationum III, *Opera Omnia* XII, pp. 51–52](https://arsastronomica.com/works/tycho-brahe-thesaurus-observationum-tomus-tertius/) · [Progymnasmata, solar and stellar refraction tables](https://arsastronomica.com/works/tycho-brahe-astronomiae-instauratae-progymnasmata/) · [Astronomia Danica, p. 185](https://arsastronomica.com/works/longomontanus-astronomia-danica/)

### What the pairs resolve

The two recorded declination methods disagree on the evening-minus-meridian
change by **65–165″**. In the modern comparison the signal in that observable is
**1.9–3.0″**, even though Venus’s horizontal parallax at those dates is about
14–19″. An illustrative refraction law of `58″ × tan(zenith distance)` gives
44–71″ of differential declination refraction across the pairs if retained in
full. Even the historical 850-radius signal of 32–39″ is smaller than the
disagreement between the methods. By the armillae, the recorded change exceeds
the modern motion by 128–140″ on March 4, 11, and 15. On the four later dates
the excess is between −58″ and +28″. After motion, parallax, and refraction
are removed, the residuals still scatter by 55–80″ from pair to pair under
[every combination of assumptions](planetary-parallax-comparisons.md#all-seven-venus-pairs).
These seven pairs give a sensitivity check.
An independent distance estimate would require the individual instrument
calibrations, a reconstruction of the corrections already applied to the recap,
and a fit that accounts for the shared errors within each session.

## Reproducing the comparisons

The [planetary correction comparisons](planetary-parallax-comparisons.md) cross
historical and modern refraction with both parallax inputs for Mercury and Venus
and extend the calculations to Mars, Jupiter, and Saturn. One
[script](planetary-parallax-comparisons.md#inputs-and-reproduction) regenerates
every table on both pages from committed inputs.

- **Dates and times.** The log examples use Julian dates. For the modern benchmark,
  add 10 days to express these dates in the Gregorian calendar and treat the
  published clocks as approximate local mean solar times, subtracting 50 min
  47.7 s for Uraniborg. The p. 69 clocks are afternoon hours. Shifting both
  clocks of each Venus pair by ±15 min changes the modern motion difference by
  less than 0.1″. An error in the interval between clocks still matters. These
  times are calculation assumptions. [Uraniborg coordinates](https://web.astronomicalheritage.net/show-entity?identity=100&idsubentity=1)
- **Modern inputs.** Use [Horizons observer tables](https://ssd-api.jpl.nasa.gov/doc/horizons.html)
  for Mercury `199` and Venus `299` from Earth’s center `500@399`, `TIME_TYPE=UT`,
  `QUANTITIES=2,20`, airless coordinates, and `ANG_FORMAT=DEG`. The returned
  DE441 ranges in au convert to Earth radii by multiplying by
  `149597870.7 / 6378.1366`. Modern orbital change is the difference in geocentric
  apparent declinations, including apparent-coordinate effects in the ephemeris.
- **Declination projection.** Use `asin((sin(δ) − sin(φ)/n) / sqrt(1 + 1/n² − 2 sin(h)/n)) − δ`
  for the topocentric-minus-geocentric declination on a spherical Earth, with
  latitude `φ = 55°54′28.3″`. Use the recorded altitude as a geometry approximation
  for `h` and convert the result to arcseconds. Subtract the meridian shift from
  the evening shift. For the 850-radius and 796-radius historical comparisons,
  use the two altitude-derived declinations as geometric approximations for `δ`.
  For the refraction scenarios project the vertical change into declination
  using `(sin(φ) − sin(h) sin(δ)) / (cos(h) cos(δ))`.
