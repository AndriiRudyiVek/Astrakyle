# 003 — Circular orbital motion

## Overview

An ideal circular orbit is a fixed circle in inertial space, traversed at constant angular speed. Altitude determines its radius and speed; inclination and RAAN orient its plane; an initial orbital angle places the satellite on the circle. We can calculate position directly at any requested time without stepping through intermediate times.

This supplies the satellite ECI position needed by [Reference frames and Earth’s rotation](002-reference-frames-and-earth-rotation.md). After conversion to ECEF and local ENU coordinates, we can apply the visibility rule in [Satellite service conditions](001-satellite-service-conditions.md).

## Assumptions and inputs

Use an ideal two-body model with a spherical Earth, negligible satellite mass, and zero orbital eccentricity. Ignore atmospheric drag, Earth’s oblateness, third-body gravity, and maneuvers. The orbital plane remains fixed in a simplified Earth-centered inertial (ECI) frame: the origin is Earth’s center, +z points along the north polar axis, and +x and +y are fixed reference directions in the equatorial plane. They do not rotate with Earth.

| Input | Meaning | Units or convention |
| --- | --- | --- |
| h | Altitude above the spherical surface | km |
| i | Inclination: orientation of the orbital plane relative to the equator | radians in calculations; 0°–180° |
| Ω | Right ascension of the ascending node (RAAN) | From ECI +x toward +y in the equatorial plane |
| u₀ | Initial argument of latitude | From the ascending node, in the direction of motion |
| t₀ | Epoch of the initial position | Time reference |
| t − t₀ | Elapsed time | seconds |

The worked examples use the rounded constants: **R_E = 6378 km** and **μ_E = 398600 km³/s²**. These are educational model choices, not precision geodetic constants. Keep the same radius and units in the ground-location model.

The ascending node is the equatorial crossing toward the north; the descending node is the crossing toward the south. Inclination 90° gives a polar orbit. For an exactly equatorial orbit, the ascending node and RAAN are undefined; choose a reference direction consistently, such as Ω = 0, and measure the initial phase from it.

## 1. Radius, speed, and period

Orbital radius is measured from Earth’s center, not its surface:

$$
r = R_E + h.
$$

Gravity supplies the centripetal acceleration:

$$
\frac{\mu_E}{r^2} = \frac{v^2}{r}.
$$

Therefore, orbital speed and angular speed are

$$
v = \sqrt{\frac{\mu_E}{r}}, \qquad n = \sqrt{\frac{\mu_E}{r^3}}.
$$

Here v is in km/s and n is in rad/s. The orbital period is

$$
T = \frac{2\pi}{n} = 2\pi\sqrt{\frac{r^3}{\mu_E}}.
$$

A higher circular orbit has both a longer path and a lower speed. Its period increases as r to the power 3/2, consistent with Kepler’s third law [1]. Doubling the **radius**, rather than the altitude, makes the period about 2.83 times longer.

## 2. Advance the orbital angle

$$
u(t) = u_0 + n(t-t_0).
$$

In this formula the symbol is **u**, the argument of latitude. It is convenient for a circular orbit because there is no unique periapsis (closest point) from which to measure a true anomaly. Angles may be reduced modulo 2π for evaluation.

Within the orbital plane, the position is simply

$$
\mathbf{r}_{\mathrm{plane}}(t) = r
\begin{bmatrix}
\cos u(t) \\
\sin u(t) \\
0
\end{bmatrix}.
$$

## 3. Orient the circle in ECI

First tilt the circle about its x-axis by inclination i, then rotate it about the ECI z-axis by RAAN Ω. Positive rotations follow the right-hand rule: a positive rotation about +z carries +x toward +y. The resulting components are:

$$
x(t) = r\left[\cos\Omega\cos u(t)-\sin\Omega\cos i\sin u(t)\right].
$$

$$
y(t) = r\left[\sin\Omega\cos u(t)+\cos\Omega\cos i\sin u(t)\right].
$$

$$
z(t) = r\sin i\sin u(t).
$$

Earth’s rotation is **not added to these ECI equations**. It enters later when expressing the position in ECEF. RAAN is measured from the inertial reference direction, not from the rotating Greenwich meridian.

Although z changes, altitude remains constant:

$$
\sqrt{x^2+y^2+z^2} = r, \qquad h = r-R_E.
$$

The z-coordinate measures displacement from the equatorial plane. It is not altitude above Earth’s surface.

## Worked examples

### A 500 km orbit inclined at 45°

Set h = 500 km, i = 45°, Ω = 0°, and u₀ = 0°. The satellite starts at the ascending node. Convert angles to radians before evaluating trigonometric functions.

| Quantity | Value |
| --- | --- |
| Orbital radius | 6878 km |
| Orbital speed | 7.6127 km/s |
| Angular speed | 0.001106816 rad/s |
| Period | 94.6135 minutes |

| Elapsed time | Orbital angle | ECI position (x, y, z), km |
| --- | --- | --- |
| 0 | 0° | (6878, 0, 0) |
| T/4 ≈ 23.6534 min | 90° | (0, 4863.48, 4863.48) |
| T/2 ≈ 47.3068 min | 180° | (−6878, 0, 0) |
| 3T/4 ≈ 70.9601 min | 270° | (0, −4863.48, −4863.48) |
| T ≈ 94.6135 min | 360° | (6878, 0, 0) |

### Separate inclination, RAAN, and initial phase

1. Change only i to 90°. With Ω = 0°, the orbit lies in the xz-plane. After a quarter orbit, the satellite is above the North Pole at (0, 0, 6878) km.
2. Change Ω to 90°. The polar plane rotates into the yz-plane. With u₀ = 0°, the satellite starts at (0, 6878, 0) km and still reaches the North Pole after a quarter orbit.
3. Change u₀ to 90°. The satellite now starts above the North Pole. After a quarter orbit it reaches (0, −6878, 0) km, crossing the equator southward at the descending node.

For the third configuration, 600 seconds after the epoch:

```text
u = π/2 + 0.0011068159014474056 × 600
  ≈ 128.0495°

ECI position ≈ (0, −4239.20, 5416.28) km
```

The decreasing z-coordinate does not indicate decreasing altitude. The radius is still 6878 km and the altitude is still 500 km. These values were recomputed from the stated constants, rather than rounded intermediate angles . All examples are analytical illustrations, not simulation results.

## Calculation recipe

```text
Inputs: elapsed_seconds, altitude_km, inclination, RAAN, initial_angle
Convert input angles to radians if supplied in degrees.

r = 6378 + altitude_km
n = sqrt(398600 / r³)
u = initial_angle + n × elapsed_seconds

x = r × (cos(RAAN) × cos(u) − sin(RAAN) × cos(inclination) × sin(u))
y = r × (sin(RAAN) × cos(u) + cos(RAAN) × cos(inclination) × sin(u))
z = r × sin(inclination) × sin(u)

Return (x, y, z) in km in the chosen ECI frame.
```

## Geometric properties and model limitations

A circular trajectory repeats after one period. After half a period, the position vector is the negative of its starting value; after a full period, it returns to that value. Rotating the orbital plane changes the coordinate components but preserves the orbital radius, speed, and period.

The model has constant **speed**, but not constant **velocity**. Velocity is tangent to the circle and continuously changes direction; gravitational acceleration points toward Earth’s center. The angular speed n describes motion within the orbital plane and is distinct from Earth’s rotation rate.

Inclination determines how far the trajectory extends north and south of the equator, while RAAN rotates that plane around the polar axis. Initial phase changes the satellite’s location within the same plane. These parameters separate orbit size, orientation, and timing, making the circular model useful for studying constellation geometry.

The formulas describe an unperturbed circular orbit. An eccentric orbit has a changing radius and nonuniform angular motion. Atmospheric drag, nonspherical gravity, and other perturbations can alter the orbit and its orientation over time. Those effects require a more detailed propagation model.

For a complete ground-access calculation, the resulting ECI position must be paired with an observer position at the same time, transformed into a common frame, and converted into local elevation. The coordinate transformations and elevation definitions are developed in [Reference frames and Earth’s rotation](002-reference-frames-and-earth-rotation.md).

## References

1. NASA, [Basics of Space Flight — Gravity & Mechanics](https://science.nasa.gov/learn/basics-of-space-flight/chapter3-3/), circular motion and Kepler’s laws. Accessed 2026-10-18.
