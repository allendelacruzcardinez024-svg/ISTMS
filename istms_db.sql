-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Oct 04, 2026 at 02:35 PM
-- Server version: 11.5.2-MariaDB
-- PHP Version: 8.3.14

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `istms_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
CREATE TABLE IF NOT EXISTS `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
CREATE TABLE IF NOT EXISTS `auth_group_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissions_group_id_b120cbf9` (`group_id`),
  KEY `auth_group_permissions_permission_id_84c5c92e` (`permission_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
CREATE TABLE IF NOT EXISTS `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  KEY `auth_permission_content_type_id_2f476e4b` (`content_type_id`)
) ENGINE=MyISAM AUTO_INCREMENT=45 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `auth_permission`
--

INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES
(1, 'Can add log entry', 1, 'add_logentry'),
(2, 'Can change log entry', 1, 'change_logentry'),
(3, 'Can delete log entry', 1, 'delete_logentry'),
(4, 'Can view log entry', 1, 'view_logentry'),
(5, 'Can add permission', 2, 'add_permission'),
(6, 'Can change permission', 2, 'change_permission'),
(7, 'Can delete permission', 2, 'delete_permission'),
(8, 'Can view permission', 2, 'view_permission'),
(9, 'Can add group', 3, 'add_group'),
(10, 'Can change group', 3, 'change_group'),
(11, 'Can delete group', 3, 'delete_group'),
(12, 'Can view group', 3, 'view_group'),
(13, 'Can add user', 4, 'add_user'),
(14, 'Can change user', 4, 'change_user'),
(15, 'Can delete user', 4, 'delete_user'),
(16, 'Can view user', 4, 'view_user'),
(17, 'Can add content type', 5, 'add_contenttype'),
(18, 'Can change content type', 5, 'change_contenttype'),
(19, 'Can delete content type', 5, 'delete_contenttype'),
(20, 'Can view content type', 5, 'view_contenttype'),
(21, 'Can add session', 6, 'add_session'),
(22, 'Can change session', 6, 'change_session'),
(23, 'Can delete session', 6, 'delete_session'),
(24, 'Can view session', 6, 'view_session'),
(25, 'Can add category', 7, 'add_category'),
(26, 'Can change category', 7, 'change_category'),
(27, 'Can delete category', 7, 'delete_category'),
(28, 'Can view category', 7, 'view_category'),
(29, 'Can add profile', 8, 'add_profile'),
(30, 'Can change profile', 8, 'change_profile'),
(31, 'Can delete profile', 8, 'delete_profile'),
(32, 'Can view profile', 8, 'view_profile'),
(33, 'Can add ticket', 9, 'add_ticket'),
(34, 'Can change ticket', 9, 'change_ticket'),
(35, 'Can delete ticket', 9, 'delete_ticket'),
(36, 'Can view ticket', 9, 'view_ticket'),
(37, 'Can add feedback', 10, 'add_feedback'),
(38, 'Can change feedback', 10, 'change_feedback'),
(39, 'Can delete feedback', 10, 'delete_feedback'),
(40, 'Can view feedback', 10, 'view_feedback'),
(41, 'Can add ticket update', 11, 'add_ticketupdate'),
(42, 'Can change ticket update', 11, 'change_ticketupdate'),
(43, 'Can delete ticket update', 11, 'delete_ticketupdate'),
(44, 'Can view ticket update', 11, 'view_ticketupdate');

-- --------------------------------------------------------

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
CREATE TABLE IF NOT EXISTS `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=MyISAM AUTO_INCREMENT=8 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `auth_user`
--

INSERT INTO `auth_user` (`id`, `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `date_joined`) VALUES
(2, 'pbkdf2_sha256$1000000$kKYfZQZ1lP9LNvHTJkrRO2$PakP/JroGfcVeNENOKKZSDpFnO3wtKxAnzSiZMCWnts=', '2026-10-04 14:24:09.373027', 1, 'admin', 'Maria', 'Santos', 'admin@nexora.local', 1, 1, '2026-09-27 17:17:52.591888'),
(4, 'pbkdf2_sha256$1000000$tdJk7BfhIpxQ0xxVnfvLgM$On9h2uZnVIUC6jG3Xd9MHCVPMkn99chW0GcqONxwezY=', NULL, 0, 'employee', 'Juan', 'Dela Cruz', 'employee@nexora.local', 0, 1, '2026-09-28 06:08:43.235966'),
(5, 'pbkdf2_sha256$1000000$u0EPk5r4TPXxTD42ZOHsNN$ZHtmcRg4gCnmrFJNeTH3IFYkwc1aXYa/pqQtSmuBieM=', NULL, 0, 'technician', 'Rafael', 'Santos', 'technician@nexora.local', 0, 1, '2026-09-28 06:08:45.038091'),
(6, 'pbkdf2_sha256$1000000$vMFA4Qu1XLtR2YVr0xZKKB$X4KtZufZQ1yYpkpoAQ+rVgL0kTMU8welANa5wGmPzLI=', NULL, 0, 'manager', 'John', 'Lim', 'manager@nexora.local', 0, 1, '2026-09-28 06:08:48.748317');

-- --------------------------------------------------------

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
CREATE TABLE IF NOT EXISTS `auth_user_groups` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_user_id_6a12ed8b` (`user_id`),
  KEY `auth_user_groups_group_id_97559544` (`group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
CREATE TABLE IF NOT EXISTS `auth_user_user_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permissions_user_id_a95ead1b` (`user_id`),
  KEY `auth_user_user_permissions_permission_id_1fbb5f2c` (`permission_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
CREATE TABLE IF NOT EXISTS `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) UNSIGNED NOT NULL CHECK (`action_flag` >= 0),
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6` (`user_id`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `django_admin_log`
--

INSERT INTO `django_admin_log` (`id`, `action_time`, `object_id`, `object_repr`, `action_flag`, `change_message`, `content_type_id`, `user_id`) VALUES
(1, '2026-09-28 14:14:04.022670', '8', 'System Unit', 1, '[{\"added\": {}}]', 7, 2),
(2, '2026-09-28 14:14:12.157560', '9', 'Monitor', 1, '[{\"added\": {}}]', 7, 2);

-- --------------------------------------------------------

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
CREATE TABLE IF NOT EXISTS `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=MyISAM AUTO_INCREMENT=12 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `django_content_type`
--

INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES
(1, 'admin', 'logentry'),
(2, 'auth', 'permission'),
(3, 'auth', 'group'),
(4, 'auth', 'user'),
(5, 'contenttypes', 'contenttype'),
(6, 'sessions', 'session'),
(7, 'tickets', 'category'),
(8, 'tickets', 'profile'),
(9, 'tickets', 'ticket'),
(10, 'tickets', 'feedback'),
(11, 'tickets', 'ticketupdate');

-- --------------------------------------------------------

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
CREATE TABLE IF NOT EXISTS `django_migrations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=21 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `django_migrations`
--

INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES
(1, 'contenttypes', '0001_initial', '2026-09-27 16:55:03.150167'),
(2, 'auth', '0001_initial', '2026-09-27 16:55:03.794250'),
(3, 'admin', '0001_initial', '2026-09-27 16:55:03.931986'),
(4, 'admin', '0002_logentry_remove_auto_add', '2026-09-27 16:55:03.940357'),
(5, 'admin', '0003_logentry_add_action_flag_choices', '2026-09-27 16:55:03.950782'),
(6, 'contenttypes', '0002_remove_content_type_name', '2026-09-27 16:55:04.027940'),
(7, 'auth', '0002_alter_permission_name_max_length', '2026-09-27 16:55:04.061531'),
(8, 'auth', '0003_alter_user_email_max_length', '2026-09-27 16:55:04.097310'),
(9, 'auth', '0004_alter_user_username_opts', '2026-09-27 16:55:04.105537'),
(10, 'auth', '0005_alter_user_last_login_null', '2026-09-27 16:55:04.144630'),
(11, 'auth', '0006_require_contenttypes_0002', '2026-09-27 16:55:04.145963'),
(12, 'auth', '0007_alter_validators_add_error_messages', '2026-09-27 16:55:04.153568'),
(13, 'auth', '0008_alter_user_username_max_length', '2026-09-27 16:55:04.194398'),
(14, 'auth', '0009_alter_user_last_name_max_length', '2026-09-27 16:55:04.233183'),
(15, 'auth', '0010_alter_group_name_max_length', '2026-09-27 16:55:04.276677'),
(16, 'auth', '0011_update_proxy_permissions', '2026-09-27 16:55:04.287686'),
(17, 'auth', '0012_alter_user_first_name_max_length', '2026-09-27 16:55:04.330520'),
(18, 'sessions', '0001_initial', '2026-09-27 16:55:04.373064'),
(19, 'tickets', '0001_initial', '2026-09-27 16:55:04.800487'),
(20, 'tickets', '0002_alter_feedback_ticket', '2026-09-27 16:55:04.816616');

-- --------------------------------------------------------

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
CREATE TABLE IF NOT EXISTS `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `django_session`
--

INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES
('6mvlbxawwcatlfirhqaz2mm24kfthlya', '.eJxVjDkOwjAQAP-yNbKM42tT0ucN0a4PHEC2FCcV4u8oUgpoZ0bzhpn2rcx7T-u8RBhBweWXMYVnqoeID6r3JkKr27qwOBJx2i6mFtPrdrZ_g0K9wAg6EzlkvJKXitjmJA17NiwZWXtNWXJG44KyiiMTOUvBDTI7VAMmD58vBEc4kQ:1xB4b5:_NDSylAJ0k3mn_n2g-kEr2jBG1nplp80aLJqPJVZxVo', '2026-10-12 06:12:19.764560'),
('vfxh42v8rgyulpccliqb6fdcfwzi5z7p', '.eJxVjDsOwyAQBe9CHaEF23xSpvcZ0C4LwUmEJWNXUe4eIblI2jcz7y0CHnsJR0tbWFhchRaX340wPlPtgB9Y76uMa923hWRX5EmbnFdOr9vp_h0UbKXXoNiNkDIRkjUwjRMrHpyGyKw5MlgAzEhpyJ7Jg45ojfYeWSnrjPh8AQH9OHg:1xB4Vb:hIQlxuwtyE85fAPc6NHeaulgnrWT_Ez2oKCEFdoj1SM', '2026-10-12 06:06:39.071317'),
('yxrqyi0vzh58fi6ow9xzh0vgn5wuajc9', '.eJxVjDkOwjAQAP-yNbKM42tT0ucN0a4PHEC2FCcV4u8oUgpoZ0bzhpn2rcx7T-u8RBhBweWXMYVnqoeID6r3JkKr27qwOBJx2i6mFtPrdrZ_g0K9wAg6EzlkvJKXitjmJA17NiwZWXtNWXJG44KyiiMTOUvBDTI7VAMmD58vBEc4kQ:1xBCPW:icflRWh-PoolFYSWZgduVgF_yk53MgVLj_PmlfeDnYk', '2026-10-12 14:32:54.546434'),
('s486h3jmm1zdeaznb3gtn1snpmrs4ufi', '.eJxVjDkOwjAQAP-yNbKM42tT0ucN0a4PHEC2FCcV4u8oUgpoZ0bzhpn2rcx7T-u8RBhBweWXMYVnqoeID6r3JkKr27qwOBJx2i6mFtPrdrZ_g0K9wAg6EzlkvJKXitjmJA17NiwZWXtNWXJG44KyiiMTOUvBDTI7VAMmD58vBEc4kQ:1xDN8L:98006j1FWzZEuzZch5Mbc5uv_JEqWEVFavLPuWpuFEA', '2026-10-18 14:24:09.378856');

-- --------------------------------------------------------

--
-- Table structure for table `tickets_category`
--

DROP TABLE IF EXISTS `tickets_category`;
CREATE TABLE IF NOT EXISTS `tickets_category` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  `description` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=10 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `tickets_category`
--

INSERT INTO `tickets_category` (`id`, `name`, `description`) VALUES
(1, 'Hardware', 'Laptop, desktop, peripherals and physical equipment'),
(2, 'Software', 'Business applications and installation'),
(3, 'Network', 'Internet, Wi-Fi, LAN and connectivity'),
(4, 'Account Access', 'Password, email and access concerns'),
(5, 'Printer', 'Printing, scanning and printer connectivity'),
(6, 'Other', 'Other technology-related services'),
(8, 'System Unit', ''),
(9, 'Monitor', '');

-- --------------------------------------------------------

--
-- Table structure for table `tickets_feedback`
--

DROP TABLE IF EXISTS `tickets_feedback`;
CREATE TABLE IF NOT EXISTS `tickets_feedback` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `rating` smallint(5) UNSIGNED NOT NULL CHECK (`rating` >= 0),
  `comment` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `ticket_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ticket_id` (`ticket_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tickets_profile`
--

DROP TABLE IF EXISTS `tickets_profile`;
CREATE TABLE IF NOT EXISTS `tickets_profile` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `role` varchar(20) NOT NULL,
  `department` varchar(100) NOT NULL,
  `user_identifier` varchar(50) NOT NULL,
  `avatar_initials` varchar(5) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`)
) ENGINE=MyISAM AUTO_INCREMENT=8 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `tickets_profile`
--

INSERT INTO `tickets_profile` (`id`, `role`, `department`, `user_identifier`, `avatar_initials`, `user_id`) VALUES
(2, 'admin', 'IT', 'ADM-001', 'MS', 2),
(5, 'technician', 'IT Support', 'TECH-001', 'RS', 5),
(4, 'employee', 'Operations', 'EMP-001', 'JD', 4),
(6, 'manager', 'Operations', 'MGR-001', 'JL', 6);

-- --------------------------------------------------------

--
-- Table structure for table `tickets_ticket`
--

DROP TABLE IF EXISTS `tickets_ticket`;
CREATE TABLE IF NOT EXISTS `tickets_ticket` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `ticket_number` varchar(30) NOT NULL,
  `title` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `priority` varchar(20) NOT NULL,
  `status` varchar(20) NOT NULL,
  `device_system` varchar(120) NOT NULL,
  `location` varchar(150) NOT NULL,
  `attachment` varchar(100) DEFAULT NULL,
  `resolution` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `resolved_at` datetime(6) DEFAULT NULL,
  `assigned_to_id` int(11) DEFAULT NULL,
  `category_id` bigint(20) NOT NULL,
  `submitted_by_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ticket_number` (`ticket_number`),
  KEY `tickets_ticket_assigned_to_id_142e13bf` (`assigned_to_id`),
  KEY `tickets_ticket_category_id_710dbfd0` (`category_id`),
  KEY `tickets_ticket_submitted_by_id_85d490ec` (`submitted_by_id`)
) ENGINE=MyISAM AUTO_INCREMENT=8 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `tickets_ticket`
--

INSERT INTO `tickets_ticket` (`id`, `ticket_number`, `title`, `description`, `priority`, `status`, `device_system`, `location`, `attachment`, `resolution`, `created_at`, `updated_at`, `resolved_at`, `assigned_to_id`, `category_id`, `submitted_by_id`) VALUES
(1, 'TKT-2026-FF6276', 'Cannot access email', 'Demo support request: Cannot access email. Please investigate and provide an update.', 'high', 'in_progress', 'Dell Latitude / Outlook', 'Nexora Office', '', '', '2026-09-28 06:08:50.642204', '2026-09-28 06:08:50.642241', NULL, 5, 4, 4),
(2, 'TKT-2026-94AA49', 'Printer not working', 'Demo support request: Printer not working. Please investigate and provide an update.', 'medium', 'assigned', 'HP LaserJet', 'Nexora Office', '', '', '2026-09-28 06:08:50.650693', '2026-09-28 06:08:50.650731', NULL, 5, 5, 4),
(3, 'TKT-2026-40349E', 'Laptop running slow', 'Demo support request: Laptop running slow. Please investigate and provide an update.', 'low', 'pending', 'Dell Latitude', 'Nexora Office', '', '', '2026-09-28 06:08:50.654899', '2026-09-28 06:08:50.654933', NULL, NULL, 1, 4),
(4, 'TKT-2026-95D8F8', 'Software installation', 'Demo support request: Software installation. Please investigate and provide an update.', 'medium', 'resolved', 'Adobe Acrobat', 'Nexora Office', '', '', '2026-09-28 06:08:50.658963', '2026-09-28 06:08:50.658994', NULL, 5, 2, 4),
(5, 'TKT-2026-737ACA', 'Updated Title by Admin', 'Updated detailed description by administrator.', 'critical', 'in_progress', 'Server Rack A', 'Data Center', '', 'Work in progress by administrator.', '2026-09-28 06:08:50.664509', '2026-09-28 06:12:22.145191', NULL, 2, 3, 4),
(7, 'TKT-2026-A500C8', 'ACT', 'Unimportant thing.', 'medium', 'assigned', 'Email', 'Office', '', '', '2026-09-28 14:08:51.044691', '2026-09-28 14:09:55.710477', NULL, 2, 2, 2);

-- --------------------------------------------------------

--
-- Table structure for table `tickets_ticketupdate`
--

DROP TABLE IF EXISTS `tickets_ticketupdate`;
CREATE TABLE IF NOT EXISTS `tickets_ticketupdate` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `message` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `author_id` int(11) DEFAULT NULL,
  `ticket_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tickets_ticketupdate_author_id_1d4909ba` (`author_id`),
  KEY `tickets_ticketupdate_ticket_id_96221892` (`ticket_id`)
) ENGINE=MyISAM AUTO_INCREMENT=11 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `tickets_ticketupdate`
--

INSERT INTO `tickets_ticketupdate` (`id`, `message`, `created_at`, `author_id`, `ticket_id`) VALUES
(1, 'Ticket created and entered into the centralized support workflow.', '2026-09-28 06:08:50.645653', 5, 1),
(2, 'Ticket created and entered into the centralized support workflow.', '2026-09-28 06:08:50.652047', 5, 2),
(3, 'Ticket created and entered into the centralized support workflow.', '2026-09-28 06:08:50.656468', 4, 3),
(4, 'Ticket created and entered into the centralized support workflow.', '2026-09-28 06:08:50.660110', 5, 4),
(5, 'Ticket created and entered into the centralized support workflow.', '2026-09-28 06:08:50.666369', 5, 5),
(6, 'Ticket information updated by Maria Santos.', '2026-09-28 06:12:22.147733', 2, 5),
(7, 'Ticket submitted by employee.', '2026-09-28 14:08:51.046953', 2, 7),
(8, 'Ticket assignment/status updated by Maria Santos.', '2026-09-28 14:09:28.581107', 2, 7),
(9, 'Pending', '2026-09-28 14:09:47.813967', 2, 7),
(10, 'Ticket assignment/status updated by Maria Santos.', '2026-09-28 14:09:55.714334', 2, 7);
COMMIT;


