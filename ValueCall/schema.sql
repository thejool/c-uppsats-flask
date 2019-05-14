DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS uploads;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  current_file int DEFAULT 0,
  FOREIGN KEY (current_file) REFERENCES uploads(id)
);

CREATE TABLE uploads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filepath TEXT NOT NULL,
  filename TEXT NOT NULL,
  upload_date datetime NOT NULL,
  uploaded_by int DEFAULT 0,
  FOREIGN KEY (uploaded_by) REFERENCES user(id)
);
