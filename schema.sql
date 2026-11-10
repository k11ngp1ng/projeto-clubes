CREATE TABLE IF NOT EXISTS clubs (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL, initials TEXT UNIQUE NOT NULL,
    address TEXT NOT NULL, district TEXT NOT NULL, city TEXT NOT NULL, uf TEXT NOT NULL,
    phone TEXT NOT NULL, email TEXT NOT NULL, fee INTEGER NOT NULL CHECK(fee >= 0)
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, club INTEGER REFERENCES clubs, name TEXT NOT NULL,
    email TEXT COLLATE NOCASE UNIQUE NOT NULL, password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('super','presidente','tesoureiro','associado')),
    status TEXT NOT NULL DEFAULT 'ativo', category TEXT, cpf TEXT, address TEXT,
    district TEXT, city TEXT, uf TEXT, phone TEXT, sex TEXT, civil TEXT, birth TEXT, interests TEXT,
    UNIQUE(club,cpf)
);
CREATE TABLE IF NOT EXISTS dependents (
    id INTEGER PRIMARY KEY, member INTEGER NOT NULL REFERENCES users, name TEXT NOT NULL,
    birth TEXT NOT NULL, relation TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY, club INTEGER NOT NULL REFERENCES clubs, name TEXT NOT NULL,
    starts TEXT NOT NULL, audience TEXT NOT NULL, target TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY, club INTEGER NOT NULL REFERENCES clubs, member INTEGER NOT NULL REFERENCES users,
    purpose TEXT NOT NULL, starts TEXT NOT NULL, ends TEXT NOT NULL,
    status TEXT NOT NULL, CHECK(starts < ends)
);
CREATE INDEX IF NOT EXISTS bookings_schedule ON bookings(club,status,starts,ends);
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY, member INTEGER NOT NULL REFERENCES users,
    kind TEXT NOT NULL, body TEXT NOT NULL, reply TEXT, created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dues (
    id INTEGER PRIMARY KEY, member INTEGER NOT NULL REFERENCES users,
    period TEXT NOT NULL, amount INTEGER NOT NULL CHECK(amount >= 0), paid TEXT, UNIQUE(member,period)
);
