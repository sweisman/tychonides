# Studies

Finished analyses built on the [Tychonides catalog](../resources/catalog/README.md).
Each entry gives the question, the result, the inputs, and how to rerun it. The
[status page](status.md) shows how these fit the wider objectives.

| Study | Subject | Period |
| --- | --- | --- |
| [Mars reverses direction in 1595](#mars-reverses-direction-in-1595) | Four model geometries against Tycho’s reductions | September to December 1595 |
| [Mars at the oppositions of 1580 to 1600](#mars-at-the-oppositions-of-1580-to-1600) | Tycho’s longitudes, three constructions, and printed table predictions against a modern ephemeris | 1580 to 1600 |
| [Historical refraction tables](#historical-refraction-tables) | The printed tables of Tycho and Riccioli against a modern formula | 1602 and 1665 |
| [Mars, Jupiter, and Saturn corrections](#mars-jupiter-and-saturn-corrections) | Recorded parallax and refraction against modern values | 1582 to 1599 |
| [Mercury and Venus parallax](#mercury-and-venus-parallax) | Historical reductions and the 1590 Venus test | 1582 to 1610 |

## Mars reverses direction in 1595

[Read the study](mars-apparent-motion.md)

- **Question.** How closely do Ptolemaic, Copernican, Tychonic, and modern
  constructions follow Mars through one retrograde passage as Tycho’s
  reductions record it, and how close were the table predictions he printed?
- **Result.** All four constructions produce the reversal. Where the log prints
  a usable hour, Tycho’s reductions agree with the JPL DE441 ephemeris to about
  one arcminute. Historical curves tied to one opposition longitude differ from
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
- **Reviewed.** November 25, 2026. The review replaced 14 hand-chosen rows with
  a written selection rule, used the printed hours, corrected the placement of
  the mean Sun, and added the sensitivity and validation tables.

## Mars at the oppositions of 1580 to 1600

[Read the study](mars-oppositions.md)

- **Question.** Across the oppositions Tycho’s logs cover, how close are his
  reduced longitudes to a modern ephemeris, how do the historical constructions
  follow each passage, and how close were the table predictions he printed?
- **Result.** At nine oppositions, where the log prints a usable hour, Tycho’s
  longitudes differ from the JPL DE441 ephemeris by 0.5′ to 4.6′. The printed
  Alphonsine and Copernican predictions miss by up to 4.7° and 4.2°, with
  neither reliably closer. Curves tied to each opposition depart from the log
  by up to 0.6° for the Ptolemaic and Copernican constructions and up to 0.2°
  for the Tychonic one, which was fitted to these oppositions.
- **Inputs.** 149 longitude reductions and 126 printed predictions from
  *Opera Omnia* X–XIII, selected from the catalog by the rule written for 1595,
  with Longomontanus’s opposition table and cached JPL Horizons positions.
- **Limits.** The 1600 opposition is set aside because the catalog does not
  record the calendar of its entries. Sixty rows have no usable hour. Two rows
  far from the ephemeris are kept and listed for review. Nothing is refitted
  or withheld, so this is not a predictive test.
- **Rerun.** `python examples/mars_oppositions.py --output docs/figures`
  regenerates the [summary](figures/mars-oppositions-summary.csv), the other
  tables, and both figures. A test regenerates the tables.
- **Reviewed.** November 25, 2026, when the study was first published.

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
- **Reviewed.** November 25, 2026, when the study was first published.

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
- **Reviewed.** November 25, 2026. The review reproduced every table, added the
  script, tied each printed input to its catalog entry where one entry matches,
  and made the list of Riccioli’s authorities the same on both parallax pages.

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
  between the historical and modern parallax scales. The catalog does not
  record the day of each pair, so the days are assigned in page order and
  checked against the ephemeris.
- **Rerun.** `python examples/planetary_parallax.py --output docs/figures`
  regenerates the [seven-pair table](figures/parallax-venus-pairs.csv) and
  every other table on the page from committed inputs. A test regenerates the
  tables.
- **Reviewed.** November 25, 2026. The review reproduced every table, added the
  script and the selection of the Venus pairs from the catalog, extended the
  scenario comparison from one pair to all seven, and stated the hours used for
  Mercury.
