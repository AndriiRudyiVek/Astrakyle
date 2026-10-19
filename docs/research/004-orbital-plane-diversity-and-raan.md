# 004 — Orbital-plane diversity and RAAN

## Plane orientation and position along an orbit

Two satellites can follow the same circular path at different orbital angles, or follow different paths whose planes have different orientations. These choices affect when a ground station sees a satellite.

The **ascending node** is the point where an orbit crosses the equatorial plane from south to north. **Right ascension of the ascending node (RAAN)**, written Ω, is measured in the equatorial plane from an inertial reference direction toward the ascending node, positive about Earth's north polar axis [1]. In this simplified model, that reference is ECI +x. RAAN is not the geographic longitude of a fixed ground location: Earth rotates beneath the inertial reference axes.

Three angles have distinct roles:

| Angle | Meaning |
| --- | --- |
| Inclination i | Tilt of the orbital plane relative to the equator |
| RAAN Ω | Orientation of the ascending-node direction around the polar axis |
| Argument of latitude u | Position within the orbital plane, measured from the ascending node in the direction of travel |

Inclination and RAAN specify the orbital plane and direction of motion. Argument of latitude specifies where the satellite is on its circular orbit. Circular orbits do not have a unique periapsis, so argument of latitude avoids that ambiguity. Exactly equatorial orbits have no unique ascending node; a consistent reference convention is needed.

## Rotating an orbital plane

For a circular orbit with radius r, the position from article [003](003-circular-orbital-motion.md) can be written as

$$
\mathbf r^I(t)=R_z(\Omega)R_x(i)
\begin{bmatrix}
r\cos u(t) \\
r\sin u(t) \\
0
\end{bmatrix},
\qquad u(t)=u_0+\sqrt{\mu_E/r^3}\,t.
$$

Changing only RAAN by ΔΩ therefore gives

$$
\mathbf r_{\mathrm{new}}^I(t)=R_z(\Delta\Omega)\mathbf r_{\mathrm{old}}^I(t).
$$

This rotates the whole trajectory around the polar axis. It preserves radius, altitude, speed, orbital period, inclination, and the satellite's z-coordinate at each time. It changes x and y, which changes the satellite's geometry relative to the station.

For example, set altitude to 500 km, inclination to 53°, and initial argument of latitude to 180°. The orbital radius is 6,878 km. The initial position, rounded to 0.01 km, is:

| RAAN | Initial ECI position (x, y, z), km |
| --- | --- |
| 0° | (−6878.00, 0.00, 0.00) |
| 60° | (−3439.00, −5956.52, 0.00) |
| 120° | (3439.00, −5956.52, 0.00) |
| 180° | (6878.00, 0.00, 0.00) |

These are descending-node positions. The same argument of latitude is measured from a different ascending node in each configuration.

With equal orbital radii, two satellites retain their difference in argument of latitude because they have equal angular speeds. They remain physically antipodal only when their planes and the other orientation conventions agree and their arguments differ by 180°. After RAAN changes, a 180° difference in arguments is not generally a 180° Earth-centered separation.

For inclination 53°, RAAN values 0° and 180° describe different planes, even though their equatorial node lines coincide. As a useful geometric check, satellites at (Ω, u) = (0°, 0°) and (180°, 180°) start at the same position in this ideal model but cross the equator in different directions. This configuration comparison does not address collision avoidance or operational constellation design.

## Why plane diversity changes access timing

A ground station rotates with Earth. Its distance from an inertially fixed orbital plane changes through the day. Moving satellites along one plane supplies more opportunities while that plane has favorable station geometry, but cannot eliminate times when the entire orbit lies outside the station's elevation-limited field of view.

A second plane can provide access during some of those gaps. Its benefit depends on inclination, station latitude, RAAN, orbital phase, altitude, elevation mask, and observation window. Changing RAAN does not guarantee a uniform shift of every pass by a fixed number of hours: orbital phase continues evolving as Earth rotates.

To evaluate geometric access, propagate each satellite independently, transform to ECEF, and compute local elevation as in article [002](002-reference-frames-and-earth-rotation.md). Access from at least one satellite is the union of their threshold-qualified intervals. Overlapping intervals contribute their duration only once.

Total access and continuity are different properties. Two configurations can have nearly equal total access while distributing it very differently. The longest gap is one useful continuity metric; it does not fully describe the gap distribution. Include both observation-window boundaries and keep their gaps separate unless a repeating pattern has been independently established.

## Model limitations

This discussion assumes circular two-body orbits and a spherical Earth rotating at constant rate. The planes are fixed in inertial space. Real orbital perturbations can change RAAN and other elements. Results from one station, epoch, and finite window establish neither a globally optimal constellation nor long-term coverage. Plane-diversity comparisons should be treated as controlled geometric experiments.

## References

1. NASA Glenn Research Center, [Right ascension of ascending node](https://www.grc.nasa.gov/www/k-12/TRC/laefs/laefs_r.html), definition of the orbital element. Accessed 2026-10-19.
