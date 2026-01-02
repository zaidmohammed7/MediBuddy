DROP PROCEDURE IF EXISTS EditDoctor;

DELIMITER //

CREATE PROCEDURE EditDoctor(
    IN p_doctor_id VARCHAR(255),
    IN p_action VARCHAR(10),
    IN p_first_name VARCHAR(255),
    IN p_last_name VARCHAR(255),
    IN p_specialty_id VARCHAR(255),
    IN p_address_line1 VARCHAR(255),
    IN p_city VARCHAR(255),
    IN p_state VARCHAR(2),
    IN p_zip_code VARCHAR(20),
    IN p_phone_number VARCHAR(50)
)
BEGIN
    IF p_action = 'update' THEN
        UPDATE doctor
        SET first_name = p_first_name,
            last_name = p_last_name,
            specialty_id = p_specialty_id,
            address_line1 = p_address_line1,
            city = p_city,
            state = p_state,
            zip_code = p_zip_code,
            phone_number = p_phone_number
        WHERE doctor_id = p_doctor_id;

    ELSEIF p_action = 'delete' THEN
        DELETE FROM doctor
        WHERE doctor_id = p_doctor_id;
    END IF;

    SELECT d.disease_name AS disease_name, COUNT(*) AS doctor_count
    FROM doctor doc
    JOIN disease d ON doc.specialty_id = d.specialty_id
    WHERE LEFT(doc.zip_code, 5) = LEFT(p_zip_code, 5)
    GROUP BY d.disease_name
    ORDER BY doctor_count DESC
    LIMIT 10;

END //

DELIMITER ;

CALL EditDoctor('123e4567-e89b-12d3-a456-426614174000', 'update', 'John', 'Doe', 'cardiology', '123 Main St', 'Chicago', 'IL', '60617', '555-1234');