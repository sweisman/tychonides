# Modern quantity and role reference

These terms describe source meanings and explicit conversions; they do not establish observational independence or apply new corrections.

See the [database schema](database-schema.md) and [catalog dictionary](catalog-data-dictionary.md).

JPL, USNO, Carlsberg and Tokyo coordinates are published reduced positions, not raw instrumental readings. JJMO includes original settings, source reductions and predictions. LCO supplies image metadata, not measured positions. See the [complete database schema](database-schema.md) and [source directory](data-sources.md).

## quantity

| Term | Meaning |
| --- | --- |
| `AU` | JJMO's published estimate of the astronomical unit, in the stated distance unit. |
| `AU_uncertainty` | Published uncertainty of the JJMO astronomical-unit estimate; not a newly estimated confidence interval. |
| `absolute_minus_HIP_dec` | W1J00 absolute-minus-Hipparcos declination difference, in angular seconds. |
| `absolute_minus_HIP_ra` | W1J00 absolute-minus-Hipparcos right-ascension difference, in seconds of time. |
| `angular_calibration` | Adopted angular separation per dial turn in the JJMO 2001 calibration. |
| `angular_separation` | Adopted comparison-star separation used in the JJMO calibration. |
| `baseline` | Published terrestrial chord used in JJMO's distance calculation. |
| `baseline_coefficient` | Adopted rotating-site chord coefficient in the JJMO geometry. |
| `calibration_factor` | Published angular calibration per 0.0001 inch of micrometer motion. |
| `calibration_mean` | Published mean micrometer difference for the calibration sequence. |
| `calibration_sd` | Published standard deviation of calibration micrometer differences. |
| `chord_miles` | Source-calculated terrestrial chord for one JJMO early/late pair, in miles. |
| `declination` | Published declination of the named target; coordinate origin, frame, limb and applied corrections remain source-specific. |
| `delta_hours` | Source-calculated early-to-late time separation for a JJMO observing pair. |
| `dial_difference` | Difference of original dial or micrometer settings, in turns or inches as recorded. |
| `dial_setting` | Original JJMO dial setting expressed in turns. |
| `distance` | JJMO's published Mars-distance estimate. |
| `distance_miles` | Source-calculated Mars distance for an individual observing pair, in miles. |
| `distance_uncertainty` | Published uncertainty of the Mars-distance estimate. |
| `early_mean` | Published early mean west-positive Mars/star offset. |
| `earth_period` | Adopted Earth orbital period used in the source calculation. |
| `earth_radius` | Adopted Earth radius used in the source geometry. |
| `elapsed` | Published early-to-late time interval. |
| `late_mean` | Published late mean west-positive Mars/star offset. |
| `mars_eccentricity` | Adopted Mars orbital eccentricity, not a fit to these observations. |
| `mars_perihelion_rate_factor` | Adopted enhancement of angular orbital speed at Mars perihelion. |
| `mars_period` | Adopted Mars orbital period. |
| `micrometer_setting` | Original JJMO micrometer setting in inches. |
| `motion_arcsec` | Source-calculated Mars motion correction for an early/late pair. |
| `motion_correction` | Published motion subtraction applied in the JJMO calculation. |
| `motion_mean` | Published next-evening mean west-positive Mars/star offset. |
| `motion_rate` | Published retrograde angular motion rate. |
| `observed_magnitude` | Published observed apparent magnitude in the source band; missing values remain absent. |
| `observed_minus_computed_dec` | Published observed-minus-computed declination residual in angular seconds. |
| `observed_minus_computed_magnitude` | Published observed-minus-computed magnitude difference. |
| `observed_minus_computed_ra` | Published observed-minus-computed right ascension residual in seconds of time; not a new model comparison. |
| `parallax` | JJMO's published residual parallax; importing it does not establish an independent detection. |
| `parallax_arcsec` | Source-calculated residual parallax for one observing pair. |
| `parallax_uncertainty` | Published plus/minus parallax uncertainty; no unreported statistical interpretation is added. |
| `perihelion_distance_ratio` | Adopted Mars-to-Earth distance at perihelion opposition divided by the astronomical unit. |
| `phase_correction_dec` | Published phase correction already applied to declination, in angular seconds. |
| `phase_correction_ra` | Published phase correction already applied to right ascension, in seconds of time. |
| `ra_separation` | Source-reduced right-ascension separation for a Mars/star reading. |
| `ra_separation_change` | Source-reduced change in right-ascension separation between paired readings. |
| `recorded_clock` | Recorded JJMO EDT clock; its separately stored UTC conversion does not invent exposure timing. |
| `recorded_epoch` | Source-reported epoch associated with a reduced position; its UT, UT1 or TT time scale remains explicit. |
| `reference_distance` | Source-reported Horizons model distance, distinct from an instrumental reading. |
| `right_ascension` | Published right ascension of the named target; angular conversion multiplies time seconds by 15. |
| `simulation_alpha` | Source-reported early simulated Mars/star right-ascension separation. |
| `simulation_beta` | Source-reported late simulated Mars/star right-ascension separation. |
| `simulation_difference` | Source-reported difference between simulated early and late separations. |
| `simulation_parallax` | Source-reported simulated residual parallax after its motion subtraction. |

## role

| Term | Meaning |
| --- | --- |
| `adopted_value` | Adopted calibration, comparison coordinate or model parameter; not a new measurement. |
| `instrument_reading` | Original dial or micrometer reading, before angular calibration or motion subtraction. |
| `prediction` | Source model or simulation output, retained separately from measured evidence. |
| `recorded_clock` | Clock expression reported for a source group. |
| `reduction` | Source-calculated quantity or published reduced coordinate; not relabelled as raw data. |

## unit

| Term | Meaning |
| --- | --- |
| `JPL_D12.5_UT` | JPL encoded epoch field with five implied fractional Julian-day digits. Dividing the encoded integer by 100000 yields the recorded UT Julian day; UT is not renamed UTC or UT1. |
| `arcsecond` | Angular seconds; derived magnitude is unsigned and derived_signed_value_exact retains the source sign. |
| `arcsecond_per_0.0001_inch` | Angular seconds per 0.0001 inch of micrometer displacement. |
| `arcsecond_per_hour` | Angular seconds per hour of elapsed time. |
| `arcsecond_per_turn` | Angular seconds per complete dial turn. |
| `astronomical_unit` | Source-model astronomical-unit distance; no extra distance calibration is inferred. |
| `clock_expression` | Literal recorded clock text. An existing source-EDT conversion is exposed as derived_timestamp in UTC, retaining its method and the original EDT expression. |
| `day` | Days as used in the source period calculation. |
| `dimensionless` | Unitless coefficient, ratio or eccentricity. |
| `hhmmss_millisecond` | JPL fixed-width right-ascension notation: hours, minutes and seconds with three implied fractional digits. Converted values are angular seconds. |
| `hour` | Hours of elapsed time, not angular hours of right ascension. |
| `inch` | Micrometer displacement in source-stated inches. |
| `julian_day` | Source Julian day; the associated time scale, such as USNO UT1, remains explicit. |
| `magnitude` | Source-stated astronomical magnitude or magnitude difference; the photometric band and role remain source-specific. |
| `mile` | Source-stated miles. No unstated conversion to kilometers is applied. |
| `second_of_time` | Seconds of time, including right-ascension differences; not angular seconds. |
| `sexagesimal_degree` | Source notation: signed degrees, arcminutes and arcseconds separated into three fields. Existing exact conversion is exposed in angular seconds. |
| `sexagesimal_hour` | Source notation: hours, minutes and seconds of right ascension. Existing exact conversion is exposed in angular seconds, using 15 angular seconds per time second. |
| `signed_ddmmss_centisecond` | JPL fixed-width declination notation: sign, two degree digits, two minute digits, and seconds with two implied fractional digits. Converted angular seconds retain the sign separately. |
| `turn` | Complete turns of the source dial. |
