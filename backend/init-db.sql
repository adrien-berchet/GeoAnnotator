-- Initialize GeoAnnotator PostgreSQL database with PostGIS extension

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Verify PostGIS installation
SELECT PostGIS_version();

-- Create indexes for common geospatial queries (will be handled by Django migrations)
-- This file is mainly for documentation and manual setup if needed
