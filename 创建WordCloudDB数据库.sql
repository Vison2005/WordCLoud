-- ������Ϊ WordCloudDB �����ݿ�
CREATE DATABASE WordCloudDB;
GO

-- ʹ�� WordCloudDB ���ݿ�
USE WordCloudDB;
GO

-- ������Ϊ WordCloudData �ı�
CREATE TABLE WordCloudData (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    ImageName NVARCHAR(255),
    ImageData VARBINARY(MAX),
    TextFileName NVARCHAR(255),
    TextData NVARCHAR(MAX)
);