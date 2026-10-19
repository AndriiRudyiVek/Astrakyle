# Satellite communications knowledge base

This knowledge base explains the orbital mechanics, geometry, and communication principles behind adaptive satellite constellations. Each article defines its assumptions, notation, and physical concepts so it can be read independently or used in a similar project.

## Articles

| Article | Scope |
| --- | --- |
| [001 — Satellite service conditions](research/001-satellite-service-conditions.md) | Visibility, elevation, antenna coverage, radio links, capacity, and service continuity |
| [002 — Reference frames and Earth’s rotation](research/002-reference-frames-and-earth-rotation.md) | ECI, ECEF, ENU, coordinate transformations, and pointing angles |
| [003 — Circular orbital motion](research/003-circular-orbital-motion.md) | Orbital radius, speed, period, inclination, RAAN, and ECI position over time |
| [004 — Orbital-plane diversity and RAAN](research/004-orbital-plane-diversity-and-raan.md) | Plane orientation versus orbital phase, and implications for access timing |

For a conceptual introduction, begin with service conditions. To calculate a satellite’s apparent position, combine circular orbital motion with the reference-frame transformations, then evaluate elevation and access.

## Relationship to Astrakyle

Astrakyle investigates adaptive satellite communications using a simplified initial model: circular low Earth orbits, a rotating spherical Earth, ground demand, and limited satellite capacity. Orbital motion determines satellite positions; reference-frame transformations relate them to ground locations; service conditions determine which communication links are possible.

These articles explain the underlying theory. Project scope and development status are described in the [repository README](../README.md).

## Writing conventions

Write standalone, encyclopedia-style articles for readers with no access to project conversations. Cover each topic in sufficient detail to explain its meaning, derivation, application, and limitations.

- Introduce the physical problem and define terminology, symbols, units, frames, and sign conventions before using them.
- State assumptions explicitly and distinguish simplified models from more general cases.
- Explain equations and include worked examples with reproducible inputs and clearly rounded outputs.
- Use diagrams when they clarify geometry or relationships. Keep editable assets in `figures/` and embed them with relative paths.
- Cite authoritative external references. Cross-link related articles for further depth, while retaining the context needed to understand the current article.
- Exclude references to local chats, session history, learning progress, implementation checklists, open questions, and project-specific next steps.
- Keep project planning and implementation status outside the technical articles.
- Use numbered Markdown filenames and update this index when adding an article.

For compatible math rendering, put matrix rows on separate lines, keep equality signs on a line with an expression, and use simple supported commands such as `\mathrm{atan2}`. Avoid `\operatorname`, which the current renderer rejects.
