# In plain terms

This page explains the words the [studies](studies.md) use, for a reader who
has looked at the night sky and has not studied astronomy. It also states the
one rule every study follows.

## The rule the studies follow

**What was observed comes first.** Tycho Brahe and his assistants pointed
instruments at the sky and wrote down what they read. Those records are the
reference in every study that has them. Every account of where a planet should
have been is measured by how far it falls from the recorded place. That holds
for the tables of Tycho’s day and for a modern ephemeris alike.

Three things follow from the rule.

- **The modern ephemeris is tested, not trusted.** It uses none of Tycho’s
  observations, so his logs can check it. Where the log prints the hour of an
  observation, the studies report how far the ephemeris lies from it.
- **Where a study has no observation, it says so.** On some dates the logs
  print a table’s prediction and no place of their own. There the ephemeris
  stands in, and the page marks those results.
- **An observation can be off too.** Instruments, clocks, and the air all add
  error. The studies keep every recorded value, name the ones that look
  doubtful, and send them back to the printed page for a check. They do not
  remove a value because a theory disagrees with it.

## Angles in the sky

Positions in the sky are angles. A full circle is 360 degrees (°). One degree
is 60 arcminutes (′), and one arcminute is 60 arcseconds (″). The full Moon is
about half a degree wide. Where the log prints its hours, a modern ephemeris
typically lies within five arcminutes of Tycho’s longitudes of Mars, a small
part of the Moon’s width.

## Two ways to give a position

The stars keep their pattern from year to year. The Sun, Moon, and planets
move across that pattern, and all of them stay near one line: the yearly path
of the Sun, called the **ecliptic**. The band around it is the zodiac.

Astronomers use two grids on the sky, as a globe uses longitude and latitude
on the Earth.

- **Longitude and latitude** are measured from the ecliptic. Longitude runs
  along it, starting where the Sun stands at the March equinox. Latitude is
  the distance north or south of it. The old books give longitude by zodiac
  sign, and each sign is 30° long. “17° Taurus” means 17° into the second
  sign, which is 47° of longitude. Planets are described this way because
  they move along the zodiac.
- **Right ascension and declination** are measured from the celestial equator,
  the circle in the sky above the Earth’s equator. Right ascension runs along
  it from the same starting point. Declination is the distance north or south
  of it. Instruments that turn about the Earth’s axis give these directly.

The two grids are the same sky with two sets of lines. The equator is tilted
against the ecliptic by about 23½°, and the two circles cross at the equinox
points. Turning one grid into the other is a rotation by that tilt, like
tipping a globe.

For example, a point on the ecliptic at longitude 47½° has latitude 0°. On the
other grid the same point has right ascension about 45° and declination about
17° north. At longitude 90°, the Sun’s place at the June solstice, the point
stands at right ascension 90° and declination 23½° north, the full tilt.

For any point the rule is:

```text
sin(declination) = sin(latitude) × cos(tilt) + cos(latitude) × sin(tilt) × sin(longitude)

tan(right ascension) = (sin(longitude) × cos(tilt) − tan(latitude) × sin(tilt)) ÷ cos(longitude)
```

Tycho often measured on one grid and reported on the other. The catalog keeps
both the reading and the result.

## Reading, reduction, prediction

The catalog keeps three kinds of numbers apart, and so do the studies.

- A **reading** is what an instrument or a clock showed.
- A **reduction** is Tycho’s own result worked out from readings, such as the
  longitude of Mars on a given night.
- A **prediction** is a place computed in advance from a theory. The logs often
  print one beside a reduction and name where it came from.

## Tables and ephemerides

A set of **tables** lets an astronomer compute where a planet will be on any
date. The Alphonsine Tables rest on Ptolemy’s Earth-centered models. The
Prutenic Tables rest on the models of Copernicus. An **ephemeris** is the
finished list: the places of the Sun, Moon, and planets day by day. Stadius,
Leovitius, Maestlin, and Carelli published ephemerides in the sixteenth
century.

**JPL DE441** is a modern ephemeris. It follows the Sun, Moon, and planets
step by step under their pull on one another, and it is adjusted to fit modern
measurements such as radar, spacecraft tracking, and laser ranging to the
Moon. The studies ask it for the direction of a body as seen from the center
of the Earth at a given moment.

## Refraction and parallax

Two effects move a body from its true direction to the place where an observer
sees it. Both act straight up and down.

- **Refraction.** Air bends light, so everything looks a little higher than it
  is. The effect is about half a degree at the horizon and about 1′ halfway up
  the sky.
- **Parallax.** An observer stands on the Earth’s surface, not at its center.
  A nearby body therefore looks lower than it would from the center, and the
  nearer it is, the more it drops. The size of the drop gives the distance.
  The Moon’s parallax can reach a degree. For Mars in 1587 a modern ephemeris
  gives 13″ at the horizon, where Tycho’s log applies 302″.

Because both act along the same line, a table of one can carry an error in the
other. Tycho took the Sun’s parallax as 3′, about twenty times the modern
value, and his refraction table for the Sun runs 4½′ above his table for the
stars. The [refraction study](refraction-tables.md) takes the two apart. The
[1587 Mars study](mars-parallax-1587.md) asks whether his own measurements
show the parallax his log applies.

## Earth-centered and Sun-centered

The Mars studies compare three old constructions of the planet’s motion.

- **Ptolemy.** The Sun and planets circle the Earth.
- **Copernicus.** The planets circle the Sun, and the Earth is one of them.
- **Tycho.** The Sun circles the Earth, and the other planets circle the Sun.

In outline, Tycho’s arrangement and Copernicus’s place the Earth, the Sun, and
the planets at the same angles and relative distances. They differ in which
body is taken to stand still. A planet’s position seen from the Earth is therefore
the same in both, and no position in this catalog can separate them. The
differences the Mars studies find between the constructions come from their
detailed circles and constants. For that reason those studies do not rank the
systems.

## Where to go next

- The [studies](studies.md) give each question, result, and limit.
- The [status page](status.md) shows what is done and what comes next.
- The [catalog](../resources/catalog/README.md) holds the observations
  themselves, with links from the values to their printed pages.
