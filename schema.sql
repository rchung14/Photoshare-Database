CREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;
DROP TABLE IF EXISTS Pictures CASCADE;
DROP TABLE IF EXISTS Users CASCADE;
DROP TABLE IF EXISTS Albums CASCADE; 

CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT,
    gender VARCHAR(6), 
    email varchar(255) UNIQUE,
    password varchar(255) NOT NULL,
    dob DATE NOT NULL, 
    hometown VARCHAR(40), 
	fname VARCHAR(40) NOT NULL, 
	lname VARCHAR(40) NOT NULL, 
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Albums ( 
  album_id INT AUTO_INCREMENT, 
  Name VARCHAR(40) NOT NULL, 
  date_of_creation DATETIME DEFAULT CURRENT_TIMESTAMP, 
  user_id INT NOT NULL, 
  PRIMARY KEY (album_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE Pictures (
  picture_id INT AUTO_INCREMENT, 
  user_id INT, 
  caption VARCHAR(200), 
  imgdata LONGBLOB, 
  album_id INT NOT NULL, 
  PRIMARY KEY (picture_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id),
  FOREIGN KEY (album_id) REFERENCES Albums(album_id) ON DELETE CASCADE 
);


