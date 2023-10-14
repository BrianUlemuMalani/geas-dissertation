-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Oct 09, 2023 at 02:15 PM
-- Server version: 10.4.28-MariaDB
-- PHP Version: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `gate`
--

-- --------------------------------------------------------

--
-- Table structure for table `admin`
--

CREATE TABLE `admin` (
  `id` int(11) NOT NULL,
  `username` text NOT NULL,
  `password` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `admin`
--

INSERT INTO `admin` (`id`, `username`, `password`) VALUES
(1, 'brian', 'brian1234');

-- --------------------------------------------------------

--
-- Table structure for table `auth_log`
--

CREATE TABLE `auth_log` (
  `auth_id` int(11) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `actions` varchar(255) DEFAULT NULL,
  `time_stamp` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `encodings`
--

CREATE TABLE `encodings` (
  `encod_id` int(11) NOT NULL,
  `user_id` varchar(10) DEFAULT NULL,
  `encoding` blob DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `face_image`
--

CREATE TABLE `face_image` (
  `facial_id` int(11) NOT NULL,
  `user_id` varchar(10) DEFAULT NULL,
  `img_data` blob DEFAULT NULL,
  `qr_code` blob DEFAULT NULL,
  `hashed_pin` varchar(200) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `reg_user`
--

CREATE TABLE `reg_user` (
  `user_id` varchar(10) NOT NULL,
  `firstname` varchar(200) DEFAULT NULL,
  `lastname` varchar(200) DEFAULT NULL,
  `phone_number` varchar(13) DEFAULT NULL,
  `gender` varchar(10) DEFAULT NULL,
  `reg_date` date DEFAULT curdate()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Triggers `reg_user`
--
DELIMITER $$
CREATE TRIGGER `log_delete_reg_user` AFTER DELETE ON `reg_user` FOR EACH ROW BEGIN
    INSERT INTO gate.auth_log (name, actions)
    VALUES (CONCAT(OLD.firstname, ' ', OLD.lastname), 'DELETE');
END
$$
DELIMITER ;
DELIMITER $$
CREATE TRIGGER `log_insert_reg_user` AFTER INSERT ON `reg_user` FOR EACH ROW BEGIN
    INSERT INTO gate.auth_log (name, actions)
    VALUES (CONCAT(NEW.firstname, ' ', NEW.lastname), 'INSERT');
END
$$
DELIMITER ;
DELIMITER $$
CREATE TRIGGER `log_update_reg_user` AFTER UPDATE ON `reg_user` FOR EACH ROW BEGIN
    INSERT INTO gate.auth_log (name, actions)
    VALUES (CONCAT(NEW.firstname, ' ', NEW.lastname), 'UPDATE');
END
$$
DELIMITER ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admin`
--
ALTER TABLE `admin`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `auth_log`
--
ALTER TABLE `auth_log`
  ADD PRIMARY KEY (`auth_id`);

--
-- Indexes for table `encodings`
--
ALTER TABLE `encodings`
  ADD PRIMARY KEY (`encod_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `face_image`
--
ALTER TABLE `face_image`
  ADD PRIMARY KEY (`facial_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `reg_user`
--
ALTER TABLE `reg_user`
  ADD PRIMARY KEY (`user_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admin`
--
ALTER TABLE `admin`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `auth_log`
--
ALTER TABLE `auth_log`
  MODIFY `auth_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=51;

--
-- AUTO_INCREMENT for table `encodings`
--
ALTER TABLE `encodings`
  MODIFY `encod_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=41;

--
-- AUTO_INCREMENT for table `face_image`
--
ALTER TABLE `face_image`
  MODIFY `facial_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=70;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `encodings`
--
ALTER TABLE `encodings`
  ADD CONSTRAINT `encodings_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `reg_user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `face_image`
--
ALTER TABLE `face_image`
  ADD CONSTRAINT `face_image_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `reg_user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
