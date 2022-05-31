INSERT INTO partners(partner_name, partner_status)
    VALUES ('A', TRUE)
ON CONFLICT(partner_name)
    DO NOTHING;
INSERT INTO partners(partner_name, partner_status)
    VALUES ('B', FALSE)
ON CONFLICT(partner_name)
    DO NOTHING;
INSERT INTO partners(partner_name, partner_status)
    VALUES ('C', TRUE)
ON CONFLICT(partner_name)
    DO NOTHING;