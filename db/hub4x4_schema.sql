-- HUB 4x4 Quality Dashboard - tables read by hub4x4.data._fromDb()
-- Generic SQL; adjust types (DATETIME/TIMESTAMP, IDENTITY/SERIAL) to your database.

CREATE TABLE hub_production (      -- one row per line per time slot (e.g. hourly)
    ts        DATETIME    NOT NULL,
    line      VARCHAR(10) NOT NULL, -- 110A, 110B, 120A, 120B, 130A
    plan_qty  INT NOT NULL DEFAULT 0,
    fg_qty    INT NOT NULL DEFAULT 0,
    ok_qty    INT NOT NULL DEFAULT 0,
    ng_qty    INT NOT NULL DEFAULT 0
);

CREATE TABLE hub_inspection (      -- one row per measured point per part
    ts      DATETIME    NOT NULL,
    seq     INT         NOT NULL,
    point   CHAR(1)     NOT NULL,   -- A..F
    value   FLOAT       NOT NULL,
    lcl     FLOAT       NOT NULL,
    ucl     FLOAT       NOT NULL,
    target  FLOAT       NOT NULL
);

CREATE TABLE hub_abnormal (        -- NG + Repair events (Abnormal List, Top 5 Defects)
    ts          DATETIME    NOT NULL,
    seq         VARCHAR(20) NOT NULL,
    line        VARCHAR(10) NOT NULL,
    point       CHAR(1)     NOT NULL,
    result      VARCHAR(10) NOT NULL, -- NG | Repair
    process     VARCHAR(20) NOT NULL, -- OP130A ...
    defect_type VARCHAR(50) NOT NULL, -- Scratch, Dimensional, ...
    detail      VARCHAR(255)
);

CREATE TABLE hub_repair (
    ts     DATETIME    NOT NULL,
    seq    VARCHAR(20) NOT NULL,
    cause  VARCHAR(50) NOT NULL,   -- Repair A..D
    status VARCHAR(20) NOT NULL    -- OPEN | CLOSED
);

CREATE TABLE hub_line_status (
    line        VARCHAR(10) PRIMARY KEY,
    performance FLOAT NOT NULL,     -- %
    updated     DATETIME
);
