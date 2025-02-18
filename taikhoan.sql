-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Feb 11, 2025 at 05:29 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `taikhoan`
--

-- --------------------------------------------------------

--
-- Table structure for table `login_log`
--

CREATE TABLE `login_log` (
  `id` int(11) NOT NULL,
  `username` varchar(50) DEFAULT NULL,
  `login_time` datetime DEFAULT NULL,
  `client_ip` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `login_log`
--

INSERT INTO `login_log` (`id`, `username`, `login_time`, `client_ip`) VALUES
(1, 'admin', '2025-02-06 23:05:19', '127.0.0.1'),
(2, 'admin', '2025-02-06 23:05:20', '127.0.0.1'),
(3, 'admin', '2025-02-06 23:05:38', '127.0.0.1'),
(4, 'admin', '2025-02-06 23:05:39', '127.0.0.1'),
(5, 'admin', '2025-02-06 23:05:39', '127.0.0.1'),
(6, 'admin', '2025-02-06 23:10:34', '127.0.0.1'),
(7, 'admin', '2025-02-06 23:10:40', '127.0.0.1'),
(8, 'admin', '2025-02-06 23:10:40', '127.0.0.1'),
(9, 'admin', '2025-02-06 23:10:40', '127.0.0.1'),
(10, 'admin', '2025-02-06 23:10:40', '127.0.0.1'),
(11, 'admin', '2025-02-06 23:11:17', '127.0.0.1'),
(12, 'admin', '2025-02-06 23:11:25', '127.0.0.1'),
(13, 'admin', '2025-02-06 23:11:25', '127.0.0.1'),
(14, 'admin', '2025-02-06 23:11:25', '127.0.0.1'),
(15, 'admin', '2025-02-06 23:11:25', '127.0.0.1'),
(16, 'admin', '2025-02-06 23:11:25', '127.0.0.1'),
(17, 'admin', '2025-02-06 23:11:25', '127.0.0.1'),
(18, 'admin', '2025-02-06 23:11:29', '127.0.0.1'),
(19, 'admin', '2025-02-06 23:11:31', '127.0.0.1'),
(20, 'thinh', '2025-02-06 23:15:23', '127.0.0.1'),
(21, 'admin', '2025-02-06 23:16:36', '127.0.0.1'),
(22, 'admin', '2025-02-07 00:03:39', '127.0.0.1'),
(23, 'admin', '2025-02-07 00:05:20', '127.0.0.1'),
(24, 'PC1', '2025-02-07 00:20:45', '127.0.0.1'),
(25, 'admin', '2025-02-07 00:22:48', '127.0.0.1');

-- --------------------------------------------------------

--
-- Table structure for table `taikhoan`
--

CREATE TABLE `taikhoan` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `taikhoan`
--

INSERT INTO `taikhoan` (`id`, `username`, `password`) VALUES
(1, 'admin', '1234'),
(2, 'PC1', 'PC1');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `login_log`
--
ALTER TABLE `login_log`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `taikhoan`
--
ALTER TABLE `taikhoan`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `login_log`
--
ALTER TABLE `login_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=26;

--
-- AUTO_INCREMENT for table `taikhoan`
--
ALTER TABLE `taikhoan`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
