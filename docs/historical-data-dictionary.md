# Historical quantity and role reference

These terms describe source meanings and explicit conversions; they do not establish observational independence or apply new corrections.

See the [database schema](database-schema.md) and [catalog dictionary](catalog-data-dictionary.md).

## quantity

| Term | Meaning |
| --- | --- |
| `altitude` | Angle above the local horizon; limb, correction state and instrument remain source qualifications. |
| `altitude_difference` | Difference between two stated altitudes, not a separate absolute altitude. |
| `angle_component` | An isolated place of a written angle whose complete coordinate is not established. |
| `angular_area` | Solid angular extent of a sky region, expressed in explicitly printed square degrees. It is distinct from a linear angle or star count; exact conversion preserves stated approximation flags. |
| `angular_daily_motion` | Angular motion per source-defined day. |
| `angular_diameter` | Apparent angular diameter of the stated body. |
| `angular_diameter_variation` | Stated change or range in angular diameter, distinct from the body's angular diameter itself. Preserve bounds and assumptions. |
| `angular_hourly_motion` | Angular motion per source-defined hour. |
| `angular_length` | Angular extent of a feature or construction, with endpoints retained in context. |
| `angular_minutely_motion` | Angular motion per source-defined minute of time. |
| `angular_motion_difference` | Difference between stated angular motions over their recorded interval. |
| `angular_offset` | Directional angular offset of a subject from a reference, with the coordinate axis unestablished. It is not an absolute coordinate or necessarily the total great-circle separation. |
| `angular_semidiameter` | Apparent angular radius of the stated body; source adjustment instructions are preserved separately and are not applied again. |
| `angular_separation` | Angle between the stated subject and reference endpoint. |
| `angular_yearly_motion` | Angular change per source year, retaining the source definition and qualifications; no conversion to modern mean years or seconds is implied. |
| `annotated_time` | A time supplied by an annotation; not automatically the observing clock. |
| `ascensional_difference` | Angular difference between right and oblique ascension in the source geometry; this is an angle, even when the header says Temp., and is distinct from tabular interpolation increments. |
| `azimuth` | Horizontal direction in the source's stated origin and orientation convention. |
| `azimuth_correction` | Stated adjustment to azimuth, preserved separately from the recorded direction. |
| `calculation_angle` | Angle in a stated geometrical or numerical calculation. |
| `calculation_epoch` | Time assigned to a calculation rather than an observed clock reading. |
| `clock_component` | An isolated hour, minute or smaller place without an established complete clock. |
| `clock_correction` | Stated adjustment to a clock reading, with sign and application retained separately. |
| `clock_drift` | Stated clock gain or loss over the source's interval. |
| `clock_elapsed_time` | Duration between source events; not a clock-of-day timestamp. |
| `correction_ratio` | Ratio used to scale a source correction. |
| `declination` | Equatorial angular distance from the celestial equator; hemisphere requires source evidence. |
| `declination_correction` | Stated adjustment to declination, not silently applied to the original reading. |
| `declination_difference` | Difference between stated declinations, with direction qualified by the source. |
| `distance_in_german_miles` | Historical length in the source's German miles; no modern physical conversion implied. |
| `distance_in_ordinary_miles` | Historical length in the source's ordinary miles; distinct from German miles. |
| `distance_in_paces` | Native length in source paces, with no assumed physical conversion. |
| `distance_in_semidiameters` | Distance expressed in multiples of a source-named body's semidiameter. |
| `distance_in_stadia` | Distance expressed explicitly in source stadia, retained as a native length without selecting a modern stadium length. |
| `distance_in_unspecified_miles` | Native length in miles whose convention is unstated; no German, ordinary or modern equivalence inferred. |
| `eclipse_extent` | Reported or predicted eclipsed extent, or a stated input extent, in native points or explicitly identified digits with sexagesimal subdivisions; role distinguishes observations, inputs and predictions. No assumed conversion to diameter fractions. |
| `ecliptic_latitude` | Angular distance north or south of the source's ecliptic plane. |
| `ecliptic_longitude` | Position along the ecliptic; a zodiac-sign origin remains explicit. |
| `expected_clock` | Predicted or expected clock reading, distinct from a recorded reading. |
| `geographical_latitude` | Terrestrial latitude in the source's stated geographic context; distinct from celestial latitude and site altitude readings. |
| `geographical_longitude` | Terrestrial longitude in the source reference-meridian convention; not an ecliptic coordinate or an assumed Greenwich longitude. |
| `horizon_inclination` | Inclination involving the horizon in the stated geometrical construction. |
| `hour_angle` | Angular displacement relative to the meridian, with source orientation retained. |
| `inferred_time` | Time inferred by the source from other readings or calculations. |
| `instrument_altitude_bias` | Stated instrument offset or error affecting altitude measurements. |
| `instrument_dimension_angle` | Angle describing instrument construction or dimensions. |
| `instrument_separation_bias` | Stated instrument offset or error affecting angular separations. |
| `latitude_correction` | Stated correction to latitude in the source's identified coordinate system. |
| `latitude_difference` | Difference between stated latitudes in their source coordinate system. |
| `longitude_correction` | Stated correction to longitude; origin and coordinate system remain contextual. |
| `longitude_difference` | Difference between stated longitudes, not an independent absolute coordinate. |
| `meridian_distance` | Source-labeled angular distance from the meridian; not silently equated with hour angle or zenith distance. |
| `meridian_time_difference` | Time difference associated with meridian passages or the source's meridian comparison. |
| `net_refraction_parallax` | Source-stated combined effect of refraction and parallax, without inventing its separate components. |
| `oblique_ascension` | Equatorial arc rising with the stated star or ecliptic point in the source oblique sphere; retains latitude, attribution and calculation context. |
| `oblique_descension` | Equatorial arc setting with the stated star or ecliptic point in the source oblique sphere; retains latitude, attribution and calculation context. |
| `obliquity` | Angle between equator and ecliptic as stated by the source; reported historical values and corrections retain separate roles. |
| `orbital_longitude` | Longitude in a source-defined orbital plane, distinct from ecliptic longitude. |
| `parallax_angle` | Stated parallactic angle; altitude, longitude and latitude components remain qualified. |
| `polar_distance` | Angular distance from the source-identified celestial pole. |
| `proportional_minutes` | Sexagesimal interpolation or proportion parameter, not automatically an angular or clock minute. |
| `recorded_clock` | Literal observing-clock reading with its original day and origin convention. |
| `refraction_angle` | Source-stated atmospheric refraction or refraction correction. |
| `right_ascension` | Equatorial coordinate along the celestial equator in the source's stated origin convention. |
| `right_ascension_difference` | Difference between stated right ascensions. |
| `rising_amplitude` | Angular distance on the horizon between equinoctial rising and the rising point of the stated celestial body or ecliptic point; direction and terrestrial latitude remain explicit source qualifications. |
| `separation_correction` | Stated adjustment to an angular separation. |
| `separation_difference` | Difference between angular separations or a stated separation residual. |
| `separation_ratio` | Ratio of separations in a stated source comparison. |
| `source_fraction` | An explicit fraction whose physical interpretation is retained in source context. |
| `source_scalar` | Scalar, count or model length in a source-defined scale, not an inferred physical unit. |
| `source_scale_ratio` | Proportional or scale ratio explicitly given by the source. |
| `source_sexagesimal_length` | A linear model length stated in native parts and sexagesimal subdivisions; angular-style printed marks do not establish angular units. The stated reference radius belongs to the source context. |
| `stated_angular_precision` | Source-stated angular precision or resolution limit, retaining approximation and instrument context; not an inferred standard deviation or correction. |
| `stellar_magnitude_class` | Native visual stellar magnitude class, retaining source punctuation and qualifications; not a calibrated modern photometric magnitude. |
| `temporal_hour_count` | Count of unequal or temporal hours in the stated day or night, retaining native sexagesimal subdivisions without conversion to ordinary clock seconds. |
| `transit_clock` | Clock reading associated with a transit or meridian passage. |
| `unclassified_angle` | Known angular expression whose more specific observational role is unresolved. |
| `unclassified_numeric_expression` | Preserved numerical expression whose unit or interpretation is unresolved. |
| `zenith_distance` | Angular distance from the zenith as stated by the source; kept distinct from altitude and distance from the meridian. No complement is silently applied. |

## role

| Term | Meaning |
| --- | --- |
| `adopted_value` | Value selected or adopted by the historical source. |
| `calculation_epoch` | Time reference for a calculation, not an observing clock by default. |
| `calculation_intermediate` | Intermediate quantity in a printed calculation. |
| `calibration` | Reading or parameter used in a source calibration. |
| `cancelled_reading` | Reading explicitly canceled in the source, retained as evidence. |
| `contextual_coordinate` | Supporting coordinate rather than the primary target reading. |
| `editorial_addition` | Quantity supplied by an editor, distinct from the recorded observation. |
| `editorial_suggestion` | Tentative editorial reading or interpretation, left unapplied. |
| `editorial_variant` | Alternative reading recorded in the editorial apparatus. |
| `expected_calibration` | Expected calibration result rather than a measured calibration reading. |
| `historical_comparison` | Value quoted for comparison with another historical result. |
| `historical_correction` | Correction stated by the historical source and preserved separately. |
| `historical_input` | Stated input to a historical calculation or model. |
| `historical_prediction` | Position or value predicted by a historical model. |
| `printed_correction` | Correction explicitly printed in the source, without silent substitution. |
| `recorded_clock` | Clock reading attached to a source event. |
| `recorded_coordinate` | Coordinate as recorded; the role alone does not establish whether earlier reductions were applied. |
| `recorded_reading` | Reading reported in the observational record. |
| `reduction` | Quantity resulting from a stated observational reduction. |
| `repeated_reading` | A separately recorded repeat; not an automatically independent observation. |
| `source_alternative` | Alternative supplied by the source and retained without replacing the principal reading. |

## unit

| Term | Meaning |
| --- | --- |
| `arcsecond` | Angular second: 1/3600 degree. Not a second of time. |
| `arcsecond_per_source_day` | Angular seconds per day under the source's day convention. |
| `arcsecond_per_source_hour` | Angular seconds per source hour. |
| `arcsecond_per_source_minute` | Angular seconds per source minute of time. |
| `arcsecond_per_source_year` | Arcseconds per year as stated by the source, without an inferred year length or time scale. |
| `mile` | Base native mile component, with German or ordinary mile defined by the quantity; no SI conversion. |
| `mile_minute` | One sixtieth of the source-named mile; a length component, not an angular or clock minute. |
| `mile_second` | One sixtieth of a mile-minute, hence 1/3600 of the source-named mile. |
| `ratio` | Dimensionless exact ratio in the stated source comparison. |
| `second_of_time` | Clock or duration second; original clock origin and calendar remain explicit. |
| `semidiameter_second` | A sixtieth of a semidiameter-minute, hence 1/3600 of the source-named radius; a length component, not an arcsecond. |
| `source_angle_component` | An isolated angular place; consult components rather than treating it as a full angle. |
| `source_clock_component` | An isolated time place; consult components rather than treating it as a full clock. |
| `source_eclipse_digit` | Explicitly stated native eclipse digit with minutes of 1/60 digit and seconds of 1/3600 digit. Preserves the source extent without converting to angles or assuming a diameter fraction. |
| `source_eclipse_point` | Native eclipse point. A point-minute is 1/60 point; this is not an angular unit or an asserted fraction of a body's diameter. |
| `source_fraction` | Source-defined fraction without an inferred physical dimension. |
| `source_german_mile` | German mile as stated in the source. Preserve local scale and qualifications; no assumed kilometer equivalence. |
| `source_length_part` | One native linear part; a part-minute is 1/60 part and a part-second is 1/3600 part. No angular or physical-distance conversion is implied. |
| `source_numeric_expression` | Literal numerical notation without an established scalar conversion. |
| `source_ordinary_mile` | Ordinary mile as stated in the source. Preserve local scale and qualifications; no assumed kilometer equivalence. |
| `source_pace` | Pace as stated in the source; no assumed physical length. |
| `source_scalar` | Source-scale scalar or count; its physical scale is not inferred. |
| `source_semidiameter` | Multiple of the semidiameter explicitly named in the source. |
| `source_stadium` | The source stadium, a historical length unit. No metric size or equivalence with a pace or mile is assumed. |
| `source_temporal_hour` | One source unequal/temporal hour, a twelfth of the stated day or night. Native minutes and seconds subdivide this count by 60 and 3600; they do not establish SI durations. |
| `source_unspecified_mile` | Source mile of unstated convention; no assumed physical length. |
| `source_visual_magnitude_class` | Source visual magnitude classification. Numerical or fractional class values remain in their native scale; no flux ratio or modern passband conversion implied. Nebulous and uncertain entries can remain without a scalar. |
| `square_degree` | Area on the sky in square degrees, retained as a native area value. No conversion to an angular length, position, or star count is implied. |
