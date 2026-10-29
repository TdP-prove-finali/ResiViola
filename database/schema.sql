CREATE DATABASE IF NOT EXISTS comodato_libri
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE comodato_libri;

DROP TABLE IF EXISTS distanza;
DROP TABLE IF EXISTS classe_isee;
DROP TABLE IF EXISTS adozione;
DROP TABLE IF EXISTS studenti;
DROP TABLE IF EXISTS libro;
DROP TABLE IF EXISTS scuola;

CREATE TABLE scuola (
    codice_scuola  VARCHAR(10)  PRIMARY KEY,
    denominazione  VARCHAR(200) NOT NULL,
    indirizzo      VARCHAR(200),
    tipologia      VARCHAR(150),
    lat            DECIMAL(9,6),
    lon            DECIMAL(9,6)
);

CREATE TABLE libro (
    isbn      VARCHAR(20)  PRIMARY KEY,
    titolo    VARCHAR(300),
    autori    VARCHAR(300),
    editore   VARCHAR(150),
    prezzo    DECIMAL(6,2) NULL
);

CREATE TABLE adozione (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    codice_scuola   VARCHAR(10)  NOT NULL,
    anno_corso      TINYINT      NOT NULL,
    sezione         VARCHAR(10)  NOT NULL,
    combinazione    VARCHAR(100),
    disciplina      VARCHAR(150),
    isbn            VARCHAR(20)  NOT NULL,
    da_acquistare   TINYINT(1)   NOT NULL,
    nuova_adozione  TINYINT(1)   NOT NULL,
    consigliato     CHAR(2)      NOT NULL,
    FOREIGN KEY (codice_scuola) REFERENCES scuola(codice_scuola),
    FOREIGN KEY (isbn)          REFERENCES libro(isbn),
    INDEX idx_classe (codice_scuola, anno_corso, sezione)
);

CREATE TABLE studenti (
    codice_scuola  VARCHAR(10) NOT NULL,
    anno_corso     TINYINT     NOT NULL,
    classi         INT         NOT NULL,
    alunni         INT         NOT NULL,
    PRIMARY KEY (codice_scuola, anno_corso),
    FOREIGN KEY (codice_scuola) REFERENCES scuola(codice_scuola)
);

CREATE TABLE distanza (
    codice_1  VARCHAR(10)  NOT NULL,
    codice_2  VARCHAR(10)  NOT NULL,
    km        DECIMAL(7,3) NOT NULL,
    PRIMARY KEY (codice_1, codice_2),
    FOREIGN KEY (codice_1) REFERENCES scuola(codice_scuola),
    FOREIGN KEY (codice_2) REFERENCES scuola(codice_scuola)
);

CREATE TABLE classe_isee (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    descrizione          VARCHAR(30)   NOT NULL,
    limite_inf           DECIMAL(10,2) NOT NULL,
    limite_sup           DECIMAL(10,2) NULL,
    nuclei_con_minori    INT           NOT NULL,
    nuclei_senza_minori  INT           NOT NULL
);
