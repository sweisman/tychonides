# Comparing historical and modern corrections

Tycho’s and other astronomers’ recorded observations are the common evidence for
the analyses. Corrections produce linked results; they never replace a recorded
reading. Numerical normalization changes units and notation without applying an
astronomical correction.

## Comparison cases

| Case | Meaning |
| --- | --- |
| As recorded | Preserve the source value and its known or unresolved reduction state. |
| Uncorrected | Use an established raw reading, or a separately documented recovery of it. |
| Historical | Reproduce the applicable contemporary table or procedure, including Tycho’s refraction values. |
| Modern | Apply a specified modern calculation to the same eligible input and quantity. |

Not every observation supports every case. If only a reduced coordinate survives,
do not manufacture its underlying instrument reading. A recoverable historical
correction can be undone as an explicit derivation; an uncertain reduction remains
uncertain. A missing correction is distinct from an explicit zero correction.

## Revisions already incorporated in a printed table

Keep reported means and later marginal corrections as separate coordinate
states. A mean label does not identify which earlier state or weights were used.
Arithmetic scenarios can be examined separately, but numerical agreement cannot
select the source inputs. Likewise, “with the Radius corrected” on XIII
pp.112–113 supplies no correction amount and does not by itself establish use of
the earlier four-arcminute instruction.

The November 26 separation table on XII p.295 presents a revised series. Its
detached note quotes a codex-E instruction and reports two earlier entered
figures alongside two instructed replacements. The catalog marks the six
table separations as `printed_correction` and retains the four note figures
separately, without an observing clock for the examples. They do not supply the
remaining original entries or a correction formula. These source revisions
cannot be treated as unreduced instrument readings, undone by a guessed column
swap, or applied a second time. The declinations and clock readings retain their
own source roles. See the [published editions and scans](sources.md).

## Instrument corrections

The great-globe examinations on X pp.34–35 give a four-minute upper limit and
a half-minute addition that would make the respective stellar-distance
constructions coincide. Both retain
`source_correction_application=conditional_not_reported_applied`, their
addition direction and their separate target sets. The four-minute value is a
bound. Preserve the quoted distances and the source's conditional status;
the coincidence claim supplies no measured statistical uncertainty or general
instrument correction.

The examination on X p.29 compares three Augsburg stellar separations with
later sextant measurements. The paired differences are 5′, 4′ and 6′; these
arithmetic diagnostics do not define a uniform instrument correction. The
separate “smaller than both by ⅙” claim leaves its reference unit unstated.
Its bracketed instruction to qualify observations is attributed only to
Bartholinus, with no established application to individual records. Retain the
two calibration columns, the literal fraction and the witness qualification as
separate evidence when constructing correction scenarios.

On XIII p.110, the November 28–29 instrument warning concerns a fixed brass
channel near the Radius's eye end. Its stated thickness, ⅔ degree, is a
dimension parameter; the resulting “parallax, or aberration of sight” remains
unquantified. The proposed fixed-star comparison with and without the attachment
is a calibration plan. Preserve the recorded Mars distances without treating
the dimension as an error angle, applying it as a correction or counting it as
celestial parallax.

On XIII p.111, the December 5 check records 7°26′ between Orion's two shoulders
and says the other observations fall short by 4′ and are to be corrected.
Retain the calibration distance, the addition instruction and its unestablished
application separately. The text supplies no complete list of affected records
or printed expected 7°30′ calibration distance. Neither value should be invented,
and equal nominal clock values must not merge separate planetary and stellar
calibration events.

The sextant discussion on XII p.432 compares two Mars right-ascension routes and
two dated stellar separations. Its warning that distances were too short has no
universal correction amount or precisely established range of applicability.
The text separately gives an approximate 2½′ error estimate and states that the
following Jupiter distances were increased by 2½′. The catalog preserves the
estimate, the adopted amount, the addition direction and the reported application
as separate claims. An instrument warning cannot by itself authorize adding the
same offset to every Mars separation.

The following worked Jupiter reductions retain four explicitly corrected
separations and their linked calculation outputs. Independent review of the
original counterpart inputs on p.431 confirms that all four additions equal
2½′. This checks the printed arithmetic, not the accuracy of the adjustment or
the recovery of raw instrument readings. Right-ascension arithmetic across 0° is checked as circular arithmetic;
the adopted combinations retain unknown weights.

## Historical parallax and time reductions

On X p.199, a later inserted leaf explicitly written in another hand adds 2′
to Mars's longitude when recomputing opposition. Preserve that annotation's
coordinate table, correction amount and epoch separately from the main text.
Its writer is unidentified. The source's refraction terminology does not by
itself identify a modern correction or authorize changing every Mars record.

The main calculation on X p.200 adopts a Mars–Earth distance of 721 Earth radii,
attributed to Copernicus, and calculates altitude, longitude and latitude
parallaxes from that premise. These are model-dependent reductions, not three
independent parallax measurements. Future comparisons can vary the adopted
distance while preserving the given coordinates and altitude; a distance cannot
be inferred independently from angles that were themselves calculated using it.

The Mars recalculation on XIII p.154 gives northern latitude 3°27′, adds 2′
of parallax and obtains “true” latitude 3°29′. Preserve the input, addition
and output separately. The output already includes this historical correction;
adding another parallax term would apply a correction twice. The 2′ term is
an adopted historical adjustment, not a new parallax detection or a modern
distance measurement. See the [published editions and scans](sources.md).

The same passage distinguishes an earlier 12⅙-hour epoch from 12⅗ hours
equated and reduced to Uraniborg's meridian. This identifies a reduction meridian,
not Fabricius's observing site. Keep the two source expressions without splitting
their difference into an unstated clock error, equation of time or longitude
offset. Unknown calendar and clock-origin conventions still prevent an accepted
absolute observing timestamp.

On XIII p.155, the following longitude correction adds 6′ for latitude and
Mars's proper path, giving 2°35′ in the stated orbit frame. A separate conditional
branch prefers the December 10 observations and permits 2°34′. Preserve both
branches and their qualifications. The longitude/path correction is distinct
from the earlier latitude-parallax addition; neither value should replace its
input or be selected because it fits the following model comparison better.

## Refraction

On X p.390, the source raises the adopted southern Gemini-head right ascension
from 109°56′ to 109°58′, attributing the change to refraction of solar rays. It
then says Mars longitudes derived from that reference should increase by 2′.
Preserve the old stellar input, revised input, addition instruction and affected
reduction method separately. This is a historical correction claim; it does not
supply a modern atmospheric correction or authorize adding 2′ to raw Mars
readings. Later opposition and apogee calculations may already use the revision.

The same page's apogee trials include a tabular term called a parallax equation.
Retain it with its model arguments and subtraction instruction. It is not an
independent instrumental measurement of diurnal parallax.

Reviewed ecliptic coordinates can carry `source_coordinate_state` labels of
`refracted` or `true`. These preserve the source’s terminology and do not establish
which modern corrections remain necessary. An untagged record is not assumed raw.
Use the linked source correction inputs and results to avoid applying an existing
correction again.

`corrected_as_stated` preserves a Mars declination adopted as a historical input
when the source calls it corrected but does not identify the adjustment. This
label supplies no correction amount, original reading, hemisphere, or assurance
that refraction and parallax have both been removed.

A `declination_correction` records an angular adjustment separately from the
recorded and adopted declinations. Its `source_correction_operation` preserves
the source's `add` or `subtract` instruction, with `source_approximate` when
the stated amount is approximate. Catalog readings remain unchanged, and
agreement with one calibration difference does not identify an exclusive choice
among several instrument readings. A reported clock adjustment at noon likewise
does not supply corrected versions of every preceding clock.

Compare the source’s stated refraction, a reconstruction from the applicable
historical table and a modern calculation where the necessary inputs exist. Identify
the table edition, argument, interpolation rule and applicable range. For modern
calculations, identify the formula or software version and its required atmospheric
inputs. Unknown pressure, temperature or other conditions remain declared scenario
assumptions with sensitivity ranges, rather than measurements of historical weather.

Preserve whether an altitude or direction is apparent or unrefracted. For angular
separations, account for the directions of both objects where the method requires
them; a correction to one altitude is not automatically a correction to their
separation. Keep refraction separate from parallax, including when the source gives
only a combined correction. A source’s confidence claim supplies no numerical error
bar or validation of its refraction model.

## Scenario records

Every derived result will identify:

- The recorded input IDs, source citations and reduction state.
- The correction choices, historical sources or modern formulas, and their versions.
- Parameters, units, reference frames, time conventions and environmental assumptions.
- The corrections already present, operations performed and their order.
- The output quantity, uncertainty treatment and unresolved requirements.

Vary historical and modern choices separately and in compatible combinations.
Refraction, timing, reference-star positions and other adjustments can interact;
unsupported combinations should have an explicit reason for being unavailable.
Keep correction choices distinct from the orbital model and its parameter source.

## Uncertainty and sensitivity procedure

| Kind | Representation |
| --- | --- |
| Recorded precision | Preserve written components and increments; printed precision alone is not a standard deviation. |
| Random scatter | Estimate from suitable repeated measurements with the estimator, sample and assumptions stated. |
| Shared errors | Model instrument, clock, reference-star and calibration effects at the group level; repetitions do not average away a common offset. |
| Interpretive alternatives | Keep supported readings, calendars, clock conventions and correction states as separate scenarios. Their spread is sensitivity, not automatically a confidence interval. |

Retain dependencies of derived coordinates on their readings and calibrations.
Compare correction scenarios on a declared common eligible selection and explain
any scenario-specific exclusions. Do not select assumptions because they reduce
the residuals.

For parallax, simulate zero and known nonzero signals using the actual cadence,
measurement types, accepted geometry and timing. Include plausible shared errors
and test confusion with orbital motion, clocks, instruments and refraction. Report
recovery bias, false-positive rate, interval coverage and detection threshold.
Declare the criteria for a detection, bound or inconclusive result before examining
the fitted result; a useful sensitivity limit is a complete feasibility result.

## Comparisons and checks

*Opera Omnia* XIII p.219 reports that the Benátky sextant and revolving
quadrant gave altitudes 2′ too high from their initial setup on 28 August,
and that the affected entries were corrected wherever they could be found.
The note leaves the starting year and individual application status to be
established from context and surviving readings. Preserve this correction
claim before constructing scenarios: an as-recorded value may already reflect
the adjustment. Do not subtract it again or manufacture an uncorrected original.
The claim does not automatically apply to Fabricius's separate instruments.

The January 20 stellar sextant checks on XIII p.220 report a separate 1½′
separation shortfall. The two displayed measured/expected differences are
90 and 100 arcseconds; preserve both pairs and the stated 90-arcsecond deficit.
The limited Mars distances also differ from their raw counterparts by varying
amounts. No single addition, or reuse of the earlier altitude correction, is
established for all of them. Historical correction scenarios must retain this
unresolved application rather than silently regularizing the printed values.

The latitude construction on XIII p.222 gives two separate 110-arcsecond
additions, their January 23/24 input coordinates and the results containing
those additions. Their physical correction type is unstated. Preserve both
chains and the later adopted latitude; do not add the terms again or replace
them with modern refraction before their meaning and required inputs are
established. These coordinate inputs do not recover raw instrumental readings.

Compare scenarios on the same eligible source records, preserving repeated-reading
groups and reporting exclusions. Report changes caused by correction choice as well
as residuals against the specified astronomical prediction. Assess sensitivity to
uncertain inputs without choosing corrections merely because they reduce residuals.

Validate reconstructed historical examples against their printed calculations,
modern methods against their documented reference cases, and both against consistent
units and direction conventions. Any recovery and reapplication check must state its
numerical tolerance. The catalog currently records the evidence for these analyses;
the correction engine and scientific comparisons remain planned.
