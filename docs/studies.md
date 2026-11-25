# Studies

Finished analyses built on the [Tychonides catalog](../resources/catalog/README.md).
Each entry gives the question, the result, the inputs, and how to rerun it. The
[status page](status.md) shows how these fit the wider objectives.

| Study | Subject | Period |
| --- | --- | --- |
| [Mars reverses direction in 1595](#mars-reverses-direction-in-1595) | Four model geometries against Tycho’s reductions | September to December 1595 |
| [Mars, Jupiter, and Saturn corrections](#mars-jupiter-and-saturn-corrections) | Recorded parallax and refraction against modern values | 1582 to 1599 |
| [Mercury and Venus parallax](#mercury-and-venus-parallax) | Historical reductions and the 1590 Venus test | 1582 to 1610 |

## Mars reverses direction in 1595

[Read the study](mars-apparent-motion.md)

- **Question.** How closely do Ptolemaic, Copernican, Tychonic, and modern
  Keplerian geometries follow Mars through one retrograde passage as Tycho’s
  reductions record it?
- **Result.** All four produce the reversal. The 14 reductions follow the modern
  track most closely, with a root-mean-square longitude difference of 0.10°.
  Three historical geometries, built on one shared opposition longitude and
  apsidal direction, differ from the reductions by 0.29° to 0.65° and give
  retrograde spans of 14.2° to 15.2°, against 16.0° for the modern track. On
  four dates the Alphonsine longitudes printed in the log lie within 6′ of
  Tycho’s reductions on average, and the printed Copernican ones about 114′.
- **Inputs.** Fourteen dated longitude reductions from *Opera Omnia* XII,
  pp. 442–460, in a [source table](../examples/mars-1595-observations.csv) with
  catalog identities. The opposition anchor and Tychonic parameters come from
  Longomontanus’s *Astronomia Danica*.
- **Limits.** A date-level comparison at nominal noon. The historical curves
  test the stated constructions under common conditions, not the historical
  tables. The scatter describes this selection and carries no uncertainty
  estimate.
- **Rerun.** `python examples/mars_1595.py --output docs/figures` regenerates
  the [numerical output](figures/mars-1595-results.csv) and all three figures.
  It needs NumPy and Matplotlib.

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
- **Rerun.** The page states its formulas and sources. No script is published yet.

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
  sensitivity to each assumption and do not estimate a parallax.
- **Rerun.** The page states its formulas and sources. No script is published yet.
