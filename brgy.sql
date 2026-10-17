create database brgy_db;
use brgy_db;

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` varchar(20) DEFAULT 'Staff',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `residents` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `first_name` varchar(100) NOT NULL,
  `middle_name` varchar(100) DEFAULT NULL,
  `last_name` varchar(100) NOT NULL,
  `extension` varchar(10) DEFAULT 'N/A',
  `gender` varchar(10) DEFAULT NULL,
  `birthdate` date DEFAULT NULL,
  `civil_status` varchar(20) DEFAULT NULL,
  `contact` varchar(20) DEFAULT NULL,
  `occupation` varchar(100) DEFAULT NULL,
  `voter_status` varchar(20) DEFAULT 'Non-voter',
  `emergency_contact` varchar(20) DEFAULT NULL,
  `purok` varchar(20) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `households` (
  `household_id` int(11) NOT NULL AUTO_INCREMENT,
  `head_id` int(11) NOT NULL,
  `purok` varchar(20) DEFAULT NULL,
  `Members_Count` int(11) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`household_id`),
  KEY `head_id` (`head_id`),
  CONSTRAINT `households_ibfk_1` FOREIGN KEY (`head_id`) REFERENCES `residents` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `household_members` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `household_id` int(11) NOT NULL,
  `resident_id` int(11) NOT NULL,
  `relationship` varchar(50) DEFAULT 'Member',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `household_id` (`household_id`),
  KEY `resident_id` (`resident_id`),
  CONSTRAINT `household_members_ibfk_1` FOREIGN KEY (`household_id`) REFERENCES `households` (`household_id`) ON DELETE CASCADE,
  CONSTRAINT `household_members_ibfk_2` FOREIGN KEY (`resident_id`) REFERENCES `residents` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `blotters` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `complainant_name` varchar(255) NOT NULL,
  `defendant_name` varchar(255) NOT NULL,
  `nature_of_case` varchar(100) DEFAULT NULL,
  `complainant_address` varchar(255) DEFAULT NULL,
  `complainant_contact` varchar(50) DEFAULT NULL,
  `defendant_address` varchar(255) DEFAULT NULL,
  `defendant_contact` varchar(50) DEFAULT NULL,
  `status` varchar(50) DEFAULT 'Active',
  `remarks` text DEFAULT NULL,
  `hearing_schedule` datetime DEFAULT NULL,
  `last_incident` date DEFAULT NULL,
  `total_incidents` int(11) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `blotters_incidents` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `blotter_id` int(11) NOT NULL,
  `incident_date` date DEFAULT NULL,
  `details` text DEFAULT NULL,
  `statement` text DEFAULT NULL,
  `speaker` varchar(20) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `blotter_id` (`blotter_id`),
  CONSTRAINT `blotters_incidents_ibfk_1` FOREIGN KEY (`blotter_id`) REFERENCES `blotters` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `officials` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `position` varchar(100) NOT NULL,
  `full_name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `certificate_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `resident_id` int(11) NOT NULL,
  `certificate_type` varchar(100) DEFAULT NULL,
  `purpose` varchar(255) DEFAULT NULL,
  `or_number` int(11) DEFAULT NULL,
  `amount_paid` decimal(10,2) DEFAULT 0.00,
  `issued_by` varchar(50) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

COMMIT;