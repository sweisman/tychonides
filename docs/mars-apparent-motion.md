# Mars reverses direction in 1595

In September and October 1595, Tycho’s reductions place Mars in Taurus. Its
longitude drops from 56°06′30″ on September 30 to 40°26′16″ on December 6, a
westward movement of **15°40′14″**. By December 23 it is moving eastward again.
All four model geometries produce the reversal. They predict different extents
and rates of motion, which can be compared with the recorded positions.
[*Thesaurus Observationum* III, *Opera Omnia* XII, pp. 443–460](https://arsastronomica.com/works/tycho-brahe-thesaurus-observationum-tomus-tertius/)

![The 1595 longitude curve and model-minus-log differences](figures/mars-1595-motion.png)

The plot uses 14 dated longitude reductions from the log. Each curve shares the
October 31 reference longitude **47°30′40″**, taken from Longomontanus’s table of
positions reduced to true opposition. The comparison fixes this single historical
anchor before looking at the other dates. The lower panel shows signed departures
from Tycho’s reductions across the rest of the passage. [*Astronomia Danica*, Theorics, book II, chapter VIII, opposition VIII](https://arsastronomica.com/works/longomontanus-astronomia-danica/)

| Model | First station | Second station | Retrograde span | Earth–Mars projected distance at the reference epoch | RMS longitude difference |
| --- | --- | --- | ---: | ---: | ---: |
| Ptolemaic equant | Sep 24 | Dec 3 | 14.81° | 0.482 | 0.44° |
| Copernican circles | Sep 24 | Dec 3 | 14.23° | 0.491 | 0.65° |
| Tychonic, Longomontanus | Sep 24 | Dec 3 | 15.23° | 0.504 | 0.29° |
| Modern Keplerian | Sep 24 | Dec 4 | 16.01° | 0.496 | 0.10° |

Stations are turning points in modeled longitude, rounded to the nearest
Julian date. The distance column uses each model’s mean annual radius as one
unit. In Ptolemy’s construction this is the radius of the epicycle that carries
the annual motion. These distance ratios depend on the model geometry. A
terrestrial baseline would supply a separate test of the distance scale.
[Planetary parallax and refraction comparisons](planetary-parallax-comparisons.md)

## Four ways to draw the same reversal

![Four model planes showing three dated lines of sight from Earth to Mars](figures/mars-1595-geometry.png)

Blue-gray marks Earth. Gold marks the Sun in the Copernican, Tychonic, and
modern panels, and the epicycle center in the Ptolemaic panel. The gray lines go
from Earth to Mars on September 25, October 31, and December 6. Mars’s direction
is the angle of that line. The tracks cover a longer interval so the underlying
motion is visible.

| Formulation | Calculation |
| --- | --- |
| **Ptolemaic** | An epicycle center travels around a deferent of radius 60. Earth and the equant sit 6 units on opposite sides of the deferent center. The epicycle radius is 39½ and its absolute direction follows the mean Sun. Mars reverses when the component of motion on the epicycle temporarily outweighs that of its center. [Ptolemy, *Almagest*, X.7–8 and XI](https://classicalliberalarts.com/resources/PTOLEMY_ALMAGEST_ENGLISH.pdf) |
| **Copernican** | Earth follows the annual circle in Copernicus’s worked Mars construction. Mars’s eccentric circle uses the offset 1,460 and small-circle radius 500 per 10,000, and the Earth circle has radius 6,580 on the same scale. The line of sight swings backward when Earth overtakes Mars. [Copernicus, *De Revolutionibus*, V.16–17](https://de.wikisource.org/wiki/Nicolaus_Coppernicus_aus_Thorn_%C3%BCber_die_Kreisbewegungen_der_Weltk%C3%B6rper/F%C3%BCnftes_Buch_Teil_B) |
| **Tychonic** | The Sun travels around a fixed Earth center and carries the center of Mars’s motion. This calculation follows the longitude geometry in Longomontanus’s *Astronomia Danica*. The two small circles have radii 14,840 and 3,710 per 100,000. The annual radius varies under his rule for the solar and Martian anomalies. [*Astronomia Danica*, Theorics, book II, chapters VIII–IX](https://arsastronomica.com/works/longomontanus-astronomia-danica/) |
| **Modern heliocentric** | Earth and Mars follow inclined, eccentric paths computed from JPL’s long-span Keplerian elements and rates, with the Earth–Moon barycenter representing Earth. Kepler’s equation sets the position along each ellipse. In Newtonian mechanics the two-body ellipse follows from inverse-square gravity. The JPL elements incorporate secular trends for an approximate modern ephemeris. [JPL Table 2a and formulas](https://ssd.jpl.nasa.gov/planets/approx_pos.html) |

The Copernican and Tychonic arrangements can give identical Earth-to-Mars
directions when they share the same relative trajectories. In heliocentric
coordinates the line of sight is Mars relative to the Sun minus Earth relative
to the Sun. In a Tychonic expression it is the Sun relative to Earth plus Mars
relative to the Sun. The curves here differ because their published orbit
constructions and parameters differ. The origin of the diagram alone leaves the
predicted direction unchanged.

## Tycho’s comparison with published tables

The log also gives enough information for a comparison using the ephemeris
values Tycho actually had on these dates. He lists an Alphonsine calculation
from the Ptolemaic tradition and a Copernican calculation alongside his own
reductions. All entries below are within Taurus. Differences are table minus
log. [*Opera Omnia* XII, pp. 445–447](https://arsastronomica.com/works/tycho-brahe-thesaurus-observationum-tomus-tertius/)

| Julian date | Tycho’s reduction | Alphonsine | Difference | Copernican | Difference |
| --- | ---: | ---: | ---: | ---: | ---: |
| Sep 30 | 26°06′30″ | 26°16′ | +9.50′ | 24°20′ | −106.50′ |
| Oct 12 | 23°52′30″ | 23°51′ | −1.50′ | 21°56′ | −116.50′ |
| Oct 16 | 22°55′45″ | 22°50′ | −5.75′ | 21°00′ | −115.75′ |
| Oct 25, morning | 19°53′00″ | 19°46′ | −7.00′ | 17°54′ | −119.00′ |

On these four dates the Alphonsine longitudes are closer, with a mean absolute
difference of 5.9′ versus 114.4′. This result concerns the tables actually used.
The phase-aligned curves above answer a different question about the shape
of an apparition. Longomontanus also prints his own reconstructed opposition
for October 31. His predicted 17°29½′ Taurus is 1′10″ below the reported
17°30⅔′, using the printed positions. That opposition belongs to the set he
used in developing his theory. [*Astronomia Danica*, Theorics, book II, chapter VIII](https://arsastronomica.com/works/longomontanus-astronomia-danica/)

## How the path looks against the sky

![Mars follows an S-shaped path in longitude and latitude, with Tycho’s paired reductions over the modern track](figures/mars-1595-sky.png)

On this passage Mars travels northward in ecliptic latitude while it reverses
twice in longitude. The early September point above the modern track comes
from the larger of two globes noted in the log. The latitude inferred with the
smaller globe on the same date is 2° south, versus 1° south with the larger one.
The historical calculations here implement longitude only. The modern latitude
and the paired log values show how the reversal looks on the sky.
[*Opera Omnia* XII, pp. 442–443](https://arsastronomica.com/works/tycho-brahe-thesaurus-observationum-tomus-tertius/)

## Inputs and reproduction

- [Selected source quantities](../examples/mars-1595-observations.csv) give the
  exact angle, the stated sign or direction through its normalization, the
  printed page, and the catalog identity. The catalog release is
  [Tychonides 1.3.1](https://github.com/sweisman/tychonides/releases/tag/tychonides-1.3.1).
  The selection uses reviewed dated reductions, one longitude per date. Where
  depicted, a paired latitude comes from the same source reduction. October 28
  has competing latitude values and contributes longitude only. The adopted
  readings on October 28, October 30, November 3, and December 18 are used as
  printed. The CSV makes the choices among the remaining reductions explicit.
- The positions represent date-level comparisons. Julian dates are mapped to
  Gregorian dates by adding ten days and evaluated at nominal noon UT. The
  published coordinates already carry historical reductions, sometimes including
  refraction and parallax. Their original correction and timing details are
  preserved in the catalog. No new correction is applied to the source points.
  The modern geometric track omits light time, sub-day time-scale offsets,
  and an explicit ecliptic-of-date transform. Its longitude is rotated by a
  constant to the shared anchor. The scatter is descriptive for this selection.
- The historical curves share the opposition phase and the apsidal direction
  148°55′20″, inferred from the mean longitude, anomaly, and precession in
  Longomontanus’s opposition row. They use common sidereal Mars and tropical
  annual periods of 686.98 and 365.2422 days, respectively. The equations use
  radians internally. Longomontanus’s first inequality reproduces his printed
  1613 worked example within half an arcminute. The comparison tests the stated
  constructions in common conditions. Historical epoch tables, ancient
  precession, and the original full latitude theories are separate work.
- The [numerical output](figures/mars-1595-results.csv) includes predicted
  longitude, residual in arcminutes, and modern latitude at each source date.
  Run the [analysis script](../examples/mars_1595.py) with NumPy and Matplotlib
  installed to regenerate the CSV and all three figures.

```sh
python examples/mars_1595.py --output docs/figures
```
