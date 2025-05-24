# GitHub自动打包Windows EXE指南

## 🚀 快速开始

### 第一步：创建GitHub仓库
1. 访问 [GitHub.com](https://github.com)
2. 点击右上角的 "+" → "New repository"
3. 填写仓库信息：
   - Repository name: `pdf-downloader`
   - Description: `PDF批量下载器`
   - 选择 Public（公开）
   - **不要**勾选 "Add a README file"
4. 点击 "Create repository"

### 第二步：推送代码到GitHub
复制以下命令在当前目录执行：

```bash
# 添加远程仓库（替换YOUR_USERNAME为您的GitHub用户名）
git remote add origin https://github.com/YOUR_USERNAME/pdf-downloader.git

# 推送代码
git branch -M main
git push -u origin main
```

### 第三步：触发自动构建
代码推送后，GitHub Actions会自动开始构建：
1. 在GitHub仓库页面，点击 "Actions" 标签
2. 查看 "Build Windows EXE" 工作流
3. 等待构建完成（大约3-5分钟）

### 第四步：下载exe文件
构建完成后：
1. 点击最新的构建任务
2. 向下滚动到 "Artifacts" 部分
3. 点击下载 "PDF下载器-Windows-exe"
4. 解压得到完整的Windows版本

## 📁 您将得到的文件

下载的压缩包包含：
- `PDF下载器.exe` - 主程序（约20-30MB）
- `test_urls.xlsx` - 测试URL文件  
- `urls.xlsx` - 主URL文件
- `README.txt` - Windows使用说明

## 🔄 手动触发构建

如果需要重新构建：
1. 在GitHub仓库的 "Actions" 页面
2. 选择 "Build Windows EXE" 工作流
3. 点击 "Run workflow" 按钮
4. 点击绿色的 "Run workflow" 确认

## ⚠️ 注意事项

1. **GitHub账户要求**：需要GitHub账户（免费）
2. **构建时间**：首次构建约3-5分钟
3. **文件保存**：构建产物保存30天
4. **下载限制**：需要登录GitHub账户才能下载

## 🔧 如果遇到问题

**问题1：推送被拒绝**
```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

**问题2：构建失败**
- 检查GitHub Actions页面的错误日志
- 确认所有文件都已推送

**问题3：找不到Artifacts**
- 确保构建状态为绿色✅
- 刷新页面重试

## 📞 替代方案

如果GitHub方案有问题，我还为您准备了其他方案：
- 方案B：在线打包服务
- 方案C：Docker交叉编译
- 方案D：手动Windows打包

---

## 🎯 现在开始

请按照上述步骤操作，我已经为您准备好了所有必要的文件和配置。

大约5-10分钟后，您就能获得可直接在Windows上运行的exe文件！ 