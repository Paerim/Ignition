-- Receiving station - tables used by receiving.data when USE_DB = True
-- Generic SQL; adjust types (DATETIME/TIMESTAMP, IDENTITY/SERIAL) to your database.

CREATE TABLE rcv_truck_plan (            -- one row per planned truck per day (Truck Receiving Monitoring)
    id            INT IDENTITY PRIMARY KEY,
    plan_date     VARCHAR(10) NOT NULL,  -- 'yyyy-MM-dd'
    supplier      VARCHAR(20) NOT NULL,  -- ABC, DEF, XYZ (see SUPPLIERS in the script)
    truck_no      VARCHAR(20) NOT NULL,  -- Truck01 ...
    arrive_plan   VARCHAR(5)  NOT NULL,  -- 'HH:mm'
    depart_plan   VARCHAR(5)  NOT NULL,  -- 'HH:mm'
    arrive_actual DATETIME    NULL,      -- written by the HMI Truck Arrive button / PLC
    depart_actual DATETIME    NULL       -- written by the HMI Truck Departure button / PLC
);

CREATE TABLE rcv_ccr_inbox (             -- CCR drops new orders here; Handheld "รับออเดอร์จาก CCR" processes them
    order_no  VARCHAR(40)  PRIMARY KEY,
    sequence  VARCHAR(500) NOT NULL,     -- e.g. ABCAABAABCABAABACABA
    status    VARCHAR(10)  NOT NULL DEFAULT 'NEW'   -- NEW | DONE | ERROR
);

CREATE TABLE rcv_ccr_order (             -- accepted CCR orders (Mini WMS)
    order_no    VARCHAR(40)  PRIMARY KEY,
    sequence    VARCHAR(500) NOT NULL,
    received_ts DATETIME     NOT NULL,
    status      VARCHAR(10)  NOT NULL
);

CREATE TABLE rcv_supplier_order (        -- CCR order split per supplier (Handheld)
    order_no     VARCHAR(50) PRIMARY KEY, -- <ccr order>-<supplier>
    ccr_order_no VARCHAR(40) NOT NULL,
    supplier     VARCHAR(20) NOT NULL,
    status       VARCHAR(10) NOT NULL,   -- OPEN | RECEIVING | RECEIVED
    created_ts   DATETIME    NOT NULL,
    confirmed_ts DATETIME    NULL
);

CREATE TABLE rcv_supplier_order_item (
    order_no    VARCHAR(50) NOT NULL,
    part_no     VARCHAR(20) NOT NULL,
    part_name   VARCHAR(50) NOT NULL,
    qty         INT NOT NULL,
    scanned_qty INT NOT NULL DEFAULT 0,
    PRIMARY KEY (order_no, part_no)
);

CREATE TABLE rcv_scan_log (
    ts       DATETIME    NOT NULL,
    order_no VARCHAR(50) NOT NULL,
    part_no  VARCHAR(20) NOT NULL,
    qty      INT NOT NULL
);
