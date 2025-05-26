-- 创建名为 WordCloudDB 的数据库
CREATE DATABASE WordCloudDB;
GO

-- 使用 WordCloudDB 数据库
USE WordCloudDB;
GO

-- 创建名为 WordCloudData 的表
CREATE TABLE WordCloudData (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    ImageName NVARCHAR(255),
    ImageData VARBINARY(MAX),
    TextFileName NVARCHAR(255),
    TextData NVARCHAR(MAX)
);