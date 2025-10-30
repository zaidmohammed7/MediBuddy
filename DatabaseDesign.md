# Database Design – DDL Specification (MySQL 8.0)

## Contents

1. [Database & Safety Drops](#database--safety-drops)
2. [Core Clinical Schema](#core-clinical-schema)

   * [specialty](#specialty)
   * [disease](#disease)
   * [symptom](#symptom)
   * [doctor](#doctor)
   * [disease_symptom](#disease_symptom)
3. [User, Preferences, & Meds](#user-preferences--meds)

   * [user](#user)
   * [notification_prefs](#notification_prefs)
   * [drug](#drug)
   * [side_effect](#side_effect)
   * [prescription](#prescription)
   * [reminder](#reminder)
   * [emergency_contact](#emergency_contact)

---

## Database & Safety Drops

```sql
-- Create and select database
CREATE DATABASE IF NOT EXISTS aloo
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
USE aloo;

-- Safety drops (reverse dependency order)
DROP TABLE IF EXISTS emergency_contact;
DROP TABLE IF EXISTS reminder;
DROP TABLE IF EXISTS prescription;
DROP TABLE IF EXISTS side_effect;
DROP TABLE IF EXISTS notification_prefs;
DROP TABLE IF EXISTS drug;

DROP TABLE IF EXISTS disease_symptom;
DROP TABLE IF EXISTS doctor;
DROP TABLE IF EXISTS symptom;
DROP TABLE IF EXISTS disease;
DROP TABLE IF EXISTS specialty;

DROP TABLE IF EXISTS `user`;
```

---

## Core Clinical Schema

### `specialty`

* Canonical list of medical specialties (referenced by doctors & diseases)

```sql
CREATE TABLE specialty (
    specialty_id   CHAR(36)       NOT NULL,
    specialty_name VARCHAR(100)   NOT NULL UNIQUE,
    PRIMARY KEY (specialty_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

---

### `disease`

* Diseases mapped to a specialty

```sql
CREATE TABLE disease (
    disease_id      CHAR(36)       NOT NULL,
    disease_name    VARCHAR(255)   NOT NULL UNIQUE,
    specialty_id    CHAR(36)       NULL,
    PRIMARY KEY (disease_id),
    CONSTRAINT fk_disease_specialty
        FOREIGN KEY (specialty_id) REFERENCES specialty (specialty_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

---

### `symptom`

* Master list of symptoms

```sql
CREATE TABLE symptom (
    symptom_id      CHAR(36)       NOT NULL,
    symptom_name    VARCHAR(255)   NOT NULL UNIQUE,
    PRIMARY KEY (symptom_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

---

### `doctor`

* Providers mapped to a specialty

```sql
CREATE TABLE doctor (
    doctor_id       CHAR(36)       NOT NULL,
    last_name       VARCHAR(100),
    first_name      VARCHAR(100),
    specialty_id    CHAR(36)       NULL,
    address_line1   VARCHAR(255),
    address_line2   VARCHAR(255),
    city            VARCHAR(100),
    state           VARCHAR(100),
    zip_code        VARCHAR(20),
    phone_number    VARCHAR(25),
    PRIMARY KEY (doctor_id),
    CONSTRAINT fk_doctor_specialty
        FOREIGN KEY (specialty_id) REFERENCES specialty (specialty_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

---

### `disease_symptom`

* Junction table (many-to-many) between diseases and symptoms

```sql
CREATE TABLE disease_symptom (
    disease_id  CHAR(36) NOT NULL,
    symptom_id  CHAR(36) NOT NULL,
    PRIMARY KEY (disease_id, symptom_id),
    KEY idx_disease (disease_id),
    KEY idx_symptom (symptom_id),
    CONSTRAINT fk_ds_disease
        FOREIGN KEY (disease_id) REFERENCES disease (disease_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_ds_symptom
        FOREIGN KEY (symptom_id) REFERENCES symptom (symptom_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

---

## User, Preferences & Meds

### `user`

* Application account and reminder window

```sql
CREATE TABLE `user` (
    user_id                  CHAR(36)      NOT NULL,
    name                     VARCHAR(255)  NOT NULL,
    email                    VARCHAR(255)  NOT NULL,
    time_zone                VARCHAR(64)   NOT NULL,      -- e.g., 'America/Chicago'
    preferred_window_start   TIME          NULL,
    preferred_window_end     TIME          NULL,
    PRIMARY KEY (user_id),
    UNIQUE KEY uq_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

ALTER TABLE `user`
  ADD CONSTRAINT chk_user_window_range
  CHECK (
    preferred_window_start IS NULL
    OR preferred_window_end IS NULL
    OR preferred_window_start < preferred_window_end
  );
```

---

### `notification_prefs`

* 1:1 with `user` (PK = FK); stores communication settings

```sql
CREATE TABLE notification_prefs (
    user_id              CHAR(36)   NOT NULL,
    email_reminders      BOOLEAN    NOT NULL DEFAULT TRUE,
    missed_dose_summary  BOOLEAN    NOT NULL DEFAULT TRUE,
    PRIMARY KEY (user_id),
    CONSTRAINT fk_notifprefs_user
        FOREIGN KEY (user_id) REFERENCES `user` (user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

---

### `drug`

* Catalog of drugs (RxNorm optional but unique if present)

```sql
CREATE TABLE drug (
    drug_id      CHAR(36)       NOT NULL,
    rxnorm_code  VARCHAR(32)    NULL,
    name         VARCHAR(255)   NOT NULL,
    PRIMARY KEY (drug_id),
    UNIQUE KEY uq_drug_name (name),
    UNIQUE KEY uq_rxnorm_code (rxnorm_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

---

### `side_effect`

* Multi-valued attribute of drug; one row per (drug, effect)

```sql
CREATE TABLE side_effect (
    drug_id     CHAR(36)       NOT NULL,
    effect      VARCHAR(255)   NOT NULL,
    description TEXT           NULL,
    PRIMARY KEY (drug_id, effect),
    KEY idx_sideeffect_drug (drug_id),
    CONSTRAINT fk_sideeffect_drug
        FOREIGN KEY (drug_id) REFERENCES drug (drug_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

---

### `prescription`

* User-specific prescriptions for a given drug (not unique by user-drug)

```sql
CREATE TABLE prescription (
    rx_id        CHAR(36)       NOT NULL,
    user_id      CHAR(36)       NOT NULL,
    drug_id      CHAR(36)       NOT NULL,
    frequency    VARCHAR(50)    NOT NULL,    -- e.g., 'once_daily', 'q8h', 'bid'
    qty_on_hand  INT UNSIGNED   NOT NULL DEFAULT 0,
    refills      INT UNSIGNED   NOT NULL DEFAULT 0,
    rx_text      TEXT           NULL,        -- free-form instructions
    PRIMARY KEY (rx_id),
    KEY idx_prescription_user (user_id),
    KEY idx_prescription_drug (drug_id),
    CONSTRAINT fk_prescription_user
        FOREIGN KEY (user_id) REFERENCES `user` (user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_prescription_drug
        FOREIGN KEY (drug_id) REFERENCES drug (drug_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

---

### `reminder`

* Scheduled notification tied to a specific prescription (and user)

```sql
CREATE TABLE reminder (
    reminder_id         CHAR(36)       NOT NULL,
    user_id             CHAR(36)       NOT NULL,
    rx_id               CHAR(36)       NOT NULL,
    remind_time         DATETIME       NOT NULL,
    override_frequency  VARCHAR(50)    NULL,
    PRIMARY KEY (reminder_id),
    KEY idx_reminder_user (user_id),
    KEY idx_reminder_rx (rx_id),
    CONSTRAINT fk_reminder_user
        FOREIGN KEY (user_id) REFERENCES `user` (user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_reminder_rx
        FOREIGN KEY (rx_id) REFERENCES prescription (rx_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

---

### `emergency_contact`

* Per-user contact with a unique email constraint

```sql
CREATE TABLE emergency_contact (
    contact_id  CHAR(36)       NOT NULL,
    user_id     CHAR(36)       NOT NULL,
    name        VARCHAR(255)   NOT NULL,
    phone       VARCHAR(25)    NULL,
    email       VARCHAR(255)   NULL,
    `trigger`   VARCHAR(50)    NOT NULL,    -- e.g., 'missed_dose', 'low_supply'
    PRIMARY KEY (contact_id),
    UNIQUE KEY uq_contact_user_email (user_id, email),
    KEY idx_contact_user (user_id),
    CONSTRAINT fk_contact_user
        FOREIGN KEY (user_id) REFERENCES `user` (user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```
