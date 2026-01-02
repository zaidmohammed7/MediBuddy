DELIMITER //

CREATE TRIGGER ZeroRefillsTrig
-- Event: Update prescription
AFTER UPDATE ON prescription
	FOR EACH ROW
	BEGIN
		-- Condition: Check if refills just hit 0 AND were previously > 0
		IF new.refills = 0 AND old.refills > 0 THEN
			-- Action: Add a reminder to call the doctor
			INSERT INTO reminder (reminder_id, user_id, rx_id, remind_time)
			VALUES (UUID(), new.user_id, new.rx_id, NOW());
		END IF;
END //
    
DELIMITER ;