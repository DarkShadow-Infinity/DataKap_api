-- SQL Schema for DataKap API
-- This script defines the tables for users and registrations.

-- -----------------------------------------------------
-- Table `Usuarios`
-- Stores user information for authentication and roles.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Usuarios (
  id VARCHAR(255) PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL, -- Should be stored as a hash
  full_name VARCHAR(255),
  phone VARCHAR(50),
  role VARCHAR(50) CHECK (role IN ('admin', 'leader', 'promoter')),
  goal INTEGER,
  status VARCHAR(50) CHECK (status IN ('active', 'pending', 'disabled')),
  verification_code VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  temporary_password VARCHAR(255)
);

-- -----------------------------------------------------
-- Table `Registros`
-- Stores the data collected by the users.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Registros (
  id VARCHAR(255) PRIMARY KEY,
  user_id VARCHAR(255),
  role VARCHAR(50) CHECK (role IN ('promoter', 'leader')),
  requires_photo BOOLEAN DEFAULT FALSE,
  fields JSON, -- Using JSON type for flexibility
  photo_url VARCHAR(255),
  sync_status VARCHAR(50) CHECK (sync_status IN ('synced', 'pending', 'failed', 'deleted')),
  client_request_id VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  synced_at TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES Usuarios(id)
);

-- ---
-- Notes:
-- 1. The `password` in the `Usuarios` table should always be stored as a secure hash (e.g., using bcrypt), never as plain text.
-- 2. The `fields` column in the `Registros` table is defined as JSON. This is well-supported in PostgreSQL. If using MySQL, you might need a recent version or consider using the TEXT type and handling JSON parsing in the application.
-- 3. This schema is a starting point and can be extended as needed.
-- ---
