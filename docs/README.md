# Project knowledge base

These notes record Astrakyle's learning progress, working assumptions, and open questions. They are evolving research notes, not claims of completed experiments or implemented features.

## Research notes

| Note | Scope | Status |
| --- | --- | --- |
| [001 — Satellite service conditions](research/001-satellite-service-conditions.md) | Visibility, elevation, tracking, and the other requirements for communication | Conceptual study; implementation pending |
| [002 — Reference frames and Earth’s rotation](research/002-reference-frames-and-earth-rotation.md) | ECI/ECEF transformations, local ENU, azimuth, elevation, and range | Conceptual study; implementation pending |

## Current project direction

Astrakyle explores adaptive satellite communications through incremental learning and simulation. The initial model uses circular low Earth orbits, a rotating spherical Earth, synthetic ground demand, and simplified satellite capacities.

The planned decisions are which satellite serves each ground location and how capacity is allocated. Evaluation will consider demand served, satisfaction at each location, and periods without service. Future scenarios include satellite failures, satellite additions, and regional demand changes.

The learning sequence is orbital mechanics → visibility and coverage → constellations → classical optimization/control → AI and reinforcement learning. The service-condition concepts in Note 001 and the reference-frame geometry in Note 002 have been studied conceptually. Simulation and later optimization/AI stages remain planned work.

## Maintaining these notes

Use numbered Markdown notes for new topics, with a date, status, assumptions, explanations, references, and open questions. Keep diagrams in `figures/`, embed them using relative paths, and distinguish illustrative examples from simulation results. Update this index as the project progresses.

The initial record was consolidated on 2026-10-18 from the project chats **Research** and **Satellite Service Conditions**. Equations and original diagrams in Note 001 make the discussed geometry explicit; they do not represent a completed simulation.

Note 002 was consolidated on 2026-10-18 from **Reference frames and Earth’s rotation**. It extends the visibility geometry with explicit coordinate transformations and a local pointing example.
