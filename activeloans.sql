SELECT
  m.member_id,
  m.member_name,
  b.title,
  bc.copy_id,
  l.date_borrowed,
  l.due_date
FROM loan AS l
JOIN member AS m
  ON l.member_id = m.member_id
JOIN bookcopy AS bc
  ON l.copy_id = bc.copy_id
JOIN book AS b
  ON bc.book_id = b.book_id
WHERE l.date_returned IS NULL
ORDER BY m.member_name, l.date_borrowed;