BEGIN TRANSACTION;
CREATE TABLE accounts (
  guid           TEXT(32) PRIMARY KEY NOT NULL,
  name           TEXT(2048)           NOT NULL,
  account_type   TEXT(2048)           NOT NULL,
  commodity_guid TEXT(32),
  commodity_scu  INTEGER              NOT NULL,
  non_std_scu    INTEGER              NOT NULL,
  parent_guid    TEXT(32),
  code           TEXT(2048),
  description    TEXT(2048),
  hidden         INTEGER,
  placeholder    INTEGER
);
INSERT INTO "accounts" VALUES
  ('585c9d227802e657949d5c95e7ddc2bb', 'Root Account', 'ROOT', '07d6c5190b0cfd8016fc6e18916c53ba', 100, 0, NULL, '', '',
                                       0, 0);
INSERT INTO "accounts"
VALUES ('d46da663d18f692acb3501180b2a5efd', 'Template Root', 'ROOT', NULL, 0, 0, NULL, '', '', 0, 0);
CREATE TABLE billterms (
  guid           TEXT(32) PRIMARY KEY NOT NULL,
  name           TEXT(2048)           NOT NULL,
  description    TEXT(2048)           NOT NULL,
  refcount       INTEGER              NOT NULL,
  invisible      INTEGER              NOT NULL,
  parent         TEXT(32),
  type           TEXT(2048)           NOT NULL,
  duedays        INTEGER,
  discountdays   INTEGER,
  discount_num   BIGINT,
  discount_denom BIGINT,
  cutoff         INTEGER
);
CREATE TABLE books (
  guid               TEXT(32) PRIMARY KEY NOT NULL,
  root_account_guid  TEXT(32)             NOT NULL,
  root_template_guid TEXT(32)             NOT NULL
);
INSERT INTO "books"
VALUES ('00b1769f439614aa594ad4ed5c833ef1', '585c9d227802e657949d5c95e7ddc2bb', 'd46da663d18f692acb3501180b2a5efd');
CREATE TABLE budget_amounts (
  id           INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  budget_guid  TEXT(32)                          NOT NULL,
  account_guid TEXT(32)                          NOT NULL,
  period_num   INTEGER                           NOT NULL,
  amount_num   BIGINT                            NOT NULL,
  amount_denom BIGINT                            NOT NULL
);
CREATE TABLE budgets (
  guid        TEXT(32) PRIMARY KEY NOT NULL,
  name        TEXT(2048)           NOT NULL,
  description TEXT(2048),
  num_periods INTEGER              NOT NULL
);
CREATE TABLE commodities (
  guid         TEXT(32) PRIMARY KEY NOT NULL,
  namespace    TEXT(2048)           NOT NULL,
  mnemonic     TEXT(2048)           NOT NULL,
  fullname     TEXT(2048),
  cusip        TEXT(2048),
  fraction     INTEGER              NOT NULL,
  quote_flag   INTEGER              NOT NULL,
  quote_source TEXT(2048),
  quote_tz     TEXT(2048)
);
INSERT INTO "commodities"
VALUES ('07d6c5190b0cfd8016fc6e18916c53ba', 'CURRENCY', 'EUR', 'Euro', '978', 100, 1, 'currency', '');
CREATE TABLE customers (
  guid           TEXT(32) PRIMARY KEY NOT NULL,
  name           TEXT(2048)           NOT NULL,
  id             TEXT(2048)           NOT NULL,
  notes          TEXT(2048)           NOT NULL,
  active         INTEGER              NOT NULL,
  discount_num   BIGINT               NOT NULL,
  discount_denom BIGINT               NOT NULL,
  credit_num     BIGINT               NOT NULL,
  credit_denom   BIGINT               NOT NULL,
  currency       TEXT(32)             NOT NULL,
  tax_override   INTEGER              NOT NULL,
  addr_name      TEXT(1024),
  addr_addr1     TEXT(1024),
  addr_addr2     TEXT(1024),
  addr_addr3     TEXT(1024),
  addr_addr4     TEXT(1024),
  addr_phone     TEXT(128),
  addr_fax       TEXT(128),
  addr_email     TEXT(256),
  shipaddr_name  TEXT(1024),
  shipaddr_addr1 TEXT(1024),
  shipaddr_addr2 TEXT(1024),
  shipaddr_addr3 TEXT(1024),
  shipaddr_addr4 TEXT(1024),
  shipaddr_phone TEXT(128),
  shipaddr_fax   TEXT(128),
  shipaddr_email TEXT(256),
  terms          TEXT(32),
  tax_included   INTEGER,
  taxtable       TEXT(32)
);
CREATE TABLE employees (
  guid          TEXT(32) PRIMARY KEY NOT NULL,
  username      TEXT(2048)           NOT NULL,
  id            TEXT(2048)           NOT NULL,
  language      TEXT(2048)           NOT NULL,
  acl           TEXT(2048)           NOT NULL,
  active        INTEGER              NOT NULL,
  currency      TEXT(32)             NOT NULL,
  ccard_guid    TEXT(32),
  workday_num   BIGINT               NOT NULL,
  workday_denom BIGINT               NOT NULL,
  rate_num      BIGINT               NOT NULL,
  rate_denom    BIGINT               NOT NULL,
  addr_name     TEXT(1024),
  addr_addr1    TEXT(1024),
  addr_addr2    TEXT(1024),
  addr_addr3    TEXT(1024),
  addr_addr4    TEXT(1024),
  addr_phone    TEXT(128),
  addr_fax      TEXT(128),
  addr_email    TEXT(256)
);
CREATE TABLE entries (
  guid             TEXT(32) PRIMARY KEY NOT NULL,
  date             TEXT(19)             NOT NULL,
  date_entered     TEXT(19),
  description      TEXT(2048),
  action           TEXT(2048),
  notes            TEXT(2048),
  quantity_num     BIGINT,
  quantity_denom   BIGINT,
  i_acct           TEXT(32),
  i_price_num      BIGINT,
  i_price_denom    BIGINT,
  i_discount_num   BIGINT,
  i_discount_denom BIGINT,
  invoice          TEXT(32),
  i_disc_type      TEXT(2048),
  i_disc_how       TEXT(2048),
  i_taxable        INTEGER,
  i_taxincluded    INTEGER,
  i_taxtable       TEXT(32),
  b_acct           TEXT(32),
  b_price_num      BIGINT,
  b_price_denom    BIGINT,
  bill             TEXT(32),
  b_taxable        INTEGER,
  b_taxincluded    INTEGER,
  b_taxtable       TEXT(32),
  b_paytype        INTEGER,
  billable         INTEGER,
  billto_type      INTEGER,
  billto_guid      TEXT(32),
  order_guid       TEXT(32)
);
CREATE TABLE gnclock (
  Hostname VARCHAR(255),
  PID      INT
);
CREATE TABLE invoices (
  guid             TEXT(32) PRIMARY KEY NOT NULL,
  id               TEXT(2048)           NOT NULL,
  date_opened      TEXT(19),
  date_posted      TEXT(19),
  notes            TEXT(2048)           NOT NULL,
  active           INTEGER              NOT NULL,
  currency         TEXT(32)             NOT NULL,
  owner_type       INTEGER,
  owner_guid       TEXT(32),
  terms            TEXT(32),
  billing_id       TEXT(2048),
  post_txn         TEXT(32),
  post_lot         TEXT(32),
  post_acc         TEXT(32),
  billto_type      INTEGER,
  billto_guid      TEXT(32),
  charge_amt_num   BIGINT,
  charge_amt_denom BIGINT
);
CREATE TABLE jobs (
  guid       TEXT(32) PRIMARY KEY NOT NULL,
  id         TEXT(2048)           NOT NULL,
  name       TEXT(2048)           NOT NULL,
  reference  TEXT(2048)           NOT NULL,
  active     INTEGER              NOT NULL,
  owner_type INTEGER,
  owner_guid TEXT(32)
);
CREATE TABLE lots (
  guid         TEXT(32) PRIMARY KEY NOT NULL,
  account_guid TEXT(32),
  is_closed    INTEGER              NOT NULL
);
CREATE TABLE orders (
  guid        TEXT(32) PRIMARY KEY NOT NULL,
  id          TEXT(2048)           NOT NULL,
  notes       TEXT(2048)           NOT NULL,
  reference   TEXT(2048)           NOT NULL,
  active      INTEGER              NOT NULL,
  date_opened TEXT(19)             NOT NULL,
  date_closed TEXT(19)             NOT NULL,
  owner_type  INTEGER              NOT NULL,
  owner_guid  TEXT(32)             NOT NULL
);
CREATE TABLE prices (
  guid           TEXT(32) PRIMARY KEY NOT NULL,
  commodity_guid TEXT(32)             NOT NULL,
  currency_guid  TEXT(32)             NOT NULL,
  date           TEXT(19)             NOT NULL,
  source         TEXT(2048),
  type           TEXT(2048),
  value_num      BIGINT               NOT NULL,
  value_denom    BIGINT               NOT NULL
);
CREATE TABLE recurrences (
  id                        INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  obj_guid                  TEXT(32)                          NOT NULL,
  recurrence_mult           INTEGER                           NOT NULL,
  recurrence_period_type    TEXT(2048)                        NOT NULL,
  recurrence_period_start   TEXT(8)                           NOT NULL,
  recurrence_weekend_adjust TEXT(2048)                        NOT NULL
);
CREATE TABLE schedxactions (
  guid              TEXT(32) PRIMARY KEY NOT NULL,
  name              TEXT(2048),
  enabled           INTEGER              NOT NULL,
  start_date        TEXT(8),
  end_date          TEXT(8),
  last_occur        TEXT(8),
  num_occur         INTEGER              NOT NULL,
  rem_occur         INTEGER              NOT NULL,
  auto_create       INTEGER              NOT NULL,
  auto_notify       INTEGER              NOT NULL,
  adv_creation      INTEGER              NOT NULL,
  adv_notify        INTEGER              NOT NULL,
  instance_count    INTEGER              NOT NULL,
  template_act_guid TEXT(32)             NOT NULL
);
CREATE TABLE slots (
  id                INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  obj_guid          TEXT(32)                          NOT NULL,
  name              TEXT(4096)                        NOT NULL,
  slot_type         INTEGER                           NOT NULL,
  int64_val         BIGINT,
  string_val        TEXT(4096),
  double_val        float8,
  timespec_val      TEXT(19),
  guid_val          TEXT(32),
  numeric_val_num   BIGINT,
  numeric_val_denom BIGINT,
  gdate_val         TEXT(8)
);
INSERT INTO "slots" VALUES
  (1, '00b1769f439614aa594ad4ed5c833ef1', 'counter_formats', 9, 0, NULL, NULL, '1970-01-01 00:00:00',
      'd35eeea5887e4da2a1f9b4fc137b66aa', 0, 1, NULL);
INSERT INTO "slots" VALUES (2, '00b1769f439614aa594ad4ed5c833ef1', 'counters', 9, 0, NULL, NULL, '1970-01-01 00:00:00',
                               'e1348bc1496348508718f2e02b62537e', 0, 1, NULL);
INSERT INTO "slots" VALUES
  (3, 'e1348bc1496348508718f2e02b62537e', 'counters/gncBill', 1, 4, NULL, NULL, '1970-01-01 00:00:00', NULL, 0, 1,
   NULL);
INSERT INTO "slots" VALUES
  (4, 'e1348bc1496348508718f2e02b62537e', 'counters/gncEmployee', 1, 4, NULL, NULL, '1970-01-01 00:00:00', NULL, 0, 1,
   NULL);
INSERT INTO "slots" VALUES
  (5, 'e1348bc1496348508718f2e02b62537e', 'counters/gncInvoice', 1, 4, NULL, NULL, '1970-01-01 00:00:00', NULL, 0, 1,
   NULL);
INSERT INTO "slots" VALUES (6, '00b1769f439614aa594ad4ed5c833ef1', 'features', 9, 0, NULL, NULL, '1970-01-01 00:00:00',
                               'fb3f980f4aac42aba2d9f7305de5200d', 0, 1, NULL);
INSERT INTO "slots" VALUES
  (7, 'fb3f980f4aac42aba2d9f7305de5200d', 'features/ISO-8601 formatted date strings in SQLite3 databases.', 4, 0,
      'Use ISO formatted date-time strings in SQLite3 databases (requires at least GnuCash 2.6.20)', NULL,
      '1970-01-01 00:00:00', NULL, 0, 1, NULL);
INSERT INTO "slots" VALUES (8, 'fb3f980f4aac42aba2d9f7305de5200d', 'features/Number Field Source', 4, 0,
                               'User specifies source of ''num'' field''; either transaction number or split action (requires at least GnuCash 2.5.0)',
                               NULL, '1970-01-01 00:00:00', NULL, 0, 1, NULL);
INSERT INTO "slots" VALUES (9, '00b1769f439614aa594ad4ed5c833ef1', 'options', 9, 0, NULL, NULL, '1970-01-01 00:00:00',
                               'a590db3fa6184c34b7f66eca85fd4071', 0, 1, NULL);
INSERT INTO "slots" VALUES
  (10, 'a590db3fa6184c34b7f66eca85fd4071', 'options/Accounts', 9, 0, NULL, NULL, '1970-01-01 00:00:00',
       '9aab76e97e3949e7bfe34d1d67e28b98', 0, 1, NULL);
INSERT INTO "slots" VALUES
  (11, '9aab76e97e3949e7bfe34d1d67e28b98', 'options/Accounts/Day Threshold for Read-Only Transactions (red line)', 2, 0,
       NULL, 46.0, '1970-01-01 00:00:00', NULL, 0, 1, NULL);
INSERT INTO "slots" VALUES
  (12, '9aab76e97e3949e7bfe34d1d67e28b98', 'options/Accounts/Use Split Action Field for Number', 4, 0, 't', NULL,
       '1970-01-01 00:00:00', NULL, 0, 1, NULL);
INSERT INTO "slots" VALUES
  (13, '9aab76e97e3949e7bfe34d1d67e28b98', 'options/Accounts/Use Trading Accounts', 4, 0, 't', NULL,
       '1970-01-01 00:00:00', NULL, 0, 1, NULL);
INSERT INTO "slots" VALUES
  (14, 'a590db3fa6184c34b7f66eca85fd4071', 'options/Budgeting', 9, 0, NULL, NULL, '1970-01-01 00:00:00',
       '58c94ceb2ac74e99a2c661d86e9b8218', 0, 1, NULL);
INSERT INTO "slots" VALUES
  (15, 'a590db3fa6184c34b7f66eca85fd4071', 'options/Business', 9, 0, NULL, NULL, '1970-01-01 00:00:00',
       '76de62c473fe4ce7b3f5534a22a49863', 0, 1, NULL);
INSERT INTO "slots" VALUES
  (16, '76de62c473fe4ce7b3f5534a22a49863', 'options/Business/Company Address', 4, 0, 'Rue de la Chenille éclairée, 22',
       NULL, '1970-01-01 00:00:00', NULL, 0, 1, NULL);
INSERT INTO "slots" VALUES
  (17, '76de62c473fe4ce7b3f5534a22a49863', 'options/Business/Company Contact Person', 4, 0, 'John Michu', NULL,
       '1970-01-01 00:00:00', NULL, 0, 1, NULL);
INSERT INTO "slots" VALUES
  (18, '76de62c473fe4ce7b3f5534a22a49863', 'options/Business/Company Email Address', 4, 0, 'woozie@example.com', NULL,
       '1970-01-01 00:00:00', NULL, 0, 1, NULL);
INSERT INTO "slots" VALUES
  (19, '76de62c473fe4ce7b3f5534a22a49863', 'options/Business/Company ID', 4, 0, 'SIREN 123 456 789', NULL,
       '1970-01-01 00:00:00', NULL, 0, 1, NULL);
INSERT INTO "slots" VALUES
  (20, '76de62c473fe4ce7b3f5534a22a49863', 'options/Business/Company Name', 4, 0, 'Woozie Inc', NULL,
       '1970-01-01 00:00:00', NULL, 0, 1, NULL);
INSERT INTO "slots" VALUES
  (21, '76de62c473fe4ce7b3f5534a22a49863', 'options/Business/Company Phone Number', 4, 0, '+33 1 33 33 33 33', NULL,
       '1970-01-01 00:00:00', NULL, 0, 1, NULL);
INSERT INTO "slots" VALUES
  (22, '76de62c473fe4ce7b3f5534a22a49863', 'options/Business/Company Website URL', 4, 0, 'www.woozie.com', NULL,
       '1970-01-01 00:00:00', NULL, 0, 1, NULL);
CREATE TABLE splits (
  guid            TEXT(32) PRIMARY KEY NOT NULL,
  tx_guid         TEXT(32)             NOT NULL,
  account_guid    TEXT(32)             NOT NULL,
  memo            TEXT(2048)           NOT NULL,
  action          TEXT(2048)           NOT NULL,
  reconcile_state TEXT(1)              NOT NULL,
  reconcile_date  TEXT(19),
  value_num       BIGINT               NOT NULL,
  value_denom     BIGINT               NOT NULL,
  quantity_num    BIGINT               NOT NULL,
  quantity_denom  BIGINT               NOT NULL,
  lot_guid        TEXT(32)
);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES ('slots', 22);
CREATE TABLE taxtable_entries (
  id           INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  taxtable     TEXT(32)                          NOT NULL,
  account      TEXT(32)                          NOT NULL,
  amount_num   BIGINT                            NOT NULL,
  amount_denom BIGINT                            NOT NULL,
  type         INTEGER                           NOT NULL
);
CREATE TABLE taxtables (
  guid      TEXT(32) PRIMARY KEY NOT NULL,
  name      TEXT(50)             NOT NULL,
  refcount  BIGINT               NOT NULL,
  invisible INTEGER              NOT NULL,
  parent    TEXT(32)
);
CREATE TABLE transactions (
  guid          TEXT(32) PRIMARY KEY NOT NULL,
  currency_guid TEXT(32)             NOT NULL,
  num           TEXT(2048)           NOT NULL,
  post_date     TEXT(19),
  enter_date    TEXT(19),
  description   TEXT(2048)
);
CREATE TABLE vendors (
  guid         TEXT(32) PRIMARY KEY NOT NULL,
  name         TEXT(2048)           NOT NULL,
  id           TEXT(2048)           NOT NULL,
  notes        TEXT(2048)           NOT NULL,
  currency     TEXT(32)             NOT NULL,
  active       INTEGER              NOT NULL,
  tax_override INTEGER              NOT NULL,
  addr_name    TEXT(1024),
  addr_addr1   TEXT(1024),
  addr_addr2   TEXT(1024),
  addr_addr3   TEXT(1024),
  addr_addr4   TEXT(1024),
  addr_phone   TEXT(128),
  addr_fax     TEXT(128),
  addr_email   TEXT(256),
  terms        TEXT(32),
  tax_inc      TEXT(2048),
  tax_table    TEXT(32)
);
CREATE TABLE versions (
  table_name    TEXT(50) PRIMARY KEY NOT NULL,
  table_version INTEGER              NOT NULL
);
INSERT INTO "versions" VALUES ('Gnucash', 3000000);
INSERT INTO "versions" VALUES ('Gnucash-Resave', 19920);
INSERT INTO "versions" VALUES ('books', 1);
INSERT INTO "versions" VALUES ('commodities', 1);
INSERT INTO "versions" VALUES ('accounts', 1);
INSERT INTO "versions" VALUES ('budgets', 1);
INSERT INTO "versions" VALUES ('budget_amounts', 1);
INSERT INTO "versions" VALUES ('prices', 3);
INSERT INTO "versions" VALUES ('transactions', 4);
INSERT INTO "versions" VALUES ('splits', 4);
INSERT INTO "versions" VALUES ('slots', 4);
INSERT INTO "versions" VALUES ('recurrences', 2);
INSERT INTO "versions" VALUES ('schedxactions', 1);
INSERT INTO "versions" VALUES ('lots', 2);
INSERT INTO "versions" VALUES ('billterms', 2);
INSERT INTO "versions" VALUES ('customers', 2);
INSERT INTO "versions" VALUES ('employees', 2);
INSERT INTO "versions" VALUES ('entries', 4);
INSERT INTO "versions" VALUES ('invoices', 4);
INSERT INTO "versions" VALUES ('jobs', 1);
INSERT INTO "versions" VALUES ('orders', 1);
INSERT INTO "versions" VALUES ('taxtables', 2);
INSERT INTO "versions" VALUES ('taxtable_entries', 3);
INSERT INTO "versions" VALUES ('vendors', 1);
CREATE INDEX tx_post_date_index
  ON transactions (post_date);
CREATE INDEX splits_tx_guid_index
  ON splits (tx_guid);
CREATE INDEX splits_account_guid_index
  ON splits (account_guid);
CREATE INDEX slots_guid_index
  ON slots (obj_guid);
COMMIT;
