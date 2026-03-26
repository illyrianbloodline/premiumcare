-- ============================================================
-- Sample Invoice Data for MedPlatform Dashboard Charts
-- Run: psql -U medplatform_user -d medplatform -f sample_invoices.sql
-- ============================================================

-- Only insert if no invoices exist yet
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM invoices LIMIT 1) THEN

    -- Last 6 months of invoices tied to existing patients
    INSERT INTO invoices (patient_id, doctor_id, invoice_date, due_date, total_amount, amount_paid, status, notes, created_by)
    SELECT
      p.id,
      1,
      (CURRENT_DATE - (n || ' days')::INTERVAL)::DATE,
      (CURRENT_DATE - (n || ' days')::INTERVAL + INTERVAL '30 days')::DATE,
      amount,
      paid,
      CASE WHEN paid >= amount THEN 'paid'
           WHEN paid > 0 THEN 'partial'
           ELSE 'unpaid' END,
      'Konsultë e zakonshme',
      1
    FROM (VALUES
      -- Oct (150 days ago)
      (150, 85.00,  85.00),
      (145, 120.00, 120.00),
      (142, 65.00,  65.00),
      (138, 200.00, 200.00),
      -- Nov (120 days ago)
      (120, 85.00,  85.00),
      (118, 150.00, 150.00),
      (115, 95.00,  95.00),
      (112, 85.00,  0.00),
      -- Dec (90 days ago)
      (90,  85.00,  85.00),
      (88,  240.00, 240.00),
      (85,  120.00, 120.00),
      (82,  85.00,  42.50),
      -- Jan (60 days ago)
      (60,  85.00,  85.00),
      (58,  175.00, 175.00),
      (55,  95.00,  95.00),
      (52,  85.00,  0.00),
      (50,  300.00, 300.00),
      -- Feb (30 days ago)
      (30,  85.00,  85.00),
      (28,  130.00, 130.00),
      (25,  85.00,  85.00),
      (22,  95.00,  0.00),
      (20,  85.00,  85.00),
      -- Mar / this month
      (10,  85.00,  85.00),
      (8,   200.00, 200.00),
      (5,   95.00,  95.00),
      (3,   85.00,  0.00),
      (1,   150.00, 75.00)
    ) AS v(n, amount, paid)
    CROSS JOIN (SELECT id FROM patients ORDER BY id LIMIT 1) p;

  END IF;
END $$;

SELECT
  'Invoices inserted: ' || COUNT(*) AS status,
  '€' || SUM(total_amount)::int || ' total billed' AS billed,
  '€' || SUM(amount_paid)::int || ' collected' AS collected,
  COUNT(*) FILTER (WHERE status = 'unpaid') || ' unpaid' AS unpaid
FROM invoices;
