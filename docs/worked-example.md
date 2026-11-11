# From a source passage to an exported altitude

On 18 January 1583, the account of the lower head of Gemini's meridian transit
gives an altitude of `63 3`, described as *partium 63 3, exactly, as before.*
See Tycho Brahe, *Opera Omnia* X, printed p.245, in the
[published English edition](https://arsastronomica.com/works/tycho-brahe-thesaurus-observationum-tomus-primus/)
and its [PDF](https://books.arsastronomica.com/Tycho_Brahe_Thesaurus_Observationum_Tomus_Primus.pdf).
The [original print](https://archive.org/details/operaomniaedidit10brahuoft)
is a separate representation of the same underlying printed account.

The executable [example](../examples/altitude.py) contains this short excerpt and
an explicit review input: altitude, lower head of Gemini, recorded-reading role,
and degree/minute components. It runs the ordinary compiler, public-field
projection and SQLite/CSV exporter. Its temporary files are removed afterward;
the printed JSON shows the review, complete normalization and selected CSV fields.

From a source checkout with the project dependencies installed:

```sh
python -m examples.altitude
```

Expected numerical results:

| Exported field | Value |
| --- | --- |
| `expression` | `63 3` |
| `quantity` | `altitude` |
| `role` | `recorded_reading` |
| `unit` | `arcsecond` |
| `value_exact` | `226980` |
| `value_degrees_decimal` | `63.05` |
| `printed_page` | `245` |

The exact conversion is 63 × 3,600 + 3 × 60 = 226,980 arcseconds.
“Exactly” is the source's wording, not a modern uncertainty estimate. This example
does not accept an absolute observing epoch, reconstruct refraction or estimate
instrument error. It omits the passage's joint instrument and timing relationships.
Its identifiers bind this excerpt only and are not the release's full-book record
identifiers; do not import it as another observation.

This demonstrates numerical processing and export. A source-to-residual scientific
example additionally needs the [first-subset requirements](research-plan.md#next-research-milestones).
