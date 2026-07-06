import pytest

from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.gm.cluster_speed import (
  gm_cluster_cruise_speed_from_raw_ms,
  gm_cluster_display_kph_from_raw_display_kph,
  gm_raw_cruise_speed_from_cluster_ms,
  gm_raw_display_kph_from_cluster_display_kph,
)


@pytest.mark.parametrize("raw_kph, cluster_kph", [
  (0.0, 0.0),
  (24.0, 25.0),
  (28.0, 29.0),
  (95.0, 100.0),
  (154.0, 160.0),
])
def test_raw_display_speed_to_cluster_display_speed(raw_kph, cluster_kph):
  assert gm_cluster_display_kph_from_raw_display_kph(raw_kph) == pytest.approx(cluster_kph)


@pytest.mark.parametrize("cluster_kph, raw_kph", [
  (0.0, 0.0),
  (25.0, 24.0),
  (30.0, 28.0),
  (100.0, 95.0),
  (160.0, 154.0),
])
def test_cluster_display_speed_to_raw_display_speed(cluster_kph, raw_kph):
  assert gm_raw_display_kph_from_cluster_display_kph(cluster_kph) == pytest.approx(raw_kph)


def test_cruise_speed_helpers_use_ms():
  raw_speed_ms = 95.0 * CV.KPH_TO_MS
  cluster_speed_ms = gm_cluster_cruise_speed_from_raw_ms(raw_speed_ms)

  assert cluster_speed_ms * CV.MS_TO_KPH == pytest.approx(100.0)
  assert gm_raw_cruise_speed_from_cluster_ms(cluster_speed_ms) == pytest.approx(raw_speed_ms)
