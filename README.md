# Anime-RSS-to-Aria2

## 环境变量列表

| 配置文件项       | 环境变量         | 属性   | 默认值 | 说明                                           |
| ---------------- | ---------------- | ------ | ------ | ---------------------------------------------- |
| aria2.host       | ARIA2_HOST       | 必须   |        | Aria2的地址                                    |
| aria2.port       | ARIA2_PORT       | 非必须 | 6800   | Aria2的端口                                    |
| aria2.secret     | ARIA2_SECRET     | 必须   |        | Aria2的密码                                    |
| telegram.enable  | TELEGRAM_ENABLE  | 非必须 |        | 传入任意值启用Telegram通知                     |
| telegram.token   | TELEGRAM_TOKEN   | 非必须 |        | Telegram Bot的Token                            |
| telegram.chat_id | TELEGRAM_CHAT_ID | 非必须 |        | Telegram的Chat ID                              |
| mongo_url        | DATABASE         | 必须   |        | MongoDB的链接                                  |
| base_url         | BASE_URL         | 非必须 |        | 基础链接，媒体的实际链接将为`base_url`+`title` |

## RSS配置文件

默认读取`data/rss.yaml`，可以通过定义环境变量`RSS_CONFIG`来定义读取的文件。

例如将其定义为`rss2.yaml`，则会读取`data/rss2.yaml`文件。

也可以将其定义为一个链接（必须以http开头），例如 https://raw.githubusercontent.com/Apocalypsor/Anime-RSS-to-Aria2/master/data/rss_example.yaml
。

如果链接需要 `Bearer Authentication`（例如Github），可以定义环境变量`AUTHORIZATION_TOKEN`来验证。

### RSS源:

1. https://mikanani.me/

2. https://rssbg.now.sh