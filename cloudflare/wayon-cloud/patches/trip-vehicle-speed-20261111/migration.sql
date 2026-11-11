-- trip-vehicle-speed-20261111: marks trips stored with vehicle speed statistics.
-- Existing rows keep NULL, so their speed columns are never filled later.
ALTER TABLE trips ADD COLUMN speed_stats INTEGER;
