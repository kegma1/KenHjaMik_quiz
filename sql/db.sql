-- MySQL Script generated by MySQL Workbench
-- Thu May 11 17:15:07 2023
-- Model: New Model    Version: 1.0
-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema stud_v23_kma150
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema stud_v23_kma150
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `stud_v23_kma150` DEFAULT CHARACTER SET utf8 ;
USE `stud_v23_kma150` ;

-- -----------------------------------------------------
-- Table `stud_v23_kma150`.`questionType`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `stud_v23_kma150`.`questionType` ;

CREATE TABLE IF NOT EXISTS `stud_v23_kma150`.`questionType` (
  `questionType_ID` INT NOT NULL AUTO_INCREMENT,
  `type` VARCHAR(45) NULL,
  PRIMARY KEY (`questionType_ID`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `stud_v23_kma150`.`quiz`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `stud_v23_kma150`.`quiz` ;

CREATE TABLE IF NOT EXISTS `stud_v23_kma150`.`quiz` (
  `quiz_ID` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT NULL,
  `totalQuestions` INT NOT NULL,
  PRIMARY KEY (`quiz_ID`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `stud_v23_kma150`.`question`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `stud_v23_kma150`.`question` ;

CREATE TABLE IF NOT EXISTS `stud_v23_kma150`.`question` (
  `question_ID` INT NOT NULL AUTO_INCREMENT,
  `question` VARCHAR(255) NOT NULL,
  `questionType` INT NOT NULL,
  `quiz` INT NOT NULL,
  PRIMARY KEY (`question_ID`, `quiz`),
  INDEX `fk_question_questionType_idx` (`questionType` ASC) VISIBLE,
  INDEX `fk_question_quiz1_idx` (`quiz` ASC) VISIBLE,
  CONSTRAINT `fk_question_questionType`
    FOREIGN KEY (`questionType`)
    REFERENCES `stud_v23_kma150`.`questionType` (`questionType_ID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_question_quiz1`
    FOREIGN KEY (`quiz`)
    REFERENCES `stud_v23_kma150`.`quiz` (`quiz_ID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `stud_v23_kma150`.`user`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `stud_v23_kma150`.`user` ;

CREATE TABLE IF NOT EXISTS `stud_v23_kma150`.`user` (
  `username` VARCHAR(255) NOT NULL,
  `isAdmin` TINYINT NOT NULL DEFAULT 0,
  `firstName` VARCHAR(255) NOT NULL,
  `lastName` VARCHAR(255) NOT NULL,
  `password` TEXT NOT NULL,
  PRIMARY KEY (`username`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `stud_v23_kma150`.`correctionStatus`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `stud_v23_kma150`.`correctionStatus` ;

CREATE TABLE IF NOT EXISTS `stud_v23_kma150`.`correctionStatus` (
  `correctionStatus_ID` INT NOT NULL AUTO_INCREMENT,
  `status` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`correctionStatus_ID`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `stud_v23_kma150`.`answer`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `stud_v23_kma150`.`answer` ;

CREATE TABLE IF NOT EXISTS `stud_v23_kma150`.`answer` (
  `answer_ID` INT NOT NULL AUTO_INCREMENT,
  `answer` TEXT NOT NULL,
  `question` INT NOT NULL,
  `user` VARCHAR(255) NOT NULL,
  `comment` TEXT NULL,
  `status` INT NOT NULL,
  PRIMARY KEY (`answer_ID`, `question`),
  INDEX `fk_answer_question1_idx` (`question` ASC) VISIBLE,
  INDEX `fk_answer_user1_idx` (`user` ASC) VISIBLE,
  INDEX `fk_answer_correctionStatus1_idx` (`status` ASC) VISIBLE,
  CONSTRAINT `fk_answer_question1`
    FOREIGN KEY (`question`)
    REFERENCES `stud_v23_kma150`.`question` (`question_ID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_answer_user1`
    FOREIGN KEY (`user`)
    REFERENCES `stud_v23_kma150`.`user` (`username`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_answer_correctionStatus1`
    FOREIGN KEY (`status`)
    REFERENCES `stud_v23_kma150`.`correctionStatus` (`correctionStatus_ID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `stud_v23_kma150`.`choices`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `stud_v23_kma150`.`choices` ;

CREATE TABLE IF NOT EXISTS `stud_v23_kma150`.`choices` (
  `choices_ID` INT NOT NULL AUTO_INCREMENT,
  `choice1` VARCHAR(255) NOT NULL,
  `choice2` VARCHAR(255) NOT NULL,
  `choice3` VARCHAR(255) NOT NULL,
  `choice4` VARCHAR(255) NOT NULL,
  `question_question_ID` INT NOT NULL,
  `question_quiz` INT NOT NULL,
  PRIMARY KEY (`choices_ID`),
  INDEX `fk_choices_question1_idx` (`question_question_ID` ASC, `question_quiz` ASC) VISIBLE,
  CONSTRAINT `fk_choices_question1`
    FOREIGN KEY (`question_question_ID` , `question_quiz`)
    REFERENCES `stud_v23_kma150`.`question` (`question_ID` , `quiz`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
