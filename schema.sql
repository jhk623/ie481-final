create table if not exists user (
  user_id integer primary key autoincrement,
  uid integer not null,
  pw_hash string not null
);
