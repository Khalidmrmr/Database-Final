SELECT
  b.book_id,
  b.title,
  COUNT(bc.copy_id) AS total_copies,
  SUM(CASE WHEN bc.status = 'Available' THEN 1 ELSE 0 END) AS available_copies
FROM book AS b
LEFT JOIN bookcopy AS bc
  ON b.book_id = bc.book_id
GROUP BY b.book_id, b.title
ORDER BY b.title;
