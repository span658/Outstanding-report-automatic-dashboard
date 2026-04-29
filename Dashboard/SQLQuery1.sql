USE BillDB;
DROP TABLE IF EXISTS dbo.BillsReceivableRaw;
DBCC CHECKIDENT ('dbo.BillsReceivableRaw', RESEED, 0);

CREATE TABLE dbo.BillsReceivableRaw (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    BillDate NVARCHAR(20),
    RefNo NVARCHAR(100),
    PartyName NVARCHAR(255),
    PendingAmount DECIMAL(18,2),
    DueOn NVARCHAR(20),
    OverdueDays INT
);
SELECT * FROM dbo.BillsReceivableRaw;
SELECT COUNT(*) FROM dbo.BillsReceivableRaw;
SELECT TOP 963 *
FROM dbo.BillsReceivableRaw;
SELECT * 
FROM dbo.BillsReceivableRaw
ORDER BY BillDate;
USE BillDB;

SELECT SUM(PendingAmount) AS TotalOutstanding
FROM dbo.BillsReceivableRaw;
DBCC CHECKIDENT ('dbo.BillsReceivableRaw', RESEED, 0);













































