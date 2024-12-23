create database db;
use db;

CREATE TABLE users (
    email VARCHAR(255) PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL
);


CREATE TABLE financial_data (
    ticker VARCHAR(10) NOT NULL,    
    timestamp DATETIME NOT NULL,    
    value FLOAT NOT NULL,           
    PRIMARY KEY (ticker, timestamp) 
);