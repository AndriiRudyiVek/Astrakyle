# 001 — Satellite service conditions

## Overview

A satellite being above the horizon is a geometric prerequisite in a surface-based geometric model. Successful communication also requires suitable antenna coverage, a usable radio link, available communication capacity, and a path through the network. Visibility alone does not guarantee service.

## Conditions for service

| Condition | Meaning |
| --- | --- |
| Visibility | Earth does not block the line of sight, and elevation meets the chosen minimum. |
| Antenna/beam coverage | The location lies within an active satellite beam, and the ground terminal can point or steer appropriately. |
| Usable radio link | Received signal quality supports the intended communication, given power, antenna gains, losses, noise, and interference. |
| Available capacity | Sufficient bandwidth, power, time slots, or other communication resources are available for the requested service. |
| Network connectivity | A route connects the satellite link to its destination, through a gateway or, where applicable, inter-satellite links. |

Beam coverage and allocation are distinct: a location inside a beam can still receive insufficient capacity. ESA describes both multi-beam coverage and adapting resources to changing demand [3].

## Visibility and elevation

The **local horizon** is the plane tangent to Earth at the ground location in a spherical-Earth model. **Elevation** is the angle from that plane toward the satellite. It is an angle, not the satellite's altitude above Earth's surface.

- **90°:** directly overhead, at the zenith.
- **0°:** on the ideal geometric horizon.
- **Below 0°:** blocked by Earth for a ground point on the spherical surface.
- **At or above the minimum elevation:** passes the geometric eligibility rule.

![Elevation measured from the local horizon, with zenith and an illustrative minimum elevation](../figures/satellite-elevation.svg)

*Figure 1. A local cross-section. The 30° satellite elevation and 10° mask are illustrative, not universal operating thresholds. The Earth curvature is schematic.*

A positive minimum elevation excludes low-angle links. Real systems may also use a direction-dependent mask for terrain or structures; minimum-elevation and azimuth-dependent masks are supported in established access-analysis tools [1]. The minimum elevation is a system-design parameter rather than a universal constant.

### Calculation for a spherical Earth

Let **g** and **s** be the Earth-centered position vectors of the ground location and satellite, expressed in the **same coordinate frame at the same time**. Use consistent distance units.

The unit local-up vector and the ground-to-satellite vector are

$$
\hat{\mathbf{u}} = \frac{\mathbf{g}}{\|\mathbf{g}\|}, \qquad
\boldsymbol{\rho} = \mathbf{s}-\mathbf{g}.
$$

Projecting the line of sight onto local up gives

$$
e = \arcsin\left(\frac{\boldsymbol{\rho}\cdot\hat{\mathbf{u}}}{\|\boldsymbol{\rho}\|}\right).
$$

For numerical implementation, clamp the argument to [-1, 1] before applying arcsine, reject a zero-length line-of-sight vector, and convert radians to degrees if the threshold is in degrees.

For a surface ground point and a nonnegative minimum elevation, the geometric eligibility rule is

$$
V(g,s,t) = \begin{cases}
1, & e(g,s,t) \ge e_{\min}, \\
0, & e(g,s,t) < e_{\min}.
\end{cases}
$$

The equality convention includes the boundary; exactly 0° is only an ideal tangent ray. This rule does not model terrain, atmospheric refraction, or radio propagation. On an ellipsoidal Earth, the local surface normal generally differs from the geocentric radial direction used above.

### A small geometry example

Take a ground location **g** = (R, 0, 0), so local up points along the positive x-axis. If **s** = (R + a, b, 0), with a > 0 and b ≥ 0, then

$$
e = \mathrm{atan2}(a,b).
$$

For a = 500 km and b = 500 km, elevation is 45°. For b = 0, the satellite is overhead at 90°. Here a is the local-up displacement; it is not generally orbital altitude. These examples describe instantaneous geometry rather than a trajectory over time.

## Motion, tracking, and handovers

A geostationary satellite ideally remains at the same apparent position relative to a fixed ground observer. A low Earth orbit satellite moves across the observer's sky, so directional terminals must track it and continued service may require switching to another satellite. ESA's introductory overview explains this distinction [2].

Earth rotation and orbital motion both affect the geometry over time. In an Earth-fixed frame, a fixed ground station has constant coordinates while the satellite coordinates change. In an inertial frame, the ground location rotates with Earth. Mixing these frames would produce incorrect elevation angles. [Reference frames and Earth’s rotation](002-reference-frames-and-earth-rotation.md) develops the transformations and local pointing calculations.

![Two overlapping geometric access windows with an example opportunity for handover](../figures/access-windows.svg)

*Figure 2. Schematic access windows after applying an elevation mask. The overlap offers a possible handover interval; capacity, link quality, and network connectivity must still be checked. Bar widths are illustrative and are not simulated pass durations.*

Changing which satellite serves a location, steering a beam, and allocating capacity are communication-resource decisions. They do not necessarily involve changing satellite orbits. Resource allocation can therefore adapt to changing demand even when the orbital trajectories remain unchanged.

## Access intervals and service continuity

An **access interval** is a continuous span of time during which the geometric visibility condition holds for a station–satellite pair. Its boundaries occur when elevation crosses the selected mask. A station can have access to several satellites simultaneously, or none at all. Access is a geometric opportunity; service additionally depends on the other conditions above.

Evaluating elevation at discrete times approximates these intervals. A coarse sampling interval can miss a short pass or shift its apparent beginning and end. More accurate boundary times can be obtained by locating threshold crossings between samples. The appropriate resolution depends on the required timing accuracy and how quickly elevation changes.

A **handover** transfers service between satellites or beams. Overlapping access windows provide time to establish the next connection before the current one becomes unavailable. An overlap alone does not ensure uninterrupted service: the next link must also have capacity, suitable antenna pointing, and network connectivity.

## Scope of the geometric model

The elevation rule assumes a ground point on an unobstructed spherical surface and a straight ray to the satellite. It does not evaluate signal quality or account for terrain, buildings, or atmospheric refraction. For elevated observers, the visible geometric horizon can lie below the local horizontal; a negative elevation is then not by itself proof of Earth blockage. Such cases require explicit line-of-sight obstruction geometry.

A link budget accounts for transmitter power, antenna gains, propagation and equipment losses, and receiver noise. Together with the required data rate and modulation/coding, it determines whether a geometrically available link can carry useful information. Capacity allocation then determines how those usable links share limited resources.

## References

1. MathWorks, [groundStation: minimum elevation and visibility masks](https://www.mathworks.com/help/satcom/ref/matlabshared.satellitescenario.satellitescenario.groundstation.html). Accessed 2026-10-18.
2. ESA, [About Telecommunications](https://www.esa.int/Applications/Connectivity_and_Secure_Communications/About_Telecommunications). Accessed 2026-10-18.
3. ESA, [Automatically balanced load and increased capacity in communication systems and data networks](https://www.esa.int/Enabling_Support/Space_Engineering_Technology/Automatically_balanced_load_and_increased_capacity_in_communication_systems_and_data_networks). Accessed 2026-10-18.

Both figures are original, editable SVG diagrams created for this repository.
