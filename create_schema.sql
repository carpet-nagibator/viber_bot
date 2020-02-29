create table if not exists users (
    user_id integer primary key autoincrement,
    viber_id text not null unique,
    all_answers integer not null default 0,
    correct_answers integer not null default 0,
    question text,
    dt_last_answer timestamp
);

create table if not exists learning (
    user_id integer not null,
    word text not null,
    right_answer integer not null default 0,
    dt_last_answer timestamp,
    primary key (user_id, word),
    foreign key (user_id) references users(user_id)
);
