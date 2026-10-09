# 阿盘·收盘扫盘 同款工具

手机可用的板块资金流向分析网页。

## 功能
- 黑马（偷偷建仓）：钱进来了，价没抬
- 冒头（明牌启动）：钱到位，已经动了
- 失血：大钱在跑，位置还在高位
- 一句话总结 + CSV下载

## 本地运行
```bash
pip install -r requirements_sector.txt
streamlit run sector_scan_app.py
```

## 免费部署到手机可用（推荐）

1. 把 `sector_scan_app.py` 和 `requirements_sector.txt` 上传到你的 GitHub 仓库
2. 打开 https://share.streamlit.io
3. 用 GitHub 登录 → Create app
4. 主文件选择 `sector_scan_app.py`
5. 部署成功后得到链接，手机浏览器打开即可使用

每天收盘后打开链接点一下「开始扫盘」就能看到同款分析。
