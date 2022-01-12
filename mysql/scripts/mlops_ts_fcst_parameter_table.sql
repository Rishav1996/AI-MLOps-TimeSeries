CREATE DATABASE  IF NOT EXISTS `mlops_ts_fcst` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `mlops_ts_fcst`;
-- MySQL dump 10.13  Distrib 8.0.26, for Win64 (x86_64)
--
-- Host: localhost    Database: mlops_ts_fcst
-- ------------------------------------------------------
-- Server version	8.0.26

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `parameter_table`
--

DROP TABLE IF EXISTS `parameter_table`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `parameter_table` (
  `parameter_id` int NOT NULL AUTO_INCREMENT,
  `parameter_grp` varchar(50) NOT NULL,
  `parameter_name` varchar(50) NOT NULL,
  `parameter_value` varchar(256) NOT NULL,
  `parameter_range_values` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`parameter_id`),
  UNIQUE KEY `parameter_id_UNIQUE` (`parameter_id`)
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `parameter_table`
--

LOCK TABLES `parameter_table` WRITE;
/*!40000 ALTER TABLE `parameter_table` DISABLE KEYS */;
INSERT INTO `parameter_table` VALUES (1,'INGESTION_STAGE','ing_start','ING_S',NULL),(2,'INGESTION_STAGE','ing_processing','ING_P1',NULL),(3,'INGESTION_STAGE','ing_end','ING_E',NULL),(4,'INGESTION_STAGE','ing_failed','ING_F',NULL),(5,'DATA_PROCESSING_STAGE','data_proc_start','DP_S',NULL),(6,'DATA_PROCESSING_STAGE','data_proc_processing','DP_P1',NULL),(7,'DATA_PROCESSING_STAGE','data_proc_end','DP_E',NULL),(8,'DATA_PROCESSING_STAGE','data_proc_failed','DP_F',NULL),(9,'FORECAST_STAGE','fcst_start','FCST_S',NULL),(10,'FORECAST_STAGE','fcst_processing','FCST_P1',NULL),(11,'FORECAST_STAGE','fcst_end','FCST_E',NULL),(12,'FORECAST_STAGE','fcst_failed','FCST_F',NULL),(13,'WINDOW_SPLITTER','sliding_window_splitter','SLIDE',NULL),(14,'WINDOW_SPLITTER','expanding_window_splitter','EXPAND',NULL),(15,'INGESTION_STAGE','ing_flag','ING',NULL),(16,'DATA_PROCESSING_STAGE','data_proc_flag','DP',NULL),(17,'FORECAST_STAGE','fcst_flag','FCST',NULL),(18,'IMPUTER','impute_choice','linear','linear,mean,median,nearest'),(19,'IMPUTER','impute_if_zero','False','True,False'),(20,'OUTLIER','outlier_choice','if','if,lof,zscore'),(21,'OUTLIER','outlier_cnt','auto',NULL),(22,'OUTLIER','zscore_cutoff','3',NULL),(23,'FORECASTING','test_size','0.5',NULL),(24,'FORECASTING','forecast_horizon','0.1',NULL),(25,'FORECASTING','model_choice','single','single,multi'),(26,'FORECASTING','model_types','1','1,2,3,4,5,6'),(27,'FORECASTING','auto_ensemble','0',NULL),(28,'FORECASTING','ensemble','0',NULL),(29,'FORECASTING','data_split','expanding','expanding,sliding,both');
/*!40000 ALTER TABLE `parameter_table` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2021-12-28  7:13:27
