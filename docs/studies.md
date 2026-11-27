# Studies

Finished analyses built on the [Tychonides catalog](../resources/catalog/README.md).
Each entry gives the question, the result, the inputs, and how to rerun it. The
[status page](status.md) shows how these fit the wider objectives.

What Tycho recorded is the reference in these studies. Each account of a
planet’s motion, whether a sixteenth-century table or the modern JPL DE441
ephemeris, is measured by how far it falls from the recorded place. DE441 uses
none of Tycho’s observations, so his logs test it. Where a study has no
observation to measure from, its entry says so. The
[plain-language guide](plain-language.md) explains the terms and this rule.

| Study | Subject | Period |
| --- | --- | --- |
| [Mars reverses direction in 1595](#mars-reverses-direction-in-1595) | Four model geometries against Tycho’s reductions | September to December 1595 |
| [Mars at the oppositions of 1580 to 1600](#mars-at-the-oppositions-of-1580-to-1600) | A modern ephemeris, three constructions, and printed table predictions against Tycho’s longitudes | 1580 to 1600 |
| [Printed predictions for the Moon and planets](#printed-predictions-for-the-moon-and-planets) | Table and ephemeris positions printed in the logs against Tycho’s own values, with a modern ephemeris held to the same test | 1563 to 1600 |
| [Tycho’s solar theory](#tychos-solar-theory) | His equinoxes, apogee, and eccentricity against a modern ephemeris and his own altitude corrections | 1584 to 1588 |
| [Historical refraction tables](#historical-refraction-tables) | The printed tables of Tycho and Riccioli against a modern formula | 1602 and 1665 |
| [Mars, Jupiter, and Saturn corrections](#mars-jupiter-and-saturn-corrections) | Recorded parallax and refraction against modern values | 1582 to 1599 |
| [Mercury and Venus parallax](#mercury-and-venus-parallax) | Historical reductions and the 1590 Venus test | 1582 to 1610 |
| [The parallax of Mars in 1587](#the-parallax-of-mars-in-1587) | Mars-to-star distances of two nights against the log’s parallax and a modern one | February and March 1587 |
| [Mars from Kassel and from Uraniborg](#mars-from-kassel-and-from-uraniborg) | Distances of Mars from the same stars on the same nights at two observatories | 1593 and 1595 |

Every study is computed from the current catalog,
[release 1.4.0](../resources/catalog/README.md#download).

## Mars reverses direction in 1595

[Read the study](mars-apparent-motion.md)

- **Question.** How closely do Ptolemaic, Copernican, Tychonic, and modern
  constructions follow Mars through one retrograde passage as Tycho’s
  reductions record it, and how close were the table predictions he printed?
- **Result.** All four constructions produce the reversal. Where the log prints
  a usable hour, the JPL DE441 ephemeris lies about one arcminute from Tycho’s
  reductions. Historical curves tied to one opposition longitude differ from
  the log by 0.27° (Tychonic), 0.50° (Ptolemaic), and 0.67° (Copernican). That
  order changes with the assumed apsidal direction, so it does not rank the
  systems. From September 30 the printed Alphonsine predictions stay within 10′
  of the log, and the printed Copernican ones run 106′ to 119′ behind.
- **Inputs.** Twenty-one longitude reductions on 16 dates from *Opera Omnia*
  XII, pp. 443–460, [selected from the catalog](../examples/mars-observations.csv)
  by a written rule. The opposition anchor and Tychonic parameters come from
  Longomontanus’s *Astronomia Danica*. Modern positions are cached from JPL
  Horizons.
- **Limits.** One passage, with residuals that are correlated from night to
  night and carry no uncertainty. The Tychonic parameters were derived from a
  set of oppositions that includes this one. Nine rows have no usable hour and
  are evaluated at local noon.
- **Rerun.** `python examples/mars_1595.py --output docs/figures` regenerates
  the [results](figures/mars-1595-results.csv), the summary, sensitivity,
  validation, and prediction tables, and all three figures. The tables need
  NumPy and the figures need Matplotlib. A test regenerates the tables.

## Mars at the oppositions of 1580 to 1600

[Read the study](mars-oppositions.md)

- **Question.** Across the oppositions Tycho’s logs cover, how close does a
  modern ephemeris come to his reduced longitudes, how do the historical
  constructions follow each passage, and how close were the table predictions
  he printed?
- **Result.** At nine oppositions, where the log prints a usable hour, the JPL
  DE441 ephemeris lies 0.5′ to 4.6′ from Tycho’s longitudes. The printed
  Alphonsine and Copernican predictions miss them by up to 4.7° and 4.2°, with
  neither reliably closer. Curves tied to each opposition depart from the log
  by up to 0.6° for the Ptolemaic and Copernican constructions and up to 0.2°
  for the Tychonic one, which was fitted to these oppositions. Longomontanus’s
  fourteen tabulated oppositions reproduce from DE441 within 4′ in longitude
  and three hours in time, and the timing differences follow the 7′ excess of
  his solar equation.
- **Inputs.** 149 longitude reductions and 125 printed predictions from
  *Opera Omnia* X–XIII, selected from the catalog by the rule written for 1595,
  with Longomontanus’s opposition table and cached JPL Horizons positions.
- **Limits.** The 1600 opposition is set aside because the catalog does not
  record the calendar of its entries. Sixty rows have no usable hour. Two rows
  far from the ephemeris are kept and listed for review. Nothing is refitted
  or withheld, so this is not a predictive test.
- **Rerun.** `python examples/mars_oppositions.py --output docs/figures`
  regenerates the [summary](figures/mars-oppositions-summary.csv), the other
  tables, and both figures.
  `python examples/mars_opposition_table.py --output docs/figures` regenerates
  the [opposition table comparison](figures/mars-opposition-table.csv). Tests
  regenerate the tables.

## Printed predictions for the Moon and planets

[Read the study](printed-predictions.md)

- **Question.** How close were the table and ephemeris positions that Tycho’s
  logs print for the planets, measured from his own values, and how does a
  modern ephemeris fare by the same measure?
- **Result.** On 31 dates near the oppositions of Mars where the log prints
  its hours, JPL DE441 lies a median of 0.8′ from Tycho’s longitude. The
  Copernican longitudes of Mars have a median difference from the log of 17′
  more than 60 days from opposition and 1.9° near it. The Alphonsine medians
  are 1.4° and 3.6°. For Saturn in 1590 and 1591 the study has no log value.
  Measured from DE441, the Alphonsine longitudes there run 2.9° ahead and the
  Copernican ones stay within 10′, while the Copernican latitudes lie about 1°
  south.
- **Inputs.** 528 printed predictions from 1563 to 1600 and 350 values of the
  log on the same dates, [selected from the catalog](../examples/printed-predictions.csv),
  with cached JPL Horizons positions.
- **Limits.** The log prints an hour for 232 of the 462 comparisons. The other
  230 use local noon. The 66 predictions of the Moon are listed and
  not compared. Forty Mars predictions of 1599 and 1600 are set aside because
  their calendar is not recorded. Samples for Mercury, Venus, and Jupiter are
  small. Twelve more predictions carry a label that names no table, 35 have
  no single complete date, and 64 latitudes have no printed direction, so
  they enter no comparison. DE441 is not tested against the log for Saturn,
  and in May 1564 the log and DE441 differ by 91′ to 107′.
- **Rerun.** `python examples/printed_predictions.py --output docs/figures`
  regenerates the [summary](figures/printed-predictions-summary.csv), the
  [results](figures/printed-predictions-results.csv), the
  [ephemeris check](figures/printed-predictions-ephemeris-check.csv), and the
  figure. A test regenerates the tables.

## Tycho’s solar theory

[Read the study](solar-theory.md)

- **Question.** Do Tycho’s printed equinoxes and intervals give his solar
  apogee and eccentricity, how do they compare with a modern ephemeris, and
  what explains the difference?
- **Result.** His construction reproduces: the printed intervals give an apogee
  of 95.5° and an eccentricity of 0.03585, as he prints. His equinoxes fall
  about three hours from JPL DE441, early in spring and late in autumn, which
  makes his summer half-year six hours too long and his eccentricity 6% too
  large. His own corrections to a solar altitude, a 3′ parallax and a
  refraction of 44″ at the equinox altitude, displace the equinoxes by 3.4
  hours and give an eccentricity of 0.0362 from the DE441 Sun.
- **Inputs.** Ten printed equinoxes and thirteen printed elements and
  constants from the *Progymnasmata*,
  [selected from the catalog](../examples/solar-theory-inputs.csv), Tycho’s
  solar refraction table from the refraction study, and cached JPL Horizons
  positions of the Sun.
- **Limits.** No instrument reading enters the study, so the ephemeris is its
  only measure of the equinoxes. The equinox table is a smoothed series with
  one vernal and one autumnal instant. The reduction models one exact meridian altitude in
  standard air. The pole altitude of the 1588 work is not printed in the
  chapter. The entries into the middle of Taurus and Leo are printed only as
  intervals.
- **Rerun.** `python examples/solar_theory.py --output docs/figures`
  regenerates the [equinoxes](figures/solar-theory-equinoxes.csv), the
  [intervals](figures/solar-theory-intervals.csv), the
  [elements](figures/solar-theory-elements.csv), and the figure. A test
  regenerates the tables.

## Historical refraction tables

[Read the study](refraction-tables.md)

- **Question.** How do the refraction tables Tycho and Riccioli printed compare
  with modern refraction at the same altitudes?
- **Result.** Tycho’s fixed-star table stays within 1′ of modern refraction
  from 4° to 16°, then falls to zero at 20°, where modern refraction is 2′42″.
  His solar table runs 4½′ higher, which does not cancel his 3′ solar parallax.
  Riccioli’s equinoctial solar table equals Tycho’s solar table less that
  parallax, within about an arcsecond from 0° to 24°.
- **Inputs.** 310 table entries from the *Progymnasmata* and the *Astronomia
  Reformata*, [selected from the catalog](../examples/refraction-tables.csv)
  with their altitude arguments.
- **Limits.** Printed tables, not observed refraction. Modern values come from
  Bennett’s formula over a stated range of air conditions. Tycho’s lunar table,
  Longomontanus’s tables, and Riccioli’s reprint of Tycho lack recorded
  altitudes in the catalog and are left out.
- **Rerun.** `python examples/refraction_tables.py --output docs/figures`
  regenerates the [summary](figures/refraction-tables-summary.csv), the other
  tables, and the figure. A test regenerates the tables.

## Mars, Jupiter, and Saturn corrections

[Read the study](planetary-parallax-comparisons.md)

- **Question.** What diurnal-parallax corrections do Tycho’s records apply to
  the outer planets, and how do they change under modern distances and
  refraction?
- **Result.** The printed corrections reproduce from the distances Tycho
  adopted. For Mars in December 1582, 721 Earth radii gives the printed 3′39″
  at 40° altitude. Those distances come from the planetary models. Modern
  distances make the same corrections roughly twenty times smaller. None of
  the cited records is a parallax measured across a terrestrial baseline.
- **Inputs.** Reductions in *Opera Omnia* X–XIII and the *Progymnasmata*,
  Riccioli’s table of model parallaxes, and JPL Horizons distances for the
  recorded dates.
- **Limits.** The recorded geometry is held fixed while distance and refraction
  vary one at a time. Modern distances are taken at noon, independent of the
  source clocks.
- **Rerun.** `python examples/planetary_parallax.py --output docs/figures`
  regenerates the [outer-planet table](figures/parallax-outer-planets.csv) and
  every other table on the page from committed inputs. A test regenerates the
  tables.

## Mercury and Venus parallax

[Read the study](mercury-venus-parallax.md)

- **Question.** What parallax did Tycho calculate for Mercury and Venus, what
  did his March 1590 Venus test show, and what would modern distances give?
- **Result.** The printed corrections reproduce from the printed distances and
  altitudes, apart from one Venus reduction whose triangle discrepancy remains
  open. Tycho judged Venus’s parallax imperceptible where the Ptolemaic
  hypothesis led him to expect about 4′. His solar distance of 1,146 Earth
  radii makes horizontal parallaxes about 20.5 times the modern values.
- **Inputs.** The *Progymnasmata*, *Opera Omnia* XII, and Longomontanus’s
  *Astronomia Danica*, with JPL Horizons distances for comparison.
- **Limits.** Scenario calculations from recorded readings. They show the
  sensitivity to each assumption and do not estimate a parallax. Across the
  seven Venus pairs the residuals scatter by 55″ to 80″, more than the 34″
  between the historical and modern parallax scales. The study assigns the
  days of the pairs in page order. They agree with the catalog’s dates and
  with the ephemeris.
- **Rerun.** `python examples/planetary_parallax.py --output docs/figures`
  regenerates the [seven-pair table](figures/parallax-venus-pairs.csv) and
  every other table on the page from committed inputs. A test regenerates the
  tables.

## The parallax of Mars in 1587

[Read the study](mars-parallax-1587.md)

- **Question.** Do Tycho’s distances of Mars from fixed stars on the nights of
  February 23 and March 10, 1587 show the 302″ horizontal parallax his log
  applies, or the 13″ of a modern ephemeris?
- **Result.** They show neither with any certainty. Five pairs of sessions give
  −312″, 289″, 259″, 47″, and 28″, with a mean of 62″ ± 108″. All distances
  fitted together give −13″ ± 33″ and scatter less about the modern parallax
  than about the log’s. Three whole sessions stand 1¼′ to 4¼′ from the computed
  distances, which hides a parallax of 13″ and is as large as the one Tycho
  sought.
- **Inputs.** 48 distances with their printed clocks and recorded altitudes,
  [selected from the catalog](../examples/mars-parallax-readings.csv), modern
  positions of six stars, and cached JPL Horizons positions of Mars.
- **Limits.** Two nights and six stars. Standard air for both nights. The
  grouping of the fit was settled after a first look at the residuals, so every
  case is shown. The campaign of 1582 and 1583 is not covered.
- **Rerun.** `python examples/mars_parallax_1587.py --output docs/figures`
  regenerates the [distances](figures/mars-parallax-1587-readings.csv), the
  [pairs](figures/mars-parallax-1587-pairs.csv), the
  [fits](figures/mars-parallax-1587-summary.csv), the
  [clock check](figures/mars-parallax-1587-clocks.csv), and the figure. A test
  regenerates the tables.

## Mars from Kassel and from Uraniborg

[Read the study](mars-kassel.md)

- **Question.** On nights when Jost Bürgi at Kassel and Tycho’s observers at
  Uraniborg measured Mars from the same star, do the two sets of sextant
  distances agree?
- **Result.** In 14 pairs on seven nights of 1593 and 1595 they agree within a
  median of 1.7′, and 12 of the 14 within 3.1′. Kassel’s distances run 1.8′
  longer on average. Distances computed from JPL DE441 and modern star
  positions lie at most 1.4′ from Uraniborg’s readings and up to 5.5′ from
  Kassel’s. One further pair differs by 7° and is set aside: the log’s printed
  distance is in question.
- **Inputs.** 22 distances from Snellius’s *Observationes Hassiacae* and 65
  from *Opera Omnia* XII with their printed clocks,
  [selected from the catalog](../examples/mars-kassel-readings.csv), modern
  positions of five stars, and cached JPL Horizons positions of Mars.
- **Limits.** Fourteen pairs, ten of them resting on a single Kassel reading.
  Kassel prints its hours to the half hour. Standard air for every night. The
  motion of Mars between two readings of a night comes from DE441, so the
  readings are also given as read. One reading is left out because its printed
  altitude contradicts its printed hour, by a rule added after the first run.
- **Rerun.** `python examples/mars_kassel.py --output docs/figures`
  regenerates the [readings](figures/mars-kassel-readings.csv), the
  [pairs](figures/mars-kassel-pairs.csv), the
  [summary](figures/mars-kassel-summary.csv), the
  [altitude check](figures/mars-kassel-altitudes.csv), and the figure. A test
  regenerates the tables.
