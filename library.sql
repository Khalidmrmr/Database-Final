-- SQL script: schema creation and sample data inserts for Library Management System

-- Drop existing tables to reset the schema
DROP TABLE IF EXISTS loan;
DROP TABLE IF EXISTS bookcopy;
DROP TABLE IF EXISTS member;
DROP TABLE IF EXISTS book;
DROP TABLE IF EXISTS author;

-- 1. Author table
CREATE TABLE author (
    author_id SERIAL PRIMARY KEY,
    author_name VARCHAR(255) NOT NULL,
    biography TEXT
);

-- 2. Book table
CREATE TABLE book (
    book_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    isbn VARCHAR(13) UNIQUE,
    publication_year INT,
    genre VARCHAR(100),
    author_id INT
        REFERENCES author(author_id)
        ON DELETE SET NULL
);

-- 3. BookCopy table
CREATE TABLE bookcopy (
    copy_id SERIAL PRIMARY KEY,
    book_id INT NOT NULL
        REFERENCES book(book_id)
        ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('Available','On Loan','Maintenance','Lost'))
);

-- 4. Member table
CREATE TABLE member (
    member_id SERIAL PRIMARY KEY,
    member_name VARCHAR(255) NOT NULL,
    address VARCHAR(255),
    phone_number VARCHAR(15),
    join_date DATE NOT NULL DEFAULT CURRENT_DATE
);

-- 5. Loan table
CREATE TABLE loan (
    loan_id SERIAL PRIMARY KEY,
    copy_id INT NOT NULL
        REFERENCES bookcopy(copy_id)
        ON DELETE RESTRICT,
    member_id INT NOT NULL
        REFERENCES member(member_id)
        ON DELETE RESTRICT,
    date_borrowed DATE NOT NULL,
    due_date DATE NOT NULL,
    date_returned DATE,
    CONSTRAINT chk_return_date
        CHECK (date_returned IS NULL OR date_returned >= date_borrowed)
);

--------------------------------------------------------------------------------
-- Sample data inserts

-- Authors
INSERT INTO author (author_name, biography) VALUES
  ('J.R.R. Tolkien',  'English writer, poet, philologist, and academic.'),
  ('Frank Herbert',   'American science-fiction author best known for Dune.'),
  ('William Gibson',  'American-Canadian speculative fiction writer.');

-- Books
INSERT INTO book (title, isbn, publication_year, genre, author_id) VALUES
  ('The Hobbit',      '9780547928227', 1937, 'Fantasy',          1),
  ('Dune',            '9780441172719', 1965, 'Science Fiction',  2),
  ('Neuromancer',     '9780441569595', 1984, 'Cyberpunk',        3);

-- BookCopies
INSERT INTO bookcopy (book_id, status) VALUES
  (1, 'Available'),
  (1, 'On Loan'),
  (2, 'Available'),
  (2, 'Available'),
  (2, 'Maintenance'),
  (3, 'Available');

-- Members
INSERT INTO member (member_name, address, phone_number) VALUES
  ('Alice Smith', '123 Maple St',   '555-1234'),
  ('Bob Johnson', '456 Oak Ave',    '555-5678');

-- Loans
-- Loan 1: Returned
INSERT INTO loan (copy_id, member_id, date_borrowed, due_date, date_returned) VALUES
  (4, 2, '2025-07-01', '2025-07-22', '2025-07-20');

-- Loan 2: Active (not yet returned)
INSERT INTO loan (copy_id, member_id, date_borrowed, due_date, date_returned) VALUES
  (2, 1, '2025-07-15', '2025-08-05', NULL);
