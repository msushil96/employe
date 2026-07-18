-- Run this against the target MySQL database to initialize schema.
-- Database name expected: employee_directory (see .env.example)

CREATE DATABASE IF NOT EXISTS employee_directory;
USE employee_directory;

CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample seed data (optional)
INSERT INTO employees (name, role, department, email) VALUES
('Asha Rao', 'Backend Engineer', 'Engineering', 'asha.rao@example.com'),
('Vikram Shah', 'DevOps Engineer', 'Infrastructure', 'vikram.shah@example.com');
