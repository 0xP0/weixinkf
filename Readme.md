

### 文档 https://kf.weixin.qq.com/api/doc/path/94745
### 配置页 https://work.weixin.qq.com/kf/frame#/config
edit .ENV.yaml

```yaml
weixinkf:
  appid: #客服账号id
  token: #token
  aeskey: #EncodingAESKey
  corpsecret: #Secret
  welcome_text: #欢迎文本
  qrurl: #欢迎文本中的跳转地址
  kfimg: #回复中的图片
redis:
  host: xxxxxxxxxx
  passwd: xxxxxx
  port: 6379
  db: 8
```

### 手动启动

```bash
# 监听服务 负责更新 token
nohup python WeixinServer.py &
# 工具类 & 消息处理  欢迎消息、自动回复
nohup python WxUtil.py &
```
### 容器启动
```bash
docker-compose up -d
```
