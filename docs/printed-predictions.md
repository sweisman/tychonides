# Printed predictions for the Moon and planets

Tycho’s logs print positions computed from the tables and ephemerides of his
day beside his own observations. This study collects every such longitude and
latitude of the Moon and the five planets, 485 in all from 1563 to 1600. Each
is compared with the log’s own value for the same date and with the modern
JPL DE441 ephemeris.

The [Mars opposition study](mars-oppositions.md) compared the predictions
printed near nine oppositions of Mars. This study adds the other bodies and the
rest of the logs.

![Printed longitudes minus DE441 for each planet, by table or ephemeris](figures/printed-predictions.png)

## Main results

- **Saturn separates the tables most clearly.** Six Alphonsine longitudes of Saturn
  from 1590 and 1591 run 2.9° ahead of DE441, and one from 1595 runs 2.2°
  ahead. The seven Copernican longitudes of 1591 stay within 10′.
- **The Copernican latitudes of Saturn are a degree off.** The seven printed in
  1591 lie 53′ to 61′ south of DE441. The eight Alphonsine latitudes stay
  within 7′.
- **Jupiter follows the same pattern in longitude.** Four Alphonsine longitudes
  fall 16′ to 87′ behind. The Copernican and Prutenic ones lie between 33′
  behind and 14′ ahead.
- **For Mars, the Copernican error depends on where Mars is.** More than 60
  days from an opposition, the 13 Copernican longitudes have a median
  difference of 20′ and none exceeds 37′. Near opposition the median is 1.9°.
  The Alphonsine medians are 1.6° and 3.6°.
- **Mercury in February 1592.** With the hours the log prints, the Copernican
  longitudes are 11′ ahead and 9′ behind. The Alphonsine ones are 35′ and 88′
  ahead.
- **Tycho’s own values agree with DE441 far better than any table.** Where the
  log prints the hour, the median difference between his longitude and DE441
  is 1.0′ to 4.8′ for Mars, 4′ for Mercury and Venus, and 0.1′ for Jupiter.

## Longitudes

Each cell is the printed value minus DE441, in arcminutes.

| Body | Source | Predictions | Mean | Median size | Largest |
| --- | --- | ---: | ---: | ---: | ---: |
| Mercury | Alphonsine | 4 | +83 | 66 | 167 |
| Mercury | Copernicus | 2 | +1 | 10 | 11 |
| Mercury | Prutenic | 2 | +89 | 89 | 99 |
| Venus | Alphonsine | 2 | −19 | 19 | 35 |
| Venus | Copernicus | 2 | −44 | 44 | 53 |
| Venus | Stadius | 2 | −20 | 20 | 21 |
| Venus | Carelli | 2 | +48 | 48 | 48 |
| Mars, away from opposition | Alphonsine | 25 | −38 | 94 | 227 |
| Mars, away from opposition | Copernicus | 13 | −5 | 20 | 37 |
| Mars, away from opposition | Prutenic | 10 | +34 | 126 | 240 |
| Mars, away from opposition | Stadius | 8 | +40 | 32 | 96 |
| Mars, away from opposition | Leovitius | 1 | −170 | 170 | 170 |
| Mars, away from opposition | Carelli | 3 | −64 | 65 | 66 |
| Mars, near opposition | Alphonsine | 57 | +89 | 219 | 318 |
| Mars, near opposition | Copernicus | 50 | −57 | 111 | 335 |
| Mars, near opposition | Prutenic | 10 | +21 | 37 | 124 |
| Jupiter | Alphonsine | 4 | −59 | 66 | 87 |
| Jupiter | Copernicus | 2 | −11 | 22 | 33 |
| Jupiter | Prutenic | 1 | +14 | 14 | 14 |
| Jupiter | Stadius | 2 | +1 | 1 | 1 |
| Jupiter | Carelli | 2 | −39 | 39 | 39 |
| Saturn | Alphonsine | 7 | +169 | 174 | 176 |
| Saturn | Copernicus | 7 | −3 | 6 | 9 |
| Saturn | Prutenic | 1 | +3 | 3 | 3 |
| Saturn | Stadius | 2 | −37 | 37 | 37 |
| Saturn | Carelli | 2 | +100 | 100 | 100 |

“Near opposition” means within 60 days of an opposition in Longomontanus’s
table, the window of the opposition study. The sources are named as the log
names them. Stadius, Leovitius, and Carelli published ephemerides. The others
are tables. The log keeps “Copernicus” and “Prutenic” apart, and so does this
page, although the Prutenic Tables rest on Copernicus’s models.

The samples cover different years, so two rows are not a like-for-like test of
two sources. The Copernican and Prutenic rows for Mars away from opposition,
for example, share one date.

## Latitudes

| Body | Source | Predictions | Mean | Median size | Largest |
| --- | --- | ---: | ---: | ---: | ---: |
| Mercury | Alphonsine | 4 | −18 | 22 | 31 |
| Mercury | Copernicus | 2 | +3 | 7 | 10 |
| Mercury | Prutenic | 2 | −78 | 78 | 86 |
| Venus | Alphonsine | 2 | +23 | 51 | 74 |
| Venus | Copernicus | 2 | +85 | 85 | 168 |
| Mars, away from opposition | Alphonsine | 15 | −5 | 17 | 60 |
| Mars, away from opposition | Copernicus | 10 | −16 | 14 | 42 |
| Mars, away from opposition | Prutenic | 3 | −33 | 43 | 59 |
| Mars, away from opposition | Stadius | 1 | −19 | 19 | 19 |
| Mars, away from opposition | Leovitius | 1 | −13 | 13 | 13 |
| Mars, near opposition | Alphonsine | 45 | −9 | 12 | 53 |
| Mars, near opposition | Copernicus | 46 | +20 | 35 | 74 |
| Mars, near opposition | Prutenic | 5 | −5 | 40 | 54 |
| Jupiter | Alphonsine | 5 | +12 | 14 | 32 |
| Jupiter | Copernicus | 2 | +3 | 37 | 40 |
| Jupiter | Prutenic | 2 | −1 | 2 | 3 |
| Saturn | Alphonsine | 8 | −4 | 5 | 7 |
| Saturn | Copernicus | 7 | −59 | 60 | 61 |
| Saturn | Prutenic | 1 | −50 | 50 | 50 |

A positive difference is north of DE441. In September 1591 the printed
latitudes of Venus are −2° 17′ (Alphonsine) and −0° 43′ (Copernicus), where
DE441 gives −3° 31′ and the mean of the log’s four values is −3° 25′.

The [summary](figures/printed-predictions-summary.csv) also gives every
difference from the log, and the medians for the rows with a printed hour. The
[results](figures/printed-predictions-results.csv) list each prediction.

## May 1564

The earliest entries compare the ephemerides of Stadius and Carelli on May 1
and 2, 1564, when Tycho was seventeen. Stadius’s Jupiter is 1′ from DE441 on
both days. Carelli’s Saturn is 100′ ahead.

On May 1 the log’s own longitudes for Venus, Mars, Jupiter, and Saturn are
whole degrees, and all four lie 91′ to 107′ east of DE441. This study does not
explain that shared offset. It is recorded as a question for the reading of
that page.

## The Moon is listed and not compared

The logs print 59 predictions of the Moon on 12 dates. The log has values of
its own on some of those dates, but none carries a usable printed hour. The
Moon moves 6° to 7° in longitude in twelve hours, and an observed place of the
Moon can include up to a degree of parallax. Without the hour the comparison
has no meaning, so the differences are left blank. Several dates carry two or
three values from one table that differ by up to 1.75°, which suggests
calculations for different hours.

## Rows flagged or set aside

- **Venus, September 1, 1590.** The longitudes printed on *Opera Omnia* XII
  p. 71 are 127° 50′ and 127° 00′. Release 1.3.1 dated them July 15, when DE441
  puts Venus at 76°, and this study flagged the entry because no table of the
  period errs by 51°. The [audit](status.md#audit-of-the-tycho-log-records)
  found the cause. The heading over the calculation names the morning
  observation of September 1, and the earlier date was carried from another
  entry. With the printed date the Alphonsine longitude is 3′ from DE441 and
  the Copernican one 53′. The rule still flags any longitude more than 10°
  from DE441, together with the other predictions of that body in the same
  printed entry. It now flags none.
- **Mercury, October 25, 1586.** Release 1.3.1 dated the four predictions on
  *Opera Omnia* XI p. 79 October 29. Their heading prints October 25, before
  noon. The mean of the log’s five longitudes for that day is 13′ from
  DE441. The Alphonsine longitude is 167′ ahead and the Prutenic one 99′.
- **Predictions typed by the audit.** Release 1.3.4 types 98 more longitudes
  and latitudes of the Moon and the planets as predictions, from labels that
  give them to a named model, a set of tables, or an ephemeris. The catalog
  does not yet record the name of the source for these values, so 78 of them
  have no model name here, and 20 have no single complete date. They are
  listed among the excluded candidates and enter no comparison. The same
  release gives the log more values of its own on four dates: Mercury on
  October 25 and 29, 1586, the Moon on January 6, 1587, and Venus on
  September 27, 1591. The differences from the log changed on those dates.
  No difference from DE441 changed.
- **Mars, 1599 and 1600.** The catalog records no calendar for 40 predictions
  from these years. Read as Julian, the log’s own longitudes of October 1599
  lie 4.3° to 4.7° from DE441, the pattern of a ten-day calendar shift. These
  predictions are reported as a separate set in the summary file.
- **One Copernican entry for Mars in 1591** is printed as 4 sexagenae 7° 42′.
  The catalog records it as a mean longitude counted from the first star of
  Aries. It is not a place in the zodiac and is left out.

| Left out | Count | Reason |
| --- | ---: | --- |
| Predictions without a printed latitude direction | 32 | A direction is never supplied from neighboring entries. |
| Predictions without one complete date | 35 | The date claim is missing, partial, or multiple. |
| Predictions without a model name | 87 | The catalog records no name for the table. For 78 the page names it. |
| Prediction that is a mean longitude | 1 | It is counted from the first star of Aries, not from the equinox. |
| Log values superseded on their date | 55 | The log prints an adopted value for the same date. |
| Log values without a printed zodiac sign | 38 | A sign is never supplied from neighboring entries. |
| Log values without a printed latitude direction | 36 | As above. |

The [excluded candidates](../examples/printed-predictions-excluded.csv) are
listed one by one. Forty-five predicted longitudes have no printed zodiac sign
and are compared within the sign.

## Limits

- **The hour of a prediction is often not stated.** DE441 is taken at the
  hours of the log’s own values for that date where the log prints them all,
  which covers 169 predictions. For 63 more the log prints the hour of the
  calculation itself, and DE441 is taken there. The other 194 compared
  predictions use local noon. Two of them carry an hour marked “A.M.”, which
  the rule does not place, because it can mean a clock hour or hours before
  noon. In twelve hours DE441 moves by up to 36′ in longitude for Mercury and
  Venus, 22′ for Mars, 4′ for Jupiter, and 3′ for Saturn. The noon-based
  differences carry that much uncertainty. The Jupiter and Saturn results
  hardly depend on it.
- **Small samples.** Mercury appears on 4 dates, Venus on 4, Jupiter on 7, and
  Saturn on 11. Mars appears on 98.
- **Repeated entries count each time.** A later summary page can repeat a
  prediction from an earlier page. In 1593, *Opera Omnia* XII p. 291 prints the
  values of pp. 284 to 286 with dates one day earlier, so a date can itself be
  uncertain by a day.
- **These are the values as printed.** A slip in the arithmetic of a printed
  calculation counts here as an error of its table.
- **One observing site is assumed.** Local time is converted with the
  longitude of Uraniborg for every year. Tycho worked elsewhere before 1576
  and after 1597. The difference is at most about ten minutes of time, under
  1′ for every planet.
- **Nothing is fitted.** Under the project’s
  [model-comparison protocol](research-plan.md#model-comparison-protocol) this
  compares printed predictions with published values. It is not a predictive
  test of any model.

## Inputs and reproduction

The [selection script](../examples/predictions_select.py) states its rules and
reads the released catalog. It writes the
[predictions](../examples/printed-predictions.csv), the
[log values on the same dates](../examples/printed-predictions-references.csv),
and the excluded candidates. No ephemeris is consulted in the selection.

The [ephemeris script](../examples/predictions_ephemeris.py) caches the
[JPL Horizons positions](../examples/printed-predictions-ephemeris.csv):
apparent geocentric ecliptic longitude and latitude of date. The
[analysis script](../examples/printed_predictions.py) then runs offline:

```sh
python examples/predictions_select.py downloads/tychonides.sqlite
python examples/predictions_ephemeris.py
python examples/printed_predictions.py --output docs/figures
```

A test regenerates the tables from the committed inputs, and a second test
checks the input files against the catalog.
