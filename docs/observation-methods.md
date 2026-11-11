# Historical Record Casebook

Detailed source cases from Tycho’s *Thesaurus Observationum*, its Pafko controls,
and the [supplementary historical books](historical-books-ingestion.md) explain
how particular readings are represented. Use the topic guide or search for a
source page, instrument or notation. Each case retains its own evidential scope.

For the processing sequence, use the [workflow](data-workflow.md). For source
selection and general rules, use the [ingestion strategy](ingestion-strategy.md).
The [review reference](review-reference.md) documents contributor syntax.

## Essential Distinctions

| Distinction | Consequence |
| --- | --- |
| Reading, reduction, prediction and adopted input | Preserve the stated role before choosing records for an analysis. |
| Native notation and numerical conversion | Exact arithmetic does not establish measurement accuracy or resolve an unknown unit. |
| Recorded clock and observing epoch | A clock does not supply its calendar, day origin, meridian or time scale. |
| Repeated publication and independent observation | Establish lineage and shared dependencies before combining records. |
| Source correction and modern correction | Keep originals, application state and supported alternatives separate. |

The [terminology](catalog-terms.md) defines what review, verification and
analysis eligibility establish. Examples below do not create universal rules
for a whole book or observing program.

## Guide to the methods

Use [catalog terminology](catalog-terms.md), the [ingestion strategy](ingestion-strategy.md)
and [worked numerical examples](catalog-data-dictionary.md#worked-numerical-examples)
for the general rules. The cases below retain their individual source scope; a
rule demonstrated in one passage is not automatically valid throughout a book.

| Topic | Entry points |
| --- | --- |
| Clocks and calendars | [Angles and clocks](#angles-and-clocks); [relative dates](#relative-dates-inherited-directions-and-mixed-quantities) |
| Angular notation and signs | [Angles and clocks](#angles-and-clocks); [sexagenae](#sexagenae-and-historical-opposition-arguments) |
| Corrections and uncertainty | [Correction scenarios](correction-comparisons.md); [alternative reductions](#alternative-reductions-and-near-horizon-comparisons) |
| Instruments | [Meridian checks](#meridian-checks-and-instrument-alignment); [failed clocks](#failed-clocks-and-instrument-checks) |
| Source relationships | [Evidence layers](#keep-the-evidence-layers-separate); [matching](#match-records-without-their-measured-values); [printed pages](#printed-pages-and-scan-images) |
| Extending the catalog | [Starting another work](ingestion-strategy.md#starting-another-work); [proportionate verification](ingestion-strategy.md#verification-proportional-to-the-change); [other bodies and records](#before-extending-to-another-planet-or-record-type); [source queue](data-sources.md#planned-ingestions) |

## Keep the evidence layers separate

Word-valued numbers require complete, unit-qualified occurrences. A parser must
not select “six thousand” inside “thirty-six thousand”, or “two miles” at the end
of a longer written number. Retain a complete unsupported expression when its
scalar cannot be established; an Arabic restatement and its written equivalent
do not create independent observations. Markdown escaping of a table bar can be
recognized for literal validation while the original escaped expression remains
unchanged and its numerical meaning remains unresolved.

An annual calendar of stellar risings and settings is a collection of recurring
phase claims, rather than a sequence of independently dated observing nights.
Keep its horizon, reference-year limits, comparative dates and named authorities
explicit. A zodiac degree rising or setting with a star describes an associated
horizon point; it must not silently become the star's intrinsic ecliptic
longitude. Retain phase entries that have no printed angle, and preserve symbolic
sign boundaries without inventing a recorded numerical zero.

A zodiac glyph can form part of a star's name rather than identify the origin
of its numerical longitude. Interpret the complete label and its source context
before adopting a sign. A historical name also need not identify the modern
star with the same name: Origanus explicitly calls his chart's Scheat the right
shin of Aquarius. Preserve that description without substituting a Pegasus
identification. In diagram descriptions, original labels can resume after an
English explanation; select the actual label occurrences throughout the
description and count a translated repetition only once.

An ecliptic longitude within a named zodiac sign retains its native magnitude
and a separate longitude from zodiac zero. Bind a printed sign directly to the
expression, or bind its inherited origin to a reviewed context with explicit
scope. Resolve that context within its source review. A nearby sign belonging to
another body, expected planetary motion or numerical agreement cannot supply
the origin. Preserve ambiguous signs and unresolved expressions without choosing
an absolute longitude. A source-bound metadata correction must preserve the
literal, components, native magnitude and identity, with its prior interpretation
retained separately. The same origin evidence must survive CSV and SQLite export.

Computational tables retain their row and column arguments, component units and
the author's names for their results. A lunar mean center, anomaly or tabulated
common angle is not automatically an observed ecliptic longitude. Keep a
proportional part distinct from the corrected equation to which it is added.
Printed worked examples preserve the stated inputs, lookup results, intermediate
values and rounding instructions; ingestion does not require reproducing their
algorithm. A repeated root in an example is another publication occurrence,
not another observation. Queried entries remain unresolved and bracketed
editorial replacements remain unapplied alternatives.

A queried native model length retains its literal expression and
`source_length_part` unit without an adopted scalar. It does not become an angle
because the table uses sexagesimal notation. An editorial length replacement
must link to its unchanged original and remain explicitly unapplied. Where an
editorial insertion interrupts adjacent degree/minute/second columns, bind the
original component sequence as ordered literal fragments under the reviewed
column headings; preserve the inserted proposal as a separate alternative.

Longomontanus's lunar correction tables distinguish angular corrections, native
model lengths and proportional minutes. The latter express a ratio to a whole
of 60 proportional minutes, rather than clock or angular minutes. Preserve
head/foot reading directions and printed add/subtract rubrics as operations,
not coordinate hemispheres. His altitude-parallax tables retain lunar distance
columns in Earth semidiameters; they supply historical model corrections, not
parallax detections. His refraction synopsis attributes its values to Tycho's
Uraniborg tables. Retain the stated pole elevation and atmospheric qualifications,
and leave blank stellar cells absent rather than extrapolating zeros.

Riccioli's planetary latitude procedures also distinguish a sine on a radius of
60 from the angular latitude obtained in a later lookup. In the *Astronomia
Reformata*, Precept 117, steps 5–6, states that distinction; Precepts 120 and 123
apply the same procedure to Jupiter and Mars; Precepts 126 and 129 likewise
distinguish the sine from the final latitude for Venus and Mercury. The native
latitude-sine entries retain proportional coefficients. The adjacent
reduction and curtation columns retain their separately stated angular units.
Degree-like place headings do not alone make every entry an angular coordinate.
Keep the table arguments, conditional north/south sign headings and unapplied
correction rules with each value. Likewise, the tables' “parallaxes of the annual
orb” are model equations and must remain distinct from observed diurnal parallax.

In his Venus and Mercury canons, differences of proportional scruples printed
under an S heading are proportional seconds of the same whole, rather than
arcseconds. A standalone S component does not require an invented minute place.
Queried coefficients retain the ratio unit without an adopted value; editorial
coefficient replacements remain linked and unapplied. If a printed heading and
the number of components conflict, preserve the full expression without choosing
units from neighbouring values or expected smoothness.

Mean-motion tables can share one printed increment between longitude and anomaly,
or one elapsed argument among several planets. Preserve that occurrence once
with its stated applications. A shared elapsed argument can name the planetary
calculation collectively; it does not create separate clocks or observations.
Retain world/Christ epoch labels and month names without inventing absolute
observing timestamps. A field with fewer component places than its heading
remains unresolved when the omitted place is not established.

Astronomical calculations within astrological discussions retain their numerical
roles: chart positions, ephemeris inputs, ascensions, geometrical corrections and
tabulated angular/time correspondences. A calculated natal chart is not an
astronomical observing session. Preserve the source's clock qualifications and
direction-to-age rules without treating claims about life events as measurements.
Horary times written in degrees and minutes are equatorial arcs per unequal hour;
their angular units must survive export. Distinguish a physical body's position
from a constructed aspect point and retain shared chart magnitudes once, with
their stated applications.

An explicitly counted unequal-hour quotient uses `temporal_hour_count`, with
its exact value in `source_temporal_hour`. Its sexagesimal minute and second
places divide that native count; they do not establish an ordinary-clock or SI
duration. Keep the angular horary times used in the calculation separately.

Keep compartment labels and glyphs without attached numbers as diagram context.
When distinct zodiac signs flank one magnitude, preserve that magnitude and
leave its origin unadopted unless the source establishes the binding.

Morning and evening identify dayparts, not the origin of the historical day.
Keep unusual chart hours and their A.M./P.M. labels as written. A morning date
in prose and a preceding-day chart label remain separate claims until their
clock conventions are established. Differences between a chart and its prose
explanation likewise retain both printed values; agreement with a prediction
cannot select or repair either occurrence.

An explicit chart heading such as “Day, Hour, Minute” establishes separate
calendar and clock fields: retain the day in its date claim and the literal
hour/minute pair in the clock record. Do not convert the calendar day into an
elapsed duration. A temporal hour is a division of the stated day or night;
it is not automatically 3,600 seconds. Distinguish it from ordinary time used
in the author's conversion. Equatorial “times” take their angular units from
the local explanation, rather than from a general interpretation of that word.

A duration printed across adjacent table columns can retain one complete
expression with explicit consecutive column bindings. An editorial replacement
of one component inherits only the unchanged components of its linked original;
it remains unapplied. When a coordinate crosses a page turn, bind its literal
fragments and retain both source pages. A diagram description that refers to an
absent label list establishes a coverage question: retain the available caption
fields and flag the missing companions rather than importing them from apparatus.

Native size statements require their comparison measure and endpoint order.
A bulk factor, a diameter ratio and a fraction of the apparent solar diameter
are different claims. Preserve inverse wording such as "smaller by39times"
with its stated factor; keep ratio operands and fractional supplements separate.
Likewise, a physical diameter and a radial distance can share Earth-radius units
without describing the same quantity. Retain the source length role and any
explicit editorial alternative. A source's calculated size remains distinct from
its reported apparent diameter.

A comparison table can juxtapose earlier and revised source versions without
providing independent observations. Retain each attributed distance column and
the source's stated differences. A printed `plus` or `minus` label, including
the contraction `min⁹`, describes that comparison, not celestial hemisphere.
Bind the complete label before parsing its magnitude. Preserve discrepancies
between the printed differences and subtraction of the inputs. Where a compiler
explicitly selected readings closest to his own, retain that selection statement;
the resulting agreement cannot independently validate his accuracy.

Preserve the original record, its transcription, any translation, and each derived numerical representation separately. The final publication text is the authoritative comparison input. Bibliographic references and scans establish the printed location; they do not supply missing figures without a separately documented source reading.

Three independent questions govern validation:

1. Does the final edition agree with the independent transcriber's quotation?
2. Does that quotation agree with the transcriber's numerical conversion?
3. What does the printed source actually show?

Agreement between two transcriptions does not prove that either reproduces the print. A disagreement can involve the quotation, conversion, contextual interpretation, or source matching. Record which check failed before proposing a correction.

Link a corrigendum to an existing reading or correction state rather than
counting its repeated numbers as another measurement. Keep changes to targets,
dates, clock scope and diagrams alongside numerical replacements.

Dreyer states on X p.431 that none of codex L is in Tycho's hand, and that he
obtained access to the 1585 volume of codex V after most of that year's
observations had been typeset. Preserve these witness qualifications with
their scope. They do not supply a numerical transcription-error rate. See the
[published volume](https://books.arsastronomica.com/Tycho_Brahe_Thesaurus_Observationum_Tomus_Primus.pdf).

An annotation's marker identifies its attachment point. A note describing a
whole page may have a broader scope; the attachment page alone does not settle
that scope. Keep edition annotations distinct from the historical observer's
comments and preserve unresolved scope explicitly.

An edition's collected footnotes may have no printed-page location of their
own. Retain the note marker, its definition and its attachment to the cited
passage. An annotation-only review checks those literal links without creating
an observing event or assigning an invented page. Editorial arithmetic and
suggested readings remain qualifications or separate alternatives; they do not
replace the historical numbers automatically.

Numerical endnotes use the same literal attachment checks. Each value keeps
its editorial role, note marker and link to the original quantity. A marker
citation permits an unpaged editorial value; it does not permit an unpaged
observation. Keep partial components partial, and distinguish readings reported
from another copy from values suggested by arithmetic or a table progression.
Both kinds of proposed replacement remain unapplied.

Editorial calculations can also supply native scalar terms, such as a column
step or a proposed sine-table value. Retain the stated table scale and the
editorial role, with a link to the affected source quantity. A supplied arithmetic
operand is not automatically a proposed replacement. Keep an approximate range
distinct from discrete alternatives joined by “or,” and leave the inclusivity of
bounds unstated when the note does. Partial minute or second fields retain their
component scope; they do not become complete coordinates by borrowing unchanged
components from the table.

Automated page indexes are provisional claims. A date number in a running
header can be mistaken for a page number. Keep an accepted, source-reviewed
citation when it conflicts with such an index, and retain the conflicting
claim separately. This is a provenance problem, not evidence of inaccurate
numerical transcription. Do not interpolate an unknown page from nearby
records or equate an annotation's attachment with its physical location.

Resolve contextual clock and instrument references within their stated source
scope. Equal local labels in different passages do not establish identity.
Supplementary quantities from an already catalogued session reuse its observing
group through an explicit source-bound association. The compiler checks the
edition and target and retains that group's clock and epoch links; adding a
missed quantity does not create another observation.
An explicitly reviewed clock in that same source statement may fill a group's
previously empty observing-clock link. It cannot replace an existing link.
Lower and upper clock bounds attach to the group as interval evidence and leave
the point-clock link unset; no midpoint or absolute epoch is inferred.

Structured dates already recorded in source contexts can also appear in the
date tables. These are named source labels, with the original date expression,
context type and clock qualification retained where stated. A calculation's
date does not become an observation date. Relative-night wording and incomplete
components remain explicit; neither a calendar nor an absolute epoch is supplied
from the numeric components alone. The underlying context records remain intact.
Complete clock components derived from an explicit earlier hour remain
separate from the components printed in the row; they establish no absolute
timestamp. A later column identification can revise an angle's interpreted
quantity type while preserving its original classification, numbers and
remaining instrument uncertainty.

A missing catalog/control link is not evidence of an omitted observation.
Prose may contain several readings on one line, and an older extraction may
use a different logical column convention. Bind such cases explicitly by
reviewed source location, printed order and instrument or pinnule qualifiers.
Preserve both original identities and all numerical fields. Neither numerical
agreement nor the number of currently unlinked rows establishes an omissions
count.

A chapter's planet does not determine every measurement's subject. XI p.84
places a Spica refraction table inside the Mercury observations. Its columns
give declination and right-ascension components, which must retain their own
geometry rather than becoming universal vertical-refraction corrections.
Resolve topical scope from the heading's words as well as its level: XI's
fixed-star sections begin under fourth-level headings after Mercury. A nearby
third-level planet heading does not make those stellar observations planetary.

## Angles and clocks

Calendar and era are separate. In his dedication, Origanus explicitly equates
the Julian year 1654 with 1609 of the Christian Dionysian era. Preserve both
labels; a different era count is not evidence of a mistranscribed year. His
instructions on time also distinguish current years from completed years.
Establish the local era and counting convention before assigning an absolute
epoch, and do not transfer an offset to every occurrence of “Julian.” See the
[published edition](https://arsastronomica.com/works/david-origanus-ephemerides-brandenburgicae/).

Eclipse extents written in points with sexagesimal minutes retain their own
native unit. For example, 13 points 27′ becomes exactly 269/20 points. The prime
here subdivides a point; it does not make the value an angle. A conversion to a
fraction of the eclipsed body's diameter requires separate evidence for the
point scale. Tabular extents remain predictions, even when adjacent to an
observed eclipse report.

Dates belong to their source and observing group. Bürgi's planetary series in
Snellius explicitly identifies the Julian calendar; its before-noon,
after-noon and evening labels remain separate from the numerical clocks.
An omitted daypart remains unknown, and two clocks preceding several readings
do not establish which clock belongs to each reading. Preserve out-of-order
dates and the edition's qualifications without repairing chronology.
Source-date claims expose these recorded components without asserting an
absolute observing epoch. Cross-source date links are rejected.

A staged clock match can cover only the leading field when a heading repeats
a unit before superscript notation, as in `Hour 0^h^ 44^m^`. Bind the complete
marked sequence through the shared materializer; the leading zero alone does
not represent the recorded clock. Preserve genuinely absent minute or second
fields as absent. A central-box Day/Hour tuple also keeps its calendar day
separate from the clock components.

A repeated unit mark can be a source-level notation question. On XIII p.181,
the native print and final text both give the December 31 longitude as
17°38′9′ in Leo. Preserve all three numerals and their visible marks while
leaving the scalar interpretation unresolved. The matching print establishes
no transcription discrepancy, and does not by itself establish that the final
component means seconds. Keep a source notation question distinct from an
edition error. Similarly, a solid quadrant retains its own instrument label
without being renamed a steel or mural quadrant.

A following-night or preceding-night label keeps its named day and explicit
relation. Do not advance or retreat the date before establishing the calendar
and day origin. Alternating planetary separations and comparison-star altitudes
retain their own targets and stated pointing associations; the stellar altitude
does not become a Mars altitude or a numbered clock. A generic quadrant label
does not establish a mural, rotating or steel instrument subtype.

Twilight and sunrise are different time anchors. Preserve an interval stated
before twilight without choosing a modern twilight definition, solar altitude,
weather condition or absolute observing time. A visual offset expressed as a
planet's own body diameter retains its relative scale and direction; it does
not supply the body's angular diameter. Source statements that the comparison
stars still need identification qualify their descriptive labels and must not
be resolved from proximity or a later observation alone.

A visual separation ratio has two angular pairs: the planet–star separation
and the comparison baseline. Retain both pairs, the dimensionless number and
its approximate, by-eye character. “About double” does not give an absolute
angle or justify adopting a modern catalog separation. Likewise, “three or
four hours before sunrise” retains two approximate duration alternatives linked
to one observation, rather than a midpoint or two observing sessions. Stellar
meridian conditions remain qualitative unless a numbered time is recorded.

Use `angular_offset` for a directional angular displacement whose coordinate
axis is unestablished. Preserve the reference, direction and exact magnitude
alongside the source geometry. For example, Walther's reported displacement
west of Regulus also has a southward component (Riccioli, *Astronomia
Reformata*, book VIII, chapters III and IX, pp.331 and 340). The westward
component alone supplies neither an absolute coordinate nor the total
great-circle separation. Assign a longitude or latitude difference when the
source establishes that particular coordinate component.

Paired observing tables can print an original clock, a corrected clock and
companion coordinates within one observing group. Preserve their association
without counting the correction as another observation. An omitted hour stays
unstated unless source evidence establishes its inheritance; a printed minute
alone does not supply a complete clock. A comparison-star column labeled
only by its western position does not establish altitude or azimuth. These
distinctions occur together in Riccioli's Mercury tables (*Astronomia
Reformata*, book IX, chapter III, pp.345–347).

Keep a source's stated count of observing days separate from the printed dated
rows. Riccioli describes nine days of Mercury observations in February 1651
but supplies eight dated rows (*Astronomia Reformata*, book IX, chapter VI,
p.350). Preserve both facts without supplying a ninth observation.

Repeated separations retain each printed numerical occurrence. An explicit
“repeated twice” attached to one occurrence is a repetition claim, not permission
to synthesize another numerical record. A twilight qualification applies to the
reading it marks, without making every reading in the series doubtful.

When one written magnitude qualifies several coordinates, retain one numerical
occurrence and state all of its applications in the supporting context. For
example, a single approximate full-degree discrepancy applying to both longitude
and latitude does not supply two independently written values. Use shared
relationships rather than duplicating the occurrence or labeling an identical
copy as an alternative reading.

A preceding-transit interval is not an observing clock. For example, “a minute
and a half before” can normalize to 90 seconds while its approximate label and
relative anchor remain explicit; it supplies no exact derived transit timestamp.

An exact fraction can still lack a physical unit. Preserve its numerator,
denominator and original expression without choosing degrees, arcminutes or
body diameters from context alone. A qualitative comparison with a body's
diameter is not a measured numerical diameter. Keep a marginal reduction untimed
when no calculation epoch is supplied, and distinguish identically numbered
footnotes on different pages by their actual targets.

Distinguish the edition's disclosed interpretation from explicit printed marks.
On XI p.72, a bare figure is construed as seconds because the row sum closes;
on p.76, an altitude's degree unit is supplied from context. On p.69 the edition
explicitly substitutes ¾ for a printed 8/4 fraction. Preserve the reported print
and the supplied interpretation separately. A disclosed editorial choice is
neither a new observation nor, by itself, a transcription error.

The books use sexagesimal notation, including fractional minutes and seconds. Pafko's workbook preserves quotations and numerical components as well as signed decimal degrees. Comparing only the decimal column loses information needed to diagnose differences.

| Form | Exact interpretation | Pitfall |
| --- | --- | --- |
| 11°18⅙′ | 11 degrees, 18 minutes, 10 seconds | A fraction of a minute is not a fraction of a degree. |
| 1°23⅓′ | 1 degree, 23 minutes, 20 seconds | Small printed fractions can be confused in either transcription. |
| H. 3 27⅙ | 3 hours, 27 minutes, 10 seconds, when the clock schema supports it | Bare components need a labeled or otherwise established context. |
| H. 1¾ | 1 hour, 45 minutes | A fraction attached to hours has a different scale. |

A raised ending can change an abbreviation's meaning. In the Mercury–Jupiter
comparison, `Mtis` abbreviates *minutis*, a minute unit, rather than naming Mars.
Retain the local expansion without applying it to every similar abbreviation.

Use rational numbers for normalized arcseconds and clock seconds. Preserve the original expression, explicit precision, fraction, and unit. Keep sign or hemisphere separate from magnitude. A sign on an instrument orientation or comparison star cannot establish the planet's hemisphere. An omitted hemisphere remains unknown even when a decimal column supplies a sign.

Published periods may continue below seconds into thirds, fourths and fifths of
time. Establish their dimension from the complete day/hour/minute/second
sequence, rather than treating prime-like marks as angular by default. If a
source explicitly reuses previously named days and hours, bind those exact
occurrences and the new lower components with source fragments and the stated
continuation. This preserves shared parameters without inventing another raw
observation. Keep an interposed corrigendum separate from the original period;
unchanged places may pass to its linked editorial variant, with the correction
explicitly unapplied.

Origanus also expresses a lunation in days followed by sexagesimal fractions
of a day through a sixth place. Preserve the day scale for all six places,
separately from a neighbouring expression in hours, minutes and seconds of
time. A table headed only “minutes” or “Scrup.” does not by itself establish
the denominator: preserve a native value and the unresolved scale rather
than choosing a base from the sequence of numbers.

Calendar tables can use Roman numerals for native counts and letters for
indexing in adjacent fields. Establish the column or prose role first;
reviewed numeral aliases such as `IIII`, `XIIX` and `XXIIX` retain their written
form while using the shared native-count conversion. An indexing letter is
not converted merely because it resembles a numeral. Preserve star symbols,
blank cells and paired conditional epact labels separately. When equal labels
occur more than once in one cell, retain both the physical column and the
reviewed character interval for each occurrence. A correction that changes a
whole set of labels does not establish a one-to-one correction of its members.

In day-length calculations, prime marks on differences or proportional parts
can denote minutes, seconds and thirds of time. Establish their dimension from
the stated calculation: an angular interpolation argument and its corresponding
time increment remain separate quantities. A printed intermediate clock above
24 hours retains that value until the source's own rollover step; do not wrap
it during ingestion. Day-length table entries may serve several stated purposes,
such as a semidiurnal interval and a setting hour. Retain one source occurrence
with those applications. At polar latitudes, blanks explicitly explained as
continuous daylight or darkness are not numerical zeroes.

Equation-of-time tables require their stated conversion direction. In Origanus,
the solar and syzygy tables convert mean time to apparent time, while the lunar
instructions also describe the reverse conversion. Preserve the printed A/S or
Ad/Sub labels and their row and column scope, including labels inserted inside
a table. Their operation reverses with the conversion direction; S here is a
subtraction instruction. Paired upper and lower zodiac headers can use opposite
degree columns and different operations for the same written magnitude.

A meridian catalog supplies geographical inputs for astronomical reductions.
Retain the source reference meridian and distinguish transferring a predicted
event time from finding a planetary position at a supplied local time: the
source can prescribe opposite operations. Classify columns from their explicit
units and supported table structure while preserving an inconsistent heading.
Keep historical place names, absent operation letters and ruled blank cells as
written. In Origanus's Latin place catalog, explicit Mer./Meri. labels mark
southern latitude; an unmarked entry acquires no hemisphere from its place name.
Reported competing longitude determinations remain separate attributed claims.

Dotted time notation can be sexagesimal. The X p.387 note gives endpoints
7.36 and 4.12 with a stated interval of 8.36 hours. Preserve those expressions
and their contextual hour/minute components; do not read 8.36 as decimal hours.
This local convention supplies no universal rule for every decimal point.

Check the numeric column against the source hemisphere separately from checking the quotation. An unsigned quotation can agree in magnitude while its converted sign conflicts with an explicit source heading. Clock abbreviations such as `M.` for minutes must not enter the declination label; neither can the orientation of the armillae supply its sign.

Raw and corrected clocks may refer to the same reading. Preserve both and their documented association. Multiple clocks in one expression must not be collapsed to the first clock. A clock key is a recorded expression, not an absolute timestamp: calendar, day origin, local time, and AM/PM interpretation require separate investigation.

A corrigendum can exchange a clock expression with an angular separation, as
on X p.393. Keep separate variants for each quantity and interpret each with its
own units. The corrected clock remains a time and the corrected separation an
angle; exchanging already normalized scalar values would lose that distinction.
Both originally printed readings remain preserved.

A source review can establish that a reading has **no assigned clock**. In the derived catalog, an explicit null preferred clock with a scan-review basis records that finding and overrides a provisional forward-filled clock. For example, Volume X, printed p. 399 leaves the 26 April 1585 declination untimed; a 9h50 clock elsewhere on that page belongs to a separate 15 April calculation.

The same applies to hour angles: Volume X, printed p. 322 describes a comparison star's distance from the meridian as H.2 15′ and Mars's distance as H.1 M.56. These expressions cannot supply observing clocks. Preserve the provisional extraction for audit, but use the reviewed preferred clock, including null, in subsequent selections. A clock in a dated calculation heading belongs to that calculation's epoch; it does not turn its adopted declination into a raw measurement.

An H.-labeled annotation beside an angular meridian arc can retain uncertain
timing meaning even when its hour and minute units are legible. On X p.386,
preserve “H. 10.7′” separately from the 42°38′ arc. Its association as an
observing clock or hour angle remains unresolved; neither value supplies the
other's interpretation.

## Tables and measurement roles

Keep inked figures, explicitly bracketed editorial supplies, and mechanically
carried components distinct. A supplied whole degree can support an exact
conversion under the edition's stated interpretation while retaining
`source_editorial_component_supply` and its literal brackets. Attach the supply
qualification to the affected quantities; a general table note alone is not a
per-value classification. Keep separately proposed corrections unapplied.

A printed label such as *Sinus* does not by itself establish a reference scale
or numerical encoding. Preserve the native count and label when those remain
unestablished. Do not assign a modern sine scale or logarithmic interpretation
by numerical resemblance. A table that explicitly states a radius of 60 can
instead retain its native whole/sixtieth coefficients as ratios to that radius.

Multipurpose proportional-motion tables require an explicit application for
each numerical interpretation. Origanus's folded table can supply several
different angular unit sequences from the same three fields. The selected
hours-by-arcminutes interpretation gives degrees, minutes and seconds; its
identity travels with each value. Preserve the other source uses, including
any unresolved meaning of a first-place label, without deriving that label's
scale from expected products. Under the author's stated point rule, a terminal
point adds half of the last place: `0 0 2.` becomes 2½ arcseconds in this selected
application. This rule requires an explicit interpretation and is not a general
way to read a period after a historical numeral.

A shared eclipse-digit conversion for the Sun or Moon retains one printed
entry with both stated applications. Bare figure columns require their
reviewed native header units; digits and their sexagesimal subdivisions are
neither angular coordinates nor clock readings. A queried figure keeps its
native unit without an adopted magnitude. Preserve extrapolated table entries
as printed rather than limiting them to the extent of a physically possible
individual eclipse or interpreting them as a photometric fraction.

When a published rendering excerpts a large table in overlapping panels,
record which panels are supplied. Retain structural blanks and unread cells
separately, and link repeated renderings by their printed plate coordinates.
Neither missing interiors nor unread arguments may be filled from the table's
arithmetic pattern.

Distinguish a repeated argument introduced by a modern split-table rendering
from a separately printed occurrence. Riccioli's table 38 is rendered in two
halves with a repeated left argument; that repetition does not create a second
source argument. Preserve the circular and elliptical forms, their conditional
add/subtract instructions and the circular form's difference columns separately.
Those differences are tabular calculation entries, not observational residuals.

Words distributed down a column can replace numerical entries. In Riccioli's
tables 32 and 33, “does not set” and “left empty by design” qualify particular
argument ranges. Preserve their scope and distinguish them from printed zeroes.
A source value outside the stated component convention, such as `68 72` in a
degree/minute column, remains literal without an adopted scalar until its
interpretation is resolved; it is not automatically an edition error.

A carry-down interpretation needs its own source evidence. Riccioli's table 39
explicitly instructs that blank cells take the figure above. Its sparse leading
solar-parallax and apparent-semidiameter components can therefore be resolved
within the stated table scope, retaining their printed origins. This does not
establish how to fill every omitted degree in table 47. Bare minute entries
there retain no adopted full-angle scalar when the degree is unestablished;
complete degree/minute pairs remain usable under their stated interpretation.
Keep A./S. operation annotations distinct from latitude hemispheres. Sparse
shadow-axis settings are separate printed inputs with continuing applicability,
rather than additional quantities manufactured for each blank row.

Keep a correction table's attribution and applicability with its values.
Riccioli's table 40 presents corrected refractions based on Tycho, other
observers and Riccioli himself. Its summer, equinoctial and winter columns are
historical scenarios for the Moon, Sun and fixed stars. They are not Tycho's
unchanged original table, measured weather conditions or corrections applied
to catalog observations.

Catalog population counts describe the source's entries, not independent
observing events. Keep ancient, Tychonic, later-added and unpublished subsets
distinct, including their magnitude classes and inside/outside-figure status.
A stated total followed by class counts is a list of separate native counts,
even when a colon separates bare numerals. A repeated total or a statement that
another catalog has “just as many” does not create another observed star.
Historical magnitude classes retain their source meaning without conversion
to a modern photometric scale. Reported new stars retain source-specific
identities until evidence supports a modern identification.

Population contexts identify their constellation or catalog and link each
qualification to the exported quantity identity. Local extraction keys alone
do not supply a usable public relationship. Additive contextual enrichment
preserves earlier readings and review decisions while supplying those links.

Longomontanus distinguishes two uses of stellar tables in *Astronomia Danica*.
The tables for 1630 in *Spherics* II, ch. IV, pp. 80–85, give ecliptic points
on the meridian or horizon at a star's transit, rising or setting. Their star
names identify the associated event; the tabulated longitude belongs to the
ecliptic point. Preserve the printed reference numbers and names independently
where the two tables disagree.

The canonical catalog in *Theory* I, ch. IV, pp. 202–217, instead gives
adopted stellar longitudes, latitudes and magnitude classes for reference epoch
1600. Its heading explicitly defines latitude B as north and A as south.
Keep that convention local to this catalog and retain each constellation and
entry designation. Store the reference epoch separately from observing dates.
Blank fields remain incomplete; composite sign labels, queried numerals and
noncanonical degrees retain their interpretation limits. Descriptive magnitude
labels such as `neb.` retain their wording without an invented numerical class.

Planetary periods can combine native years, explicitly included leap years,
days and time parts. Preserve a year component separately from the day/time
remainder when its duration is unspecified. Leap years described as included
in a period are not extra years to add. Keep zodiacal periods and periods
described as circuits about the Sun distinct, with their original model and
approximation qualifications.

An unsigned difference column is a source comparison, with its two attributed
versions and complete DMS expression. Preserve the missing sign explicitly;
do not infer one from subtraction or replace a discrepant printed difference.
An “Ours” column that combines observations and calculations retains that
unresolved row-level distinction. See the
[comparison fields](catalog-data-dictionary.md) for the shared representation.

Read the whole comparison-star label before interpreting an ordinal as a
repetition. In Snellius's planetary tables, “Third Star of Aries” names an
endpoint; “second” or “third” on its own can identify a repeated reading.
An endpoint correction must also follow through to explicitly dependent
repetitions. Preserve the original numerical expression and conversion, and
retain the earlier interpretation with the source-bound correction decision.


Braces can share a degree component between distinct instrument readings.
Snellius's *Observationes Hassiacae*, pp. 8–9, places one degree value beside
separate minute values for the larger and smaller quadrants. Bind each reading
to its own minutes and the shared printed degrees, retaining instrument and
date associations. These are separate readings, not editorial alternatives.
Fragments must match complete numerical tokens: `4′` is not the `4′` inside
`24′` or `1/4′`. A solstice label without a day number remains an undated
solstice entry within its stated year.

A report can name its observer and list instruments without assigning a site
or an instrument to every reading. Fabricius's 1599 report supplies his name,
a sextant and a three-foot iron quadrant; later plans for a new sextant do not
establish which instrument was used earlier. A statement that leaves were sent
twice and inserted in two codices concerns source witnesses, not two independent
observing events. Preserve inline dates independently: the December 3 note
alongside a December 2 row has its own elapsed interval and separation.

A continuous comparison table can state its sign, hemisphere and units in the
first entry of each column and omit them below. Review that column's scope
separately for every model and quantity; retain the first marked entry as its
origin and flag inherited marks. This convention does not authorize carrying
labels into another table or choosing signs from expected motion. Observation
recaps remain separate source versions from earlier reductions, even when most
values agree; differences alone establish neither a correction method nor a
transcription error.

“True declination” can label a historical result derived from a meridian
altitude, local equator elevation and a diurnal-motion adjustment. Preserve
that stated method and label separately from raw declinations. An unsigned
result remains unsigned, and an unstated numerical equator elevation or raw
input-row correspondence remains unknown. Calculation dates retain the
printed day even when it differs from a nearby observation heading.

A coordinate described as calculated “from” a star remains a planetary
coordinate, with the star retained as reduction provenance rather than an
angular-separation endpoint. A result labeled *limitata* is an adopted or
constrained result; the word alone does not establish an arithmetic mean.
Preserve the individual reductions, adopted value and stated calculation date.
Explicit sign and hemisphere marks remain distinguishable from inherited
column context and from marks absent in an individual result.

Compact coordinate pairs such as `0. 36` can use a period between degree and
minute components. Resolve the local schema from adjacent explicit units and
parallel coordinates; retain the punctuation rather than treating the pair as
decimal degrees. Numbered stars and geometric point pairs require their own
interpretation and must not inherit an angular unit merely from that punctuation.

Visual equality to a descriptive stellar baseline can be preserved as a
relationship while its angular scale and stellar identifications remain
unresolved. Likewise, retain a comparative fraction's literal value and wording
with its geometric meaning unassigned. An unlabelled schematic can support
that context without supplying named vertices or measurable angles.

A calculated conjunction can report one longitude shared by two planets.
Preserve that single value with both participants in its context, rather than
counting it as two independent observations. Its reported time is a calculation
epoch with its own date qualification; it supplies no observing clock or civil
date conversion when the calendar and day origin are unstated.
A retrospective statement that a conjunction had already passed by a named
hour supplies a timing boundary. Normalize the printed hour label separately
from an exact event time, preserving the witness and the unspecified clock
origin. Carry an explicit calendar label only within its supported source scope.
An explicitly incomplete conjunction does not establish identical participant
positions. Keep a proposed alternative place linked to the quoted value, with
the source's date and observation-versus-table qualifications attached.

A clock at the start of a distance series can anchor that report without
establishing an exact time for every comparison or for separate meridian
altitudes. Preserve a calculated opposition's stated solar reference: an
opposition to the mean Sun is not a measured alignment with the observed Sun.

An explicit statement that comparisons were not taken belongs in the catalog
with its targets, reference star and stated reason. A low stellar altitude in
that explanation remains a stellar quantity; refraction susceptibility supplies
neither a numerical correction nor an omitted planetary distance. Qualitative
meridian timing can link the recorded series without supplying a transit clock.

“Could have had” marks an altitude estimate, distinct from both an approximate
observational report and an explicitly instrumental reading. Preserve those
roles and attach an instrument only where stated. Coordinates embedded in a
comparison-star description belong to that star; a dated observation heading
does not establish their coordinate epoch or an unprinted latitude hemisphere.

An observing-site declaration can govern an entire report while appearing after
its final planetary section. Preserve that explicit scope as supporting
metadata. Keep the observing site distinct from a region of dispatch, and retain
historical longitude values without a modern geographic conversion until their
reference meridian and qualifications are established.

An endpoint description can continue into the next table row. On XIII p.179,
“the lower preceding one” and “in the quadrangle of Ursa Major” jointly name
one reference star; preserve both source rows as evidence. Another endpoint
names a star of the left hind foot without specifying its constellation in that
passage. Retain the description without supplying a modern identification or
borrowing one from similar later wording. A repeated date heading starts its
own source occurrence even when its calendar components match the preceding
series. Unequal repeated readings retain their individual fractions.

A page can mix direct measurements, reductions, means, recalculations, and calibration stars. Identify target and role from headings and local structure before interpreting a number. A heading such as “Mars” does not guarantee that every following row measures Mars.

An appendix's title year need not date every entry. Fabricius's appendix to
1598 includes explicitly dated 1597 observations, followed by 1598 observations
and then a return to 1597. Preserve the local dates and source order. Separate
clock claims for different planets remain separate; a neighbouring fixed-quadrant
stellar calibration can be untimed. A derived stellar declination and its stated
agreement with a table do not supply a second measurement or an unstated hemisphere.

Supporting stellar measurements can be made much later than the planetary
observations they help interpret. On XIII p.145, the September 1598 Sagittarius
measurements investigate Walther's earlier Mars opposition. Their date and
observer attribution must remain distinct from his; Nuremberg names the earlier
observing site. A star's approximate offset from a line through other stars is
not automatically a spherical star–star separation or planetary parallax.
An “or” alternative in the observational text need not be an editorial
correction. Preserve it beside its original, with any inherited component
explicit and neither value adopted automatically.

Repeated reports can describe the same observing sequence. On XIII p.144, the
March 7 note says a 28′ distance was taken twice, while its later summary says
three times. Preserve both claims and the diagram's repeated angle. Do not add
the counts to infer five independent measurements or give an untimed summary
the first note's approximate clock.

An editorial cancellation note can govern one cell rather than a whole row.
On XIII p.143, the note to the 24°41⅙′ Procyon separation reports cancellation
of that distance. Preserve the canceled value and its source role without
extending cancellation to the neighbouring clock, altitude or angular reading.

Known angular units and an unknown measurement type are separate questions.
Retain such a value as an `unclassified_angle` with
`measurement_type_unresolved`, preserving its subject and source column context.
Exact degree-and-minute conversion does not identify an altitude, azimuth or
hour angle. A plausible numerical trend cannot supply the missing type.

An explicit same-amount statement can supply a value through a source relation.
Keep its wording and comparison star, link the first separation and leave its
numeric components empty. Do not print a second numeral into the original field.
An interval after sunset remains an elapsed time; it supplies no civil clock
without a separately established sunset and clock convention. Historical model
differences can be checked arithmetically while preserving their printed values;
a qualified upper or lower bound must not be tested as an exact residual.

Keep a nominal reference angle separate from a qualified shortfall. On XIII p.142,
the Aries star is described as almost 33° high, falling short by at least ⅙°.
Those two numbers do not supply an exact observed altitude of 32⅚°. Likewise,
“taken twice” preserves a repetition count; one printed result does not supply
two separately recoverable readings. Source setup warnings concern observational
quality and do not establish a numerical transcription problem.

A planet used as a color or brightness comparator is not necessarily the
observed target. In XIII p.115, “reddish like Mars” describes the Cetus star;
its magnitude class and the nearby Jupiter/star angles do not measure Mars.
Retain the qualitative comparison, attribute each number to its own subject,
and keep an observer's tentative identification separate from an editor's later
identification. Queue relevant measurements for their own research strand.

An instruction to adopt a row can govern more than its typographically emphasized
cell. On XII p.458, the December 18 “Put” rows pair adopted distances with adopted
declinations; the latter are not additional raw measurements merely because they
lack italics. Preserve both quantities, their source roles and any uncertainty in
the reduction procedure. An adoption row without a clock does not acquire the
preceding observation’s clock, and agreement with one reading does not identify
the selection or weighting rule.

An instrument difference reported among reduced coordinates must retain that
role. On XII pp.459–460, twenty arcseconds separates the limited right ascensions
obtained from the two sextants. It does not establish a universal twenty-second
offset for the raw separations. Preserve each instrument’s result, the subsequent
combined value and the unstated combination weights separately.

Qualitative accounts need separate attribution and measurement roles. The Mars–
Jupiter report on XII p.134 preserves a wholly-covered claim beside a narrator’s
not-fully-covered account. Its handwriting note does not establish the narrator’s
identity. The six-hour reference concerns going to a lecture; retain its printed
hour unit without treating it as a timed limb contact or an angular measurement.

An editor’s suggested comparison star is distinct from the recorded endpoint.
On XIII p.44, the January 12 star name is absent and the note only tentatively
proposes bright Aries. Keep the exact measured angle with an explicitly unknown
reference and retain the proposal separately. A plausible identity or a good fit
cannot supply a missing original name.

Preserve distinct stellar labels before attempting modern identification. “First
of Aries” and “bright star of Aries” have separate meridian calibrations in XII
pp.451–452; their shared constellation does not justify merging the endpoints.

A later reduction need not reuse previously listed stellar parameters. Carry
those constants forward only with source support; otherwise retain the route
with its unstated inputs rather than manufacture an arithmetic disagreement.

Specific findings worth testing elsewhere:

- A second reading can continue in the same cell or an unlabelled following row.
- A declination label can appear inside a horizontal row rather than in a column heading.
- A later reduction can share a clock with an earlier direct reading.
- Two parallel columns can contain separate reductions rather than repeated observations.
- A table can continue across a page boundary, but inherited column meanings need a traceable basis.
- A label can wrap across rows: “The declination” followed by “of Aldebaran” identifies a calibration star. Resolve the complete label before assigning the first reading.
- An altitude block can temporarily occupy a nominal declination column. A subsequent explicit declination label restores the quantity; a transit clock alone does not change the column's meaning.
- An inline label can assign a previously blank value column beside a separate star column. Preserve that assignment for its continuation reading without turning the label's own column into numerical data.
- Pafko's rows 874 and 875 refer to Aldebaran calibration measurements in *Opera Omnia* XIII, printed p. 45. Keep them in workbook validation while excluding them from a Mars measurement selection.

Keep uncertain column roles flagged. A scan review resolving one column on one page does not establish a global rule. Computed reductions belong in transcription validation but must retain their role when selecting astronomical observations.

## Match records without their measured values

Use volume, printed page, date, recorded clock, explicit raw/corrected clock associations, and justified printed order. Do not select the candidate whose angular value happens to agree: that would conceal transcription errors.

Derive control coverage from actual source-identity links. Do not extrapolate a
workbook row range from the number of raw readings: consecutively numbered
controls can skip an entire source date or adjacent printed records.

The current matcher uses monotone sequence alignment within each volume and retains ambiguity across all optimal metadata alignments. A unique best sequence is still an interpretation that needs controls. Review page/date conflicts explicitly, and retain unmatched rows rather than discarding them. A visually verified identity can override automated matching only through a separate, source-bound review decision.

Repeated rows are readings, not necessarily independent observing nights. Before modeling another target, determine whether the independent catalog is exhaustive, selective, reordered, or includes reductions and calibration objects.

Pafko's workbook is a comparison subset, not a complete Mars inventory. A checked omission is the declination **17°20¼′ on 21 January 1585**, in *Opera Omnia* X, printed p. 385 ([Ars Astronomica edition](https://arsastronomica.com/works/tycho-brahe-thesaurus-observationum-tomus-primus/)). The workbook contains no row for that date or printed page. That page also records Mars–star angular separations and altitudes. A complete inventory must count additional declinations and other measurement types independently; the workbook's 923 rows do not establish the total number of Mars records.

A reference star's distance from the meridian can be expressed in hours and minutes. Such an expression is not automatically the observing clock time. Preserve the identity and meaning of every timed quantity before using it for absolute-time normalization.

## Printed pages and scan images

For a source review spanning multiple pages, bind each quantity to its own
printed-page segment and scan page. The opening page's scan locator must not
propagate to later pages. Preserve uncertain printed labels where explicitly
recorded, and leave an unknown later scan locator unset. A corrected locator
changes provenance only; retain the earlier state and verify that identities,
literal readings, numerical interpretations and other qualifications remain
unchanged.

Pagination can change within a book. The *Progymnasmata* star catalog includes
recto-only foliation and unnumbered versos before ordinary pagination resumes.
Use explicit scan-page locators for those faces and retain bibliographic folio
labels separately from numerals actually printed. An uncertain digit or a
misnumbered recto does not justify extending a constant offset across the book.

Printed numbering can also skip labels without losing text. In the
*Progymnasmata*, the edition notes that p.496 is followed by p.499, with the
catchword and the next heading establishing continuity. Retain those printed
labels and their individual scan locators; neither insert two missing pages nor
continue the earlier numerical offset. Supplied repeated table headers likewise
describe the edition's layout and do not create additional observations.
When a flattened header repeats a shared geographic argument, retain one
parameter with its column applications. A genuinely repeated printed row
retains its separate source occurrence.

Table parameters can occur in captions above the column headings. Locate the
full page opening rather than selecting a fixed number of lines before the
header. Bind each parameter to its own leaf, including when an earlier review's
context interval overlaps that opening.

Printed page numbers and PDF page numbers are distinct identifiers. For the source copies checked in this project, the one-based PDF page is the original printed page plus the following offset:

| Opera Omnia volume | Offset | Copy |
| --- | ---: | --- |
| X | 42 | Toronto scan |
| XI | 14 | Toronto scan |
| XII | 14 | Toronto scan |
| XIII | 17 | Hannover scan |

These are copy-specific mappings, not properties of the books. Verify the visible running header after opening an image. A replacement scan can change the offset while an earlier page mapping refers to another copy. Preserve both provenance references instead of silently rewriting them. Public bibliographic links are maintained in [the source registry](../src/data/public_sources.json).

A holding library's page identification can establish a bibliographic locator
when the printed numeral is illegible. Retain the identification's authority
and the numeral's unresolved status separately. For Snellius, the
[BSB canvas labeled “8 (0022)”](https://api.digitale-sammlungen.de/iiif/presentation/v2/bsb10501735/canvas/22)
matches the solar entries from November 1572 through March 1574. This identifies
the leaf; it does not claim an independent reading of its damaged page numeral.

An ending page note can describe text above it. Apply it to the identified PDF page, rather than only to following lines. Keep a provisional page map separate from `preferred_source_page` and its `page_basis`; a reviewed correction must not erase the earlier mapping. For example, several Mars entries on printed p. 458 initially mapped to p. 457.

An explicit, input-bound review may identify a particular unlabelled table cell as a declination. Record that supplementary extraction as `source_bound_review_column`, take its wording and figures only from the final edition, and validate the review's workbook and edition fingerprints before matching. This does not establish a general column rule for other pages.

Preserve incomplete print. Volume XII, printed p. 452 has a second parallel declination written “17…” at 8h18⅙ on 30 October 1595. Keep its identity and partial expression, but leave the normalized magnitude null. Neither a workbook numerical cell, the other column, nor a predicted position can complete it.

## Review and reproducibility

For each case, retain its stable row ID, bibliographic locus, input hashes, candidate identities, original expressions, exact normalized quantities, outcome of each check, and evidence supporting a decision. Append decisions so later reviews supersede earlier ones without erasing them. Corrections belong in a derived catalog; neither original transcription is overwritten.

Retain difficult rows and fixed controls across parser improvements. A regression case should capture the actual failure mechanism, especially accidental value-based matching, inherited targets or signs, clock aliases, continuation rows, and changed scan copies. Recheck an unchanged sample separately from the full run. Hash checks establish input stability; they do not establish transcription accuracy.

Preserve record identities across verified layout revisions. Keep the original edition fingerprint as an identity and evidence locator, and record the current revision fingerprint separately. Compatibility requires unchanged selected passages, line positions, reviewed supporting intervals and page provenance, together with a fresh search for additional candidate passages. Retain the prior evidence. This check covers the catalog's source bindings; it does not certify unrelated book content or authorize changes to recorded numbers.

Public releases require a field whitelist containing reviewed measurements and bibliographic citations. The published books and scans provide the full source context. Dataset readiness must state which checks are complete and which uncertainties affect scientific use.

## Reviewed source assertions and inspected coverage

Keep source assertions, scientific measurements and event groupings separate. One session can state repeated separations, accompanying altitudes, raw clocks, comparison-star hour angles, expected transit times and arithmetic reductions. Counting all those quantities as independent observations inflates the dataset. Preserve their links and roles before making a scientific selection.

An unlabelled numeric continuation requires its column geometry and inherited label, not a plausible magnitude. In X p.385 the value at 6h55 belongs to the altitude column while the separation cell is blank. Preserve the blank. The expected and observed Aldebaran transit clocks are distinct, and the following clock-verification statement has a bounded scope. An instrument named for that transit does not automatically apply to the neighbouring Mars pointings.

Bind reviews to edition and interval fingerprints. Count inspected intervals as a union so overlapping reviews cannot inflate coverage; checking a date heading elsewhere does not certify all intervening lines. Exact rational normalization must retain the complete printed number, including fractional minutes, and must not depend on JSON field order. Arithmetic checks of historical reductions should flag disagreement while leaving the stated historical output intact.

Column identity may depend on native page geometry even when every numeral is transcribed correctly. On XII p.45, reduced table structures drop a continued stellar label and place a standalone number beside a Mars transit clock. Inspect alignment before assigning that number to Mars; record a recovered label as a source-bound interpretation and log lost structure separately from numeric transcription errors. Multiple declinations on one row also need separate source-column identities.

For historical corrections, retain the stated input, output, correction direction and combined physical terms. Check exact arithmetic only when the operation is explicit. A discrepancy is an audit result until its cause is established; do not invent a rounding rule or replace the source output. Keep net refraction/parallax corrections distinct from isolated parallax signals, and preserve editorial correction alternatives without applying or averaging them.

An explicitly stated arithmetic mean can be checked using exact fractions; a
merely “limited” or adopted position does not establish equal weights. On XII
p.451, the stated mean declination agrees with the two readings, while the stated
mean altitude differs from their exact mean by 2½ arcseconds. Preserve both the
stated result and the arithmetic comparison. Keep the subsequent one-minute
declination subtraction and final adopted north declination as separate historical
steps; neither changes the recorded readings.

An abbreviated coordinate can preserve legible trailing components without a full
normalized position. Keep an unprinted leading degree unresolved rather than
treating it as zero. When a latitude correction crosses zero, preserve the source’s
change of hemisphere; unsigned output magnitudes cannot verify that signed result.

Preserve bounds in angles and dates. Normalize an angular threshold as a threshold;
a station predicted before a named day does not occur on that day. Keep an exact
adjustment distinct from a later lower bound even when both name the same amount.

Model-comparison tables can combine author reductions, attributed predictions and later editorial completions. Preserve the calculation epoch shared by each row without creating observation events for the predictions. Distinguish the source's Copernican and Prutenic labels. When only a minute component was supplied by an editor, retain that component attribution alongside the surviving degree component; do not describe the completed number as an intact manuscript value.

An authorial label such as “our calculation” identifies a printed prediction
without necessarily identifying its model or parameter set. Snellius's collection
of Tycho's Bohemian observations places such solar longitudes beside reductions
from measured altitudes. Retain the label and date context, leave the model
unidentified, and keep the prediction distinct from the reduced observation.
Where an edition explicitly notes an absent degree figure, preserve the surviving
minute component as an incomplete angle; neither zero degrees nor a neighbouring
degree value follows automatically. A later quotation of the next day's altitude
is another publication occurrence of that reading, not an independent observation.

Snellius states that the selected solar observations from 1561 through 1582
preserve the instrumental readings without refraction or parallax adjustment.
This statement applies to those recorded readings. It does not make their
derived declinations or solar positions raw readings, and it does not establish
the correction state of later years. Store the source claim with its stated
year range, then link eligible earlier readings by source identity and date in
a separate, reviewable enrichment step.

His later comparison quotes Rothmann's stellar altitudes and Bürgi's pole
estimate, then calculates solar declinations using specified historical
parallaxes. Keep the quoted measurements, calculated values, and assumed
corrections as distinct publication occurrences. A quoted stellar reading does
not establish its original observing date. An author's estimate of instrument
or parallax error describes his judgment, not a measured standard deviation.
Where a numerical result continues across a printed page, bind its ordered
literal fragments to the continuation before assigning a complete value.

For a historical model table, retain each named author's value and the table's
stated scale. Snellius gives solar eccentric-center distances in parts of an
eccentric diameter of 1,000,000; those parts do not supply a physical length.
An apogee table may put the zodiac sign in a separate column. Bind a written
name such as “Gemini” to the same row with explicit source evidence. A later
prose quotation without an explicit sign retains an unstated zodiac origin
unless a separate reviewed relationship establishes it.

Mixed planetary observations retain both bodies. On XII p.153, Venus–Mars distances
are accompanied by Venus altitudes, a Venus declination and a stellar calibration;
the resulting coordinates and model comparisons concern Venus. The source adds
12′ to a distance of 48°23′ and 13½′ to a declination of 23°32½′. These explicit
historical reductions provide comparison cases for refraction, without establishing
modern atmospheric values or a parallax detection. Conditional corrections at
altitudes 1°, 2° and 3° remain rules rather than independent observations.

The same page prints a Venus declination of 2°28¾′; the final edition preserves the
printed number. A later calculation assumes 23°28′. Keep their unresolved relation
visible without silently repairing the original or calling it a translation error.
Likewise, the printed Venus–mean-Sun longitude difference differs by one arcsecond
from subtraction of the explicitly named-sign coordinates. Preserve the stated
result and its precision; an arithmetic difference alone does not establish its cause.

The p.154 reductions separately adjust Venus and Mars declinations for refraction.
Preserve the object, altitude argument and stated correction for each. A one-minute
adjustment to Mars’s right ascension for a change of time is an angular quantity;
the source does not establish whether the adjacent right ascension is before or
after that adjustment. Do not invent the missing result or a clock correction.
An observed altitude can differ from the altitude argument used in the calculation.

On p.155, the source’s “half” rule for refraction corrections is a dimensionless
historical claim. Keep its relationship and uncertain application scope distinct
from the individual angle corrections. The bare refraction terms `7 10` and
`12 15` mean arcminutes and arcseconds, not degrees or clock time. An approximate
ten-minute fast-clock statement applies to the following pointings under its date;
it supplies neither an exact clock rate nor automatically corrected timestamps.

A single reduction table can contain different epochs. On 11 November, the source
uses 4:48 for the separation and 4:40 for the declination. Preserve both input groups;
the final coordinate group has no invented common epoch. Quality words in a
nonnumeric cell remain qualifications with explicit scope, rather than missing
declinations supplied from neighbouring rows. A statement that Venus lay on the
horizon supplies no measured zero altitude.

A correction sum can differ at a finer scale than the printed output: 44°32¾′ plus
9⅓′ gives 44°42′5″, while the source states 44°42′. Retain the exact arithmetic
finding and the minute-resolution source value without assigning a cause. A footer
reporting an earlier written altitude of 2°25′ belongs to the marked 2 October
altitude of about 3°, despite appearing after 10 October observations. Both readings
retain their source roles and their link.

Check angular units and origins before comparing model outputs. Sexagenae contain 60 degrees; zodiac signs contain 30 degrees. XII p.151 explicitly identifies the first star of Aries as an origin before adding precession to obtain a longitude from the equinox. Unit conversion alone does not put those arguments in a common celestial frame. Source precession and calculation arguments retain their historical definitions until an independently specified transformation is available. Keep a conditional parameter adjustment separate from a measured correction or an independently fitted model.

Historical distance units need their own normalization. XII p.46 gives a distance from Earth in “semidiameters” and a corresponding parallax, without explicitly naming the unit's reference body in that line. Preserve the count and source unit, retain the surrounding calculation context, and defer physical calibration and the distance-to-parallax formula. A stated “observed latitude” inside a recap calculation remains a historical input until linked to a raw reading by evidence. Successive computed, true-labeled and adopted latitudes are separate assertions; numerical proximity does not establish an averaging or correction algorithm.

Keep a printed clock correction alongside its unchanged original clock, linked as a correction variant. An expression containing only minutes does not inherit an hour automatically: XII p.139 corrects one clock to 56¾ minutes without restating the hour, while another explicitly gives 2h3m. Preserve the first as a minute component with its hour unresolved. Neither supplies a modern epoch, and the original source event keeps its original clock link. “After midnight” is a daypart label; it does not establish the historical day boundary or move the named date.

A later editorial note can dispute a separation endpoint while leaving its numeral unchanged. Preserve the main endpoint claim and the printed editorial alternative separately. XII p.139's “same one of Ophiuchus” has an editorial alternative of the southern Libra scale-pan; neither is silently substituted for the other. Likewise, “perhaps equatorial” is an unresolved measurement qualification, not permission to treat a distance as a spherical separation or a right-ascension difference.

Footnotes can follow a new planetary heading while referring back to a marked
calculation for the previous planet. Assign them through the source marker and
content rather than the nearest heading. Section-based machine screening can miss
these references; retain an explicit coverage gap until the note is selected and
its quantities imported. Reading a note as context does not itself normalize its
numbers or certify intervening observations.

A reviewed reference link can add the complete note block to the candidate
inventory. Bind its marker and text to an independently selected parent and check
both source fingerprints. Keep the surrounding planet’s section label and require
a separate quantity review; the link supplies relevance, not a measurement type,
date, observing clock or numerical correction.

A calculation's named date may differ from its surrounding observation heading. On XII p.140, a reduction explicitly says 12 May beneath a 13 May observation group. Preserve separate date contexts and calculation epochs; do not reconcile them through an assumed astronomical day boundary. Explicit 13-/14-hour calculation epochs also do not fill missing hours in earlier corrected-clock expressions. A corrected-only transit time has no invented original clock or correction parent.

Triangular calculation tables need an intermediate-quantity role. Preserve each source column's letter labels and angular numbers, including repeated labels and unlabelled entries. A label such as CA or BAC does not by itself establish celestial endpoints, a coordinate type or the author's exact formula. Keep those links and transformations unresolved until the relevant geometry is identified.

Apply source reliability warnings to the quantities they name. On XII p.141, the warning against trusting the 21 May distances from the heart of Scorpio does not automatically invalidate the later Ophiuchus or Vulture distances, the declination, or every reading that night. Retain the warned values and their scope; a qualitative warning does not supply a numerical uncertainty. The estimated ten-degree vapour boundary describes atmospheric conditions, not Mars's altitude.

Diagrams can preserve useful source geometry without supplying measurable angles. Register native labels, vertices, edges and the source's stated purpose; leave angular scale, projection, modern star identities and links to other diagrams unresolved. The XII p.141 triangle labels Mars, the hand of Ophiuchus and the bright Vulture star for a refraction argument. Its drawn proportions are not observational measurements.

Bare clock cells may put both original and corrected expressions before any bracketed rendering. Splitting at the first bracket alone cannot isolate the original. Identify the labeled expressions separately and retain their correction link; never consume the correction's numbers as extra components of the original clock.

A printed correction can appear after a later date heading while referring to an earlier marked reading. XII p.142 corrects the 6 June altitude 6°43½′ to 6°23′ in a footer following the 10 June heading. Keep the original, its attached marker, the source's explicit rejection and the linked alternative. Assign the note through its marked parent, not the nearest date. This is a printed-source correction, not a transcription error in a faithful rendering.

Nonnumeric remarks in a nominal numeric column are not measurements. The 6 June “doubtful because of clouds” entry supplies no declination. If the qualification's exact attachment is unclear, retain the row context and flag its scope as unresolved rather than assigning a numerical error or inventing a missing value. Preserve zodiac signs individually when a sequence crosses from Capricorn to Sagittarius; within-sign angles alone would obscure the continuous longitude.

An instrument check can compare new readings with an earlier observation whose date is not stated. XII p.143 gives two same-evening Vulture–Ophiuchus distances and then an older value. Keep the two checks as separate calibration readings, and the earlier value as a historical reference with unknown observing date and clock. It is not an independent true standard, and its quotation alongside a dated test does not supply its original epoch. Equal numerical values in adjacent source entries likewise do not merge those entries.

Two clocks under one brace do not always have an explicit correction label. XII p.144 gives 9h36 and 9h40 together. Preserve both time claims with unresolved association and leave the event's preferred clock null; a later calculation using one time does not resolve the raw record. Compilation rejects assigning an event clock while its clock association is flagged unresolved. A separately labeled corrected-only time likewise supplies no invented original clock.

Cell labels can change the target inside a nominal column. On XII p.144, comparison-star altitudes occupy columns otherwise used for Mars altitude or declination, and a Vulture-east meridian angle appears in an altitude column. Preserve the explicit local target and quantity. Approximate by-eye Mars/Jupiter altitudes remain estimates; a separation from the Moon's western limb retains that limb endpoint without an automatic center correction.

A source's confidence assessment and a printed editorial qualification are distinct evidence. Keep the June28 statement that repetitions support reliability alongside the visibility difficulty and the note that a proposed refraction addition was not applied. Neither establishes a numerical precision, zero physical refraction or a source-independent accuracy test.

## Before extending to another planet or record type

A comparison's presence does not identify the subject of every nearby coordinate. In XIII's Moon–Mars comparison, paired limb declinations belong to the Moon; a later Mars declination is a reference in a lunar calculation. Preserve both and classify each quantity by its actual subject. Generic table extraction must not propagate Mars through all columns or exclude an entire lunar section.

Preserve the full table, including headers, delimiters, blank cells and unsupported numeric forms, before interpreting its columns. Track labels and inherited pinnule descriptions separately. An explicit cell label can change a quantity from longitude to latitude even when the column header remains unchanged. Short clocks under H.M.S. can omit an inherited hour; keep them unresolved until their layout is established. Do not turn source-row or numeric-cell counts into observation counts.

Do not propagate a planetary target across unrelated date/subject sections. Source-bound coordinate checks found solar, stellar and other-planet records among an older Mars extraction's candidates, including a prose altitude misbound as a declination. Retain the candidates and their corrected classifications so the defect is auditable. In a mixed-target table, another planet's symbol can establish that a particular coordinate belongs to it without excluding the table's Mars quantities. A cell-level classification does not establish whole-span inspection.

Bilingual numeric renderings can disagree within the same cell. Compare their exact quantities before accepting a shared normalization; retain both expressions and check the printed witness. A fraction in the bracketed transcription may correctly preserve unusual historical print while an English rendering silently changes it. Keep that edition discrepancy separate from uncertainty about the intended historical value.

Multiple literal matches can be parallel English/bracketed renderings, true repeated values, or both. Preserve all locations and diagnose their structure before choosing an occurrence. A reviewed computed Mars position remains Mars material but must be distinguished from a direct instrument reading.

Recognized number-free pinnule or quality phrases can be represented separately while normalizing the adjacent magnitude. Match their whole supported form, preserve the original cell, and leave unknown comments or additional numeric quantities unresolved. A source label such as “exactly” does not quantify modern uncertainty; a grouping brace does not establish a repeated series on its own.

Footnote-reference locations and physical note pages are separate evidence. Resolve references within their volume, retain duplicate-key ambiguity and trace note-to-note chains explicitly. A standalone reference may attach structurally to the immediately preceding block; stop at intervening headings or other blocks. Neither that relation nor a page encoded in a note ID verifies a physical page. Editorial/transcription notes may contain numbers that are not historical measurements.

In mixed lunar/Mars material, identify the measured endpoint explicitly: a distance from the Moon's western limb to Mars is not automatically a center-to-center separation. Adjacent declinations can belong to the Moon, and a stated parallax investigation can be lunar. After Mars becomes invisible, subsequent lunar altitude/azimuth readings remain contextual comparison material. Preserve paired-row ordering and literal inf./sup. labels without guessing their physical meaning, filling blank clocks or asserting simultaneous measurements. Instrument scope must be established separately for each quantity.

Keep a reduction table's input coordinates and stated epochs separate from raw instrument readings. A Mars coordinate can serve a lunar calculation without constituting a new Mars observation. Do not infer a lunar limb-to-center correction, interpolation or observing time from a later adopted distance. Zodiac longitudes need their literal sign as well as degrees/minutes: retain the within-sign angle and derive a separate full-zodiac angle with exact arithmetic. The sign offset does not establish an equinox or modern coordinate frame.

A source statement that a number was recorded twice does not supply a second numerical entry. Retain the statement as repetition context. Preserve different instrument series separately and keep adopted values distinct from their preceding readings; do not infer an averaging rule. A comparison star's adjacent declinations are not Mars quantities. Same-side meridian readings yield an ordered angular difference, while opposite-side readings can require a sum; neither is automatically the spherical separation of the two objects. An elapsed interval from noon is not a clock epoch. A successfully checked difference does not validate the instrument readings or supply a statistical uncertainty.

Apparent diameter, clock drift and manuscript timing additions require separate quantity types. Preserve an approximation without inventing a standard error; preserve fast/slow drift over its stated interval without subtracting it from every clock. A corresponding time supplied in a printed witness note can annotate a stellar meridian reading without becoming a certified observing clock. Attached note markers remain in the source expression and are explicitly excluded from numeric components. Printed order can group quantities rather than follow clock order; do not reorder or repair nonchronological values automatically.

Headers can change meaning within a table: in XII p.44, stellar west meridian readings interrupt a nominal Mars-azimuth column. A qualitative altitude/refraction claim does not supply an altitude or a computed refraction correction. Local hemisphere continuation needs a traceable reviewed scope; do not carry a sign across dates or infer it from a modern ephemeris.

A reviewed source-date claim is not an accepted observing epoch. Export only explicitly structured year/month/day and daypart components, without choosing a calendar, moving the day boundary, adding twelve hours or deriving a Julian day. Link claims through reviewed context identities rather than nearby rows or event membership. The same named date can accompany observations, calculations and relative intervals. Preserve multiple date claims and reject conflicting uses of one claim ID. Deduplicating equivalent date facts does not merge their source evidence or imply an independent observing day.

Preserve printed corrections as linked variants. When an erratum changes only fractional minutes, inherit the unchanged degree component through an explicit checked link. Non-reduced fractions need literal treatment: the Corrigenda for X p.385 prints 3²⁄₈′, meaning 3¼′. A canceled observation retains its original numbers and cancellation status. A historical adopted value retains its stated epoch and input series without an invented averaging or interpolation algorithm.

Start with a small set spanning different table structures. Establish target labels, measurement quantities, instruments, units, calendars, clock conventions, and reduction roles from that material. Reuse the exact arithmetic, provenance, review ledger, and value-independent matching methods. Revalidate extraction assumptions and source-copy mappings for the new material before scaling up.

Angular separations retain both named endpoints and their source order, including Venus–Mars pairs. Altitudes retain instrument and refraction context; an unstated site or correction remains unknown. Coordinates quoted in a reduction remain calculation inputs, even when nearby direct readings differ. Capturing these roles does not require reconstructing an unprinted reduction algorithm.

On XII p.145, explicit braces pair clocks across separate rows, including a correction row that also contains a stellar calibration angle. Preserve the linked correction without replacing the original event clock. A multiline endpoint and its numeric distance can belong to the same printed pointing; that source geometry supports an event link without filling a blank clock cell. A standalone corrected expression supplies no original. The marginal dispute about September26 clock correction stays scoped to that date; its fragmentary two-minute statement establishes no signed offset or rate.

Within the historical calculation, bare `6 45` means refraction 6′45″ at the stated altitude 9°, not 6°45′ or a clock. The printed declination sum establishes an exact arithmetic check; it does not independently validate the correction model. A recapitulated “observed declination” inside a calculation is historical input, not another raw reading.

On XII p.146 the explicit confidence brace covers only the last two Sagittarius separations; an untimed transit statement supplies no clock, even after a timed declination. Keep a source-rejected distance with its original number and rejection flag. A printed zodiac glyph in a comparison-star description remains literal even if nearby entries use another constellation: October10 prints the tail of Scorpio. A source star ordinal such as 18 in the right knee of Aquarius is an identifier, not 18 degrees of longitude. A relative preceding-day position comment does not establish an accepted absolute date or exact conjunction epoch.

XII p.147 changes observing provenance to Padua, Magini and Gellius Sascerides. Preserve the new observer/location context before continuing target or clock inheritance. “New Style” is a reviewed Gregorian calendar claim here, with validation unperformed; it establishes no day origin or absolute epoch. Two different clocks striking 2h six minutes apart do not authorize a synthetic 2h6m reading. “Shortly after” supplies relative ordering, not a numeric time. Explicit number words can be normalized only through checked source-word mappings; the current cases are third=3 and six=6. Keep the literal words in protected evidence. A footnote’s marked coordinate parent determines its December10 date despite placement below June20 observations. A numerical equality between a calculated and raw declination does not merge them.

XII p.148 explicitly narrows the July8 observer attribution to Magini alone. Preserve this override instead of carrying both names from the series introduction. A clock described as not yet struck keeps its approximate/before-bell qualification; “now struck” without a numeral and “shortly after” do not supply invented exact clock readings. “And more” qualifies the preceding distance as a lower bound. Calculation dates can point back to June20 after a June21 heading. Preserve the source latitude abbreviation A as unresolved when its expansion has not been established. A three-second angle-closure difference involving a total recorded only to arcminutes is a literal arithmetic finding, not automatically an observational or edition error. Compare source precision before interpreting it. A cross-page paragraph must await joint review before its whole inventory span is marked inspected.

A paragraph can cross a printed-page boundary inside one inventory span. Review the whole span against both witnesses, then bind contiguous source-line segments to their physical pages. Do not assign every quantity a single page citation. On XII pp.148–149, source time arithmetic is separate from raw clocks: sunset 7h40 + 2 hours = 9h40 from noon, then + 12 minutes of meridian difference = 9h52. July8’s missing offset remains absent. Calendar columns describe distinct historical reduction claims; matching dates under two calendars does not prove identical observing epochs. Collective refraction statements need no invented single date. When selecting a separation input, identify both subject and reference: the same line can contain a computed Vulture–Libra separation and a recapitulated Mars–Libra distance. Numerical agreement never selects the identity. Explicit prime-marked single angles must retain arcminute units, rather than being interpreted as degrees.

On XII p.150, adopted and subsequently “verified” places have distinct printed clock references; preserve them instead of choosing a preferred one by coordinate agreement. The opposition calculation’s day 8 and final “completed time” day 7 require an unresolved counting convention, not an automatic typo correction. Two date labels printed for one calculated row remain two source claims attached to one set of quantities. Daily motion is a rate per nominal source day; an elapsed day component is not a calendar-day number. A source claim of model timing error retains its attribution, direction when stated, and inclusive/exclusive lower bound. The source’s 13-minute meridian rule remains distinct from the preceding 12-minute example.

## Meridian checks and instrument alignment

Preserve geographical settings and instrument capabilities as source claims.
A pole elevation is not automatically a modern geodetic latitude; a historical
longitude with an unknown origin cannot be converted to Greenwich. Communication
dates do not date the measurement of site parameters. A stated instrument range
is capability metadata, not a planetary distance or a rule for discarding later
measurements just beyond its approximate limit.

A transit clock, an altitude and an equatorial instrument indication are different quantities even when reported at the same instant. In XII pp.182–183, the Mars transit has two altitudes from different instruments. The equatorial offset recorded at that transit is a calibration reading; it is not automatically a celestial hour angle or a time interval. The explicit 9 December date takes precedence over the nearby 10 December heading. Stellar checks in the continuation lack individual explicit dates and retain that uncertainty.

The same section describes a 7′ alignment error, a 28-second additive clock correction, an at-most-half-minute statement and a further half-minute instruction. Preserve their separate roles and application conditions. The source conversion of 7′ to 28 seconds is arithmetically consistent; the 30-second upper bound is not a conflicting exact measurement. The installation date and eligibility of individual earlier observations require further evidence before applying a correction. The main account and its N.B. also express the cutoff differently: retain both wordings rather than manufacture a shared absolute endpoint.

## Failed clocks and instrument checks

Keep an instrument's stated dimension separate from its resulting error.
“Parallax” can describe an instrumental aberration of sight. A proposed
comparison with and without an attachment supplies no measured correction.
Dates qualifying instrument use do not establish when its dimensions were
measured or supply otherwise unrecorded planetary positions.

When a log explicitly reports that the clock could not be read, nearby stellar angles do not supply replacement observing times. XII p.219 records a broken clock cord on 23 January 1592: its Mars–Cetus separations, north declinations, altitudes and Orion meridian indications retain null clocks. Paired declinations remain separate source values without an inference of simultaneous measurement.

A label such as "with both" can qualify one stated declination; it does not justify duplicating the value as two measurements. Doubt or cancellation attached to a separation applies to that quantity; preserve adjacent coordinates and clocks separately, using the label or note marker to establish scope. Numbered sextant checks retain their separate readings, while a claimed approximate instrument excess remains a calibration quantity. Computed stellar transit times likewise remain expected calibrations, distinct from observed transits.

Weather qualifications can apply across planetary sections. The 17 February 1592 note on XII p.212 explicitly concerns Mars and Saturn despite its position in the Saturn material. Its confidence is conditional on selecting and reducing readings, not a source-independent accuracy estimate. Footnote placement requires the marked parent: the p.219 "In the margin" note belongs to an earlier instrument comment, rather than the adjacent Mars sequence.

## Calculation epochs and collective repetitions

Historical calculations can use several distinct epochs before adopting a limited position. Keep each epoch with its own inputs and results; a later adopted epoch does not replace an observed clock. On XII p.220, north is explicit in a reduction input but absent from the raw declination header. Preserve that difference rather than supplying raw hemispheres from the calculation. A longitude sign printed only in one comparison column does not establish every other column’s sign.

A prose statement that a value was found three times differs from three individually numbered readings. Preserve the collective value and the reported repetition count without inventing individual ordinals or statistical independence. Instrument labels such as old and new require their own historical identification. An approximately one-arcminute excess remains distinct from a separate instrument’s measured value; neither the source’s wording nor numerical agreement alone establishes an exact correction to apply.

Fractions attached to degrees retain degree units: 29¼° is 29 degrees plus one quarter of a degree. Missing clocks, hemisphere labels and exact calculation procedures remain unresolved even when an arithmetic convention would produce a plausible value.

## Relative dates, inherited directions and mixed quantities

A heading such as last day of February can be preserved as a month and a last-day rule without selecting a calendar or inventing a numbered day. A bare calculation epoch such as H.8 retains hour precision without adding printed minute or second components. These source claims remain distinct from accepted observing timestamps.

A repeated table header can conflict with a direction change in the observing sequence. On XII p.221, the explicit switch to west continues into a later table whose reconstructed header repeats east. Preserve the header wording, document the conflict and identify the normalized direction from the printed continuation. Keep these label corrections separate from numerical changes. Printed distance discontinuities that match the scan remain source readings requiring astronomical analysis.

Explicit row labels override a generic column title: an altitude-labeled column can contain a separately labeled azimuth. Likewise, an Alt/Azim column can alternate those quantities on successive rows. A compound row may state altitude in its label and azimuth in its numeric cell; retain two quantities with their own source bindings. Near equality of a planet and star with respect to the horizon does not supply equal altitudes or a numerical zero.

## Interplanetary comparisons and calibration scope

A Mars comparison can appear in another planet’s section. XII p.224 gives four Mercury–Mars separations together with southern Mercury declinations, Mercury altitudes and azimuths. Preserve both separation endpoints and identify whose coordinate is recorded. The neighbouring Orion meridian angles are clock calibrations, not additional interplanetary separations.

An earlier Sun clock check marked A.M. has its own temporal scope. It supplies neither an offset to apply nor a morning label for later readings. A computed stellar transit remains an expected calibration; an adopted separation at a central epoch remains distinct from the original timed observations. Agreement with one raw value does not establish an averaging method or justify changing that observation’s clock.

Small date glyphs require sufficient image resolution before proposing a correction. Source ordering across planetary sections does not establish chronological order. A footnote beneath one planet’s observations can belong to marked material from a preceding planetary section; resolve the marked parent before assigning provenance.

## Stellar reductions and inferred times

An “observed by us” catalog heading can introduce coordinates reduced to a
common epoch. Keep that epoch separate from the underlying observing dates,
and retain the stated observers, borrowed catalogs and calibration methods.
Riccioli's certainty classes describe his assessment of those different
lineages; they do not supply standard deviations. Native visual magnitude
classes likewise remain distinct from calibrated modern photometry.

Preserve printed coordinates alongside unapplied manuscript or editorial
alternatives. In the *Astronomia Reformata* stellar catalog, the edition
assigns Virgo and Scorpio where the printing uses a single sort for both.
Those assignments retain their editorial qualification; ingestion does not
repeat their modern-coordinate checks or treat them as independently read
glyphs. A blank hemisphere remains unknown, while an explicit latitude letter
takes precedence over a general column heading.

Descriptions such as “head” or “following shoulder” retain their constellation
rubric and any antecedent supplied by the printed list. They are native source
labels, not global star identifiers; a shared label alone does not establish
that two entries describe the same star. Preserve joint attributions as one
printed value. In Riccioli's distance table, “for Tycho” denotes an instrumental
basis, while “Tychonically” denotes a distance calculated from Tycho's
coordinates. Keep that distinction, the computed appendices and the separately
attributed radius measurements of Metius and the navigators.

An eclipse ephemeris can change its source meridian and table family between
year ranges. Apply only its explicitly stated canon, preserving unknown or
out-of-range attributions. Keep apparent time, clock origin, calendar and
eclipse phase separate: a heading “from noon” does not identify a contact or
the eclipse midpoint. Predicted durations remain predictions, and a totality
label without a number supplies no assumed digit extent. Retain totality
qualifiers alongside printed digit fractions and subdivisions.

A time that the source derives from an observed altitude remains an
`inferred_time` with role `reduction`. The `comparison_star_altitude` inference
basis identifies a corresponding time obtained from a comparison star;
`observed_altitude` covers an explicitly stated correspondence with another
observed body's altitude. Preserve the body, instrument and association in
source context. Neither supplies an independent observing clock or an absolute
epoch. Keep differing clocks printed for an observing statement and its later
calculation separately, with their source qualifications.

The corrected tables on XII p.305 state an eccentric-center displacement as
9½ of 60. Preserve that relative scale without assigning Earth radii or a
physical Mars–Earth distance. Column-specific years can occur inside angular
cells; separate them from the angle components. Northern maximum latitude is
a parameter, distinct from an observed position. Repeated table values remain
separate assertions, including the later 1587 observed half-minute change.
Residual “less,” “more” and “the same” signs describe observed-minus-computed
comparisons; check their magnitudes separately from latitude hemispheres and
avoid interpreting them as uncertainty estimates.

The appendix on XII p.305 compares historical computed and observed latitudes
for several years. Keep summarized observed coordinates separate from raw
instrument readings and from computed values. Its proportional scruples are
sexagesimal coefficients with sixty proportional minutes equal to unity, not
angles or clock minutes. Preserve blank cells and year-only contexts. The
editor's reported 1583 manuscript year remains a variant of the printed 1593
reference input; it does not duplicate a measurement or automatically apply to
every later date. The stated 12h p.m. convention supplies no accepted civil-date
rollover. Inspect detached notes with their marked parents and count their
source coverage once when subsequent parent sections are reviewed.

The December 30 reduction on XII p.299 explicitly says that parallax is included
in its coordinate pair. Preserve that source qualifier without reconstructing
an unprinted correction or applying another one. Its calculation epochs and
adopted northern declination remain distinct from the raw observing clocks and
unsigned readings. A printed zero model latitude supplies no hemisphere; keep
the zero unsigned rather than supplying a northern label by default.

In the December 19 comparison on XII p.298, the Latin daily-motion phrase
qualifies 34 angular minutes per source day. Do not create an elapsed-time
quantity from the English wording “for 34 M.” Keep the approximate latitude
difference and conditional preference for a meridian-altitude reduction
separate from a definite weighting rule. Final coordinates after a limiting
procedure do not identify a unique uncorrected input: reversing the stated
parallax correction must not create an unprinted intermediate position.
The final 5⅗-hour epoch and model-comparison 5¾-hour epoch remain distinct.

The two December 19 reductions on XII p.298 use different methods and epochs.
Keep the right-ascension routes separate from the spherical triangle using two
stellar ecliptic positions. A repeated calculation epoch preserves another
printed statement without creating another independent observation. Retain a
latitude complement as a calculation angle, and distinguish within-sign
stellar longitudes from whole-zodiac differences. Missing stellar right
ascensions must not be supplied from another night. A declination explicitly
derived from meridian altitude remains a reduction rather than a raw reading.

On XII p.297, the December 13 latitude reduction prints 3¼′, an added parallax
correction of 1′40″, and a final latitude of 5′. Their literal sum is 4′55″.
Preserve the five-second discrepancy as source arithmetic; the print confirms
the edition's figures. Neither an assumed rounding rule nor a replacement
input follows from the difference. An equatorial stellar indication without
an east/west label retains an unspecified direction, even if another night's
similar column supplies one. An unclocked declination pair following a transit
retains its own group unless an explicit association establishes its time.

The December 10 calculation on XII p.297 uses two reference-star routes at
different calculation times and a combined position at a third time. Preserve
each route and epoch. Agreement of the combined number with a simple midpoint
does not establish a weighting or interpolation method. A right-ascension sum
that crosses 360° needs angular wrapping; an unsupported plain sum must not
produce a false disagreement. The stated parallax corrections retain their
coordinate, unsigned magnitude and printed operation. Keep the southern
latitude before correction and northern latitude after it without changing the
source's subtraction wording into an assumed signed-north subtraction.

XII pp.288–289 state that the August 24 clock ran 8½ minutes fast throughout the
sequence. The first corrected pair and the observed transit pair differ by that
amount, while the printed middle pair, 10h49½m to 10h40m, differs by 9½ minutes.
Native numerals and the brace agree with the edition. Preserve the one-minute
consistency discrepancy and the unapplied source rule without changing raw
clocks, correcting a numeral for plausibility or extending the rule to another
date. Instrument labels distinguish the mural, steel and revolving altitudes;
they do not assign instruments or exact times to adjacent declinations.

An unknown denominator such as `2/[?]` is part of a numerical expression, rather
than removable bilingual apparatus. XII p.288 supplies a legible printed `2/8`
where the final edition leaves that denominator unresolved. Keep the proposed
scan reading separate from the incomplete canonical clock; do not substitute
zero or silently complete the expression.

Inline Pone values on the same page are adopted separations, distinct from the
original timed measurements. “Set here” supplies no exact adoption epoch. The
mouth–outer-wing Pegasus calibration has its own reliability note, identified by
a marked footnote as added later in another hand. Bind that attribution through
the marker and physical page, even when the definition follows a later dated
section in the continuous text. It qualifies the note, not the observer or all
Mars readings on the page.

XII pp.287–288 distinguish a source-reported repetition from separately printed
readings: `bis` qualifies one 46°2′ separation without supplying another exact
clock. The August 22 clock correction runs from 0h30½m to 0h20⅔m in the original
print. Preserve its direction and full values without a plausibility repair.

The adopted-input table retains four hour labels, including 12h0m and 1⅙ hours,
without identifying them through a clock-cycle conversion. Its final sentence
prescribes later reduction to meridian-transit times. Keep that instruction
separate from a completed calculation. A stated two-minute calculation
discrepancy remains contextual while its unit, quantity and input attachment are
unresolved; it supplies neither a clock correction nor an angular uncertainty.

The before-midnight sequence on XII pp.286–287 prints clocks progressing from
11h to 0h and 1h. Preserve those values and the named date without inferring a
civil-date change or a midnight clock origin. The unclocked meridian-altitude
table retains no exact association with the adjacent corrected-clock pair.

Five stellar routes are later reduced to a common half-hour epoch before a
separate adopted position is stated at another printed half-hour reference.
Keep all seven epoch assertions and their coordinate results distinct. Repeated
coordinates and adopted values remain historical calculations. The raw “end of
the tail” and calculated “following tail” Capricorn labels retain their wording
without an assumed stellar alias; the Pisces-knot comparison has its own target.

Abbreviated labels can require terminology review independently of their
numerals. XII p.286 renders Mars's *Merid.* qualifier as “Meridian,” while another
Mars passage renders the same abbreviation “southern.” Preserve the unresolved
reading and proposed interpretation separately; do not use a suspected
translation correction to supply a hemisphere. Likewise, distinguish the right
and left shoulders of Aquarius as different historical reference objects.
Inline “plus” and a separate-row “minus” qualify their own latitude-difference
cells; they do not supply missing longitude signs or model hemispheres.

On XII pp.285–286, August 18 has two explicit clock-correction pairs with
different numerical offsets, followed by an observed meridian transit. Preserve
the full corrected values and the transit role. Local headers distinguish the
first Pegasus-wing star from the outermost wing star, with a later east-to-west
change. A repeated column heading cannot override those local labels.

The adopted right ascension chiefly favors both Aquarius and Aries; two named
preferences supply no numerical weights. The model table explicitly labels
both latitudes south and both longitudes Pisces. Its separate plus/minus rows
qualify the differences. Literal magnitude differences depart by 5–7 arcseconds
from the displayed comparison figures; retain them without assuming a rounding
rule. The morning heading and “this evening” diameter note both match print.
Their temporal relation remains unresolved, and the qualitative size comparison
supplies no angular diameter.

On XII pp.284–285, the August 11 clock failure changes the meaning of the
corresponding-time column: its six values are inferred from equatorial distances.
Keep the angular indications and the derived times as separate assertions, with
no selected observing clock. The last Cetus comparison supplies no time. Later
calculation epochs and adopted inputs are separate printed quantities, even when
their numerical values repeat earlier entries.

The sextant calibration crosses the page boundary inside a sentence; its
Aries–Aldebaran distance belongs to p.285. A claim that the instrument has no fault
does not supply a zero-valued correction. The later model table prints Pisces
only for the Copernican longitude and leaves model latitudes unsigned. Preserve
those limits alongside the difference columns. The prose ten-day interval and
latitude changes are source claims, without an accepted start date, absolute
duration, daily rate or inferred hemisphere.

On XII p.284, the July 31 calculation uses separation inputs at 1h37 and 1h57,
then labels both resulting Mars right ascensions at 1h45. Preserve all three
epochs. The author adopts a right ascension closer to the Aries result; this
qualitative preference does not specify a weighted mean. A literal sum of the
stated Pegasus reference right ascension and ascension difference can be checked
without claiming to reconstruct the timing or interpolation procedure.

Body labels can override a repeated table header. On the same page, an explicit
Mars-west label assigns the following 0°30′ indication to Mars, despite a header
referring to the Vulture. Instrument names qualify the two meridian altitudes
separately; adjacent declinations do not inherit those instruments. The original
print confirms fractional minutes of one quarter and one twelfth, which require
exact rational normalization.

## Alternative reductions and near-horizon comparisons

Separate calculation versions can share a numerical epoch without sharing their
inputs or corrections. XII p.225 prints 5h40m in one Mercury reduction and 5⅔ hours
in its repetition. Preserve distinct epoch claims, their original component
precision and each version’s own distance and Mars right ascension. The codex-V
attribution belongs to the marked repetition heading. It does not cover every
calculation or observation on the page.

An assumed Mercury parallax of 3′15″ is subtracted from a refraction of 8′15″ to
give a combined adjustment of 5′. This is a historical calculation input, not a
detected parallax. Its longitude and latitude projections remain distinct from
the first version’s distance and declination corrections. Literal subtraction
differs from the printed final longitude by four arcseconds and latitude by one
arcsecond. Both outputs match the printed witness. Preserve the discrepancies
without an established rounding rule, a silent numerical repair or a claim of
translation error.

Target and hemisphere scope require local evidence. The Mars declination marked
S. is northern in this calculation; a general rule expanding S as south would
reverse it. Mercury’s explicitly southern calculation inputs do not supply
hemispheres for the later raw readings, whose header leaves them unstated. A
qualifier translated “with both” supplies no additional number and, without
further evidence, no identification of the two referents as particular instruments
or pinnules. Preserve an explicitly written zero-second component as stated
precision rather than dropping it.

An approximately 50-degree inclination of the interplanetary line to the horizon
is an approximate geometry input, distinct from the bodies’ angular separation.
Retain diagram labels and qualitative topology without assigning unnamed vertices
to celestial bodies or deriving angles from drawing proportions. A linked
Mercury–Aries sequence can provide context for a Mars comparison even though its
rows do not repeat the Mars name. Its source relationship establishes relevance,
not an automatic correction, a new Mars coordinate or an observing epoch.

A reduction can continue across a page boundary without restating its epoch or
inputs. Link to the existing source quantities rather than copying their numbers
into new records. XII p.226 adds four arcminutes to the Mercury declination from
p.225; its observing status and hemisphere do not change merely because the
addition is arithmetically consistent. Later stated epochs belong to their own
calculation cases. A limited position does not establish an averaging algorithm.

Labels can extend vertically into another table row. The bare 5⅚ beneath
“altitude of Mercury” is an angular argument in degrees; the earlier 5⅚-hour
entry is a calculation epoch. A nearby `alt.` beside a second declination does
not establish an altitude measurement. Preserve that alternative and its
unresolved attribution separately.

Keep a missing separation and an unresolved fractional denominator incomplete,
with no numerical magnitude. An expected subtraction result cannot supply the
missing fraction. Retain the source image evidence and unresolved reading; a
source scan that does not confidently settle the numeral is not grounds for an
edition correction. A footer containing several notes can mix a codex
attribution for a Mercury/Mars calculation with an unrelated stellar identity;
review each marked parent independently.

## Solar observations collected for a planetary purpose

An explicit statement that observations were collected for both the Sun and Mars
establishes relevance without changing their target. XII p.269’s five declinations
and four meridian altitudes belong to the Sun. Its three recorded clocks retain
their original hours and minutes. Do not assign the last clock to the untimed
altitude sequence, infer a calendar or clock origin, or carry a northern
hemisphere or instrument label forward from another date.

Repeated source rows and a “both pinnules” label remain distinct: the former
preserve separately written quantities; the latter qualifies one value. Literal
“one” and “other” labels do not identify their referents without further evidence.
The mural, steel and revolving-instrument labels retain their local scopes. A
clear/calm weather statement supplies no numerical uncertainty. A suspected small
fraction discrepancy remains separate from exact conversion of the edition’s
stated number, with no silent source substitution.

## Local targets, directions and clock cautions

A repeated table header need not identify every subsequent quantity. XII p.277
explicitly labels Mars’s altitude beneath a general Jupiter-altitude heading. In
the next comparison on p.278, Jupiter’s own altitude label continues through the
Mars-distance rows. Preserve the actual target of each altitude. Blank
declination cells do not supply missing Mars coordinates.

The Vulture’s explicit west label likewise overrides an inherited east header.
Keep its equatorial angular indication distinct from an observing clock or a
spherical interplanetary separation. The source’s degree/minute description of
that column supplies unit evidence; a numerical resemblance to a clock does not.

An instruction to verify times is a caution, not a completed calibration. Earlier
corrected clocks from another pointing sequence do not alter later raw clocks.
“After midnight” qualifies the named June 25 date without selecting a day boundary
or shifting it. A June 29 evening sequence retains its written transition from
12-hour to 1-hour readings without an assumed modern thirteen-hour clock. A
distance described as exact retains that source claim alone; it gives neither a
modern uncertainty nor a confidence assessment of every quantity in its row.

## Codex qualifications and separate reduction methods

XII pp.278–279 use a limited Mars right ascension as an input to a Jupiter
calculation. Its note refers forward to the Mars observations without supplying
an additional reading or a value-based matching rule. A second note, “thus in
the codex,” qualifies two Jupiter outputs. Retain those values even when a
literal arithmetic check differs. A subtraction mismatch does not establish a
transcription error when the edition and printed witness agree.

The Mars-based calculation’s stated 1h0m epoch does not automatically apply to a
separately reported result from the Vulture transit or to the alternative
stellar-distance method. Keep these as distinct source groups with unresolved
epochs where needed. Different zodiac signs retain separate within-sign and
full-zodiac values; subtracting the within-sign numbers alone is not a valid
longitude audit. An unestablished historical algorithm remains uncomputed.

Footnote metadata can occur between the numeric components and a zodiac glyph.
Exclude the identified note number from numerical interpretation while retaining
both the exact source expression and its sign. A superscript within a number
cannot be removed merely by labeling it a note.

## Refraction tables with several dates and epochs

A stated altitude up to which refraction remains perceptible is an altitude
threshold, not the angular amount of refraction. Preserve a relative threshold
such as “half of that” separately from the preceding angle; its evaluated value
belongs to an explicit derivation. These source claims do not establish modern
atmospheric conditions or an applied correction.

A shared comparison star can justify including a calibration table as research
support without establishing its historical application to Mars. Record that
relationship separately from a printed cross-reference. The Spica table on XI
p.84 distinguishes altitude arguments, two equatorial refraction components
and adopted stellar inputs. Its altitude argument does not establish a measured
stellar altitude, an observing epoch or a universal vertical-refraction law.

XII p.279 tabulates five historical calculation cases under a collective
completed-twelfth-hour statement. Preserve that collective claim separately from
the row epochs. June 25 and June 29 after-midnight labels retain their named dates;
the July separator changes the month of the last row. These are source claims,
not accepted observing timestamps or newly recorded observations.

Keep altitude arguments, altitude refraction and its longitude/latitude
projections distinct. A bare 0⅓ in the longitude-correction column is one-third
arcminute; 0 50″ has an explicit zero-minute component and fifty arcseconds.
Coordinate columns labeled Refracta and Vera retain `refracted` and `true` source
states without an invented zodiac sign, hemisphere, weather model or modern
accuracy claim. Untagged older coordinates require their own correction-history
review.

Eight literal coordinate relations agree exactly in this table. The June 29
11½-hour latitude sum differs from the printed result by one arcsecond, and the
July 2 longitude subtraction differs by two. The print confirms both outputs.
Preserve the differences without an inferred rounding procedure or an edition
correction. The footnotes beneath the table belong to earlier marked results;
their physical placement does not qualify these rows.

## Meridian readings and qualitative diagrams

Repetition words describe how often a printed distance was taken; they do not
supply separately recorded values. Preserve the count with that distance.
An editor's proposed replacement remains a variant linked to the original
reading and its clock. Neither agreement with neighboring values nor an explicit
“should be” note authorizes silently replacing the recorded number. Match
footnotes by their markers and subjects, even when a page gathers notes from
different planetary sections.
Stellar plumb-line alignments and equator-on-meridian angles supply calibration
context, not Mars coordinates or numerical zero separations. Keep a later
calibration clock separate from an earlier untimed planetary distance unless
the source establishes their association. Record an instrument only within
its supported scope.

A report that a planned target did not appear is a qualitative record, not a
zero-valued measurement. Preserve its date and stated daypart without borrowing
nearby observations' clocks or explanations. On XIII p.95, the cloud difficulty
is explicitly Venus's; the separate Mars non-appearance statement gives no cause.

On XII p.298, December 29's two instrument altitudes differ by 10′10″, and
its last Aldebaran separation has a different degree component from the
preceding readings. The native print confirms the figures. Preserve them
without a numerical emendation or an invented doubt label. The first three
clocks state only hours and minutes. On p.299, December 30's brace links two
clock values to one transit; it supplies no general correction rule. The
adjacent declination pair and stellar indication remain untimed where their
own clock association is unstated.

On XII pp.297–298 the December 19 transit has instrument altitudes but no stated
clock. Preserve a separate untimed group rather than borrowing the preceding
declination clock. Three native braces identify distinct clock-correction
pairs; their different nominal offsets supply no constant clock rule. One
corrected value stops at minutes. The first declination prints 4°41⅚′, despite
later values near 4°4′. The scan confirms the number: numerical surprise alone
does not authorize changing it or adding a source doubt label.

An internal numerical superscript can be a footnote marker between bare degree
and minute columns. On XII p.296 the marked Pegasus indication prints 43 degrees
and 42 minutes; its note reports only the codex's degree component 35. Preserve
the complete printed angle and the separately linked component. The note does
not supply a complete original angle. Marker removal for numerical validation
requires the reviewed position and schema; retain the immutable expression and
do not strip numerical superscripts generally. A doubtful declination and a
pair of separations limited by the sextant's large angle retain their distinct
source qualifications, even when the evening is described as clear.

Explicit unit marks can flank an internal note marker too. On XI p.66,
`33°¹ 14′` preserves the complete printed altitude of 33°14′. The note reports
a manuscript degree component changed from 13 to 33 and suggests 30° instead.
Keep these as separately attributed degree components; the suggestion remains
unapplied and none of the notes supplies a complete alternative altitude.
The same page's longitude `39°42⅔′ ♍` exceeds the span of one sign. Preserve
that expression with its interpretation unresolved rather than choosing a
replacement degree or a modern longitude.

On XI pp.184–186, distinguish the dated input `5ᴰ 0ᴴ 15ᴹ` from an elapsed
duration: its day and clock are separate source claims. The neighbouring bare
`10 11⅔` has no assigned component units. The refraction expressions `1½`,
`1 40` and `1 30` likewise lack units in the source; their angular purpose does
not establish the component places. Preserve their distance/declination labels
and leave numerical conversion unassigned. Inline parallel labels can also
precede the actual digits within a value cell; inspect the whole cell rather
than treating a label-only text prefix as an empty reading.

Explicit clock pairs can have different corrections within one evening. XII
p.296 gives four December 8 pairs whose nominal differences are 7m30s, 9m15s,
9m and 11m50s. Preserve each relationship without inferring a constant shift.
The final corrected expression is stated only to minutes; the last difference
is arithmetic on that expression, without an inferred seconds reading or error
bar. A component label printed beside a corrected clock can still qualify the
preceding declination, and a “twice” note on one separation supplies no second
numeric reading or independent observing epoch.

A declination printed beside a corrected clock does not thereby become a
corrected declination. Preserve its source row and pair position while applying
the correction label only to the clock it explicitly qualifies.
When a correction label occupies the row-label column, bind it to the populated
quantity column. Preserve an explicitly corrected declination beside its linked
original, and count that variant separately from an additional raw observation.

A clock reset supplies an index setting, not an offset unless the source also
identifies the simultaneous original reading. Retain instrument repairs as
dated maintenance context; a repair statement alone supplies no numerical
adjustment to earlier observations.

Footnotes can report only one component of a printed clock. XII p.296 places a
marker after the minute component of 7h40m40s; the note reports 60 in the codex.
Retain the edited complete reading and the literal minute variant separately,
linked by the marker, without reconstructing 7h60m40s or carrying it into a new
hour. An internal marker after an explicit unit requires a reviewed unit anchor;
an unmarked superscript inside a number remains numerical evidence. A local
beam-obstruction warning qualifies its declination alone. Conditional source
approval that calls for a declination correction supplies no unstated corrected
value or numerical uncertainty.

A meridian-altitude label does not by itself record a transit time. On XII p.295,
December 1's 7h1m30s clock belongs to a declination; the following two instrument
altitudes and stellar indication retain an untimed group. The same section's
annual-orb “parallax” wording supplies no diurnal-parallax angle. Its five-object
diagram has labeled asterisk marks without drawn connecting lines. Preserve
the source's near-collinearity, square and cross descriptions as qualitative
claims, leaving numerical positions, angular scale and projection unresolved.
The diagram's Pisces label and the interrupted paragraph's northern-cord wording
remain available without forcing a modern star identification.

## Adopted inputs without observing epochs

A detached manuscript note can explain revisions already present in a source
table. On XII p.295, the codex-E note belongs to the marked November 26 ending,
across the intervening November 27 and December 1 material. Preserve the six
revised separations separately from two reported earlier examples and two
instructed replacements. The note's “etc.” does not supply the other original
figures, exact observing clocks for the examples, or an arithmetic procedure.
An ordered pair of named reference objects identifies the example pairs without
selecting a table row by numerical agreement. Retain the manuscript annotation
and the editor's parenthetical report as distinct attribution layers.

An instrument's source qualifier and its unresolved settings are separate facts.
The largest armillae in XII p.294 have “with one” and “with the other” declination
readings; retain both without naming unmentioned pinnules, supplying hemispheres
or inferring numerical precision. Confidence in a transit clock does not extend
automatically to the adjacent instrument readings. A later series can also have
a different Moon-quality statement from an earlier one: the November 25 Aries
distances continue on p.295 with little hindrance attributed to the Moon, while
the preceding Pisces series retains both a local brightness warning and a
separate dispute about the comparison star's identity.

Side annotations can cross the edition's column boundaries. In the October 30
sequence on XII p.294, “altitude of Mars, by the steel instrument” labels 26°41′,
while the neighbouring 7°24⅓′ and 7°24½′ remain declinations with no instrument
established by that annotation. The explicit brace pairs the transit's original
and corrected clocks; it does not supply a general correction rule for the night.
A plural Moon-nearness warning beside the later Aries distances has a shared
series context with unresolved exact extent. Preserve that uncertainty rather
than assigning the warning only to its serialized table cell or rejecting the
whole observing sequence.

Keep source confidence local to its printed target. XII p.294 places *bona*
after one Mars–Aries separation, while the evening's weather description remains
unfavourable. Neither statement supplies a numerical uncertainty or replaces
the other. The subsequent calculation's claim of agreement with both reference
directions supplies one combined right ascension, without individual route
outputs or numerical weights. Its codex-K footnote identifies the calculation's
manuscript source; a neighbouring note disputes a later comparison star's
identity. These notes do not identify the observer or qualify every nearby row.

Detached date notes can qualify an earlier heading across intervening records.
On XII p.293, the October 3 heading's marker points to a note reporting October 1
in the manuscript. Retain both date witnesses on the same readings. The note does
not qualify October 12 merely because it appears after that section. The native
page's column continuation also establishes the Vulture endpoint before the
explicit return to Aries; a repeated edition header cannot override that flow.

Instrument readings printed after a transit need not share its exact clock.
Unclocked armillae declinations retain a separate group. A statement that the
clock was corrected shortly before supplies no numerical offset. Likewise, a
stated approximate angle from the annual orb's perigee remains historical
geometry with that reference; it does not become a modern orbital anomaly or a
raw separation against a star.

An adopted separation need not have an observing clock. XII p.292 gives two
September 26 inputs without a stated epoch; the last clock in the preceding
table cannot supply one. On p.293, September 28's approximate 10-hour epoch
belongs to the adopted inputs, separately from the clocked readings. An explicit
southern adopted declination does not establish the hemisphere of unsigned raw
declinations. A doubtful separation qualifies that value alone. Preserve the
source's tentative interpretation of direct motion separately from the
Alphonsine prediction of a station on the named day.

## Sexagenae and historical opposition arguments

XII p.305 explicitly writes the simple longitude of Mars in sexagenae, each
equal to 60°. Its four-component longitude therefore uses sexagenae, degrees,
minutes and seconds; the leading component is neither a zodiac sign nor a clock
hour. Preserve the separate source roles of longitude, apogee, eccentric anomaly,
prosthaphaeresis and corrections. These source arguments do not establish a
modern coordinate frame or implement a historical planetary model.

The printed addition of 1′30″ to 310°52′28″ produces a stated result of
310°54′00″, two seconds above the exact sum. Preserve that result and report the
arithmetic discrepancy without supplying a rounding rule or changing the edition.
The same passage's instruction to add a fourteenth part of Copernicus's
prosthaphaeresis is an exact fraction, 1/14, distinct from the separately stated
Copernican value of 3°17′. Its unlabeled bottom result retains the native angular
column alignment, while its quantity name and numerical procedure remain unstated.

## Parallel latitude calculations and unresolved fractions

XII p.306 places two calculation cases side by side: August 10 completed, at
the following midnight, and August 24 at 2¼ hours after noon. Preserve the first
as a source date and midnight label without supplying 12h or 0h; the second has
an explicit fractional-hour epoch. The subsequent paired test retains these
case associations through the native column layout, rather than acquiring a
new observing date or independent reading.

Keep each eccentric argument, commutation argument, angular addition,
latitude argument, proportional coefficient, input latitude and response
latitude distinct. Neither an unsigned input latitude nor the phrase “response
latitude” establishes a hemisphere or an observed coordinate. The explanatory
editorial note identifies the 6°45′ addition as the longitude difference between
the apogee and the place of greatest latitude; it is a separately printed value
linked to its marked parent.

The source calls for reconciliation of its results, saying that one should be
greater by ⅙ and the other smaller by 1/12. Retain those exact fractions and
comparison directions with their named dates. Their reference whole and unit
are unstated: do not turn them into angular minutes, multiply a latitude by
them, or publish corrected latitudes. A literal fraction can be exact while its
physical interpretation remains unresolved.

## Angular counts, abbreviations and arithmetic precision

XII p.306 explicitly writes a commutation of six signs, or 180°. Keep this
30° sign count distinct from the 60° sexagenae used elsewhere on the page.
The explicit count supplies the unit for the repeated true-commutation row;
it does not establish the units of earlier unlabeled arguments by analogy.
The trial's `6 18 0` and `6 25 45`, and a later abbreviated `41 50`, retain
their literal components with no converted magnitude until the unit or omitted
prefix is established. A separate named Pisces longitude does not authorize
filling that abbreviation.

Source durations of one day and eleven hours remain separate from their
angular increments. Their nominal conversion to seconds of time neither
creates observing clocks nor establishes an angular rate. The explicit
fourteen-hour after-noon calculation epoch retains its source date without an
accepted civil-day rollover.

Exact arithmetic checks can disagree with a source result printed to fewer
components. Preserve the twenty-second difference in the anomaly subtraction,
the seventeen-second difference in the apogee trial's stated latitude
difference, and the ten-second difference in the final trial. None alone
establishes a rounding rule, a transcription error or an observational error.

## Alternative latitude tables and shared parallax instructions

XII p.307 compares tables using eccentricities stated as 12 and 9½. Preserve
those bare parameters without silently supplying a reference whole or identifying
them with modern elliptical eccentricity. The unlabelled argument numbers in the
proposed end-of-table rows likewise retain their numbers without assumed degrees.
By contrast, the 70 35 and 60 46 rows occupy the angular lookup columns that
continue the explicit degree arguments; they are distinct from the following
proportional-minute coefficients. Do not infer an unprinted complement formula.

The native braces place 17 over the first pair of experimental columns and 26
over the second. Preserve each 12/9½ parameter, correction, sum, coefficient,
latitude input and response in its own column. Subsequent alternate inputs and
responses remain separate scenarios. Explicit southern-latitude context applies
to these proposed tables; it does not supply hemispheres retroactively to the
earlier unsigned trials. Fragmented instructions retain their uncertainty rather
than supplying a complete correction formula.

The closing paragraph gives model latitudes for the 24th and the 10th and calls
for approximately 4′ of parallax to be subtracted from observed latitude in both
cases. Represent this as one historical correction instruction linked to both
dates. It neither supplies new raw observations nor establishes a parallax
detection. Keep the instruction unapplied when the original readings, epochs or
previous corrections have not been established.

## Relative scales, cyclic counts and differing summaries

XII p.308 explicitly compares 12 of 60 and 9½ of 60. Preserve these relative
scales separately from earlier bare parameter values. The common northern
maximum and scale definitions are undated; they do not acquire one of the years
of the subsequent historical cases. The opening southern test instead has a
native footnote specifying the opposition of 1591.

The 1585 addition passes from count 11 to count 0 after adding 6°45′. The source
carry supports 30° sign counts and an explicitly reviewed circular sum; it does
not justify changing other operations or clock conventions. Preserve the
uncarried degree component 30 in the 1582 expression. The 1580 final value omits
seconds and differs from the literal addition by 16″; retain both the source
result and the check without assuming rounding.

For 1587, retain the heading's 3°37⅙′ separately from the later observed summary
of 3°37½′, qualified as perhaps more. The instruction to add parallax supplies
no amount and remains pending. The heading's “in 25” does not establish a month
or observing day. The 1589 opposition retains its tentative zodiac identification
without an accepted absolute longitude. These qualifications do not create new
raw observations or silently correct the edition.

## Repeated calculations and reported revisions of a summary table

XII p.309 repeats the northern calculations and then collates observed and
calculated latitude summaries. Keep every printed instance and its role. A
statement that a calculated value agrees with observation supplies no missing
observed number. An unlabelled numerical cell need not receive an angular unit.

The earlier 1580 observed summary is qualified as doubtful, obtained only with
the Radius, and perhaps insufficiently adjusted for parallax. Preserve those
qualifications on that entry; they supply neither a numerical correction nor
an uncertainty estimate. The later collation's changed value retains its own
source wording and marked note.

The editorial notes report original minute components “40 doubtful” and “6,”
and earlier residual forms “3 plus” and “3½ minus.” Store the components and
residuals separately, linked to their marked cells. Footnote markers are
apparatus, not seconds in a coordinate. These reports document earlier forms
of a summary table; they do not establish changes to the raw instrument logs,
identify the reviser or establish intent.

The collation's signs describe calculated minus observed latitude magnitudes,
including in the southern table. Preserve its sign-only “plus” without a
fabricated magnitude, and preserve printed zero differences despite literal
subminute residuals. Such discrepancies do not establish a general rounding rule.

## Common assumptions and editorial qualifications

XII p.310 identifies the northern maximum of 4°34′ as derived from the
observation of year 85 with parallax already applied. Keep it as an adopted
parameter with that correction state. Do not recover an unprinted original
latitude or correction amount from the statement.

The assumed northern node is 17° Taurus at the end of October 1585. The editor
comments on oppositions at the end of January 1585 and October 1595. Preserve
these as separate source and editorial temporal claims; do not silently relabel
the node parameter or turn “end of month” into a calendar day. The printed
before-apogee distance includes a bracketed editorial leading count of three
signs, whose attribution remains visible alongside the full printed value.

The text describes addition of northern node-distance corrections, subtraction
for southern cases, proportional lookup and logistical multiplication by the
maximum latitude. The editor's inability to find the table marked ▽ remains a
limit on reconstruction. The reported manuscript wording “greater,” against
the printed “smaller,” is an editorial textual variant rather than an automatic
translation error. The reference to two observed latitudes is a source count
claim and does not establish statistical independence or a new dataset total.

## Published parallax assumptions and inherited distance units

XII p.280 places its Jupiter parallax calculation before a reduction using Mars.
Preserve the adopted mean distance of 3,990 Earth semidiameters, the annual-orb
subtraction of 575 and the resulting 3,415 as three source quantities. The first
row explicitly names the Earth unit; the other two inherit it through the shared
subtraction table. That unit inheritance is not a kilometer calibration or a
validation of the historical distance scale. The annual-orb label alone does not
choose a physical cosmology.

Distinguish the horizontal parallax of 1′ from the 59″ stated at altitude 11° and
the separately permitted adoption of one minute. Preserve the latter’s
approximation without assuming a general rounding rule. The published
one-third ratio concerns the Sun’s mean parallax; it supplies no additional
numerical solar-parallax reading. Match a checked fraction phrase such as
“third part” without changing an ordinal “third” into a fraction elsewhere.
Distance subtraction can be checked exactly while the source’s distance-to-angle
and altitude procedures remain uncomputed. These are theoretical inputs and
reductions, not a recovered observational parallax detection.

## Common reduction epochs and successive coordinate corrections

Keep the date of an observation distinct from the date to which it is reduced.
XII p.280 reduces Jupiter observations labeled June 25, June 29 and July 2 to a
common June 29 epoch. Preserve the separate printed epoch expressions and their
links. The source explicitly calls 12h midnight; this establishes a source label,
without choosing a modern day boundary or converting it to civil 00h.

A coordinate obtained “from Mars” is a reduction using Mars as a reference, not
an additional raw Mars separation. Retain the named comparison objects and method
separately from the coordinate's subject. A sign printed in the first longitude
row does not establish the signs of unmarked later rows.

Unit alignment can change within a single column. In this reduction the bare
`0 23` adjustment occupies minute/second positions and means 23″, whereas the
bare `0 1` parallax occupies degree/minute positions and means 1′. Preserve the
third-part weighting rule separately from its stated numerical adjustment.
The literal sum 17′40″ + 23″ is 18′03″; the source's approximately 18′ remains
unchanged, without an invented rounding rule. Its “free from refraction” label
precedes a parallax subtraction and the final 17′ south latitude. Earlier
unsigned latitude entries do not acquire that final hemisphere. Historical
corrections are represented as source calculations, not applied again to raw data.

## Separate indications in mixed-target tables

A table centered on Jupiter can include a separate Mars reading. On XII p.281,
the September 28 table puts Mars's east indication in a right-hand angular column,
while the main distance column measures Jupiter against stars. A later entry in
that side column names the Vulture. Preserve each actual subject and the printed
row association, keeping angular degree/minute indications separate from the
H/M/S clocks. Their precise reference-point convention remains unstated.

Comparison-star labels need the same care: “end of the tail of Capricorn” does
not supply a brightness adjective or a modern star identity. Repeated declination
rows retain separate values and missing clocks without establishing simultaneity
or independent measurements. A doubtful or cloud-affected separation stays in the
catalog with its qualification; prose occupying a declination column does not
supply a numerical declination. The lesser-quadrant label and the low-altitude
refraction warning in this table qualify Jupiter's quantities, rather than every
object appearing alongside them. No correction magnitude or application follows
from the warning alone.

## Opposition calculations and joint motion terms

Follow explicit carry-forward wording when a later calculation reuses a reduced
position. XII p.280 repeats the preceding adopted Jupiter longitude before
computing an opposition and comparing Copernican and Alphonsine predictions.
Keep each printed input and epoch with links to the earlier quantities. These
are historical calculations involving a Mars-based reduction route, rather than
new raw readings or predictions from an implemented orbital model.

The source's joint daily-motion term is 1°7′8″. Preserve it as an unallocated
planet–Sun rate per source day, separately from the elapsed 8h33m and the Sun's
21′4″ and Jupiter's 2′50″ interval motions. Their literal sum is 23′54″, while
the source lists a 23′55″ gap. Retain the discrepancy without repairing a value
or assigning a rounding rule. The inputs have opposite Cancer/Capricorn signs;
ordinary longitude subtraction does not yield this opposition-adjusted gap.
The rate-to-time procedure remains uncomputed. The source's approximate 3½h
result and the separately printed model-row epoch do not supply observing clocks,
accepted absolute times or a modern day origin.

## Observing instructions and source qualifications

The June 13 entry on XII p.282 prescribes choosing comparison stars to form a
nearly equal-sided triangle. It reports no triangle measurement. On June 14 the
first separation continues a clock-and-endpoint label across two rows; that
specific continuation does not authorize filling every blank clock. “With both”
qualifies one declination, with its referent unresolved. The marked codex K note
belongs to the June 14 calculation, rather than every nearby italic passage.

The June 25 equatorial indication is an angular instrument reading; it does not
supply a zero declination or establish that Mars crossed the celestial equator.
On June 29, retain the literal 12h56m30 clock and following 1h08m10 without a civil
time conversion. Paired declination rows remain separate, unsigned readings.
The revolving-quadrant and lesser-quadrant labels at 2h06m qualify their respective
altitudes; neither label identifies the instrument for an adjacent declination.

Keep the subsequent “set” inputs at about 1½h distinct from those observations.
The adopted south declination does not determine the raw readings' hemispheres,
and the instruction to apply refraction after the operations is not an applied
correction or a numerical refraction value. The source's dawn and confidence
statements remain qualitative evidence.

Repeated calendar components do not identify an observing session. Preserve the
separate source headings and their qualifications when one occurrence says
evening and another says after midnight. Shared year or date labels cannot merge
those claims or establish a common absolute epoch.

## Alternative stellar routes and paired clock corrections

The second June 29 calculation on XII p.282 separately states apparent distances
at 1½h after midnight. Its 50°21′ Aries distance differs from the preceding
50°20⅓′ input; preserve both cases. The Aries right-ascension route crosses
zero degrees, so ordinary negative subtraction is not a source contradiction.
The Vulture route has a direct angular sum. Keep the two results and the limited
right ascension separate, without inferring an adoption algorithm from their
numerical agreement with a mean. Reference-star north labels do not establish
the hemisphere of an unmarked Mars observation.

On XII p.283 the July 2 brackets pair nine recorded times with explicitly
corrected values. Preserve each original, its corrected variant and the printed
grouping. Do not turn a corrected value into an offset, a second observing
occasion or a correction to a neighbouring declination. Source 12-hour notation,
fractional minutes and explicit seconds remain intact until their conventions
are established. The source's evening qualification does not settle a civil
timestamp. Clear air and interfering moonlight remain qualitative conditions.
The instruction to examine an armilla using a rising star is a proposed check;
it supplies no recorded star declination or calibration value.

## Instruments and multiple calculation epochs

XII p.283 names a steel instrument and a revolving quadrant for the July 22
meridian altitudes. Preserve both labels and values, with their local scope.
Neither instrument label identifies the source of the neighbouring two-value
declination entry. The later 3h18m30 and 3h36 clocks have no stated corrections;
nearby corrected times do not supply them.

The calculation uses one stellar route at 1h23m, another at 2h25m and a limited
result at 2h. Retain all three epochs. The southern label on the Aquarius star
does not establish the Mars input's hemisphere, and an Aries declination without
a hemisphere does not inherit north from another date. The following Copernican
and Alphonsine values are attributed historical predictions, distinct from the
author's reduction and from raw observations.

A bilingual table cell can place its numerical value after a bracketed label,
as in the Copernican latitude here. Read the whole cell before separating its
label, number and qualifier; cutting at the first bracket would lose the value.

## Cross-page calculations and model-date claims

The July 25 calculation continues from XII p.283 to p.284. Give each quantity its
physical page citation, retaining the boundary within the source interval.
“With one” qualifies each of two printed declinations without identifying a
pinnule. The later brace around 1h24m and 1h29m ends with an unnumbered correction
mark; retain both clocks and the unresolved correction scope. The first explicit
clock pair remains a separate, supported relationship.

The author's no-refraction assertion concerns the earlier high-altitude
observations. It is neither a measured zero nor an adjustment applied to the
later cloud-affected Aries reading. Keep the subsequent 1h29m, 1h50m and 1h40m
calculation epochs separate, with no unstated stellar inputs borrowed from
another date.

A retrospective calculation can follow observations for a different day. On XII
p.289, August 29 observations precede a calculation explicitly dated August 22.
Keep the latter's four route epochs, common reduction epoch and separately stated
after-midnight adoption distinct. A relative time from midnight does not select
a civil-date conversion. Restated inputs can differ in time or magnitude from an
earlier adopted table; retain both without replacing the raw readings or choosing
an input by numerical agreement.

A reference label split across two printed rows can still name one result. The
two-line Cetus label on XII p.290 supplies one right ascension. A declination
described as derived from meridian altitude does not inherit the neighboring
route's time or a hemisphere stated only in the later adopted position.
In a separate ecliptic method, keep each star's longitude, named zodiac sign and
latitude together. Preserve both the angle within its sign and its separately
derived longitude from the zodiac origin.

A claim that longitude parallax vanishes at a chosen epoch does not establish
that every parallax component vanishes. On XII p.290, an instruction to add 15″
for parallax accompanies a right-ascension collection. Preserve its angular unit,
additive operation and calculation context. The unstated combined value before
correction remains absent; an unspecified adoption cannot become an arithmetic
sum with invented inputs. The instruction does not alter the recorded readings.
Likewise, a preference for one method's longitude and a suggested slight latitude
increase do not supply a new final latitude, weights or an uncertainty estimate.

An assumed parallax can produce an exact arithmetic subtraction without validating
the assumption. XII p.291 subtracts an assumed 3′ from 6°6′ apparent latitude to
obtain 6°3′ true latitude. Keep those source labels, the local hemisphere
continuation and the assumed input distinct. “Apparent” alone does not identify
a refraction correction. The associated afternoon opposition time is calculated.

For an opposition calculation, a small difference between angles within opposite
zodiac signs is a displacement from opposition. It is not the direct separation
of their longitudes from a shared zodiac origin. Record that geometric basis
before treating a literal subtraction as an arithmetic check.

Collected positions labeled “from observations” can be reductions at their own
stated dates and hours. They are not extra raw readings. In a model-comparison
table, preserve each column's sign and hemisphere scope independently, and leave
blank prediction cells empty. A table's day and 13-/14-hour labels cannot be
merged with a journal's later date or smaller clock number through an unstated
noon or midnight convention. Small restatement differences remain separate.

The longitude of greatest latitude is a model parameter, distinct from the
planet's longitude at an observing epoch. Approximate prose about a latitude
maximum and a subsequent change does not establish a precise extremum time or
an exact arithmetic equality. A detached footnote can retain a Unicode marker
that an automated Markdown-note index omits: verify its parent against the scan,
and distinguish a cited page from the note's own physical page.

“Evening, about the meridian” describes a sky position rather than noon. A
meridian-altitude label does not supply a missing transit clock. Keep an
unclocked stellar indication separate from a nearby timed Mars measurement.
The equatorial indication on XII p.291 has angular markers in the final edition
but bare components in the native print; its angular normalization follows the
edition and does not independently settle the native unit. “With one” remains
less specific than “with one pinnule”; neither identifies a particular pinnule.

A calibration performed in the afternoon can precede an evening observing
sequence. Preserve those source date-part claims separately; the calibration
time supplies no numerical clock offset. A locally preferred pair of declinations
does not replace earlier readings or turn into correction variants merely because
one value repeats. Reported changes “since yesterday” retain both endpoints and
their approximate angular amount without becoming a rate or an exact model
station determination.

Two triangular routes can feed a single combined right ascension without
printing either route's individual result or the combining weights. Preserve
that structure rather than manufacturing a literal-sum failure. On XII p.292,
the following “longitude in its own orbit” is a separate source coordinate
from the ecliptic longitude. Keep its frame and notation without a physical
frame conversion. The manuscript note “from codex K alone” qualifies this
calculation, not adjacent raw observations or the identity of their observer.

A clock said to have been corrected at a stated hour supplies a calibration-time
claim, not the size of the correction. A correction rule from a previous observing
sequence does not carry forward automatically. Italic text can introduce a new
pair of separation endpoints while a neighboring column retains a stellar
meridian indication; preserve the local column subjects independently.

The prose's Prutenic retrogradation on July 21 and Alphonsine direct motion until
July 27 are attributed model-date claims. They do not report observed station
times. The claimed three-day interval also does not establish an exact physical
duration from accepted timestamps. Preserve it alongside the stated 4¾′ motion
and the separate arithmetic check of the dated longitude results.

A conditional request to look for a planet is contextual evidence of an observing
plan. Its date label does not establish an actual observation. XII p.336 requests
predawn attention to Mars; a later dated record must supply its own evidence that
Mars was seen. Keep any separately published repetition linked for review rather
than counting it as another measurement.

A benchmark's carried clock can support matching printed order without proving
the time of a blank-clock source row. On XII p.346 the second declination in the
Aldebaran table remains untimed. The same page distinguishes corrected observing
clocks, a computed stellar transit, and three calculation epochs. Preserve each
role separately. A surprising numerical jump is likewise a reason to check the
print: the confirmed 45°20½′ separation stays unchanged even though adjacent
readings are near 45°51′.

An explicitly “true” declination adopted in a reduction does not establish the
hemisphere or correction state of preceding raw declinations. The November 29
calculation on XII p.347 adopts a southern value while its instrumental readings
remain unsigned. Its repeated calculation is attributed to codex V and reuses
observations; it is not a second observed series. Preserve the stated correction
order and distinguish a fractional-hour epoch from nearby H/M/S clocks. A
discrepancy between printed arithmetic inputs and output remains a calculation
finding until evidence establishes a transcription error or another interpretation.

Clock corrections do not supply corrected values for neighboring unpaired clocks.
On XII pp.347–348, the December 10 pairs retain both printed clocks and their
minute or second components. The following 7h15 adoption is a calculation epoch.
The source's instruction involving mean solar parallax remains separate from its
numerical Mars parallax input. Small residuals in the ensuing correction arithmetic
are preserved alongside the stated results, without an assumed rounding rule.

An expected stellar declination used in an instrument check is a calibration
reference. On XII p.348, 25°25′ expected and 25°17′ recorded give the stated 8′
refraction in unsigned magnitudes; neither value supplies a hemisphere. The
subsequent “true” stellar separation remains a reduction, with its own source
label and no invented observing clock. A statement that the difference is
imperceptible supplies no numerical uncertainty. Visual Moon-horn alignments
and historical magnitude classes retain their wording and geometry rather than
becoming exact center-to-center separations or modern photometry.

Mixed-object tables require a subject for each column. On XII p.411 the
separations concern the Moon's eastern limb and Mars, the paired declinations
concern the Moon, and a separate altitude column concerns Mars. Keep unlabelled
lunar declination columns in source order without assigning limbs or hemispheres.
A local limb annotation can qualify one altitude without resolving a later
reading's identity. Repeated headers in a split edition table require independent
layout review before treating them as renewed source labels.

An adopted result can favor one comparison star without stating its weights
or how another route was moved to the same epoch. XII p.412 favours Regulus
while preserving separate source epochs and unsigned intermediate declinations.
Keep the adopted northern declination separate from those earlier values. A
printed calculation-side argument retains its stated unit even when its
geometrical meaning is unresolved; do not change 20′ into 20° to make a familiar
formula fit. Source-linked lunar calculations remain distinct from new Mars
observations or detected parallaxes.

A calculation may repeat an adopted epoch and distinguish limb-to-body from
center-to-body separations. Preserve each printed claim and its endpoints;
their difference does not supply a separately stated semidiameter. On XII p.413,
the 50-unit time difference is established as source minutes by the linked
6⅙h and 7h0 comparison, while the 28′ motion is angular. Daily motion remains
per source day. A source coordinate “in its own orbit” retains that frame without
an invented truth label or an epoch borrowed from a nearby calculation.

Provisional correction tables retain the author's own qualifications. On XII
p.413 the text says that its parallaxes are approximate and need revision.
Preserve those inputs, the resulting positions, and their literal arithmetic
differences without supplying a rounding rule, uncertainty interval or correction
to the recorded observations. The expected 7h18 geometrical condition is distinct
from an observed transit. A stated expected advance is a historical reference,
not an additional measurement or modern prediction.

Diagram letters and numerical triangle parameters do not identify celestial
vertices by themselves. Keep the printed BA, CA, BC and BAC labels separately
from body-to-body separations. Likewise, a node-distance consistency check has
no hemisphere or calculation epoch unless its own source context establishes
them. A detached footnote can refer back across a new date heading; bind it to
its marked parent rather than inheriting the nearest heading.

When a mixed observing sequence changes its comparison planet, preserve the
local separation endpoints independently of continuing indication-column labels.
On XII p.415, the Moon–Mars row retains a Jupiter-east header in an empty column;
that header does not change the separation into a Moon–Jupiter measurement.
The lunar lower-limb altitude is separate from the separation's unresolved limb
identity. A corrected clock pair printed later does not correct earlier clocks.

On XII p.416, the Jupiter route explicitly names the Moon's center while the
Mars route names the Moon without repeating a center label. Preserve that
difference. Adopted inputs, three calculation epochs and the recorded pointing
remain separate; their numerical differences supply no additional semidiameter,
combining weights or time-transport procedure. Two reviews using the same dated
heading can intentionally share one date identity when their anchor, components
and qualifications are identical. A following new date heading is a boundary,
not a date for preceding untimed calibration readings.

A retrospective calculation can quote times associated with earlier observations.
On XII p.432, retain the fractional-hour epochs used by the two Mars routes
without asserting that they were newly computed times or original clock readings.
The shared unsigned declination has no separately stated epoch. The printed
5′5″ right-ascension difference is angular; agreement with its subtraction does
not establish observational accuracy or transport both routes to a common epoch.

A comparison of the same stellar separation on two named dates retains both date
claims on its difference. The later reading's description as “truer” expresses
source confidence. Native column alignment and neighboring unit statements can
establish an abbreviated difference's units; numerical fit alone cannot. Keep
warnings about instrument defects separate from numerical correction amounts and
their stated application to particular series.

A numerical error estimate and the correction subsequently adopted from it are
separate source claims, even when their amounts agree. On XII p.432, the error
estimate is explicitly approximate; the following addition instruction has its
own application scope. Preserve those qualifications independently. The following
dated worked examples do not date the undated instruction itself, and recording
a reported application does not execute a correction on catalog readings.

The altitude-bias note on XIII p.219 says that the Benátky sextant and revolving
quadrant read 2′ high from August 28, and that this was corrected wherever entries
could be found. Preserve the reported bias separately from any individual
altitude. The starting year and per-record application are unstated here; do not
subtract the amount again, manufacture uncorrected readings, or extend the scope
to Fabricius's instruments. A conditional plumb-line calibration from two stellar
altitudes on XIII p.215 likewise supplies no numerical offset or individually
identified Mars input. Import those star altitudes and their transit clocks under
their own targets and source identities.

Keep timing anchors local to their subjects. On XIII p.219, the separations were
taken two hours after Mars's transit, while the altitudes belong to the meridian
group. On p.203, the lunar upper-horn altitude and approximate two-day interval
after quadrature describe the Moon; Mars is only said to be approaching transit.
Neither wording supplies a numeric Mars clock. A value described as repeated
twice remains one printed quantity with a repetition claim, rather than two
invented numerical records.

On XIII p.220, keep the two measured/expected stellar sextant checks and the
reported 1½′ shortfall as separate records. Their exact displayed differences
are not identical. A reported common deficit does not authorize replacing those
values, executing a uniform correction, or interpreting it as celestial
parallax. Raw and “limited” planetary distances can differ by different amounts;
retain the source adoption without supplying an unstated algorithm.

Eastward stellar angles read with armillae remain angular meridian distances,
with the source's instrument label and any uncertainty about the precise frame.
Do not turn them into azimuths or clock values. An explicitly inferred or
corresponding time derived from this geometry remains an `inferred_time`, with
no selected recorded event clock. A source description of a specular clock is
retained without inferring its construction or time standard.

An independent transcription can quote a calculation input rather than a direct
reading. On XIII pp.220–221, Pafko rows 923–925 identify the Mars declinations
inside the January 20–24 positional calculations. Preserve those control links
and the values, but classify their role from the source section. Repeated
adopted distances retain their new source occurrences without creating new
independent measurements. Match their earlier counterparts by the named night,
reference and source sequence before comparing numerical values.

Separate a source's adoption from a demonstrated arithmetic operation. The
January 20 text explicitly retains the latter right-ascension result for the
true place. January 22 labels the difference between two stated longitudes;
their subtraction can check the abbreviated minutes/seconds expression. Its
limited longitude need not be an exact unrounded mean. The further January 24
limitation does not identify an exact input set or weighting rule, so preserve
that uncertainty rather than constructing a formula that reproduces the value.

Carry calendar, time and coordinate-origin evidence at the source occurrence
where it is established. On XIII p.221, “old style” explicitly qualifies the
January 13 label; it does not assign a calendar to every neighboring date. The
equated time reduced to Uraniborg is a calculation qualifier, not evidence that
the observation took place there. Aligned day/hour/minute working rows retain
their day labels without accepting an absolute timestamp.

The native model heading really prints “H. 9 H. 32”. Preserve its unresolved
time-unit notation and the parallel H.9 M.32 passage separately. A correctly
transcribed source ambiguity is not an edition error. Likewise, a named-sign
longitude must retain its sign when checking source arithmetic: reconcile the
explicit zodiac origins before comparing an absolute total with a sign-relative
result. Preserve an unsigned model-difference claim without inventing a printed
sign, a named cosmology or an observational parallax detection.

Use an unclassified numerical-expression record when a printed or diagram
number's physical kind or units remain unknown. Preserve its numeric literal
without assigning degrees, time or proportional minutes from a fitted result.
Native inspection can confirm the characters without resolving that meaning.
Likewise, an internal diagram/scan-page tag is not a printed-page citation.

The refined opposition on XIII pp.221–222 retains the provisional 9h40 scenario,
later computed position and model comparison separately. Joint Sun/Mars motion
stays a joint term. The two 1′50″ latitude additions preserve their input and
result chains without an inferred refraction/parallax identity. The adopted
opposition latitude and constructed greatest northern latitude are different
source results; neither is a new independent observation or automatically a
modern orbital-inclination measurement.

On XIII p.222, preserve the distinct anchors of the following-3-February
observations. The quarter-hour duration follows the preceding observing series;
the half- and three-quarter-hour durations follow Hydra's meridian transit.
Their approximate labels remain explicit. The first Hydra-head star is only
said to be near the meridian in the earlier series, and the promised inferred
clock is unprinted. Do not substitute an exact transit or manufacture a time.

“With the sextant corrected” describes the instrument in the February 2 report.
It does not specify an arithmetic offset to add to those readings or later
series. Repetition counts, including four repetitions, retain a single printed
magnitude; a precise-repeat claim supplies no statistical uncertainty or proof
of independent observations. An approximate acronychal phase duration remains
contextual, separately from the direct angular readings.

When one paragraph contains several stellar timing conditions, bind each to its
own group. In the February 2 report, Spica approaching the meridian belongs to
the Mars–heart-of-Leo distance; Arcturus on the meridian belongs to the
Mars–bright-neck-of-Leo distance. A shared paragraph and source date do not make
the conditions interchangeable or establish a common numerical clock.

On XIII p.223, setting the clocks to 9h2 at the upper Gemini-head transit gives
a corrected clock setting, without a recorded original or an offset. Keep the
lower-head altitude as a separate pointing. The supporting Procyon transit and
Gemini altitudes retain their stellar subjects, even though they accompany a
Mars series. A visual quarter of the interval between the Aselli is a ratio
with both baseline endpoints; its northward description supplies no angular
scale or modern star identification.

The later heart-of-Leo repetitions follow the distinct qualifier “shortly after
med. 10.” Retain that unexpanded wording without assigning 10h, 10h30 or the
earlier 9h30 clock. Preserve the February 20 series' three 39°30′ readings as
printed; an expected trajectory is not evidence for replacing source numerals.
Stellar sextant checks retain measured and expected values separately, without
an inferred correction applied to every Mars reading.

The March 2 comparisons on XIII p.223 distinguish a new pinnule for the
Aries/Aldebaran distances from the old setting for the heart-of-Leo distance.
Retain those settings with their own rows; they do not identify an unstated
complete instrument or supply a numerical adjustment. The 10h clock belongs
to the Mars meridian altitude, not the preceding distance series.

The March 9 comparisons shortly before and after meridian passage are separate
from the meridian altitude. Their timing qualifiers supply neither numerical
clocks nor elapsed intervals. The accompanying “greatest parallax of the orb”
and approaching-station note is qualitative historical context; it supplies
no diurnal-parallax angle, terrestrial baseline or fitted station epoch.

In the March 15–16 tables on XIII p.224, each distance row supplies its own
clock. Keep those pointings distinct and leave the leading meridian altitudes'
clock cells blank. The tail-of-Leo expressions 47°28′20″ and 47°28⅓′ have the
same normalized magnitude but different printed precision and observing clocks;
normalization does not merge them. An old-pinnule heading can continue through
a subordinate “Conversely” orientation heading within the same dated section.
Retain that heading-based scope separately from an explicit row-level setting.

The following March 2/9/15/16 tables explicitly calculate positions from the
preceding observations. Their fractional-hour headings are calculation epochs;
the declinations are inputs to those position calculations. Keep the Pafko
control links without treating the values as additional instrument readings.
Only the March 2 table repeats an explicit north label. The later independently
headed declinations remain unsigned. Ascensional differences retain their named
stellar references and local add/subtract instructions, including the March 16
Gemini addition; those instructions do not supply a hemisphere or spherical
planet–star separation. Retain unspecified reduction algorithms when reference
coordinates or other required inputs are unprinted.

The March recap repeats reduced positions in a column labeled “observed.”
Those copies remain distinct source assertions, not additional raw observations.
Inherit Cancer/Leo signs and northern hemispheres only within their own table
columns. Latitude differences omit zero degrees and use minutes/seconds, while
longitude differences retain degrees/minutes/seconds. Keep the printed min/plus
labels separately from physical coordinate directions; unsigned latitude
magnitude differences do not define a signed north/south residual. Cross-sign
longitude arithmetic requires a common zodiac origin.

In the Latin context of the XIII p.224 latitude tables, S is read as
*septentrionalis*, north. The same volume explicitly labels northern latitude
as *Latitudo Sept.* and spells out Sept. in the nearby Mars calculations on
p.226. The native p.224 print agrees with the transcription. This contextual
expansion corrects sixteen earlier south interpretations while preserving
their expressions, unsigned magnitudes and identities. It is not a global
rule for English S labels. A numerical normalization check alone does not
establish the meaning of a historical direction abbreviation.

On XIII p.225, the March 23 table changes the Mars comparison star within the
table while retaining Arcturus as the altitude subject. Keep the row clock as
shared source context without asserting exact simultaneity. The separate 8h2
Mars transit supplies no correction to the later clocks. The resulting ecliptic
coordinates are reductions with no stated epoch; preserve the explicit B
latitude direction independently of earlier S labels. “Near the trine” and
“greatest parallax of the annual orb” remain qualitative descriptions, without
an invented exact angle, terrestrial baseline or diurnal-parallax measurement.

The March 25 table embeds a labeled Mars meridian altitude inside its usual
distance column. Keep that local override and its clock separate from the
Aldebaran altitude column and the adjacent blank-clock distance. A repetition
label without a number supplies context, not an extra equal-valued reading.
On March 26 the last Gemini-foot altitude has its own clock; the earlier and
later Mars distances remain untimed. The explicit statement that the Mars
meridian altitude was not taken records an absence. Its suggested recovery
from neighbouring observations supplies no measured or interpolated value.

In the April 6–7 tables on XIII p.225, leading meridian altitudes and the last
April 6 neck-of-Leo repeat have blank clock cells. Preserve those blanks while
retaining each printed distance clock. The observing expression 9h8⅓m differs
from the separate true-place calculation's 9⅓h epoch. Keep those units and roles
distinct; the reduction supplies no missing observing clock, declination input
or complete algorithm. Ascensional differences keep their stellar references
without inheriting add/subtract instructions from earlier calculations.

On April 12, the two blank-clock Gemini-foot repetitions stay untimed despite
the first distance's printed 9h37 clock. “Repeated twice” on the later
heart-of-Leo entry qualifies one stated magnitude and its printed clock;
preserve the count without making extra numeric records or observing epochs.
Neither leading meridian altitude inherits a following distance clock.

The April 27 and May 3 series on XIII p.226 have individual distance clocks;
the May 2 series supplies none. Keep the latter's repeated magnitudes as
separate quantities in related reference groups, without a numerical epoch or
claim of simultaneity. Castor is explicitly named on May 3 and remains that
endpoint, without substitution for another Gemini star or an assumed catalog
component. A precisely-repeated claim qualifies its angular reading and does
not establish a clock's precision or a numerical statistical error.

Corrected worked examples retain their printed inputs and outputs without
manufacturing originals. The two dated Jupiter calculations on XII p.432 use
separate fractional-hour epochs, shared only within the corresponding source
calculation. Fixed-star positions adopted in a continuing calculation can link
to a later route without becoming new observations of those stars. Preserve the
source's unstated combining weights and unknown coordinate correction labels.
Explicit circular arithmetic can verify a wrapped right ascension; it supplies
no missing spherical inputs or validation of the underlying astrometry.

Match original and corrected counterparts by source date, epoch, named reference
and printed order before comparing amounts. On XII pp.431–432, all four quoted
original Jupiter distances plus 2½′ equal the corrected distances. The original
tables are retrospective calculation inputs and do not automatically establish
four additional raw observations. The unsigned original declination stays
separate from the southern corrected adoption. Later validation links reference
the existing corrected quantities; neither those quantities nor earlier reviews
are rewritten. The source's alternative explanations—instrument fault or nearby
Moon brightness—remain available without an exclusive causal conclusion.

A dated separation in the first sentence of a paragraph does not necessarily
date the meridian-altitude parameters that follow. On XII p.431, the quoted
September 10 evening baseline has its own date while the two meridian altitudes
remain untimed. The restoration section separately repeats November 13 labels
for two stars. Preserve those statements and the source's confidence claims
without deriving missing hours or observational uncertainties.

Keep a restored stellar parameter distinct from the value later used in a
planetary calculation: 40°19⅗′ and 40°19′35″ differ by one arcsecond, and both are
printed. Route results do not establish combining weights. Likewise, the source's
longitude excess and latitude deficit against a “limited” position remain claims
with an unresolved precise baseline; agreement with a convenient later coordinate
cannot establish that baseline's identity.

Weather and confidence statements retain their own date boundaries. On XII p.440,
the clear, calm December 18 note precedes the December 31 heading. It does not
qualify the later readings, whose passing-cloud and strong-wind note has a
separate scope. A printed doubtful-reading brace can qualify one separation
without qualifying every quantity in its row.

Mixed-target tables require local instrument and quantity assignments. Jupiter's
transit and two instrument altitudes do not time the separate armillae declination
pair. Blank-clock continuation declinations preserve their printed pair ordering
without acquiring a second measured time or proof of exact simultaneity. Angular
indications headed with a star and “east” remain angular readings with an unknown
reference origin when the source does not establish that origin; they do not
automatically become observing clocks or modern hour angles.

Planet-grouped chronology can restart in January after December records of another
planet. The native XII p.441 header still gives 1595 for the January 3 and 4 Mars
entries; the preceding Jupiter dates do not establish a new year. Dawn can replace
a numerical altitude cell with prose, and a source argument that equal apparent
altitudes avoid harmful differential refraction supplies no measured zero
correction. Later clouds can terminate a series while the author explicitly
endorses the preceding readings.

An adopted calculation epoch can differ from every recorded observing clock.
On XII p.441 the January 4 reduction uses 7⅙ hours and explicitly southern
declinations; these do not replace the raw clocks or supply the raw declinations'
unstated hemispheres. Preserve literal arithmetic differences: the printed right
ascension 252°13′20″ differs by one second of arc from the sum of its stated
inputs, 241°12′55″ and 11°0′26″. Agreement between the native print and final
edition makes this a source calculation discrepancy, rather than a transcription
error or authority to rewrite the output.

An observing purpose is not a numerical observation. XII p.441's July 21
reference to the “parallax of the orb” and solar quadrature identifies the
investigation without supplying a measured parallax or an exact 90° separation.
Its nearly straight Moon-limb–star–Mars alignment remains qualitative. A southern
comparison-star label identifies the Taurus horn; it does not assign Mars a
southern declination. The first row beneath the Mars–Jupiter separation header
contains only a clock, declination and altitude: the empty separation stays empty.

A visual collinearity claim supplies no exact zero angle or numerical tolerance.
Preserve its named objects and qualification separately from numeric readings.
A proposed triangle calculation likewise supplies no unprinted result.

A northern declination of an unspecified horn of Taurus does not identify the
star as the northern horn. Preserve the coordinate direction separately from
the unresolved stellar identity.

An editor can correct the name attached to a stellar angular indication without
changing its number. Retain the printed subject and editorial alternative
separately; neither a silent relabelling nor a second measurement is warranted.

A main-text number can already contain an editorial correction. Preserve the
manuscript value reported in its note as a linked source variant, mark the
edited reading as a correction, and avoid applying that adjustment again.

When a native source preserves an ambiguous sign or separator, retain that
notation and its known quantity without choosing a scalar from the expected
motion. A selective image check can establish what is printed while leaving
the notation's meaning unresolved.

A time annotation can occupy a column otherwise used for altitude. On XII p.441,
July 22's “Resp. 2h50” remains a time with unresolved association, separate from
the 2h47⅓ observing clock and the reduction's adopted 2h40 epoch. It supplies no
automatic clock correction. Repeated equal declinations or separations retain
their distinct source entries; “with both” beside one calibration value does not
create two readings or identify the settings.

Preserve differences between a raw table's reference label and the later
calculation's label. The same page names the mouth of Pegasus in the observations
and the first star of its wing in the adopted reduction. Both labels occur in the
native print. Numerical similarity cannot establish an alias or authorize
relabeling. Likewise, two stellar reduction routes do not establish combining
weights or unprinted intermediate results. An editorial codex attribution is
separate from observer identity.

Same-date accounts can describe different observing sites. XII pp.442–443
distinguish Uraniborg instrument readings from a Copenhagen account with an
inferred time, qualitative alignments and an unscaled sketch. Positions read
from the small and largest globes remain separate reductions. They are not
additional instrument measurements or necessarily simultaneous with the logs.
Named table predictions retain their own attribution; a decreasing latitude
does not supply a missing hemisphere.

An isolated superscript time unit remains decisive: 32 minutes means 1,920
seconds even when a generic component parser normally starts with hours. Unit
checks must validate the printed unit as well as the sequence of numeric tokens.
Preserve a source's noon clock-adjustment claim separately from earlier recorded
clocks. Likewise, a one-arcminute declination instruction does not establish an
exclusive choice between two stellar calibration readings or justify merging
the later 16°53′ adoption with 16°53½′.

A retrospective separation can belong to an evening account while being gathered
from observations after midnight. XII p.443's September 9 statement retains that
derived role and its own date label; the September 10 log supplies neither an
automatic calendar conversion nor a clock for the evening alignment. A printed
instruction to correct distances, with a cross-reference to an instrument test,
does not itself specify a numerical adjustment for every recorded separation.

An adopted declination and a result from meridian altitude can coexist. Preserve
both source values and the stated method without selecting an instrument or
observatory latitude that the calculation does not identify. A “better” label
beside the revolving quadrant's altitude qualifies that reading locally. A
following stellar angle without its own clock can remain an untimed calibration
rather than inherit the planet's transit time.

A bare “with both” in a numerical column remains an annotation when no value is
printed beside it. On XII p.443, September 11's label does not authorize copying
the preceding declination into another timed row or generating two pinnule
readings. The later adopted declination explicitly says north; the unsigned raw
readings retain their unknown hemispheres.

A stellar declination shortfall is a comparison claim, distinct from an applied
planetary correction. Preserve the stated two-arcminute deficit after the
Aldebaran calibration pair while leaving its comparison value and exact baseline
unresolved. Do not manufacture an expected coordinate by adding the deficit to a
convenient reading or transfer it to Mars.

Date labels and observing series can cross a printed page boundary. Verify both
native pages, preserve each quantity's actual page and carry the supported date
through an unlabelled continuation. A clock beside “meridian altitude” need not
be reclassified as an explicit report of crossing the meridian. Date labels can
also be italicized inside brackets; requiring the literal substring `[DIE `
would miss some September headings on XII p.444.

An explicit quantity change overrides an inherited column header. On that page,
September 15's northern-declination column later holds two instrument altitudes
after the meridian-transit label. Keep both altitudes, their local instrument
names and their unsigned magnitudes. The provisional declination candidates at
those cells are excluded as the wrong quantity while their original extraction
claims remain available for audit.

Legacy coordinate extraction is not a coverage boundary. September 16 on the
same page has Mars declinations and stellar calibrations in prose-labeled tables
despite producing no legacy coordinate candidates. Inspect those structures
directly and preserve each actual subject. A source-corrected stellar transit
clock can have no printed original value; keep the corrected time without
inventing its offset. “Shortly afterwards” does not assign that clock to the
following planet or star declinations.

A printed resulting position can lack a specified calculation procedure. The
September 18 entry on XII p.444 gives a Taurus longitude and southern ecliptic
latitude after the observing tables, without identifying a formula, exact input
selection, correction state or calculation epoch. Preserve those coordinates as
reductions linked to their source context. Do not select convenient inputs to
manufacture a derivation, use the final observing clock as a calculation epoch,
or transfer the latitude's southern direction to unsigned raw declinations.

An observer's doubt can leave competing explanations unresolved. The note on
XII p.444 questions either day's declinations and alternatively the armilla's
departure from the meridian. Preserve those alternatives and the uncertain scope
of the qualification, without assigning an error bar, rejecting a whole series
or choosing a correction. Its quoted following-day declination is a historical
comparison input, distinct from that day's eventual raw log entry. Relative-day
wording alone must not acquire the current heading's date or observing clock.

A stated emendation amount need not identify which adjacent coordinate is
original or corrected. The two-arcminute addition on XII p.445 remains a separate
historical correction statement; its precise attachment to the preceding
declination pair is unresolved. Preserve the printed pair and the addition
without manufacturing a resulting coordinate or applying the amount again.
Quoted approximate times from a preceding day retain their relative-day context,
separate from the current day's observing clocks and calculation epochs.

Correction labels can apply to a time column without applying to the accompanying
coordinates. The last-day-of-September tables on XII p.445 retain six corrected
clocks with no printed originals or offsets. Their stellar calibration pair,
expected stellar declination and adopted Mars declination have distinct roles.
The known calibration dependencies do not identify which raw Mars reading was
used, its weight or a numerical correction amount; the adoption remains
uncomputed. Preserve the source's last-day date rule alongside later explicitly
numbered calculation dates, without silently replacing the observing label.

Literal arithmetic can disagree with a printed historical result even when the
edition matches the source. On XII p.445, the Orion route's right-ascension
subtraction agrees, while 26°9′ + 27°56⅙′ gives 54°5′10″ rather than the printed
54°5′. Preserve the ten-second difference without assuming rounding. The
adjacent “thus in the codex” footnote qualifies an October altitude carrying its
marker; it does not qualify this right ascension. Diagram labels and triangle
parameters remain source geometry, with no scale or astronomical identity
assigned to the unkeyed vertex A.

An observed planetary transit can have no printed clock even when nearby stellar
calibrations have times. On XII p.446, October 12's two Mars meridian altitudes
remain untimed. The separate Cetus brace preserves a source-corrected reading,
an angular indication and a reported stellar transit time whose observed or
inferred status is unresolved. Do not borrow the star's clock for Mars or derive
an unstated clock offset by imposing a twelve-hour convention.

A dated stellar-line description remains an observation group even when it
contains no numerical measurement or clock. In the September 1595 records on
XIII pp.247–248, dotted star and point labels identify references; they are not
decimal degrees or sexagesimal components. Preserve a paragraph continued across
a page break as one account. Nearer, north of a line, not yet reached and grazing
with rays describe different constraints. They supply neither a calibrated angle
nor an exact zero center offset, and relative north or south does not establish
Mars's absolute hemisphere.

A retrospective interval can be stated without identifying an earlier dated
record. The October 1595 report on XIII p.248 gives approximately eight days;
retain the duration and its relation to the current account without subtracting
it to invent an observing date or creating an extra group. An explicit absence
statement, such as the observer's being away in 1596, differs from an omission
claim or missing source text. A diagram beside mixed planetary passages retains
that layout context without an assumed subject for each unlabelled line.

Printed date order can differ from chronological order. Preserve the source
sequence and each date label without silently repairing either. In XIII
pp.248–249, the August 23 and August 22, 1597 accounts remain separate despite
their related stellar geometry. Their inline dot patterns retain distinct source
occurrences and described topology without a metric scale. A following-day
conjunction expectation is a prediction based on that account, not another
observed event or a measured zero separation.

Keep a literal numerical coefficient separate from the geometry it qualifies.
On XIII p.249, half a diameter and a little more supplies a coefficient of
one half but no securely identified diameter; the coefficient is not the full
separation. Twice-as-far wording with an editorial question retains two without
an assumed interpolation formula. Likewise, second- and third-hour labels can
share one report without a chosen single clock or an invented mean time. A
neighbouring planet's clock does not time an untimed Mars alignment, and a
retrospectively inferred sunset position remains distinct from a raw reading.

Paired dotted day labels belong to their collective source report. On XIII
p.249, November 15.16 and 19.20, 1597 identify two dates apiece, not decimal
dates, clock components or automatically independent measurements. Preserve
both dates and the reported stationary or backward-motion state without a zero
motion rate or an interpolated station epoch. An inability to tell which stellar
endpoint was nearer does not establish an exact midpoint. Retain morning only
where it is stated; the later paired report supplies no daypart.

A separation bound can be useful without a calibrated angular value. On XIII
p.250, Mars is less than a Moon's diameter from Gemini's ninth star, whose
visibility is impaired by Mars's brightness. Retain both endpoints, the strict
inequality, reference body and visibility qualification; leave an unstated
center-or-limb basis unresolved. Neither equality nor a modern lunar diameter
follows from this account. A stellar comparison of the Moon's diameter on a
different date cannot silently calibrate the earlier bound.

A reduction-purpose heading does not change the measurement type. On XIII
p.270, For the latitude introduces Mars–Procyon and Mars–Leo-neck distances.
They remain angular separations with both endpoints, without a measured latitude
or hemisphere. A separate conversely label preserves source orientation; it does
not itself identify an instrument or a numerical correction.

An instruction that no instrumental parallax is to be subtracted describes a
particular instrument configuration, not a zero celestial parallax. On XIII
pp.323–324, the instruction concerns sextant observations through both new
lower pinnules that evening. The later stellar and Mars meridian altitudes do
not acquire that instrument or correction merely by proximity. Likewise, a
stellar transit offered to verify preceding lesser-clock times does not supply
a correction for later clocks. Preserve each instruction's stated scope. The
Mars opposition note is a configuration claim, not a measured 180° separation
or an independently established absolute epoch.

Comet descriptions can mix measurements and analogies. On XIII p.388, an
altitude of 14° and a tail length of 4½° retain separate subjects; the latter
is an angular length, not a head diameter. A comparison with third-magnitude
stars remains a historical visual comparison, without a calibrated modern
magnitude. The comet's stated Saturn-and-Mars nature supplies no planetary
position. Preserve distinct first-sighting and local first-observation dates;
neither automatically dates every descriptive note in the account.

Candidate screening can also select translator explanations, symbol keys and
formatting markers. Record their exclusion explicitly. A final-edition review
containing only non-observational exclusions may leave its printed page unset;
this exception cannot introduce quantities, events or included regions.

Keep an instrument description distinct from later descriptions of the same
reading. In Volume X's preface, p.IX note 3, Dreyer warns that Lalande called
declinations taken through both sight vanes readings “by two instruments.”
That warning does not identify two independent instruments or two independent
measurements. Preserve the original instrument and sight-vane labels, and
attribute a later interpreter's description separately.

An early journal can combine visual configurations with coordinates taken from
tables. On X pp.3–4, the 1563 Leipzig entries include an explicit Dureri table
attribution and a broader Alfonsine statement whose extent is uncertain. Keep
that uncertainty with neighbouring numerical positions; the prose's location
in an observational journal does not establish a direct instrument reading.
The August 31 triangle supplies a reported longitude reduction and a strict
southern-latitude bound, without calibrated triangle angles. October 8's
alignment clock does not automatically time the following coordinate note.
Preserve “after hour 10 Urb.” as a qualified hour boundary and leave the clock
label unexpanded. An unexplained “A.” latitude label does not acquire its
hemisphere from the preceding date's signed value.

Keep an ephemeris author's name with the cited numbers. On X p.5, Stadius and
Carelli supply positions and reported distances alongside observed separations;
those names do not establish the physical cosmology to use in a reconstruction.
An omitted sign in a prose list can inherit an explicit sign from the preceding
body only within the same reviewed ephemeris statement. Preserve the literal
expression and that source link; sentence order is not a table-column number.
An adjacent English restatement of a Latin comparison table is another
representation of those entries, not another independent set of observations.

Check a reported longitude difference in a common zodiac frame before comparing
it with the source's distance. The May 2 Carelli longitudes give 18°01′ for the
Mars–Saturn difference, while the source reports 18°. Preserve both and the
arithmetic disagreement. This check does not reconstruct spherical separation
from unrecorded latitudes or establish a transcription error. Likewise, a
source's suggestion of instrument or sighting error supplies no correction
amount to apply to its readings.

Preserve calibration dependence. On X p.6 the compass method assigns a scale
from Stadius's Jupiter–Saturn distance and doubles the measured spans. Its
resulting planetary intervals cannot independently validate that reference
scale. Keep the clock, scale bound, rounded diagram intervals and visibility
limitations separate. An untitled coordinate table retains its printed body
labels and unresolved attribution even when a different assignment would make
a comparison agree.

Diagram notation needs a local unit review. The Carelli figure on X p.6 uses
dotted degree/minute pairs: 1.46 is 1°46′, or 6,360 arcseconds, rather than a
decimal-degree value. Preserve the dotted expression and interpreted components
together; this does not define a punctuation rule for every diagram or clock.
Retain the neighbouring scale's labels and unlabelled-dot descriptions as
diagram metadata without creating unprinted planetary coordinates or an
unstated zodiac origin. Printed placement near a dated entry alone does not
establish the date of every figure.

An ephemeris-anchored reduction does not recover its unprinted raw inputs.
On X p.6, May 25 adopts Jupiter's ephemeris place and derives the other
planetary places from measured distances that are not stated. Retain the known
anchor and leave the reduction links uncomputed. The source's refusal of
one- or four-minute exactness supplies no symmetric error bar, and its explicit
doubt about Mars's place does not authorize a replacement value. On May 30,
the observed near conjunction and its clock are separate from Stadius's
predicted 10′ longitude and 44′ latitude components; neither component is a
measured great-circle separation.

Keep missing table cells distinct from numerical zero. On X p.15, the
January 1568 comparison table supplies Mars longitude and latitude in separate
Alphonsine and Prutenic columns while leaving its observed-position cell blank.
Import the four predictions with their model attribution and preserve that
blank without creating an observed coordinate. Motion labels and latitude
hemispheres have their own scope within each model cell.

Preserve a reported erasure with its attachment and scope. The marginal note
attached to the January-end paragraph on X p.15 reports cancellation by erasure,
but does not identify the precise reach to individual numerical readings.
Retain the source-quality report and the recorded distance; leave individual
cancellation status unresolved where that attachment alone cannot establish it.
A manuscript cancellation report is distinct from an error in the modern
edition, and supplies no replacement number.

Clock scope can change within one named day. On February 7, X p.15 gives one
Mars–Gemini distance before a later paragraph names about the ninth hour after
noon for further distances. Keep the first distance unclocked and group the
later readings with their own clock. Likewise, an instrument heading restricted
to an earlier dated report does not establish the instrument for later dates.

Retain measured sides of a mixed-planet figure rather than enforcing its
qualitative description. The August-end 1569 account on X p.17 calls the
Mars–Venus–Canis Minor triangle nearly equilateral, but records three distinct
distances. Preserve each pair of endpoints and the two successive observing
clocks. A comparison star's stated magnitude is not a magnitude measurement
of Mars, and qualitative faintness supplies no measured distance.

Reported damage to a source witness can limit context without making a
preserved numeral incomplete. On X p.17, torn-leaf notes attach to the
September 2 Moon/Venus and Mars passages. Keep the gaps and uncertain clock
association explicit; do not reconstruct missing text. Mars's ten-arcminute
limit describes its position relative to a line through Gemini's heads, not
a direct stellar distance. Retain its upper-bound meaning. The neighbouring
lunar limb, semidiameter and no-parallax statements keep their lunar scope.

Separate coordinate blocks retain their own meaning even when their rows align.
On X p.19, the source explicitly gives the same Saturn–Venus–Mars row order in
four side-by-side blocks: places, Stadius, Alphonsine calculation, and true
observation with instrument correction. Use that declared order to identify the
unlabelled rows. Preserve the source's corrected state without treating it as
modern accuracy or supplying an unprinted correction amount. The following
great-globe results are reported as much later additions in Christiani Severini's
hand; that attribution does not identify the original observer or replace the
other coordinate states.

Instrumental “parallax” requires its local meaning. On X p.20, the short-distance
instructions add 1′ near 20°, 4′ near 10°, and 5′ at 5°. These are instrument
error terms with angular arguments, rather than measured celestial parallaxes.
Preserve the approximate arguments and the warning that even equal angles need
not have proportional errors. The three stated corrections do not establish a
universal calibration curve, a statistical uncertainty or an adjustment already
applied to any particular reading. Their writing date is unstated; the following
1570 reference-star heading supplies no date for them.

Bind a continued numerical expression to every source fragment. The January 7,
1570 Mars reduction on X pp.21–22 begins with 13 degrees and continues with
40 minutes of Virgo. Its margin separately offers 10 minutes because the figure
is ambiguous. Preserve the complete main coordinate and the linked, unapplied
alternative, with each printed-page citation. The physical location of the note
does not give it the date of a later observation. A following qualification can
also continue a numerical bound: the January 13 distance of 19°40′ is followed
by an upper limit of 19°45′. The limit remains distinct from the reading.

Written fractions retain their literal parts and exact sum. “20 degrees and
a half” is 20½°, with 20 and one half retained as the stated addends. Qualifiers
such as “nearly” remain separate from the rational conversion. Descriptive star
names and later editorial identifications likewise remain separate, even when
an identification seems familiar.

Native reference units can change within one observing sequence. On X pp.23–24,
the Aldebaran occultation account uses fractions of the illuminated lunar portion
and of the lunar semidiameter, alongside instrument distances in degrees. Keep
those references separate. A bare later fraction retains its locally unstated
reference and any contextual candidate, rather than receiving an automatic unit.
The 100000 whole-sine scale belongs to the historical computation, not to angular
arcseconds. Retain the three inferred times separately from the recorded clock.

An unprinted later operand must not be supplied merely to manufacture an
arithmetic discrepancy. The later equatorial arcs in that calculation do not
explicitly repeat the earlier solar right ascension. Keep those source results
without assuming that every operand was unchanged. A distance already described
as free of parallax is likewise a source reduction, not a recoverable raw reading
to which another correction can automatically be applied.

Use internal source relationships to establish count units. The lunar table on
X p.25 doubles 1 count 59°35′41″ to 3 counts 59°11′22″, requiring 60-degree
counts. This does not generalize to other tables' zodiac-sign counts. The same
table mixes proportional coefficients with angular corrections; 10 5½ and
36 21 in its short correction rows are angular minutes and seconds.

Keep apparent and equal time representations separate. On X p.25 the stated
six-minute addition converts 6h24m to 6h30m exactly, while the printed 7h12m
is thirty seconds above 7h5½m plus that correction. Record the difference and
leave the rounding convention unstated. The alternative Leovitius calculation
uses a separately attributed Alphonsine time adjustment. Its time correction,
corresponding lunar motion and adjusted prediction are distinct quantities.

A later conclusion can revise an earlier reduction without replacing its
source value: the same account prints both 4°8′ and 4°7′ Gemini, with respective
12′ and 13′ differences from the tabular place. The detached note reports later
lunar latitude calculations and missing codex material. Preserve that report,
its source link and its locally unsigned latitudes; proximity to an earlier
southern coordinate cannot supply their hemispheres. Claims of no perceptible
longitude parallax are qualitative claims rather than measured zero angles.

Diagram coordinate offsets remain distinct from great-circle distances. The
third latitude offset labeled “none” is an explicit zero component; it is not
zero parallax. The January 24 Moon–Mars distance explicitly includes latitude
and parallax and supplies no separate parallax amount. A referenced earlier
two-degree distance with uncertain endpoint scope remains an unclassified angle
instead of acquiring assumed endpoints.

Keep a model's opposition date separate from its predicted position on another
day. On X p.26, the Alphonsine opposition is assigned to February 10 and the
Prutenic opposition to February 15. Neither claim supplies an observed instant.
The author's approximate opposition date remains a separate historical claim.
The Prutenic February 15 position explicitly refers to midday; the accompanying
Alphonsine position does not repeat that clock qualification.

An omitted zodiac sign remains omitted even when a stated numerical difference
makes a possible completion attractive. The February 10 predictions 8.58 and
2.5 retain degrees and minutes without inherited signs. For February 15, both
signs are explicit, so the coordinate subtraction can be checked: the stated
six-degree difference is four arcminutes below 6°4′. Preserve the stated
degree precision without asserting an unstated rounding rule or edition error.

“3½, close to 4” preserves a reported coordinate and an approximate reference
mark, rather than two independent readings. Likewise, “between 8 and nine”
supplies observing bounds without an exact clock or a measured one-hour duration.

A page boundary need not end an explicitly introduced observing session. On
X pp.26–27, the February 26 eight-hour P.M. introduction governs the following
three Mars distances despite intervening detached notes. Those notes belong to
an earlier lunar/eclipse account. Reused footnote numbers must be resolved by
printed page and actual reference, rather than by proximity to a Mars paragraph.

The source explicitly derives the February 26 coordinates by drawing the
observations on a plane. Preserve those reductions and the latitude alternative
3°50′ beside the main 3°45′ north. Inheriting the unchanged degree and hemisphere
within that alternative does not authorize giving the separate Prutenic latitude
4°16′ an unstated hemisphere. The nearby five-arcminute visual alignment limit
is a bound, qualified as rather less, rather than an exact residual or a
statistical uncertainty.

An explicit clock-value reference can cross a dated heading without carrying
the earlier date with it. The March 4 “hour as above” on X p.27 links to the
preceding approximate eight-hour value. Keep the reference wording, empty numeric
components, separate observing group and its own March 4 date context. This
source statement supports the repeated value; proximity alone would not.

An unlabelled table entry can have exact numerical units and unknown attribution.
The 6°27′ under March 3 is preserved as an unassigned angle because the editor
says it belongs to another measurement. Do not attach a neighbouring endpoint,
the printed heading's observing date or March 4's restored 6°20′ by resemblance.

Walther's reported sine values 17, 556, 560, 180 and 593 retain their native
numbers and unstated reference scale. The two reported angular results remain
separate reductions. Neither a modern trigonometric result nor the resemblance
of 17 to 170 authorizes replacing a number or inventing a common denominator.
The measured stellar baseline, source “true” reference and historical calculated
distances also do not supply an automatically applied correction to Mars.

Keep the March 3 longitude from the source's “first point of Aries” distinct from
its longitude “from the equinox.” Retain the literal origin before identifying
its historical frame; an unprinted precession offset must not be supplied merely
to make the two statements agree.

A reported repetition count does not supply the individual readings. On X p.28,
the March 5 account gives four distances and says all were measured three times
with the same result. Preserve four endpoint-specific values and the source
count on each, rather than twelve rows, invented observing times or a numerical
zero variance. Two equal 4°45′ values concern different stars and keep distinct
identities. The restored bracketed 6°5′ has its own manuscript attribution.

The following Saturn series begins after 10½ and finishes later. Its clock and
quality statement do not extend the preceding Mars interval. In mixed-target
journals, an explicit target change can delimit scope within the same named day.

Distinguish a named manuscript restoration from a tentative identification.
On X p.28, the March 16 table omits one star-description word; the note restores
“lowest” from Bartholinus. Keep the recorded endpoint missing and retain the
restored reference with its witness status. This differs from choosing a modern
star by positional agreement. The March 18 note instead says the other fixed
star's name is absent, supplying no identification to adopt.

A visual alignment and a statement that no instrumental distances were taken
can coexist. Preserve the March 18 visual account, approximate clock and the
source's separate statement that Moonlight prevented Mars observations that
evening. Do not turn collinearity into a measured zero or delete one statement
to regularize the account. The nearby lunar measurements retain their own
clock, target and parallax qualifications.

A direction relative to a comparison star does not establish an ecliptic
hemisphere. The March 25 reduction on X p.29 gives latitude 2°42′ without a
hemisphere; the next paragraph places Mars north of a different star. Preserve
the unsigned latitude and the star-relative direction in their separate frames.
Likewise, a distance from that star does not become a latitude difference merely
because a possible conjunction is mentioned.

An unmeasured distance can retain a useful comparison without an invented
number. On March 22 the lowest-nape distance is reported greater than the heart
distance, but not obtained precisely. Keep that relationship alongside the
measured heart distance. The visual limits of March 25 also retain their own
line definitions and directions; “could not reach five minutes” is a strict
limit rather than a five-minute residual or statistical uncertainty.

A dated retrospective reference can identify an earlier calibration despite a
numerical disagreement. The instrument examination on X p.29 names March 3,
Aldebaran and the northern horn of Taurus, but restates 16°53′ where the earlier
entry has 16°55′. Preserve both occurrences and their shared historical report;
they do not establish two independent instrument readings. The date and named
endpoints identify the relationship without selecting by numerical agreement.

Keep the Augsburg and later sextant columns as separate calibration scenarios.
“Here” and “afterwards” do not establish a site or exact date. The source's
one-sixth comparison leaves its reference unit unstated, and the bracketed
instruction to qualify the observations is attributed only to Bartholinus.
Preserve that witness qualification and unresolved application scope before
constructing any historical or modern correction scenario. The heads of Gemini
remain an unordered pair of descriptive endpoints, without assigned modern IDs.

Separate an inferred station from the observations used to discuss it. On X
p.30, the March 28 evening account proposes March 25 or 26 as Tycho's estimate,
while reporting March 28 from Stadius. The source's approximate two-to-three-day
lookback and its three-day motion totals retain different roles. Normalizing a
nominal day interval to source-clock units does not create a stopwatch
measurement, an absolute epoch or an angular rate.

A visual bound can concern a comparison star rather than Mars. The March 31
one-degree limit describes the middle star's displacement from a line through
Mars and the lowest nape star, towards the horizon. Keep that object and line
geometry distinct from Mars's latitude. A repeated note marker can qualify two
restored phrases within one sentence; the qualification follows those phrases,
without extending to every nearby numerical reading.

A retrospective summary can explicitly supply labels absent from an earlier
entry. On X p.31, the March 25, 28 and 31 coordinates state Leo and north.
Retain those source states beside the earlier readings rather than filling
their missing signs or hemispheres. These summaries are reductions, without
new observing clocks or independent raw measurements.

The same examination compares the adopted March 26 stationary position with
Alphonsine and Stadius positions at their different station dates. Its two
reported longitude errors agree with subtraction of those positions. This
checks the printed arithmetic, not model accuracy at a common epoch. The
fragmentary timing statement retains its codex lacuna and witness omission;
neither arithmetic agreement nor a plausible date supplies the missing words.

The April 26 account on X p.34 retains introductory rectified coordinates,
an earlier geometric result and a later bracketed reduction using restored
fixed-star positions. Keep their different labels and hemispheres. The Latin
quotation and its English rendering are two source occurrences of one later
calculation; their repeated numbers are not independent measurements.

The accompanying parallelogram preserves an unlabeled corner in the drawing
even though the prose names its fourth member. Keep that distinction and the
two drawn horizontal lines. Neither the visual equalities nor the layout
supplies an angular zero, calibrated distance ratio, diagonal or projection.
The Saturn separation in the mixed paragraph retains its stated subject and
receives no observing clock borrowed from the preceding Mars account.

A declared reduction pair may not map uniquely to the preceding table's stellar
descriptions. Preserve the stated endpoints, known input links and unresolved
counterpart separately. Numerical agreement or row order cannot complete that
identification. Keep the dependency graph incomplete while that counterpart
remains unresolved.

A limb conjunction can preserve a useful bound without an angular scale. The
February 22 account on X p.42 measures the gap from the lower lunar horn's limb
to Mars in sixths of the apparent lunar diameter. Retain that endpoint and native
reference; a diameter mentioned in October cannot calibrate February. The
nearby lowest-limb altitude is a different quantity. The original February
heading has no year; Dreyer's inference of 1576 from the conjunction remains a
separate editorial date claim rather than an inserted original year.

Distinguish visual and instrumental estimates even within one paragraph.
The October 23 account gives 20′ by eye, then nearly half a degree by the
Radius with a 35′ upper limit. The latter two expressions describe the same
instrumental observation, not independent repetitions. North of a comparison
star is not an ecliptic-latitude hemisphere. The globe coordinates for October
22 and 23 retain their own calculation targets without borrowing the observing
clocks. A location attached to one heading does not establish every nearby
observation's site.

Clock wording and clock association require separate decisions. On X p.45,
“half of the ninth” remains an identified observing-clock statement while its
conversion is unresolved. Preserve its exact words and ordinal-hour context;
neither a numerical hour nor an absolute clock convention follows merely from
recognizing the phrase as time. In mixed-target tables, a clock printed in one
row does not time all neighbouring rows. The February 25 Moon-center comparison
has its own 8½ label, which does not time the preceding Mars distance.

An edition note about an unidentified mark beside a clock numeral remains a
qualification, without an invented fractional addition. Likewise, a supplied
qualifying word can limit a visual geometry claim without changing an adjacent
measured distance. Retain a comparison in units of the Moon's own diameter as
native geometric context when no angular scale is established.

A column break can interrupt a dated entry. On X p.45, the edition explicitly
states that the entry for 1 March resumes in the right column. Bind the resumed
table to that note, the column heading, the original date heading and an
independently selected Mars entry. This supports the date association; it does
not carry the preceding entry's clock into the resumed rows.

The same page preserves `Quadrante poſt` with two interpretations: the quadrant
as instrument, or a quarter of an hour past the named hour. Retain the phrase
and both alternatives while leaving its numerical clock interpretation and
instrument assignment unresolved. An explicit “at the same time” can join rows
to one event even when the event's clock cannot yet be converted. An unqualified
`Eod.` needs its own scope decision and does not by itself establish that the
preceding clock applies.

An alternate distance marked `al.` retains its link to the original reading
without becoming another independent observation. On X p.45, the Mars–Mercury
comparison also has Prutenic and Alphonsine predictions that expressly disregard
Mercury's latitude; the Alphonsine value is a lower bound. Keep those conditions
with the model values. Nearby qualitative agreement in Mars's longitude and
latitude supplies neither coordinates nor a measured zero difference.

When an editor adopts a date but reports a different manuscript date, retain
both claims with their witnesses and the editor's reason. The 12/17 March entry
on X p.45 is such a case. An evening qualification belongs to the explicitly
timed comparison; it does not establish the clock or daypart of every later
comparison under that heading.

A rejected date differs from an alternate date. On X p.46, the marked note says
that two distances were certainly not observed on 20 March, but supplies no
replacement date. Preserve the note's exact marker, its scope over those rows
and their printed placement. Keep the rejected date out of their observing-date
claims; neither a neighbouring date nor the preceding row's clock fills the gap.

Journal order need not be chronological. On X p.47, a lunar paragraph timed at
10h13 precedes a Venus–Mars comparison explicitly timed at 8h25; the following
Mars–Aldebaran and Jupiter–Regulus distances have no stated clock. Keep each
association local. The adjacent lunar-shadow account is a Moon record, even
when broad passage screening selects it beside Mars. Solar-based clock setup
and an author's claim of accuracy do not supply a numerical correction or a
verified uncertainty. A later lunar calculation date does not replace the
planetary observing report's date.

A repetition note across a column break can retain an uncertain subject and
an unsigned variation. On X p.49, “one minute” does not supply another complete
reading, a target or a correction sign. Likewise, an unresolved `mediata 9`
clock stays unconverted, while the explicit `nona cum quadrante` preserves a
native 9¼-hour label. Retain `ARILIS` as printed alongside the reviewed April
date components; the edition's missing-letter note does not authorize rewriting
the source.

An explicit backward reference can connect a planetary reduction to a preceding
eclipse report across its own recap heading. Bind the report heading, the
foregoing-eclipse heading, the stated end of the report and the later planetary
reference. Reject intervening unrelated headings. This admits only each
reviewed block; it does not assign the planet as the target of lunar or solar
calculations inside that report.

Predicted eclipse phases retain their named model, phase and native clock
values. A 13h35 prediction is not silently unfolded into a modern 1h35 epoch.
Keep observation recaps, rectified times and subsequent mechanical proposals
separate. Preserve distinct P.M.N. and P.M.M. expressions without silently
correcting one to the other. A crossed-out note beside a brace requires its
own scope qualification; neither a claim that values are good nor an uncertain
cancellation extent supplies a verified quality judgment about every value.

A book's stated starting year and an individual observation's year are
different source claims. Preserve the title's period and later additions
separately when local day/month headings do not establish an entry's year.
Similarly, an explicitly dated observation of a neighbouring star or planet
does not automatically redate the following planetary series. A shared
twilight brace establishes a condition of observing, not simultaneity or
permission to fill missing point clocks.

An attributed excerpt starts a new observing context. Hagecius's report on
X pp.72–73 does not inherit Hven from the preceding book title, and its adopted
pole elevation does not establish a modern observing site. Preserve ordinal
Aries stars as literal endpoints. A later “same star” with an unresolved
antecedent remains unresolved even if an expected position suggests a match.

The two different Mars longitudes on X p.72 are Hagecius's own reductions and
his own reported discrepancy. Retain both routes and his alternative
explanations without choosing a cause. Tycho's marginal inquiry about Radius
error near twenty degrees supplies an angle at which to investigate the
instrument, not a measured error or a correction to apply.

Two surviving copies of a report do not create two observing series. Likewise,
a repeatedly observed stellar altitude with no stated count or dates remains
one collective assertion. A shared culmination supplies a relative timing
relationship without an invented clock; a longitude assigned to “that year”
does not date the individual altitude observations.

A calculation placed beside a journal list need not belong to its final dated
entry. On X p.84, the small latitude subtraction stands beside three middle
lines. Preserve its true stellar latitude, unlabelled middle term and Mars
latitude without assigning a day or identifying the middle term from numerical
agreement alone. Its unsigned arithmetic can be checked without supplying a
missing celestial hemisphere. A tentative Radius attribution remains tentative.

Historical corrections can have different scopes within one report. On X p.84,
the November 12 prose proposes a three-minute altitude adjustment, while the
assistants' calculation gives a quadrant excess of 4′45″. Preserve both beside
the unchanged raw altitudes. Subtracting the latter excess from 57°24′ gives
57°19′15″; the printed true altitude is 57°19½′. Retain that 15″ arithmetic
difference with the source precision, without assuming a rounding rule or an
edition defect.

A braced original and corrected transit time remain linked alternatives; the
original time still identifies the raw observing event. A later calculation's
10⅚-hour label does not silently replace an earlier 10h48 clock. Keep stellar
labels such as left horn and southern horn distinct where the source changes
them, and distinguish handwriting attribution from the identity of an observer.

A table's calculation epoch can qualify model predictions and an observed
reduced position without becoming an observing clock. On X p.85, link all
three November 17 comparison rows to the stated 10-hour calculation target.
Preserve the single-component latitude forms and their declared major-component
unit convention; no hemisphere is supplied for those rows. The later great
brass globe result has its own explicitly northern latitude and no stated
point clock. Keep its 1°35′ distinct from the table's 1⅗-degree entry, and do
not reconstruct a mean by averaging the model predictions.

The same page expressly identifies the raised double ticks in the stellar
transit times as seconds of time. Preserve those clock components separately
from adjacent angular altitude components and from successive fractional
distance readings.

An observed upper bound and a later construction input can share a number
without being the same quantity. On X pp.85–86, the visual departure is at most
ten arcminutes, while a revised globe construction uses a fixed ten-minute
westward offset. Preserve both scopes, the successive stellar inputs and all
reported Mars results. An optional position described as imperceptibly wrong
remains a source alternative, not another observation or a measured error bar.

The accompanying diagram keys three bodies but leaves its apex unkeyed. Keep
that identity unknown. Its legacy figure marker does not establish the printed
page or a verified scan locator. The later stellar calibration distances carry
a shared twice-with-the-sextant claim, which supplies neither individual
repetitions nor observing dates. An editorial change from theorem IV to IX is
a reference correction, not an angular measurement or an edition error claim.

A shared repetition brace can cover a nominal reading and its upper-bound
alternative. On X p.88, preserve the five distance figure-lines and their
twice/clear-sky qualification without treating the bound as another independent
measurement. Keep each observing clock local. The later stellar transit checks
do not inherit the distance brace's weather or repetition count, and restored
pinnules supply no numerical clock correction. A comparison star's magnitude
class is a reference attribute, not an angular component. A statement that Mars
was stationary on the named day does not supply an exact station epoch or a
measured zero rate of motion.

Bind repeated footnote ordinals to their own parents. In the December 27 entry
on X p.88, the heading's note attributes Flemløse's handwriting; the nearby
struck-through note belongs to the December 25 Spica line. Handwriting does not
establish the observer. A Venus morning heading and a mount-quality comment
cannot qualify later Mars measurements merely because they share a list.

An approximate statement that Mars lay near the middle of a line can accompany
a four-or-five-minute proximity claim without defining its geometric quantity.
Preserve both angular alternatives and the unknown definition, rather than
assuming a midpoint displacement or difference between distances. “About this
time” does not assign the preceding exact clock. Keep each stellar target
literal, including pronouns resolved from source order, and limit an explicit
P.M. qualification and an approximate-altitude marker to their justified scopes.

A time reported as corrected can be retained when its uncorrected original is
absent. On X pp.89–90, the December 29 Mars transit time is tied to a stellar
transit without a stated adjustment amount. The other-codex stellar altitude
is a separate witness variant. Later clock-setting recaps differ by five
seconds from the earlier recorded stellar time; preserve both without choosing
a rounding rule or substituting either value.

The following clock report states a total drift, an elapsed interval and a
correction per reference hour. Keep all three and the native following-noon
qualification. A per-hour amount is not a fixed offset, and its individual
application to later evening observations remains unestablished. Preserve
corrected stellar inputs as historical inputs rather than new raw observations.

An annual section can contain separate solar, lunar and planetary date
sequences. On X p.104, January in the planetary section remains under the
explicit 1581 annual heading even though the preceding lunar section ended in
December. Use that source structure rather than a continuous calendar cursor
or an expected planetary position to assign the year.

Keep a sunrise slow-clock report distinct from a later subtraction at a stellar
transit. Preserve the reported time and subtraction amount without generating
an unprinted corrected reading. A near-collinearity description does not impose
an exact sum-of-distances equation, and an unclocked stellar baseline does not
inherit one of two nearby Mars clocks. Repeat claims, approximation markers and
cloud conditions require their own date and row scopes.

On X pp.104–105, April 22 explicitly separates initially untimed distances
from later retakes made after a timekeeper became available. Preserve each
printed repetition and retake as its own reading, rather than treating the later
values as corrections. The presence of a timekeeper does not supply an exact
clock for every row. A following-midday statement that the clock had not erred
remains a qualitative calibration claim; it establishes neither zero statistical
uncertainty nor an absolute observing timestamp.

On X p.105, May 2–3 retain visual coefficients alongside instrument readings.
The quarter-part comparison leaves its reference whole unresolved; the following
day's three-body-width offset supplies no calibrated angular diameter. Normalize
the stated coefficients separately, preserving their comparison wording and
qualifications. Apparent equality with comparison stars supplies no numerical
photometric magnitude. A following-midday clock report keeps its relative-day
rule rather than acquiring the preceding observation's date or changing its clock.

On X p.174, the November 12 phrase “corresponding declination by computation”
does not name a body, as the edition's note explains. Preserve the computed value
with an unassigned subject; equality with a later explicitly named Mars value
does not establish identity. Keep the separately headed place calculation and
its fractional-hour epoch distinct from observing clocks. Its adopted distance
is not another raw measurement. An azimuth measured westward from the meridian
retains that native frame, and an unstated stellar declination hemisphere must
not inherit Mars's northern label.

On X p.174, November 23 changes comparison stars while continuing the horizontal
coordinate columns. The azimuth heading measures from north toward east; a
later meridian-based heading defines a different frame. The first row's blank
altitude and azimuth are missing readings, not zeros. Preserve an abbreviated
clock's printed minute/second components and its explicit same-sequence hour
link separately. A normalized sub-hour scalar is not a complete clock or hour
zero; the complete contextual clock must retain the hour's source provenance.
The final lesser-quadrant label applies to its altitude reading. Keep the
separate eastern 90-degree wording without assuming a modern azimuth convention.

On X p.175, November 24 morning explicitly changes azimuth from eastward to
westward relative to the meridian. Its labeled meridian altitude does not
redefine the continuing distance column or supply a numerical zero azimuth.
November 25 evening starts a separate north-to-east frame. Preserve each day's
own comparison-star wording: “northern” and “upper” are not interchangeable
qualifications. The evening header assigns the sextant to separations and the
lesser quadrant to azimuth; an adjacent altitude column does not automatically
inherit either label. Minute-only clock entries retain minute precision and
their source-hour links without invented second components.

On X p.175, November 26 prints a zero azimuth beside a blank separation;
retain the zero and the absence separately. The brace marks only the two better
Leo separations. Preserve an unlabelled angular entry's exact components while
its column placement remains unresolved. A clock running “a little more than”
23 minutes fast supplies a lower-bound threshold, not an exact offset. Its
three-day scope and the Corrigenda's “three preceding days” are distinct source
claims, not permission to adjust individual clocks or infer 72 elapsed hours.
November 27's rough solar-transit method qualifies its 6½-minute calibration
estimate; keep that qualification local to the calibration.

For December 3 on X pp.175–176, the edition's note explicitly identifies the
hour/minute and minute/second clock places. Use that evidence directly. The
evening “same day” relation points to the observing-day heading, while the
intervening following-noon report remains a calibration. Preserve its slow-clock
amount as time and its statement that the motion cannot be proportional;
neither an exact several-day interval nor a linear correction follows. Keep the
printed quarter-minute separation and the Corrigenda's half-minute alternative
as distinct source states of one reading, without replacing or averaging them.

On X p.176, December 17 explicitly changes the azimuth origin within one table
from north to meridian while retaining the eastward sense. Preserve both frames
without converting either to a modern convention. The edition notes that the
first azimuth prints only `71`: normalize the degree component without adding
a source minute zero. Its `32·27` altitude retains the degree/minute column
schema and printed separator. Blank separations supply no repeated measurement.

On X pp.176–177, December 26 distinguishes measured separations from recommended
reduction inputs. “Without perceptible error” supplies no zero statistical
uncertainty. The stated 8½-hour epoch belongs to the adopted Aldebaran distance;
the alternative northern-head distance is recalled from an earlier sequence
without repeating that epoch. Preserve dot-separated clocks under their native
unit scheme, the printed clock Corrigenda, the uncorrected-clock warning and the
later four-minute index advance as separate source states. A reported physical
clock reset does not itself replace any earlier catalog time. Keep the
continued model statement's approximate geometry and event antecedent qualified.

On X p.177, December 27's first azimuth and following altitude form one compound
horizontal reading. Separate distance statements later in the list have no
point clock and do not borrow adjacent horizontal times. The nearby-star
visibility warning and relative northward statement remain local; neither
establishes an absolute hemisphere. In the uninterrupted lower-head Radius
series, the second row supplies the endpoint label for the distance phrase
begun in the first. Bind that label explicitly, without choosing it by agreement
in the measured value. The following-noon clock amount keeps the solar-transit
method qualification without an invented numerical uncertainty.

Observing instructions can interrupt a list of actual readings. Preserve proposed
comparison stars, instruments and horizon/meridian conditions as qualitative
context; a stated straight-line appearance supplies no exact zero angle. An
unqualified foot reference stays distinct from a later explicitly lower-foot
reference, even when their numerical separations are similar. Blank table cells
do not repeat the preceding measurement.

A single fractional group in an angular column can occupy the degree place
while the minute place is blank. Keep that component structure, even when a
decimal-degree conversion is exact. Preserve attached clock-note markers and
nonchronological printed clocks without inferring a correction. A nearby
editorial layout note is not automatically the note belonging to such a marker.

Reduction appendices can cite observations while adopting or revising their
inputs. Keep those citations separate from new direct readings, and distinguish
a stated calculation epoch from a repeated observing-clock expression. A later
calculation dated only to a day receives no inherited hour. Retain native zodiac
origins for longitude arithmetic and distinguish latitude suffixes from figure
point labels. Small arithmetic differences can reflect rounding or source
calculation; record the diagnostic without declaring a transcription error.

Link a reduction's cited observation to a log by its date, clock, target and
reference object before comparing measured angles. Keep a meridian-derived
coordinate separate from a later timed separation. A source's “more correct”
value is a distinct coordinate state, linked to the original without silently
replacing it. A codex-attribution note with unstated extent supplies no blanket
witness assignment for the surrounding calculations.

Establish the physical dimension of a sexagesimal expression from the complete
calculation and explicit source conversions. Degree-style notation can express
a fraction of a day in a time proportion; retain the glyphs and document the
contextual unit assignment instead of applying a global notation rule. A named
model's retrogression over an interval is a predicted angular change, distinct
from both an absolute longitude and a residual against an observation.

Preserve a refinement as a complete chain of source states: a revised stellar
separation can change an adopted star's right ascension and then a planetary
right ascension and longitude. Link the preferred results to their originals
without silently applying them. An explicit duration restatement can have lower
display precision than its sexagesimal-day form; retain both numbers rather than
forcing exact equality. A coarse cited clock does not identify a finer log clock
unless the source supplies or justifies that association.

A parallax investigation can begin with coordinate conversion and meridian
geometry before reporting any parallax angle. Preserve those intermediate roles
without supplying an unstated result. Figure letters name points within their
own geometry: the same A or B can denote a star in one construction and a pole
in another. A glyph's display rotation is not a measured celestial angle.

A historical parallax calculated from an adopted planet–Earth distance is a
model-dependent reduction. Preserve the distance's source, units and attribution
alongside its altitude, longitude and latitude components; it is not an
independent distance measurement. A later inserted annotation in another hand
retains its own correction path and terminology. Its preferred coordinates do
not silently replace the surrounding main text or establish the writer's identity.

A distance construction may use arbitrary model lengths before converting them
to terrestrial radii. Retain each scale explicitly: on X pp.201–203, AD = 10000
defines model parts, while ES = 6580 parts corresponds to 1142 Earth radii.
The resulting Mars distance of 721 Earth radii is a historical calculation,
including its displayed rounding. A model side can exceed the reference length;
it is neither a bounded sine nor an angle. The same construction's “parallax of
the orb” is an orbital geometric quantity, distinct from its earlier altitude,
longitude and latitude diurnal-parallax components.

Keep a diagram's printed state separate from a correction to its geometry.
The corrigenda request an F–S connector in the distance figure on X p.202;
this instruction does not mean the printed figure already contains that line.
Uppercase and lowercase point labels remain distinct, and an uncertain
line-through-point description does not supply an exact geometric incidence.

An observing interval supplies two bounds, not an observation at their midpoint.
Keep a separately nominated clock when one is also printed. A phrase such as
“a quarter of an hour after 11” is one clock expression: its explicit addends
support 11¼ native hours while its wording and order remain intact. Neither
interpretation establishes an absolute timestamp.

An observing-night heading can continue from a printed hour above twelve to
smaller hour numbers without explicitly changing its date label. Preserve that
order and the local evening or western-sky qualifications; do not impose a civil
midnight rollover. A clock calibration at the following noon retains its relative
timing and named clock. It does not establish that every earlier timing used that
clock or authorize applying the stated correction to all observations.

A source preference can depend on an ephemeris rather than on a separate
assessment of the instrument. The February 2, 1583 entry on X p.247 favors
four of six Mars separations by comparison with the daily motion in Mästlin's
ephemerides. Preserve all six readings and the stated selection basis; do not
convert this preference into statistical weights or discard the other values.

A transit sequence can abbreviate both hours and minutes, leaving only seconds
in later instrument rows. Preserve those printed components and link each
inherited place to its source anchor. A shared time labeled for two instruments
is one printed quantity; absent instrument altitudes remain absent. An explicit
warning about a mural quadrant's altitude adjustment supplies no numerical bias
and does not by itself invalidate its clocks or other instruments.

On X p.249, the February 19, 1583 comparison reports 1°10′ of forward Mars
motion over thirteen days, exact agreement with Alphonsine motion, and a 25′
shortfall in Copernicus. Preserve the observed extent, duration and model
shortfall separately. The passage supplies neither an absolute longitude nor
a separately printed numerical Copernican motion. Its closing nine-minute
clock error applies to an uncertain number of days; it is not nine minutes
per day and is not silently applied to the earlier readings.

One printed separation described as observed three times supplies one numerical
assertion with an explicit repetition count, rather than three invented rows.
Keep an upper-bound longitude separate from a later approximate reduction.
Model longitudes without a repeated zodiac sign retain that omission, even
when the surrounding discussion makes a shared sign plausible.

A source triangle can reuse an observed separation alongside adopted latitude
complements. Preserve the reused occurrence and the reported result as distinct
calculation inputs and output, linked to the original reading. A cited theorem
does not mean its algorithm has been implemented. Bind a codex attribution to
its printed note and scope; it supplies no additional measurements or clocks.

Spaces can group integer digits in model lengths and trigonometric arithmetic.
Declare that interpretation for the individual scalar; never remove spaces
globally from angles or clocks. Keep an intermediate digit row such as `9065`
separate from a prose result such as `906½`, and preserve the placement of
shifted partial products without inventing decimal marks or column powers.

An instrument comparison can summarize an earlier stellar transit series across
its own heading. Bind each input block by its source date, named endpoint and
comparison heading. A numeric match alone cannot establish that relationship.
Keep tabulated time differences and adopted altitudes separate from the raw
transits, including blank altitude cells and omitted clock places.

An inline proportion can contain literal vertical strokes between its terms.
Preserve their printed order and bind each term within the complete source
line; Markdown separators alone do not establish the physical column layout.
Repeated scale values also need their reference segments: the January 17
construction states both SE = 10000 and ES = 6580 in a BD = 10000 scale,
and its closing distance uses EB = 10000. Retain those labels and the
unresolved relationship between the stated scales without silently replacing
one segment with another.

Quoted observation inputs in a reduction retain their source occurrences and
`historical_input` roles. Their recorded clocks remain distinct from clocks
printed again as calculation epochs. An “about the same time” companion has a
qualified time relationship rather than an invented exact clock. Named morning
and evening labels do not establish a civil-date rollover.

The January 17 parallax calculations on X pp.286–288 adopt a Copernican distance
of 778 Earth radii. Their altitude components are reused as inputs when deriving
the stated latitude and longitude components. Those latter labels refer to the
source's reference-circle construction; an equivalence with modern ecliptic
axes is unestablished. The request to investigate fixed-star refraction supplies
no numerical refraction correction. The embedded editorial report of a separate,
undated distance calculation preserves its rejected result and inferred date
under their own scope.

Keep printed angles and corrigenda as linked alternatives. The original
38°44⅔′ and the correction 38°41⅔′ on X p.288 remain distinct. Changes of
precision between operands and results can produce small arithmetic differences;
record those comparisons without converting them into transcription defects.

A nearby reduction need not repeat the journal's date or adopted input.
On X p.321, the November 13 morning reading gives Mars's declination as
13°54′ north, while the November 12 evening calculation adopts 15°54′ north.
Preserve both occurrences and their roles without silently repairing either.
Likewise, an explicitly corrected calculation clock does not authorize changing
every original clock in the associated observing series.

An explicitly reported clock gain can remain numerically uninterpretable:
XI p.332 gives “7½” without a unit. Retain it as unresolved clock drift, with
no scalar or assumed minutes. The target normalization unit does not establish
the source unit. Likewise, a stellar angle labeled only east or west retains
its subject, orientation and calibration purpose in context without acquiring
a meridian-distance or azimuth interpretation.

In XI p.334, the day column supplies named April dates, while the Tychonic,
Alphonsine and Copernican columns supply distinct calculated positions.
Inherit zodiac signs and northern latitude labels within their stated columns;
preserve the repeated opposition calculation, its noon positions and its
April 13–15 motion interval as separate temporal claims.

Snellius's solar examples distinguish quoted instrumental altitudes from
assumed constants, derived declinations, ecliptic positions, and corrected
alternatives. In the 1568 August 24 example, the source states a trigonometric
reference whole of 1,000,000. Its sine and secant numbers retain that source
scale and their named operations; they are not physical lengths. The 1571
equinox calculation likewise gives an inferred time after noon, not an
independently observed clock reading or a secure absolute epoch. Its printed
Virgo glyph for March 9 conflicts with the date and southern declination; the
printed sign remains part of the evidence. Repeated numerals on one source line
are anchored to their specific textual occurrences. Historical claims about
timing sensitivity are kept distinct from measured scatter.

Bürgi's Kassel solar tables, as published by Snellius, give a useful example
of retaining an inconsistent printed reduction. On the March 26, 1589 row,
34°49′40″ of apparent altitude plus 2′6″ of tabular parallax yields
34°51′46″, while the printed true altitude is 44°51′46″. The edition's note
identifies the arithmetic conflict. Catalog the printed readings and their
different roles; a calculated replacement belongs in a separate analysis.
The first 1588 apogee example also gives eccentricity in sexagesimal parts of
a semidiameter of 60, rather than an angular eccentricity. Preserve its native
scale and notation when interpreting it.

Snellius's closing Kassel and Bohemian solar summaries publish selected
observations alongside the reductions used to investigate the solar apogee.
The same date can appear both in a journal and in a later summary. Preserve
each publication occurrence, link supported repetitions, and avoid treating
the printed summary as an independent measurement. A source correction to
altitude, the resulting true altitude, a derived declination, and a tabular
prediction have separate roles. The Benátky summary explicitly says Gregorian
style for 1600; its subsequent Prague 1601 heading does not restate the
calendar. Retain that difference until the date convention is established.

Regiomontanus and Walther's Ptolemaic-ruler logs report chords of zenith
distance as native instrument counts. Store the count without treating it as
degrees. Regiomontanus's table states a whole sine of 100,000 across two
adjacent rows; Walther's heading does not restate that scale. The appendix also
starts a new foliation: its first recto is unnumbered, while subsequent rectos
bear successive folio numbers. A bare eclipse altitude of “25” remains
unit-unresolved. Printed date order and qualifiers such as “doubtful” belong
to their source rows, even when the dates are not chronological.

The ruler tables print two parallel blocks per physical page. Their linearized
edition can span many source lines before the next page turn. Establish each
recto and verso boundary from the page's own first row, then bind the folio;
do not estimate a boundary from the number of rows. A page-locator correction
changes the bibliographic binding while preserving the recorded reading and
its numerical interpretation.

Walther's entries can give different instrument settings on the same stated
day. Keep the separate readings in one observing group, with each setting
attached to its own source row. “Likewise” alone does not establish an exact
day. A chord cell printed as two alternatives, such as `54900 / 54910`,
contains one source occurrence with two linked values; the second is an
unapplied source alternative, and the choice remains unresolved. An armillary
ring reading under the chord heading retains its stated instrument and the
uncertain Libra qualifier rather than inheriting the ruler method.

Schöner's worked account of Walther's 1475 Mars–Saturn observation separates
the staff's two measured linear parts from the angular separation obtained
through a Gnomonic table. The resulting “about 14°35′” is a derived,
approximate angle. The second and third hours after midnight define a
reported observing interval, not an established absolute timestamp. Repeated
mentions of the same staff parts in the worked arithmetic are explanations of
the inputs, not new readings.

The Melk 1457 lunar-eclipse account reports two altitudes of the same Pleiad,
then computes phase and opposition times from them. Keep the two altitudes in
one eclipse group; subsequent repetitions are inputs to the reduction. The
Vienna multiplication aid and sine values are historical calculation data,
not direct sky readings. “After noon” supplies a source clock origin but does
not by itself establish an absolute timestamp. The derived times and the
Alphonsine prediction have different roles.

Retain printed arithmetic conflicts. In the eclipse account, 11h49m minus
10h24m is 1h25m, while the page prints 2h25m; the next half-duration follows
1h25m. The edition notes this discrepancy. Another note observes that the
printed heading over the Sun's `4. 3.` declination says minutes and seconds,
although degrees and minutes may be physically intended. Preserve the
edition's literal notation and record the alternative as an interpretation
question, without silently changing units.

The July 1460 partial-eclipse account explicitly separates times from unnamed
tables for the Vienna meridian from what the observer saw. Its “four digits
and something more” is a lower bound on a visual estimate; the Moon's
15°18′ apparent altitude at the end is a direct reading. The 0°52′ altitude
parallax, 16°10′ true altitude and later 10h20m end time are steps in a
historical reduction. Retain the unlabelled `2. 56.` ecliptic-points value and
`0. 1. 31. 5.` lunar argument without assigning physical units. A printed
product split by a vertical bar also remains one unresolved expression; the
edition's arithmetic note can be cited without replacing its digits.

The December 1460 Vienna eclipse has three measured Alramech altitudes and
two qualitative alignments of the Moon with stars. Treat these as one eclipse
session. The subsequent page-spanning calculation repeats the altitudes and
derives phase times; the repetitions are historical inputs, and the times are
inferences in the printed after-noon or after-midnight convention. An
uncertain Scorpio sign at the star's culmination does not establish a full
zodiac longitude. The calculation also prints a whole sine of `6000` beside
an editorial `60000` correction, barred products, and an impossible-looking
`178137` in a sine calculation. Retain each printed form and its source note
without selecting a replacement from expected arithmetic.

The 1461 reports separate observed eclipse altitudes and visual planet
separations from inferred times and tabular predictions. The June lunar
opposition is inferred after midnight; the unnamed tables supply a different
time with the same local label. For the December Mars–Saturn comparison,
the 27th-degree star and Mars positions depend on the stated eighth-sphere
assumption, while the roughly 2° visual separation remains approximate.
Clouds on December 5 yielded no usable reading. On December 14, the printed
Venus–Saturn difference of 15′ conflicts with the difference between the
printed longitudes 1°51′ and 0°24′. Keep all three values with their roles
and the edition note, without substituting the arithmetic result. The
December 17 lunar-eclipse report distinguishes a predicted ten digits from
eight seen; its damaged `2[?]°` Aldebaran altitude has no scalar value.
None of these local time labels establishes an absolute observing timestamp.

The December 24 Mars conjunction with a Capricorn-tail star is qualitative;
the star's 14°29′ Aquarius position is expressly doubted, and the 17°20′ Mars
position belongs to an unspecified book calculation. The printed 2°51′ lag
is a comparison, not another observed separation. In the 1462 January
entries, a visible Mercury sighting has no measured angle, while Venus has
an estimated 45′ eastward offset from a described Aquarius star. The bare
`2 3` beside that star has no established unit or meaning. Neither those
entries nor the adjacent solar meridian altitudes restate an observing site.

The December 1461 eclipse calculation repeats Alhajoth's 38°30′ altitude
from the observing report as an input; it is a separate printed occurrence,
not a second measurement. Its 48° equinoctial altitude complements the
adopted 42° Rome pole elevation. Preserve the 93° declination-plus-equator
sum as a calculation angle, and retain the printed sine values in the
stated 60,000 radius scale rather than recasting them as sky angles.

The same reduction prints a ten-row multiplication table for Rome's
permanent multiplier. Its first product is `134502`, with an editorial
`134562` correction; the Aldebaran rule later prints `199302000`, with
an editorial `1993020000` correction. Preserve the printed products and
their notes. Aldebaran's reduction starts from `29°0′`, while the earlier
observing report has the unresolved literal `2[?]°`: the later input is
evidence for interpretation, not a replacement of the earlier source
occurrence. The two stellar reductions give solar meridian distances
81°6′ and 80°11′; the source adopts 80°38′ and claims a time error
under two minutes. Its 0h54 result after sunset and 1h56 tabular value
remain distinct, with the printed 1h2 difference. None supplies an
absolute observing timestamp by itself.

The 1462 Viterbo lunar-eclipse report is a mixed source: clouds prevented
the beginning and end from being observed, the middle was estimated, and
“nearly seven digits” is a visual bound. The tables separately give “6
points 34 minutes.” Preserve its literal sexagesimal point notation until
that unit is normalized explicitly. In the following reduction, bare `480`
has no secure unit, and `594687` is printed as a sine while the neighboring
rule uses `59487` with radius 60,000. The source values remain separate
from arithmetic or editorial corrections.

Regiomontanus's later 1462 reports use visual ratios of distances and
apparent diameters. Preserve the ratio and both named comparands: a
Venus-diameter gap, a solar-diameter offset, or a comparison with the
previous night's distance is not an absolute angle. His November solar
eclipse has a direct two-digit visual magnitude, two Sun altitudes and a
westward azimuth; the beginning was not observed. The 1464 lunar-eclipse
prose gives April 21, while its phase table prints “Day 12” for the
middle. Keep separate date contexts rather than silently reconciling them.
The table's `13 points 27 minutes` still needs an explicit scalar-unit
normalization rule; it is distinct from the observed star altitudes.

The July 1471 Mars report compares positions obtained from different
stellar catalogs. Preserve each branch with its stated inputs and
discrepancies. A coordinate called “true” by the author remains a historical
reduction, not an additional instrumental reading. The September report
records Mars–star distances as `210. 674.`, `210. 662.` and `30. 1297.`.
The prose identifies separations, but does not establish the numerical
units. Retain these expressions without interpreted components or scalar
angles. The statement that another stellar distance was equal is a
relationship, not another independently recorded number.

The January 1472 comet report also contains unlabeled pairs, `953. 190.`
and `953. 210.`, between descriptions of the comet and comparison stars.
Their attachment to individual stars is uncertain. Preserve each as a
recorded numerical expression with neither a converted value nor an
assigned comparison star. Keep the report's alignment, visual ratio,
tail direction and after-noon clock as distinct contextual evidence.

Walther's 1475 rectangular-instrument tables name their numerical columns
“first sine” and “second sine.” Preserve both native readings and their
column labels within one comparison group. Neither column is an angular
degree or minute component, and no unit-radius sine or angular separation
is supplied by the column heading alone. Exact printed fractions remain
exact native values; numerals with unresolved digits or denominators have
no scalar value. A row stating that a previous stellar interval was
assumed supplies a dependency, not another measured number. Likewise,
“two intervals” does not identify endpoints that the source leaves unstated.

Retain inherited after-midnight intervals as intervals. In the September
1475 Mars–Saturn narrative, observations on the 17th, 19th and 20th support
the author's inference of conjunction on the 18th, when clouds prevented
observation. The Almanac's prediction for the 21st is a separate claim.

Walther's October 1477 report explicitly converts a native instrument
reading into an approximate angular separation and then states an error
against unspecified tables. Retain the instrument components, derived arc
and tabular discrepancy separately. His April 1478 Moon–star comparison
gives an eastward interval greater than half a degree and less than one
degree, alongside an approximately one-degree southern offset. Export the
two bounds and the approximate offset with their qualifications, not an
invented midpoint. Locally unnamed eastern and western comparison stars
retain those relative labels; a star provisionally called the tenth of
Virgo retains that qualification rather than acquiring a confirmed identity.

The October 1478 Moon–Heart of Leo report distinguishes an approximate visual
half-degree separation from a later instrument reading of `20 | 610`,
which the author reduces to 1°52′. Preserve both observing contexts: the
first clock has an unresolved fractional component; the second is half an
hour before sunrise. Do not treat the two values as competing transcriptions
of one reading. In November 1481 Walther reports taking a Saturn–Mercury
measurement without printing a numerical result. Preserve the reported
event and the missing value; the nearby conjunction claim remains an
inference from surrounding positions.

Walther's January 1484 Mercury experiment distinguishes the clock's stated
56-tooth wheel from the observed one complete turn and 35 additional
teeth. Preserve `clock_wheel_teeth` as calibration information,
`clock_complete_turns` and `clock_additional_teeth` as recorded counts,
and the printed 1h37m rising-time difference as a separate reduction.
Keep Mercury's horizon contact and the appearance of the Sun's center
as the stated endpoints. Do not replace the printed duration with a new
calculation from the counts.

Occultation reports can contain predictions that the author subsequently
withdraws. In January 1482 the expected southern-horn contact is later
called implausible; clouds prevented observation of ingress. The later
northern-horn configuration and the altitude at an estimated middle phase
remain separate evidence. Preserve a schematic's stated orientation and
phase labels without turning its layout into measured coordinates.

Walther’s March 1489 armillary comparisons distinguish positions obtained by
solar alignment of the ecliptic from those obtained with the latitude circle.
Preserve the separate configurations and readings; their disagreement is not
itself a transcription error or an independently measured refraction correction.
His subsequent account prefers observations using a plumb line and explains
why a noon solar position advanced to sunset does not fully remove the problem
(Snellius, *Observationes Hassiacae*, printed folios 35–36). A star position
established using an adopted Venus position retains that calibration dependency;
the adopted position is an input, not an additional observed coordinate.

Native instrument notation can remain numerically unresolved even when every
character is clear. Walther’s March 18, 1489 sine reading `79,2⅜` is retained
without choosing a decimal interpretation, component split or scale
(Snellius, *Observationes Hassiacae*, printed folio 36). Its unresolved status
qualifies the numerical interpretation, not the quality of the transcription.
The surrounding solar reductions remain separate source-stated results.

An observing log can state clock readings and an elapsed duration that disagree.
Walther’s February 14, 1491 entry gives 4 and 7 hours after noon but describes
two intervening hours when discussing the motion of Venus (Snellius,
*Observationes Hassiacae*, printed folio 37). Retain the two clocks, the stated
duration, the initial stellar coordinate and the motion-adjusted coordinate
separately. This is a source-level qualification, not permission to replace
the duration with subtraction of the clocks or to count the adjusted coordinate
as another independent observation.

A source-stated instrumental precision is a historical claim, not a measured
standard deviation. Walther's December 12, 1503 statement that precision is
not to be sought within roughly ten arcminutes is retained as
`stated_angular_precision`, with its approximation and instrument context
(Snellius, *Observationes Hassiacae*, printed folio 41). It is not applied as
a correction or automatically assigned to each neighbouring observation.
Source assessments such as “most careful” and “not to be given much weight”
also remain qualifications rather than invented numerical uncertainties.

## Ordinal degrees with explicit source support

A coordinate described as minutes within a numbered degree can use ordinal rather than completed-degree notation. Preserve the printed ordinal as an `ordinal_degree` component. Conversion requires a reviewed, literal supporting coordinate in the same edition; it must agree in minutes and zodiac sign and explicitly supply one fewer completed degrees. This is a source-bound interpretation, not a general rule for every ordinal expression.

For example, Snellius’s account of the 1457 Melk eclipse (folio 12 recto–verso) gives the computed Sun at 48′ of the 20th degree of Virgo and later states 19°48′ of Virgo. The normalized record retains ordinal 20, 19°48′ within Virgo and 169°48′ from zodiac zero. These are two publication occurrences of the same supplied position, not independent observations.

## Quantities printed across adjacent table cells

When a single time or coordinate spans adjacent physical columns, retain the complete literal span and an explicit ordered `source_columns` list. The compiler checks that the columns are consecutive and that their combined source text exactly matches the expression. Component units come from reviewed table headings. Separate hour and minute columns can therefore form one time without converting the table to prose or treating the components as independent readings. The column list survives the public projection alongside the original components.

## Angular thirds and fourths

Sexagesimal angular places continue below the arcsecond: a third (`‴`) is 1/60 arcsecond and a fourth (`⁗`) is 1/3600 arcsecond. Preserve these as `arcsexagesimal_third` and `arcsexagesimal_fourth` components with exact rational values. A fraction following the final printed unit remains an explicit addend to that component, rather than being dropped or promoted to a new place. These angular places are distinct from sexagesimal fractions of a day.

The printed daily motion in Brahe’s *Progymnasmata*, p. 13, is `0° 59′ 8″ 19‴ 43⁗ ⅔`: the last component is 43⅔ fourths. Its normalized unit is arcseconds per source day. This conversion preserves the printed calculation; it does not establish observational accuracy at the smallest written place.

### Instrument counts and native feet

Instrument dimensions in feet remain source scalars qualified by `instrument_dimension_feet`; no modern length conversion is implied. `instrument_count` identifies a whole-number count of instruments, distinct from component counts and independent observing sessions. Preserve bounds and alternatives in their source context. Stated fractional-minute precision is a historical capability claim, not a standard deviation.

### Reviewed integer digit grouping

A native chord or sine can be printed with irregular spaces between digit groups: `18 22 58 68` denotes the integer 18225868 when the calculation explicitly establishes an integer radius scale. Preserve the literal and declare `source_number_grouping=spaced_integer_digits`; this is never inferred for angular or sexagesimal quantities. `comma_thousands` accepts complete three-digit groups only. These declarations reject mixed fractions, unit marks and partial matches. The reference radius and the source role remain separate metadata.

Whole native lengths can use the same declared comma grouping with a single
`source_part` component. Retain the source's scale and dimensional meaning in
bounded context: a native pace, a construction length and a squared length are
different quantities. Squared terms remain arithmetic scalars, and native paces
or German miles acquire no SI conversion. An uncertain ratio operand such as
`⟦33/53⟧` preserves alternatives, empty components and no scalar; it is not the
rational fraction 33/53. Keep such operands separate from following complete
values and from any attempted reconstruction of the historical calculation.

The Progymnasmata apogee example prints `1068·57 [106857]` for a model distance. The explicit equivalent permits `source_number_grouping=middot_integer_digits`, preserving the native expression and its eccentric-radius scale. This declared integer grouping rejects decimals and fractions. It does not apply to the following perigee example's `52 semidiameters 25′ [52·25]`, whose second component denotes sixtieths of an Earth radius. A middle dot alone does not establish either interpretation.

### Counterfactual distances and native units

Printed corrigenda are separate publication occurrences. Preserve the target
folio, side, line and sub-entry as stated, with the correction unapplied until
a source-supported target link is established. A corrected component need not
supply a complete coordinate. Keep unresolved numerals and field meanings
explicit; a known word numeral does not establish its physical unit. Page
references are not measured quantities, and an index entry is not a new
observation. A section separator can occur within a leaf, so page alignment
must follow the documentary evidence rather than counting separators.

For a correction group, its exported subject summarizes the subjects of its
quantities when they agree; mixed or purely verbal corrections retain no single
group subject. The original review remains available in processing evidence.
Correct extraction classifications through fingerprinted, source-bound decisions,
preserving the literal, components, numerical interpretation and identity.
An unidentified calculation must not acquire a celestial body from nearby prose
or from the expected value of its correction.

Preserve native paces separately from miles. A source that gives a distance in
miles without identifying their convention retains unspecified miles; geography
or agreement with another number cannot establish German or ordinary miles.
Likewise, an exact count of paces establishes no modern physical length.

An explicit three-place slash sequence can be reviewed as postfixed minutes,
seconds and thirds: `19 /6 // 1 ///` then denotes 19′6″1‴. This is an opt-in
interpretation, not a general rule for slashes. Preserve the qualification when
an edition presents it as a construal of irregular spacing. Ordinary fractions
and incomplete slash sequences do not acquire this interpretation.

The technical term “face” can denote a zodiac decan. Preserve the named sign and
ten-degree sector without inventing a point longitude. The first face of Taurus
therefore retains both its within-sign range and its range from zodiac zero;
neither is a statistical uncertainty interval. Literal ordinal wording and
source-bound sign evidence are required. Unsupported scalar conversion does not
mean that the sector itself is uninterpreted.

Historical distance arguments can tabulate what a star's apparent separation
would be at an assumed lunar, solar or Saturnian distance. Read the surrounding
argument before assigning roles: a column headed as an observed distance can
still contain counterfactual calculations. Keep the distance assumptions, upper
and lower transit cases, repeated adopted coordinates and calculated differences
distinct from raw readings. An unchanged instrument setting or a claimed
detectability threshold does not supply a measured zero parallax or a statistical
uncertainty. Preserve source disagreements and explicit editorial alternatives
without correcting one from another.

Native geometric lengths retain the declared radius scale even when a queried
numeral remains unresolved. Degree and minute marks can instead denote linear
parts and sixtieths when the source explicitly defines a length unit; that
definition requires local evidence. Reported year and month counts, including
lunar months, remain native durations without an assumed conversion to seconds.

For lunar-parallax worked examples, preserve upper and lower limbs, horns and
the center as distinct subjects where stated. A limb reading, a center derived
from it, a refraction term and a corrected center are separate quantities. Keep
the recorded clock and date linked to the example without inventing an absolute
epoch. A source comparison with Copernicus can retain a difference in parallax
or angular diameter together with which result is larger; the difference is not
another measurement. Approximate, lower-bound and upper-bound wording survives
the exact conversion of its printed magnitude. A latitude's stated hemisphere
does not establish a declination's hemisphere.

### Overlapping lunar tables and worked eclipse examples

Overlapping table panels retain separate source occurrences at their shared arguments. In the Progymnasmata lunar refraction table, the two entries at altitude 15° give 8′9″ and 8′0″. The queried second-panel entry at 30° remains unresolved even though the following panel supplies a complete value at that argument. Neither continuity nor agreement with another panel supplies missing digits.

The lunar hourly-motion table (printed p.128) records angular rates in arcminutes and arcseconds per source hour. Its paired left and right anomaly arguments and upper and lower panel labels remain distinct. The printed 54′36″ entry and irregular right-margin labels are preserved without smoothing. In the synodic table (printed p.129), adjacent sign and DMS cells form one angular field; the field labeled lunar latitude is a latitude argument. Common/leap-year day counts and synodic durations are supporting calendar and model quantities, not observing epochs. The December argument's 74-second component remains unresolved rather than being carried or replaced.

The apogee and perigee accounts distinguish source-reported parallax inferred from observations from the parallaxes obtained through the tables. Preserve both, their clock qualifications and their different values. Likewise, keep a refraction example's claimed difference even when subtraction of its listed coordinates would give a different final second. Such source calculations do not establish independent raw measurements, modern parallax detections or statistical uncertainty estimates. Later eclipse worked examples are predictions unless the source separately records an observation.

The eclipse examples express obscuration in native digits: `10 digits 55′ 6″` and `9.34′ 52″` have sexagesimal subdivisions. Their exact values remain in `source_eclipse_digit`, with an explicit `source_extent_unit=digit`; the latter expression is not a decimal. A twelve-digit diameter stated as an input remains an input. Angular semidiameters, digit extents, angular motion over an interval and hourly angular rates retain separate meanings.

Clock shorthand also needs its own interpretation. The lunar example's `6 hours 55″` does not establish a missing minute component; preserve the expression without a scalar rather than completing it from the preceding arithmetic. The printed four-day half-month and fourteen-day emendation remain linked alternatives. In the solar example, preserve the recorded Moon label and Scorpio signs beside the proposed Sun and Capricorn corrections. These corrections do not create new observations. Source disagreements in phase times, total durations and diagram radii remain visible alongside any explicitly attributed editorial alternatives.

### Venus as an intermediary for stellar calibration

The Progymnasmata's first three selected determinations pair daytime Sun–Venus measurements with nighttime Venus–star measurements. Each determination includes observing clocks, separations and coordinates, followed by calculated differences of right ascension, parallax/refraction terms and motion between the observing times. Preserve those roles and their shared session dependencies. An equatorial difference is distinct from the measured great-circle separation.

For the February 1582 sequence, the source prints a daily equatorial motion of `0° 0′ 57″`, although its later increment implies minutes. Retain 57 arcseconds per source day alongside the stated increment and discrepancy. Likewise retain both reported altitudes, 27½° and 27⅓°, and leave the separately queried declination fraction unresolved. These are source qualifications, not new findings of translation error.

The final stellar ascensions refer to the completed year 1585. Preserve that native reference epoch and the stated year/month transfer counts without supplying a modern timestamp. More than a hundred observations are mentioned, while fifteen determinations are selected for publication; those counts do not create catalog observing groups. In the preceding clock discussion, Mercury/quicksilver and Saturn/lead denote terrestrial materials and analogies, rather than planetary observations.

The following paired morning/evening collations deliberately omit individual parallax and refraction corrections, on the author's assumption that suitably matched conditions allow the effects to correct one another. Preserve that scenario and the final adopted ascension without treating the corrections as zero. The printed differences and half-differences are parts of this historical comparison, not confidence intervals. Armillary observations of equatorial differences remain `right_ascension_difference` readings; sextant sky separations remain `angular_separation` readings.

Preserve unusual source labels as well as figures. In the second collation the source calls one input right ascension that of Venus, despite its position after the solar longitude; it also explicitly names the Sun in the 53½′ daily equatorial rate. Neither target is reassigned from the subsequent arithmetic. Unpunctuated `AM` and `PM` retain their source spelling and before/after-noon meanings without establishing a clock origin or absolute epoch.

The later Venus collations preserve disagreements between headings, observing
paragraphs and retrospective tables as separate date claims. An observing date
and a stellar reduction's target year serve different roles. Likewise, a printed
degree rate with a minute correction retains both unit interpretations, and a
queried Virgo/Scorpio sign retains both candidates without an absolute longitude.
The fifteen-entry recap reports earlier determinations; its rounded values and
dates remain distinct publication occurrences and do not create new observing
sessions. An equivalent clock notation, such as 8 h 40 m and 8⅔ h, also refers to
one source time rather than two observations.

The following four-, six- and eight-star circuits reuse observed distances and
declinations in historical reductions. A table entry, a triangle input and a
summary angle remain distinct source occurrences even when they describe the
same star pair. Preserve discrepancies between them. A near-complete equatorial
sum, and the author's claim that it establishes instrument reliability, do not
independently establish accuracy or an uncertainty interval.

Keep the six-star table's unresolved distance fraction and the explicitly
unsettled triangle angles without adopted scalars. The closing declination's
printed `28 2/1` and its separate `28½` correction retain their respective
components; neither agreement with the opening row nor the closure calculation
licenses a replacement. Adjacent degree/minute columns retain their physical
column bindings. The subsequent nine-row coordinate table includes the heel of
Gemini from the six-star circuit and is complete as printed; its completed-year
1585 label is a reduction target rather than an observing epoch.

In the ensuing equatorial-to-ecliptic reductions, retain the printed sides,
angles and coordinates without replacing a result by a newly computed
complement. If the prose explicitly adopts one stated angle as the longitude,
that numerical occurrence can carry the coordinate interpretation with its
geometrical meaning retained in context; it is not a second measurement.
Approximate results keep their qualifications, and a bracketed hemisphere
remains distinct from an explicitly recorded hemisphere.

Pollux illustrates why prose, table and correction witnesses remain separate:
the prose gives latitude 6°58′ north, the summary prints 6°58′ south, and the
book's errata give 6°38′ north. The later marginal hand copies that erratum.
These are source occurrences and unapplied corrections, rather than four
observations or permission to replace the printed table. Spica's longitude also
retains its prose fraction and the table's bare minutes as separate readings.

The Spica–Draco investigation reports stellar separations measured repeatedly,
including angles greater than a quadrant. Keep those reports separate from
their restatement as triangle inputs and from the resulting coordinates. An
unnamed instrument's claimed range does not identify it with the astronomical
sextant explicitly named for another pair. The clear-air and near-meridian
qualification belongs to the stated Spica–Draco observations; it does not
establish zero refraction throughout the calculation series.

Draco's first tabulated longitude omits its zodiac sign. Later Virgo-labeled
results do not supply that missing origin automatically. Similarly, “around the
beginning of 1586” dates Spica's altitude report at year-level precision; it
does not date the independent pole calibration or establish a civil midnight.
The author's comparisons in seconds and claim of sub-minute precision remain
historical statements, rather than modern statistical error estimates.

The *Progymnasmata* comparison on pp. 220–223 quotes Copernicus and Werner,
recalculates their reported declinations and longitudes, and compares these
with Brahe's retrospective positions for 1515. Keep the reported observer,
publication author, independent pole calibration and calculation epoch
distinct. Brahe's criticism of Werner is an attributed historical judgment.
Unmarked middle-column latitudes remain unsigned, and the final Southern Pan
latitude's unexpanded S does not acquire a hemisphere from another column.

In the twelve stellar examples on pp. 227–230, two flanking reference stars
provide two separations from the principal star. The row label identifies a
reference, while the adjacent computed ascension belongs to the principal
star. Read those relationships from the block's method, not from row alignment
alone. Declination bands change from north to south and back; explicit letters
within a cell override the band. Preserve the source's adopted ascension even
when it differs from the exact mean of the two computed values. The prose,
example tables and twenty-one-star recap are distinct publication occurrences,
not independent observing sessions.

Scope direction conventions to their evidence. The recap on p. 232 explicitly
uses S for northern latitude and M for southern latitude. This does not resolve
the unexpanded S in the earlier Werner comparison. Keep the recap's printed
Virgo sign for the Northern Pan beside its unapplied Scorpio correction, and
the Gemini-foot example's printed two-degree longitude beside its separate
three-degree correction. Later-hand entries copying the book's errata retain
that relationship and any uncertainty about the underlying print; numerical
agreement does not make them independent witnesses.

Native sexagesimal lengths retain only the components printed. A length ending at a fractional part-minute is normalized exactly without adding a recorded part-second; `least_component_unit` identifies its last written place. Missing places contribute zero to arithmetic only, without adding source components or implying finer precision. A difference stated only in native seconds retains that single component; it is not an angular arcsecond.

Degree and minute marks can also express sexagesimal lengths. In the *Progymnasmata*, printed p.632, the gnomon calculation writes a shadow as 76°43′ on a scale with the gnomon equal to 60 parts. Preserve it as 76 length parts and 43 first sexagesimal places, using `source_sexagesimal_length`; it is not a sky angle. Keep the separately stated shadow/gnomon ratio and fractional excess even when they disagree. The source's scale and attribution determine the quantity, rather than the shape of its unit marks alone.

Higher angular sexagesimal places extend through `arcsexagesimal_tenth`, which is 1/60⁸ of an arcsecond. These are written computational digits, not claims of observational precision. When column heads are absent and their units are undetermined, retain the ordered numerical components without assigning those places or producing a scalar. An incomplete printed page numeral likewise remains unset: retain the source PDF page and distinguish the literal print from a later handwritten page label.

A printed degree component above 30 within an explicitly counted or named zodiac sign is retained with `normalization_issue=degree_outside_sign` and no adopted scalar. The known components remain available; they are not silently carried into another sign or replaced from the table's progression. The historical 30° endpoint remains valid: 30° Aries retains its within-sign magnitude and separate 30° zodiac-zero longitude; 30° Pisces retains a full longitude of 360°. Any positive lower component beyond that endpoint remains unsupported. A queried editorial reading is preserved separately and remains unapplied.

House tables can supply astronomical coordinate calculations without supplying
observations. Preserve their latitude, obliquity, house designation and column
sign conventions. Their time-from-noon lookup arguments and interpolation
durations are separate calculation quantities, without invented observing
epochs. A sign-only cell records a column transition; it does not supply a
written zero-degree magnitude. A queried interpolation duration retains its
literal expression and time unit without an adopted scalar.

In worked house calculations, distinguish the observing site's latitude from
the constructed polar elevations of individual house circles and from the
integer latitudes used to enter a table. A value called a latitude in that
lookup is not necessarily another site's latitude. Keep right and oblique
ascensions, ecliptic coordinates, angular interpolation increments and time
arguments separate. Native sine integers retain the stated whole-sine scale;
they are not angular readings or unit-radius trigonometric values.

A diagram label and its translated expansion represent one printed numerical
occurrence. Capture one value and retain the parallel notation as context.
Separate figures depicting different methods remain separate calculation
occurrences, with no implication of independent observations. Preserve
unattached glyphs and doubtful label associations explicitly. A crowded run of
four numerals does not establish either two coordinate pairs or four
sexagesimal places; leave its grouping unresolved. A parallel calculation must
not supply missing diagram components or settle a questioned digit.

A written fractional hour such as “hour 1 with a sixth part” can use the shared
word-number and component-addend rules. Preserve that literal alongside its
exact conversion and any separately printed equivalent clock expression.
Agreement between the two forms does not create another observation. When a
unit abbreviation conflicts with the surrounding explanation, preserve the
literal and an unresolved interpretation; the expected arithmetic result does
not establish the missing unit or authorize a correction.

An attached editorial footnote number is not a numerical component. Bind the
coordinate or interval literal separately from its note marker, retain the
attachment, and capture the note's relevant numerical claims separately.
Neither the marker nor a proposed correction may silently enter the recorded
value's arithmetic.

The *Progymnasmata* lunar table headed *In Horis et Minutis*, printed p.14,
uses the same left-panel figures twice: H/G-M-S for hour arguments and
Mi/M-S-T for minute arguments. The catalog's primary left-panel view follows
the hour band; its contexts retain the alternate argument unit and component
mapping, including angular thirds. These uses do not create additional
measurements. The right panel is a minute continuation with M/S values,
as its native heading establishes. Blank or faint places remain unfilled.

In the lunar prosthaphaeresis tables, retain the column operations separately
from the tabulated magnitudes. Bare-integer elongation and eccentric columns
whose headings establish neither a physical unit nor a scale remain native
table scalars; numerical resemblance to a model parameter does not supply a
unit. Preserve an entry written `00` as such, even when its exact native value
is zero. Interstitial differences belong to the interval between adjacent
arguments; their placement against the lower row does not make them point
measurements. A queried component remains unresolved, and apparent arithmetic
inconsistencies do not authorize replacement from adjacent rows.

A proposed correction to a native lunar table scalar remains linked to its
printed original and explicitly unapplied. A queried proposal such as `97938?`
retains no adopted scalar. A printed angular expression containing 81 seconds
likewise remains unresolved; the catalog does not silently carry it into
minutes or substitute a suggested 18 seconds.

A historical calculation time written in days, hours and minutes can retain
that native day count with the role `calculation_epoch` and explicit
non-observing qualifications. Its exact conversion to seconds does not identify
a calendar date, day origin or absolute epoch. Keep the observing date and clock
as separate source claims, including conflicting clocks in repeated accounts.
The lunar example of 1587 August 18 prints both 17h25 and 7h25 after midday;
neither account silently supplies a corrected timestamp for the other.

Keep a lunar position in its own orbit distinct from its subsequent ecliptic
reduction. A written sign name can establish a narrowly bound coordinate frame
without a zodiac glyph. A letter-shaped numeral such as `398S` remains
unresolved; retain its proposed replacement separately and unapplied. A
replacement seconds component is not a complete corrected longitude when the
original full expression remains unresolved.

An edition can complete a digit within a numerical token, as in `5[4]′ 23″`.
Declare that literal completion explicitly: it supplies 54 in the stated
component while preserving the brackets in the original expression. This rule
does not accept queried digits, replacement numbers or partial matches inside
larger tokens. Compilation and export independently check the resulting
components and their units. Proportional minutes remain coefficients on their
stated sexagesimal scale, including the endpoint 60′ 0″; they are distinct from
angular and clock minutes.

A latitude table may reuse one unsigned entry under different north/south
banners and forward/reverse arguments. Retain the printed banners and their
editorial interpretation separately; selecting a signed coordinate requires
selecting the applicable branch. In the *Progymnasmata* table, the expansions
of A/D as adding/subtracting and of bare banner numbers as sign arguments are
editorial qualifications. Preserve a correction interrupting a numerical cell
through ordered source fragments, keeping the original components and the
linked, unapplied replacement distinct.

Keep native sine integers separate from decimal display glosses in an edition.
The lunar triangle example prints a whole-sine radius of 1,000,000 alongside
integers that its editorial note relates to a different scale. Preserve both
the printed radius and the integers without inserting a zero or silently
rescaling them. A printed argument error can still have an exact numerical
representation; an out-of-range lower sexagesimal component, such as 0′ 85″,
remains a literal unresolved expression rather than an adopted correction.

The first written angular component can exceed 60 in its stated unit: 66′ 6″
is exactly 3966 arcseconds, with the original components retained. Lower written
sexagesimal places remain bounded, so 0′ 85″ is not silently carried. Likewise,
an Earth-radius distance can contain sexagesimal minutes: the author explicitly
defines these as sixtieths of a semidiameter in the discussion of solar distances
on printed p.97. Preserve the component precision and the named reference body;
this does not supply a distance in kilometers.

The same leading-component rule applies to native length counts. An isolated
`120 minutes` of an Earth semidiameter denotes two Earth semidiameters, retaining
the written component 120. Longomontanus uses this count for Earth's diameter
in the comet-size calculation (*Astronomia Danica*, appendix p.37). A lower
component in a multi-part expression must still be below 60; an explicit zero
whole component does not authorize carrying an overflowing following place.

Computed charts preserve each printed coordinate label once. A coordinate
shared by braced bodies retains the joint label; an English expansion is not
another reading. Distinct positions printed for the same body remain distinct.
In Longomontanus's appendix charts, p.41, the descriptions explicitly expand
the Sun's and Moon's `9.47` labels as 9°47′. Those labels therefore use reviewed
degree/minute components; a dot alone supplies no general decimal or
sexagesimal rule. Chart epochs, conjectured appearance times and recorded
observing clocks remain separate, even where their dates coincide.

Where a model-comparison table omits component-unit marks, retain the ordered
numbers and their stated quantity without selecting a numerical angle from
physical expectations. A queried distance likewise retains its expression and
native unit without an adopted scalar. These interpretation limits differ from
uncertainty in the transcribed digits and from the accuracy of the historical
model.

Historical mile conventions remain distinct. In the *Progymnasmata*, p. 95 uses German miles for atmospheric path lengths; pp. 97–98 state ordinary miles and a scale of 860 per Earth semidiameter. Preserve `source_german_mile` and `source_ordinary_mile` without assuming a kilometer equivalent. Exact rational conversion preserves the number under that interpretation; source qualifications such as “scarcely,” “about” and “nearly” remain attached context. A model table's Earth-radius column and its eccentric-radius column are separate assertions, even when a stated proportion relates them. Retain each printed value without forcing numerical agreement.

Calculated solar-ingress dates retain the printed year, month and day separately from the time quantity. A model-prediction date may take its attribution from an explicitly linked row context within the same source and review, provided the date components agree and the attribution is unique. `solar_ingress_on_named_day` identifies the predicted event; it does not establish an observing date, clock origin, calendar conversion or absolute epoch. Preserve each model's printed timing difference and comparison sense even when the table is internally inconsistent.

An attributed historical angular parameter can retain `unclassified_angle` with the role `historical_input` when its coordinate meaning remains unresolved. Its exact magnitude is not a signed coordinate, and it is explicitly flagged as no additional raw reading. Do not promote such a parameter to an observed position merely to satisfy an export type.

`source_component_omitted` marks a printed partial expression whose missing whole component has not been supplied from another passage. Any scalar describes only the written components, not a complete coordinate; analyses requiring the full coordinate must exclude it until an explicit interpretation is established.

### Parts and first sexagesimal places

Some printed notation uses `P. 2. 1. 10` for two whole parts and ten first sexagesimal places. A source-bound review may declare `source_unit_notation=parts_1_minutes`. The complete expression is checked against its components, including an optional counted-sign prefix. The literal `1.` remains in the original expression; it is a unit marker in this declared format, not an extra measured numeral. Native lengths and angular values remain distinct, and counted signs do not establish a coordinate origin.

### Source-specific points in stellar latitudes

Origanus's stellar-table introduction explicitly makes a point in Tycho's
latitude column worth 30 arcseconds. The shared normalizer applies this only
under `dms_latitude_terminal_half_minute`; the same punctuation in another
column receives no such conversion. Retain following latitude qualifiers and
the stated catalog epoch independently of this numerical convention.

Comparative catalog rows identify printed entries. Paired author columns and
different historical star descriptions do not by themselves establish modern
stellar identities or independent observing sessions. Preserve the source names,
author attributions and individual publication occurrences. A magnitude label
printed between two rows retains its shared or uncertain scope. Bare longitudes
do not acquire a zodiac sign from numerical rollovers.

### Angular ascensions and native factors

The `Temp.` columns of Origanus's right-ascension canons contain angular
degrees, minutes and seconds. Their headings do not turn them into observing
clocks; the accompanying definition equates an equal hour with 15 equatorial
degrees. Keep angular interpolation differences separate from elapsed time.

The general declination canons also carry native sine multipliers. Their stated
whole sine is 100000, while other worked examples use 10000000. Preserve each
local scale and the literal differences. A single unmarked angular-difference
figure retains an unresolved component unit until source evidence establishes
its denomination; numerical agreement does not choose the unit.

Origanus's oblique-ascension canons on pp.220–223 also use angular `Temp.`
columns. The two successive canon pairs have separate publication identities
even though their split titles give the same latitude and Tychonic obliquity.
Preserve both stated parameter sets and their differing entries; do not relabel
one as Copernican from its numerical behavior. `Diff. A` and `Diff. S` in these
canons label interpolation increments, distinct from the ascensional-difference
function tabulated separately.

The stellar tables on pp.225–233 distinguish rising amplitude, ascensional
difference, oblique ascension and oblique descension for each calculation.
Only the amplitude columns carry the local `B`/`M` direction labels. An
unlabelled amplitude retains an unsigned magnitude, including a nonzero
amplitude near the equator; a neighbouring row does not establish its direction.
Missing entries remain missing. A value above 360° and its stated editorial
alternative remain separate; ingestion does not reduce or replace the original.

When a worked example's explicit unit conflicts with nearby headings, retain
each literal interpretation and the discrepancy. On p.216 the Frankfurt latitude
is written with a seconds mark where neighbouring headings use minutes. This
does not authorize changing either expression or assigning the discrepancy to
the printed book or its edition without specific evidence.

The true-rising and setting table beginning on p.241 gives the **Sun's** ecliptic
longitude when the named star rises or sets. Its two coordinate columns retain
the Copernican and Tychonic attributions. They are calculated event conditions,
not measured stellar positions. Here `M` and `V` label morning and evening;
they do not supply a coordinate's hemisphere. The doctrine describes how events
in the other half of the zodiac exchange those dayparts. Preserve that rule
without generating additional source observations or adopting unstated zodiac
origins from numerical rollovers.

Printed folios can repeat. The final leaf of this table is recorded as folio 256
after folio 257; the identity of its source leaf distinguishes it from the earlier
folio 256. Retain an established pagination exception instead of forcing every
leaf to follow the usual offset. See the [edition findings](edition-findings.md).

Repeated scan exposures are additional images of the same printed occurrence.
They do not add table rows or independent observations. Map the continuation
after a repeated run separately; an earlier PDF-to-folio offset no longer
applies there. Page-boundary processing must retain empty slots for exposures
whose text is intentionally not repeated.

### Native sine tables and interpolation increments

Origanus's sine-table instructions explicitly distinguish whole units and tenths
in the narrow interpolation channels, per single source second. Preserve this
as `sine_increment_per_source_second` with the source's stated radius and the
declared notation `paired_decimal_tenths`. The two-place field is a native
interpolation scalar; punctuation alone does not establish an angular unit or
authorize a decimal interpretation elsewhere. Packed or queried fields remain
unresolved rather than being partitioned using expected sine differences.

Bind table entries by their physical columns and printed argument labels.
Keep minute-row uncertainties and corrections in the argument context, and
retain repeated boundary rows as distinct printed occurrences. Neither blank
channels nor dashes supply missing increments. Preserve printed values and
explicit editorial alternatives separately; modern trigonometric evaluation
must not replace either during ingestion. Interleaved worked calculations need
their own review and are not completed merely by extracting the tables.

Angular fifths, sixths and sevenths are retained as `arcsexagesimal_fifth`, `arcsexagesimal_sixth` and `arcsexagesimal_seventh`: respectively 1/60³, 1/60⁴ and 1/60⁵ of an arcsecond. They describe written calculation precision, not instrument accuracy. The reviewed parts/minutes format also admits the explicit angular label `G.` and the comma boundary in `P. 338, 1. 23`; `G.` is not used to infer a native length.

The longer series in the *Progymnasmata*, p. 44, uses `1.`, `11.`, `111.`, `1111.`, `V.`, `V1.` and `V11.` as successive sexagesimal place labels. A review declares `roman_sexagesimal_places`; the parser consumes the complete expression in order and rejects repeated or reversed places. A counted-sign annual displacement remains as printed, including a bissextile remainder with zero signs; no complete revolution is added silently.

In a duration expressed in days, hours, minutes and seconds, a following third (`time_third`) is 1/60 of a clock second. It is distinct from a sexagesimal third of a day (`day_third`, 2/5 second). Table headings and the surrounding discussion establish which system applies. The stated sidereal-year duration and its differences from other authors are historical calculations, not observing timestamps.

The same reviewed angular notation admits `part.` for whole parts, `l.`, `min.` or `minut.` for minutes, and `ll.` for seconds. These labels are interpreted only under an explicit notation declaration. They do not change the recorded expression or establish whether a value was observed, reduced or calculated.

### Solstice summaries and successive corrections

Brahe’s *Progymnasmata*, pp. 46–48, compares Walther’s Nuremberg and Rothmann’s Kassel solstice material. Preserve the native chord readings, reported angular values, parallax-adjusted values and refraction-adjusted values as distinct source quantities. A summary selected from several years does not establish an individual observing date. Repetition of a summer altitude during a later reduction does not add an independent observation. The author’s transfer of a refraction estimate between sites and his confidence in the resulting pole altitude remain attributed historical decisions, not modern corrections or measured uncertainties.

Tables may omit the outer vertical bars while retaining separators between columns. When a review explicitly supplies consecutive `source_columns`, the compiler includes the first and last cells and checks the complete literal span. This declaration identifies a table binding; a vertical bar inside prose does not by itself establish table columns.

A trailing numeric `[recte: …]` annotation in the last cell may be excluded from the original value’s bound expression. The entire preceding numeric span must still match the declared columns. Store the proposed correction separately, linked to the original; inherit unchanged components explicitly rather than replacing the printed value.

When a correction interrupts an original expression, bind the original's surviving parts as ordered source fragments and retain the complete cell in its context. Bind the proposed correction separately, with unchanged components inherited from the original. This also applies when an edition supplies a bracketed zero at a zodiac ingress and gives a different degree as an alternative. A supplied zero must remain distinguishable from a printed numeral.

A fragment repeated elsewhere on the same line requires an explicit character interval. The compiler checks that interval against a complete literal match and requires the first fragment to agree with the primary quantity's binding. Unpositioned fragments must still be unique; an explicit position does not permit partial numerical matches, reversed fragments, or overlap.

Daily solar ephemerides are computed positions, not additional observations. An explicit sign ingress can establish the zodiac origin for subsequent entries in the same reviewed monthly column. Leave earlier entries without an established sign unless source evidence supplies it; do not infer their sign from expected solar motion. A tabular date alone supplies neither a calendar convention nor an absolute daily epoch.

An elapsed duration’s highest written component can exceed its usual clock range: a table argument of 60 minutes remains 60 minutes and converts exactly to 3,600 seconds. Lower components still obey their sexagesimal bounds, and this provision does not relax clock-reading validation.

The same distinction applies to explicitly identified angular rates. In the *Progymnasmata* daily-motion table, 61′21″ per source day is exactly 3,681 arcseconds per source day; its printed components remain unchanged. The degree figure beside that rate is the distance-from-apogee argument, not a whole-degree component of the rate. Bind both quantities separately even where the edition presents them in one text cell.

### Stellar coordinate demonstrations

Superscript Roman place marks are numerical units: `v` in superscript denotes
the fifth sexagesimal place and `vi` the sixth. Preserve those marks before
Unicode compatibility conversion, which otherwise turns them into ordinary
letters. A qualifier such as “whole” does not remove the unit in “six whole
hours.” Conversion checks must retain the binding between each number and its
printed unit. These checks establish the stated numerical interpretation, not
the accuracy of a historical measurement or model.

Use the shared staged expression's source position when a short angle recurs
inside longer expressions. For example, a standalone degree value must not be
bound to the same digits within an earlier compound angle. Native chronology,
quoted coordinate epochs and hypothetical corrections remain separately
qualified; none establishes an absolute observing timestamp by itself.

Historical coordinate tables can attribute a single printed value to several
authorities. Preserve that occurrence once, with all stated authorities and the
source-bound table or narrative label. Keep predictions and comparisons distinct
from instrumental readings. A quotation of a reduced coordinate does not recover
the original unreduced measurement. Where a source says “us,” retain that literal
authorial reference with the cited work rather than silently assigning the result
to a different astronomer mentioned nearby.

Bind attribution evidence through the quantity's review-scoped context links.
Compiling this binding establishes where the attribution was read; it does not
independently prove the source's claim. Printed coordinate epochs, observation
dates and quoted clocks remain separate. Conflicting years, seconds or closure
sums survive as printed, without choosing the version that best fits a prediction.

In the *Progymnasmata*, pp. 282–294, the Cassiopeia demonstrations distinguish measured reference-star distances, adopted calibration coordinates, triangle sides and angles, and final ecliptic coordinates. The completed year 1572 is their calculation target; it does not date the measured distances. Keep the source's point labels and cross-references with each calculation. Where an abbreviated example refers back to a figure or first triangle, preserve that reference without manufacturing another set of numerical inputs.

A measured distance can appear first in explanatory prose and again as an adopted input in a formal demonstration. Preserve both publication occurrences and their relationship without counting the repetition as another observation. Similarly, retain contradictory printed triangle values separately: Schedir's side BC differs between triangles on p. 284, and star XXV's side CA differs between triangles on p. 294. Exact conversion of each expression does not settle which value should enter a reconstructed calculation.

Reviewed G.M. and G.M.S. headings establish angular components even where figures carry terminal points or occupy separate columns. Keep those literals and physical column bindings. If an editorial correction interrupts a coordinate before its final unit mark, ordered source fragments preserve the original coordinate while the proposed correction remains a separate, unapplied variant.

### Appearance reports and local star numbering

The *Progymnasmata* New Star account, pp. 297–304, combines native magnitude classes, comparisons with Venus and Jupiter, color descriptions and disappearance reports. Preserve the reported month or season without inventing a day or clock. A comparison can supply a bound or remain qualitative; it does not supply a modern magnitude. When a later clause explicitly resumes an earlier reference class, retain that source relationship and its temporal scope. Color, scintillation and visibility remain recorded information even when they supply no numerical quantity.

The twenty-six entries in the Cassiopeia demonstrations and the twenty-six labels of the plates on pp. 314–315 use different orders. Keep their identities separate and establish any correspondence from names and source descriptions. The separation tables on pp. 344–346 use the plate numbering; a disagreement between a row numeral and its star caption must remain visible rather than being resolved from the measured angle. Their adopted intervals follow instrumental cautions and limiting procedures. The associated instrument parallax concerns the observer's eccentric eye position, not a celestial-distance measurement.

The sextant description on pp. 336–343 supplies construction dimensions in
cubits and finger breadths, fractions of a circle and a brace position relative
to ruler length. Preserve these native quantities with their stated purpose;
the width of a degree division is a linear breadth. The proposed subdivision
into thousandths is an illustrative scale, and the rear correction table's
entries are not printed. Retain the correction instructions and missing inputs
without reconstructing that table. Similarly, the altitude procedure on
pp. 347–351 [printed 331] specifies level checks and correction directions,
without supplying an individual applied correction for every reading.

### Altitude series and stellar calibration

The *Progymnasmata*, pp. 360–365, distinguishes Paul Hainzel's maximum and minimum altitudes near Augsburg from the differences, polar distances and pole elevations calculated from them. Tycho's own Pole Star series at Hven has a separate observing context. Instrument design, ownership and publication do not establish the identity of the observer. Repeated source summaries and adopted means remain distinct from individual readings.

In this altitude series, “lowest declination” describes the star's lowest elevation above the horizon. It does not turn the value into celestial declination. Before- and after-midday clock labels retain their native convention; a complete hour/minute expression alone establishes neither a calendar nor an absolute epoch. Bracketed parallel renderings of an altitude are not additional measurements.

Preserve disagreements within calibration tables. The preceding star in the Lesser Bear's flank has a printed polar distance of 14°5⅙′, which must not be replaced by half its tabulated altitude difference. The middle-tail star's disputed fractional mark remains unresolved, with the edition's 32°46½′ alternative separately unapplied. Explicit hemisphere abbreviations in a comparison row do not establish hemispheres for the other rows.

The Cassiopeia comparison on pp. 366–376 [recte: 367] separates meridian transit intervals, adopted right ascensions, derived right ascensions, observed declinations and equatorial-armilla ascensional differences. A transit interval is not a clock reading; an ascensional difference is not a great-circle separation. Preserve published inconsistencies and the proposed epoch transfer without performing an unprinted reconstruction during ingestion. Erroneous printed page numbers retain their labels alongside the verified PDF-page locator.

### Repeated position calculations and table notes

The seven New Star determinations in *Progymnasmata*, pp. 372–388, reuse
reference-star measurements and geometric inputs. Retain each printed
occurrence, intermediate result and summary without counting the calculations
as independent observations. Preserve a nominal coordinate and its stated
shortfall separately; a later summary need not agree with the prose.
Out-of-range components, such as 22°61′40″, remain literal and unresolved.
Explicit corrections remain linked, unapplied alternatives.

A table's sign declaration may follow its rows. Bind that note to its reviewed
table scope rather than inventing a sign in the numerical cells. A brace marking
northern latitudes applies to the stated column; it does not establish the
hemispheres of earlier unmarked inputs. Calculations using Copernican or
Alphonsine reference coordinates retain that attribution and their printed
results, independently of the author's adopted position.

A final-edition paragraph can cross a leaf turn between numerical expressions.
Bind each expression to its own documented leaf, retaining the paragraph and
calculation context across the turn. Printed page numbers can also repeat in
error: the leaf at PDF page 449 prints 389 in sequence position 393. Preserve
the printed label and the verified PDF locator together; a fixed offset alone
cannot resolve these cases.

Coordinate tables can place a stellar longitude beside several solar
longitudes associated with that star's rising and setting. Preserve the
different subjects and the source's phenomenon labels: a co-rising solar point
is not the star's longitude. A date after a semicolon remains separate calendar
evidence, including any unexplained trailing component. Computed calendar
entries do not become observed events.

Hemisphere abbreviations require a local convention. Latin B/A in coordinate
columns can denote north/south, while A/S in an annual equation table can mean
add/subtract. Retain each table's stated operation and never apply one mapping
to the other. An explicit corrected zodiac sign remains a linked, unapplied
alternative to the printed coordinate.

Catalog populations, naked-eye counts and telescopic counts describe
different selections. Riccioli's *Almagestum Novum*, Book VI, chapter VI,
pp. 410–413, compares catalog entries before reporting counts by Mästlin,
Galileo, Šírek and Zupi. Preserve each authority, region, instrument description
and lower or upper bound. A reported count is not a count of independent
observing sessions. “About as many” remains a relative claim rather than a
second exact numeral.

Keep a population extrapolation separate from a counted population. Riccioli's
estimate for Orion uses an area in square degrees and the side of a smaller
square in degrees. The area retains unit `square_degree`; it is neither a
linear angular extent nor a star count. His calculated and deliberately
rounded population estimates retain calculation roles and approximation
qualifications. Historical visual magnitude ranks likewise retain their
attributed disagreements and do not become modern photometric magnitudes.

New-star reports can combine positions, appearance dates, evolving brilliance
and conditional size estimates. Keep these claims separately scoped: an
appearance date does not establish the epoch of an accompanying coordinate,
and a comparison with first-magnitude stars can describe several periods with
different qualifications. Preserve “greater than” and “scarcely exceeded”
without turning the comparison class into an exact measured brightness.
Likewise, “no sensible parallax” is a source conclusion, not a numerical zero.
If a size multiplier has a missing denominator, retain the entire mixed
fraction without a scalar. Do not infer whether “greater” describes diameter,
area or volume when the passage does not establish that convention.

Riccioli's *Astronomia Reformata*, Book IV, chapter VIII, p. 219, distinguishes
quoted measurements from distances calculated using stellar coordinates.
`ex Tych. da.` uses Tycho's declination and difference of right ascension;
`ex Tych. LL.` uses longitude and latitude. Neither label denotes a new
instrumental reading. `Nobis` marks Riccioli's adopted or corrected values;
the individual reduction state must be established separately. Repetition
marks retain their authority and frequency wording without creating unwritten
observations.

Blank pair labels can inherit a preceding explicit pair within the same
reviewed table block. An observer name printed in a label cell is not a new
stellar endpoint. A caption can also carry a numerical distance without
establishing its comparison star: the Capella/Gassendi entry on p. 221 is
retained with an unresolved reference. The [native ETH scan](https://www.e-rara.ch/i3f/v20/142000/full/full/0/default.jpg) confirms the edition's
arrangement; it supplies no basis for selecting an endpoint by numerical
agreement. Keep the known angle and the unresolved relationship separate.

Riccioli's universal catalog in *Astronomia Reformata*, Book IV,
pp. 265–279, separates four source certainty classes from visual magnitude
classes. The former describe observational and reduction lineages; they are
not statistical confidence intervals. Its 1700 coordinate target is a
calculation epoch. Quoted new-star entries bearing 1572 or 1604 need their own
timing qualifications rather than an automatic assignment to that target.
Constellation-qualified native labels retain source entries without asserting
modern stellar identities. Repeated descriptive names remain distinct at
their cited locations.

Read each table's precision from its heading. A complete degree–minute pair
in a two-place table differs from an incomplete degree–minute–second entry
whose seconds cell is empty. Neither case supplies an invented seconds
reading. A latitude-only alternative creates no additional longitude, and a
blank magnitude is absent rather than zero. A nebulous classification or star
symbol in the magnitude column need not have a numerical class.

The Schiller/Bayer/Bartsch catalog quoted on p. 242 has a 1625 calculation
target and a navigators' observational lineage. Its right ascensions are in
angular degrees and minutes, not time units. Its Greater Cloud longitude has
no written zodiac sign; the other coordinates cannot supply that missing
origin.

### Apparent disks, image scales and stellar size estimates

Riccioli's *Astronomia Reformata*, Book X, pp. 353–360, distinguishes
Saturn's globe width, globe height and full span with the ansae. Preserve
the named feature with each quantity. A Venus crescent's horn-to-horn
span likewise retains that description. Angular diameters, angular
semidiameters and source-derived physical sizes are separate quantities.

Projected-image parts, paper-circle divisions and ratios between apparent
disks retain their native scales. Record which body or interval supplies
the denominator. A disk-area ratio differs from a linear-diameter ratio;
an Earth-diameter ratio differs from a length in Earth semidiameters.
Keep the printed calibration and reduction separately, without replacing
the author's result with newly computed arithmetic.

The planetary synopsis on p. 359 is another publication occurrence of
the attributed values. Its Hortensius Mars perigee diameter is 1′40″,
whereas the preceding prose gives 1′4″. Preserve both readings and their
locations. Agreement or disagreement between such occurrences does not
establish another independent observation.

The stellar tables on p. 360 use seconds and sexagesimal thirds for
apparent diameters and ordinal visual classes for brightness. Preserve
their calibration, observing method and collective star labels. These
are historical apparent-size estimates; ingestion does not establish
physical stellar diameters or modern photometric magnitudes. One value
reported for several dates remains one printed numerical occurrence,
with all stated dates retained in its context.
