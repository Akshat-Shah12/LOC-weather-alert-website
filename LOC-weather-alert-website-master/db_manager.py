from sqlalchemy import create_engine

conn = create_engine("sqlite:///Users.db", echo=True).connect()

"""cmd = CREATE TABLE UserCreds(
    Id INT NUT NULL PRIMARY KEY,
    Email TEXT NOT NULL,
    Password TEXT NOT NULL)"""

cmd = """CREATE TABLE UserInfo(
    Id INT NOT NULL PRIMARY KEY,
    Name TEXT NOT NULL,
    Location TEXT NOT NULL,
    Allergies TEXT NOT NULL,
    Creds INT references UserCreds(Id))"""

#cmd = "DROP TABLE UserInfo"

#cmd = "ALTER TABLE UserCreds ADD FullName TEXT"

"""cmd = CREATE TABLE Allergies(
    Id INT NOT NULL PRIMARY KEY,
    Name TEXT NOT NULL,
    TempVar FLOAT,
    HumiVar FLOAT)"""

"""cmd = CREATE TABLE Cities(
    Id NOT NULL PRIMARY KEY,
    Name TEXT NOT NULL,
    Temp FLOAT NOT NULL,
    Humi FLOAT NOT NULL)"""

conn.execute(cmd)