"""Equations from knowledge-base articles 002 and 003; km, seconds, degrees."""
from dataclasses import dataclass
from math import atan2, cos, degrees, hypot, isfinite, pi, radians, sin, sqrt

EARTH_RADIUS_KM = 6378.0
EARTH_MU_KM3_S2 = 398600.0
EARTH_ROTATION_RAD_S = 7.292115e-5


@dataclass(frozen=True)
class CircularOrbit:
    altitude_km: float = 500.0
    inclination_deg: float = 53.0
    raan_deg: float = 0.0
    initial_angle_deg: float = 0.0

    def __post_init__(self):
        if not all(isfinite(v) for v in vars(self).values()):
            raise ValueError("Orbit inputs must be finite")
        if self.altitude_km <= 0 or not 0 <= self.inclination_deg <= 180:
            raise ValueError("Altitude must be positive; inclination must be in [0, 180]")

    @property
    def angular_speed(self):
        return sqrt(EARTH_MU_KM3_S2 / (EARTH_RADIUS_KM + self.altitude_km) ** 3)

    @property
    def period_s(self):
        return 2 * pi / self.angular_speed

    def position_eci(self, time_s):
        r = EARTH_RADIUS_KM + self.altitude_km
        u = radians(self.initial_angle_deg) + self.angular_speed * time_s
        i, node = radians(self.inclination_deg), radians(self.raan_deg)
        return (r * (cos(node) * cos(u) - sin(node) * cos(i) * sin(u)),
                r * (sin(node) * cos(u) + cos(node) * cos(i) * sin(u)),
                r * sin(i) * sin(u))


@dataclass(frozen=True)
class GroundStation:
    latitude_deg: float = 50.45
    longitude_deg: float = 30.52

    def __post_init__(self):
        if not all(isfinite(v) for v in vars(self).values()):
            raise ValueError("Station coordinates must be finite")
        if not -90 <= self.latitude_deg <= 90 or not -180 <= self.longitude_deg <= 180:
            raise ValueError("Latitude must be in [-90, 90]; longitude in [-180, 180]")

    @property
    def position_ecef(self):
        p, l = radians(self.latitude_deg), radians(self.longitude_deg)
        return (EARTH_RADIUS_KM * cos(p) * cos(l),
                EARTH_RADIUS_KM * cos(p) * sin(l), EARTH_RADIUS_KM * sin(p))


def eci_to_ecef(position, time_s, earth_angle_deg=0.0):
    """Synthetic epoch: Greenwich aligns with ECI +x when angle is zero."""
    theta = radians(earth_angle_deg) + EARTH_ROTATION_RAD_S * time_s
    x, y, z = position
    return cos(theta) * x + sin(theta) * y, -sin(theta) * x + cos(theta) * y, z


def elevation_deg(orbit, station, time_s, earth_angle_deg=0.0):
    satellite = eci_to_ecef(orbit.position_eci(time_s), time_s, earth_angle_deg)
    dx, dy, dz = (s - g for s, g in zip(satellite, station.position_ecef))
    p, l = radians(station.latitude_deg), radians(station.longitude_deg)
    east = -sin(l) * dx + cos(l) * dy
    north = -sin(p) * cos(l) * dx - sin(p) * sin(l) * dy + cos(p) * dz
    up = cos(p) * cos(l) * dx + cos(p) * sin(l) * dy + sin(p) * dz
    return degrees(atan2(up, hypot(east, north)))
