SELECT TOP (1000) [OrderDate]
      ,[OrderNo]
      ,[ItemName]
      ,[PendingQty]
      ,[Rate]
      ,[ValueAmount]
      ,[DueOn]
      ,[DueDays]
  FROM [Sales_outstandingDB].[dbo].[SalesData]
  SELECT * 
FROM [Sales_outstandingDB].[dbo].[SalesData];
