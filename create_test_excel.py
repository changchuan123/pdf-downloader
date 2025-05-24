import pandas as pd

# 创建正确的测试数据：第一列为文件名，第二列为URL
data = {
    0: [
        '测试文件1.pdf',
        '测试文件2.pdf'
    ],
    1: [
        'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
        'https://www.africau.edu/images/default/sample.pdf'
    ]
}

df = pd.DataFrame(data)
df.to_excel('test_urls.xlsx', index=False, header=False, engine='openpyxl')
print('✅ 创建了正确的test_urls.xlsx文件')
print('文件内容:')
print('第一列：文件名 | 第二列：URL')
print(df)