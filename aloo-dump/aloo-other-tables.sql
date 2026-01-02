SET SQL_SAFE_UPDATES = 0;

DELETE FROM reminder;
DELETE FROM emergency_contact;
DELETE FROM notification_prefs;
DELETE FROM side_effect;
DELETE FROM prescription;
DELETE FROM drug;
DELETE FROM user;

-- POPULATE USERS
-- ======================================================
INSERT INTO user (user_id, name, email, time_zone, preferred_window_start, preferred_window_end) VALUES
('62bf9644-c587-11f0-a97c-cda7de604848', 'Demo User', 'demo@medibuddy.com', 'America/Chicago', '08:00:00', '20:00:00'), -- Hardcoded ID for app.py
(UUID(), 'Alice Johnson', 'alice@example.com', 'America/Chicago', '08:00:00', '20:00:00'),
(UUID(), 'Bob Smith', 'bob@example.com', 'America/New_York', '09:00:00', '21:00:00'),
(UUID(), 'Charlie Brown', 'charlie@example.com', 'America/Los_Angeles', '07:00:00', '22:00:00'),
(UUID(), 'Diana Prince', 'diana@example.com', 'America/Chicago', '08:30:00', '20:30:00'),
(UUID(), 'Evan Wright', 'evan@example.com', 'America/Denver', '06:00:00', '18:00:00'),
(UUID(), 'Fiona Gallagher', 'fiona@example.com', 'America/Chicago', '10:00:00', '23:00:00'),
(UUID(), 'George Martin', 'george@example.com', 'Europe/London', '09:00:00', '17:00:00'),
(UUID(), 'Hannah Lee', 'hannah@example.com', 'Asia/Tokyo', '08:00:00', '20:00:00'),
(UUID(), 'Ian Somerhalder', 'ian@example.com', 'America/Chicago', '09:00:00', '21:00:00'),
(UUID(), 'Julia Roberts', 'julia@example.com', 'America/New_York', '08:00:00', '22:00:00'),
(UUID(), 'Kevin Hart', 'kevin@example.com', 'America/Los_Angeles', '07:00:00', '19:00:00'),
(UUID(), 'Laura Croft', 'laura@example.com', 'America/Chicago', '08:00:00', '20:00:00'),
(UUID(), 'Michael Scott', 'michael@example.com', 'America/New_York', '09:00:00', '17:00:00'),
(UUID(), 'Nancy Wheeler', 'nancy@example.com', 'America/Chicago', '08:00:00', '22:00:00'),
(UUID(), 'Oscar Martinez', 'oscar@example.com', 'America/Denver', '07:30:00', '19:30:00'),
(UUID(), 'Pam Beesly', 'pam@example.com', 'America/New_York', '08:30:00', '17:30:00'),
(UUID(), 'Quentin Tarantino', 'quentin@example.com', 'America/Los_Angeles', '10:00:00', '22:00:00'),
(UUID(), 'Rachel Green', 'rachel@example.com', 'America/New_York', '09:00:00', '21:00:00'),
(UUID(), 'Steve Harrington', 'steve@example.com', 'America/Chicago', '08:00:00', '23:00:00'),
(UUID(), 'Tony Stark', 'tony@example.com', 'America/New_York', '00:00:00', '23:59:00');

-- POPULATE DRUGS
-- ======================================================
INSERT INTO drug (drug_id, name, rxnorm_code) VALUES
(UUID(), 'Lisinopril 10mg', '197361'),
(UUID(), 'Atorvastatin 20mg', '259255'),
(UUID(), 'Levothyroxine 50mcg', '10582'),
(UUID(), 'Metformin 500mg', '860975'),
(UUID(), 'Amlodipine 5mg', '17767'),
(UUID(), 'Metoprolol 25mg', '866414'),
(UUID(), 'Omeprazole 20mg', '312109'),
(UUID(), 'Losartan 50mg', '213269'),
(UUID(), 'Gabapentin 300mg', '213479'),
(UUID(), 'Hydrochlorothiazide 25mg', '310798'),
(UUID(), 'Sertraline 50mg', '312935'),
(UUID(), 'Simvastatin 20mg', '312961'),
(UUID(), 'Montelukast 10mg', '312077'),
(UUID(), 'Escitalopram 10mg', '321952'),
(UUID(), 'Acetaminophen 500mg', '161'),
(UUID(), 'Ibuprofen 200mg', '197803'),
(UUID(), 'Albuterol Inhaler', '745678'),
(UUID(), 'Amoxicillin 500mg', '197313'),
(UUID(), 'Prednisone 10mg', '312535'),
(UUID(), 'Trazodone 50mg', '313319'),
(UUID(), 'Fluticasone Spray', '307362'),
(UUID(), 'Tramadol 50mg', '313253'),
(UUID(), 'Clonazepam 0.5mg', '197480'),
(UUID(), 'Insulin Glargine', '274783'),
(UUID(), 'Pantoprazole 40mg', '312273');

-- POPULATE PRESCRIPTIONS
-- ======================================================
INSERT INTO prescription (rx_id, user_id, drug_id, frequency, qty_on_hand, refills, rx_text)
SELECT 
    UUID(), 
    u.user_id, 
    (SELECT drug_id FROM drug ORDER BY RAND() LIMIT 1), 
    ELT(FLOOR(1 + (RAND() * 4)), 'Once daily', 'Twice daily', 'As needed', 'Before bed'),
    FLOOR(10 + (RAND() * 80)),
    FLOOR(0 + (RAND() * 5)),
    'Take with plenty of water'
FROM user u
LIMIT 20;

-- Add a specific one for the Demo User
INSERT INTO prescription (rx_id, user_id, drug_id, frequency, qty_on_hand, refills, rx_text)
VALUES 
(UUID(), '62bf9644-c587-11f0-a97c-cda7de604848', (SELECT drug_id FROM drug WHERE name LIKE 'Lisinopril%' LIMIT 1), 'Once Daily', 30, 3, 'Take in morning');


-- POPULATE SIDE EFFECTS
-- ======================================================
INSERT INTO side_effect (drug_id, effect, description)
SELECT 
    drug_id,
    'Drowsiness',
    'May cause drowsiness. Do not operate heavy machinery.'
FROM drug 
WHERE RAND() > 0.5;

INSERT INTO side_effect (drug_id, effect, description)
SELECT 
    drug_id,
    'Nausea',
    'May cause upset stomach. Take with food.'
FROM drug 
WHERE RAND() > 0.5;

INSERT INTO side_effect (drug_id, effect, description)
SELECT 
    drug_id,
    'Headache',
    'Mild headaches may occur. Stay hydrated.'
FROM drug 
WHERE RAND() > 0.5;

-- POPULATE NOTIFICATION PREFS
-- ======================================================
INSERT INTO notification_prefs (user_id, email_reminders, missed_dose_summary)
SELECT 
    user_id, 
    IF(RAND() > 0.5, 1, 0), 
    IF(RAND() > 0.5, 1, 0)
FROM user;

-- POPULATE EMERGENCY CONTACTS
-- ======================================================
INSERT INTO emergency_contact (contact_id, user_id, name, phone, email, `trigger`)
SELECT 
    UUID(),
    user_id,
    CONCAT('Contact for ', SUBSTRING_INDEX(name, ' ', 1)),
    '555-0199', -- Dummy phone number
    CONCAT('contact_', SUBSTRING_INDEX(email, '@', 1), '@gmail.com'),
    'After 3 missed doses'
FROM user;

-- POPULATE REMINDERS
-- ======================================================
INSERT INTO reminder (reminder_id, user_id, rx_id, remind_time, override_frequency)
SELECT 
    UUID(),
    user_id,
    rx_id,
    ADDTIME(CONCAT(CURDATE(), ' 08:00:00'), SEC_TO_TIME(FLOOR(0 + (RAND() * 36000)))), 
    NULL
FROM prescription;

SET SQL_SAFE_UPDATES = 1;