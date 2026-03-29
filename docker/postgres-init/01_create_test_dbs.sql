-- =============================================================================
-- PostgreSQL init script: create the additional test database.
--
-- Mounted at /docker-entrypoint-initdb.d/ in the db_inttest container.
-- The primary database (wine_fermentation) is created by the POSTGRES_DB env var.
-- This script creates the second database needed by the Analysis Engine
-- integration tests (wine_fermentation_test).
-- =============================================================================
CREATE DATABASE wine_fermentation_test;
