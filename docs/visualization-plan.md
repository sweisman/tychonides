# Interactive planetary visualization

The interactive explorer is planned. This page sets out its references, views,
and acceptance requirements. The [research program](research-plan.md) places it
among the other milestones, and the [status page](status.md) records progress.

Use [the Tychosium](https://ts.tychos.space/) as an interaction reference for a navigable astronomical simulation. Tychonides will connect that style of exploration to its own independently specified models and validated observations. Implementation technology and detailed screen design remain open.

## Visualization references

| Reference | Ideas to carry into Tychonides |
| --- | --- |
| [Pafko's Mars data visualization](https://www.pafko.com/tycho/observe.html) | Declination against time, with recorded observations and a calculated curve visually separated. Make this interactive with point selection, observation filters, residuals, and citations. |
| [Pafko's Mars motion visualizations](https://www.pafko.com/tycho/mars.html) | Celestial-sphere motion, observer sky views, and retrograde sequences. Link the sky view to the same date and selected reading as the time-series plot. |
| [Pafko's model illustrations](https://www.pafko.com/tycho/models.html) | Explain the geometry of different models alongside the observations and their predictions. |
| [The Tychosium](https://ts.tychos.space/) | Navigable simulation, camera exploration, and animated planetary geometry. |

Credit these as design references. Produce project-specific views from documented calculations and reviewed data; any reuse of their media or code requires suitable permission or licensing. A reader should be able to move from a recorded declination to its sky position, model geometry, and residual without losing the observation's identity.

## Views and controls

- A date control, play/pause, time-step and speed controls, and direct selection of an observing session or opposition.
- An orbital view with selectable viewing frame, observer, camera position, trails, and sight lines. Separate changes of reference frame from changes to the astronomical model.
- An observer's sky view showing apparent planetary paths and retrograde loops. Show comparison stars when their identities, positions, and epochs are established.
- Model selection for the specified Ptolemaic, Copernican, Tychonic, and modern variants. Display the formulation, parameter source, fit status, and dataset version with each prediction.
- Observation overlays with uncertainty where supported. Selecting a point opens its printed-page citation, review status, original-versus-derived role, and associated residual.
- Linked residual plots so readers can inspect where a model departs from the observations and distinguish repeated readings from independent observing sessions.

## Parallax and scale

When suitable data and forward calculations exist, add geocentric versus topocentric directions, observing-site and baseline controls, and a labeled magnification of the angular difference. Display the actual signal in angular units alongside any visual exaggeration. Keep diurnal parallax and orbital triangulation distinct, and state the assumed distance scale.

## Research integrity and reproducibility

Observed points, model predictions, historical reductions, fitted results, and illustrative geometry need distinct visual treatment and labels. Keep unresolved measurements visible through review filters; do not interpolate across gaps as though measurements existed. Exclude calibration stars from a Mars selection while retaining them in catalog inspection.

Equivalent relative trajectories expressed in different frames must produce equivalent apparent directions under equivalent observer assumptions. A camera change must not be presented as observational discrimination between cosmologies. Ptolemaic or other historical formulations need their own documented geometry; changing the origin of a modern trajectory is insufficient.

Provide shareable view settings and downloadable plots and plotted data with model parameters, data versions, filters, and time conventions. The viewer will connect the numerical catalog to public book and PDF citations, with shareable data and calculations.

## Visualization development

1. **Catalog explorer:** inspect the reviewed dataset and its completeness, provenance, and selection filters. Begin with declination versus recorded date; add a full sky path only when coordinate and clock normalization support it.
2. **Planetary geometry:** add animated orbital and observer views, with explicitly labeled illustrative geometry where observational inputs remain insufficient.
3. **Model comparison:** connect the independently tested prediction engines, synchronized observations, residual plots, and original-parameter versus refit controls.
4. **Parallax and broader records:** add the validated observer geometry and sensitivity results, then extend the shared interface to other planets and records.

Acceptance requires reproducible views, clear units and scale, traceable observations, visible review limitations, and agreement between plotted values and exported numerical results. Visualization work follows the data and model dependencies.
