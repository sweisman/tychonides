# Project status

This page records what Tychonides has finished, what is under way, and what
comes next. The [research program](research-plan.md) defines the objectives and
milestones. The [source directory](data-sources.md) defines catalog coverage.
Finished analyses are collected on the [studies page](studies.md).

Last updated November 25, 2026.

## Objectives

| Objective | Status | Done so far | Next step |
| --- | --- | --- | --- |
| Observation catalog | Available and expanding | [Release 1.3.1](../resources/catalog/README.md#download) holds 710,420 quantities from Tycho’s four logs, seven supplementary books, and modern optical collections. | [Planned acquisitions](data-sources.md#planned-ingestions) |
| Mars apparent motion and geometry | Nine oppositions compared | [The 1595 retrograde passage](mars-apparent-motion.md) and [the oppositions of 1580 to 1600](mars-oppositions.md) compare Tycho’s reductions with four constructions and the JPL DE441 ephemeris. | The 1600 opposition, once the calendar of its entries is recorded |
| Historical model comparison | Mars compared | The opposition study tabulates every Alphonsine, Copernican, and Prutenic prediction of Mars that the logs print near opposition. | Printed predictions for the other planets and away from opposition, and Ursus’s formulation where the sources permit |
| Mars, Jupiter, and Saturn parallax | Initial calculations | [Recorded and modern corrections](planetary-parallax-comparisons.md) are compared. | Parallax feasibility |
| Mercury and Venus parallax | Initial calculations | [Historical reductions and the 1590 Venus experiment](mercury-venus-parallax.md) are recomputed under historical and modern assumptions. | Parallax feasibility |
| Accuracy and refraction | Tables compared | The [refraction tables](refraction-tables.md) of Tycho and Riccioli are set against modern refraction. The [planetary comparisons](planetary-parallax-comparisons.md) vary distance and refraction independently. In 1595 Tycho’s Mars longitudes agree with DE441 to about one arcminute where the log prints a usable hour. | The tables that lack recorded altitudes, then the observations behind the tables and calibrated observing sessions |
| Kepler and opposition tables | Planned | | |
| Interactive visualization | Planned | [Visualization plan](visualization-plan.md) | Catalog explorer |
| Stellar aberration | Planned | | |
| Other planets and records | Planned | The catalog covers the planets, Sun, Moon, comets, and stars in Tycho’s logs. | |

## Milestones

The research program gives each milestone’s
[deliverable and completion criterion](research-plan.md#next-research-milestones).

| Milestone | Status |
| --- | --- |
| First astronomical subset | Open. The 1595 inputs are a date-level selection. Observing times, sites, instruments, and correction states are not yet established for them. |
| Historical calculation reconstruction | Open. |
| First observation–prediction comparison | A date-level comparison is published for 1595. A measurement-level comparison is open. |
| Parallax feasibility | Open. The published correction comparisons are groundwork, not recovery experiments. |
| Scientific visualization | Open. |

## Done to date

| Date | Result |
| --- | --- |
| November 25, 2026 | Study: [Historical refraction tables against modern refraction](refraction-tables.md). Tycho’s fixed-star table stays within 1′ of modern refraction from 4° to 16° and stops at 20°. His solar table runs 4½′ higher. |
| November 25, 2026 | Study: [Mars at the oppositions of 1580 to 1600](mars-oppositions.md). Tycho’s longitudes agree with a modern ephemeris within 5′ at nine oppositions. The printed table predictions miss by up to 4.7°. |
| November 25, 2026 | Review of the 1595 Mars study: inputs selected from the catalog by a written rule, printed hours used, the JPL DE441 ephemeris added, and sensitivity, validation, and prediction tables published with a regeneration test. |
| November 25, 2026 | Study: [Mars reverses direction in 1595](mars-apparent-motion.md), with its inputs, residuals, figure, and script. |
| November 25, 2026 | Study: [Mars, Jupiter, and Saturn corrections](planetary-parallax-comparisons.md) and [Mercury and Venus parallax](mercury-venus-parallax.md). |
| November 25, 2026 | Catalog 1.3.1: four-volume review of Tycho’s logs. 710,420 quantities and 115,972 source groups. |
| November 25, 2026 | Catalog 1.3.0: full coverage of Tycho’s logs, adding Mercury, comets, fixed stars, and the new star of 1572. |
| November 25, 2026 | Catalog 1.2.0: Sun, Saturn, and Venus from Tycho’s logs. |
| November 25, 2026 | Catalog 1.1.0: Jupiter and the Moon from Tycho’s logs. |
| November 18, 2026 | Catalog 1.0.1: qualified JPL placeholder fields and uncertain declination signs. |
| November 10, 2026 | Catalog 1.0.0: first public release, with Tycho’s Mars records, seven supplementary books, modern optical collections, and the reconciliation with Pafko’s transcription. |

The [catalog release notes](../CHANGELOG.md) describe each release.

## Next up

1. **Printed predictions.** Extend the comparison of printed Alphonsine,
   Copernican, Prutenic, and ephemeris predictions from Mars near opposition to
   the other planets and the rest of the logs.
2. **The 1600 opposition.** Establish the calendar of the 1599 to 1601 entries
   from the printed pages, then add that opposition.
3. **Refraction tables.** Record the altitude of each entry in Tycho’s lunar
   table, Longomontanus’s tables, and Riccioli’s reprint, then add them to the
   [published comparison](refraction-tables.md). Reproduce Tycho’s refraction
   values from the solar altitudes behind them.
4. **Printed calculations.** Reproduce selected historical results at their
   stated epochs from the documented parameters, beginning with the opposition
   table and the parallax campaigns.
5. **Parallax feasibility.** Test what diurnal parallax the observations could
   recover at their actual cadence under declared error assumptions.
6. **Catalog explorer.** Build the first interactive view of the catalog.
