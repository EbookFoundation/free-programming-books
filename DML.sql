CREATE DATABASE campus;
USE campus;
CREATE TABLE user(
id integer primary key auto_increment,
name varchar(255) not null,
password varchar(255) not null,
email varchar(255) unique not null
);
INSERT INTO campus.user(name,password,email) VALUES 
("aayushi","123","aauishi@gmail"),
("anishka","156","hjdjsj@gail"),
("aryan","86","hdnkdgail"),
("aayan","489","klfk@gmail.com"),
("rohan","788","aayushijgamil@");

select * from campus.user;
