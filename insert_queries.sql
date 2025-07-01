-- First, clear existing data (optional)
DELETE FROM dbo.powerbi_users_new;
DELETE FROM dbo.powerbi_reports_new;

-- Insert users
INSERT INTO dbo.powerbi_users_new (username, password, role) VALUES
('Rakesh', 'Oliva@123', 'admin'),
('Anjitha S', 'Oliva@123', 'user'),
('Aditya', 'Oliva@123', 'admin'),
('Anthony', 'Oliva@123', 'admin'),
('Chandrakanth', 'Oliva@123', 'admin'),
('Devops', 'Oliva@123', 'admin'),
('Indrapriya', 'Oliva@123', 'admin'),
('Jyoti', 'Oliva@123', 'admin'),
('kedaara', 'Oliva@123', 'admin'),
('misteam', 'Oliva@123', 'admin'),
('powerbi', 'Oliva@123', 'admin'),
('Sujal', 'Oliva@123', 'admin'),
('Udeshang', 'Oliva@123', 'admin'),
('Gangadhara G B', 'Oliva@123', 'user'),
('Mamatha Vishal Bhalke', 'Oliva@123', 'user'),
('Chandhana V', 'Oliva@123', 'user'),
('Mirza Athar Ali', 'Oliva@123', 'user'),
('Mallela Celestina', 'Oliva@123', 'user'),
('Mayndraguti Varsha', 'Oliva@123', 'user'),
('Lala Revathi Bai', 'Oliva@123', 'user'),
('K Naveen Kumar', 'Oliva@123', 'user'),
('Ruksar Shaikh Karim', 'Oliva@123', 'user'),
('Rueben Paulson', 'Oliva@123', 'user'),
('Bhavana K', 'Oliva@123', 'user'),
('Digvijay Singh', 'Oliva@123', 'user'),
('Suryakant', 'Oliva@123', 'user'),
('K Lakshmi Narasimha Raju', 'Oliva@123', 'user'),
('David Sharon', 'Oliva@123', 'user'),
('Thebarreni Sai Manesh', 'Oliva@123', 'user'),
('Imtiaz Ansari', 'Oliva@123', 'user'),
('Sumana Rana', 'Oliva@123', 'user'),
('Ankita Sanjay Dumbere', 'Oliva@123', 'user'),
('Karkala Mallesh Poornima', 'Oliva@123', 'user'),
('Vasumohanranga Madhavan', 'Oliva@123', 'user'),
('Annapurna', 'Oliva@123', 'user'),
('Binod Kumar Nayak', 'Oliva@123', 'user'),
('Tarra Divya Sai', 'Oliva@123', 'user'),
('B M Vaijinath', 'Oliva@123', 'user'),
('Vishal', 'Oliva@123', 'admin'),
('Sandeep', 'Sandeep@123', 'admin'),
('Sandhya Inala', 'Oliva@123', 'admin'),
('pushkaraj.shenai@olivaclinic.com', 'Oliva@123', 'admin'),
('riya.kumbhani@olivaclinic.com', 'Oliva@123', 'admin'),
('shashi.r@olivaclinic.com', 'Oliva@123', 'admin'),
('Oliva Reports', 'Oliva@9876', 'admin');

-- Insert reports
INSERT INTO dbo.powerbi_reports_new (username, dashboard_name, group_id, report_id) VALUES
-- Admin users with all dashboards
('Aditya', 'Call center Dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', '1c33878e-885c-44f8-b8dc-55c0b73d3afa'),
('Aditya', 'Clinic Operations dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', 'b46db7ca-a042-40d1-9458-012b5c889d80'),
('Aditya', 'Clinic Operations 360 dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', '6c075c94-f975-4854-a2de-7da66894c3c9'),
('Aditya', 'Marketing Dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', '2fc4d446-3ec5-49ee-b60f-c2a3ce1bc355'),

('Anthony', 'Call center Dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', '1c33878e-885c-44f8-b8dc-55c0b73d3afa'),
('Anthony', 'Clinic Operations dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', 'b46db7ca-a042-40d1-9458-012b5c889d80'),
('Anthony', 'Clinic Operations 360 dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', '6c075c94-f975-4854-a2de-7da66894c3c9'),
('Anthony', 'Marketing Dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', '2fc4d446-3ec5-49ee-b60f-c2a3ce1bc355'),

('Chandrakanth', 'Call center Dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', '1c33878e-885c-44f8-b8dc-55c0b73d3afa'),
('Chandrakanth', 'Clinic Operations dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', 'b46db7ca-a042-40d1-9458-012b5c889d80'),
('Chandrakanth', 'Clinic Operations 360 dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', '6c075c94-f975-4854-a2de-7da66894c3c9'),
('Chandrakanth', 'Marketing Dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', '2fc4d446-3ec5-49ee-b60f-c2a3ce1bc355'),

-- Regular users with Call Center Dashboard only
('Gangadhara G B', 'Call Center Dashboard', 'e1229faa-9727-4861-9820-0d01803a2b9a', '1c33878e-885c-44f8-b8dc-55c0b73d3afa'),
('Mamatha Vishal Bhalke', 'Call Center Dashboard', 'e1229faa-9727-4861-9820-0d01803a2b9a', '1c33878e-885c-44f8-b8dc-55c0b73d3afa'),
('Chandhana V', 'Call Center Dashboard', 'e1229faa-9727-4861-9820-0d01803a2b9a', '1c33878e-885c-44f8-b8dc-55c0b73d3afa'),
('Mirza Athar Ali', 'Call Center Dashboard', 'e1229faa-9727-4861-9820-0d01803a2b9a', '1c33878e-885c-44f8-b8dc-55c0b73d3afa'),
('Mallela Celestina', 'Call Center Dashboard', 'e1229faa-9727-4861-9820-0d01803a2b9a', '1c33878e-885c-44f8-b8dc-55c0b73d3afa'),
('Mayndraguti Varsha', 'Call Center Dashboard', 'e1229faa-9727-4861-9820-0d01803a2b9a', '1c33878e-885c-44f8-b8dc-55c0b73d3afa'),
('Lala Revathi Bai', 'Call Center Dashboard', 'e1229faa-9727-4861-9820-0d01803a2b9a', '1c33878e-885c-44f8-b8dc-55c0b73d3afa'),
('K Naveen Kumar', 'Call Center Dashboard', 'e1229faa-9727-4861-9820-0d01803a2b9a', '1c33878e-885c-44f8-b8dc-55c0b73d3afa'),
('Ruksar Shaikh Karim', 'Call Center Dashboard', 'e1229faa-9727-4861-9820-0d01803a2b9a', '1c33878e-885c-44f8-b8dc-55c0b73d3afa'),
('Rueben Paulson', 'Call Center Dashboard', 'e1229faa-9727-4861-9820-0d01803a2b9a', '1c33878e-885c-44f8-b8dc-55c0b73d3afa'),

-- Special cases
('Sandhya Inala', 'Clinic Operations Dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', 'b46db7ca-a042-40d1-9458-012b5c889d80'),
('pushkaraj.shenai@olivaclinic.com', 'Call center Dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', '1c33878e-885c-44f8-b8dc-55c0b73d3afa'),
('pushkaraj.shenai@olivaclinic.com', 'Clinic Operations dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', 'b46db7ca-a042-40d1-9458-012b5c889d80'),
('pushkaraj.shenai@olivaclinic.com', 'Clinic Operations 360 dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', '6c075c94-f975-4854-a2de-7da66894c3c9'),
('pushkaraj.shenai@olivaclinic.com', 'Marketing Dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', '2fc4d446-3ec5-49ee-b60f-c2a3ce1bc355'),
('riya.kumbhani@olivaclinic.com', 'Marketing Dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', '2fc4d446-3ec5-49ee-b60f-c2a3ce1bc355'),
('shashi.r@olivaclinic.com', 'Call center Dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', '1c33878e-885c-44f8-b8dc-55c0b73d3afa'),
('Oliva Reports', 'Oyster', 'e1229faa-9727-4861-9820-0d01803a2b9a', 'ab9d96b1-0a1a-4269-8ed2-9f3957c08267'),

-- Add Sandeep's reports
('Sandeep', 'Call center Dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', '1c33878e-885c-44f8-b8dc-55c0b73d3afa'),
('Sandeep', 'Clinic Operations dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', 'b46db7ca-a042-40d1-9458-012b5c889d80'),
('Sandeep', 'Clinic Operations 360 dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', '6c075c94-f975-4854-a2de-7da66894c3c9'),
('Sandeep', 'Marketing Dashboard v1', 'e1229faa-9727-4861-9820-0d01803a2b9a', '2fc4d446-3ec5-49ee-b60f-c2a3ce1bc355'); 