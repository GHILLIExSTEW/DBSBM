-- Simple database connection test
-- Run this first to make sure you can connect to your database

SELECT 'Database connection successful!' as status;
SELECT NOW() as current_time;
SELECT DATABASE() as current_database;
SELECT USER() as current_user;
