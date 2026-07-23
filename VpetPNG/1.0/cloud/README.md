# 桌宠编号发号服务

## 策略

| 情况 | 结果 |
|------|------|
| 首次联网 | 按设备指纹**自动分配**桌宠编号 |
| 同机再次启动 | 找回原编号 |
| 拷贝他人存档到新机 | 本地沿用存档编号（不因拷贝再发新号） |

玩家**不可手填**编号 / API / 激活码。服务地址写在客户端 `DEFAULT_PET_ID_API_URL`，或环境变量 `VPET_PET_ID_API`。

## 本地启动

```bat
python cloud/pet_id_server.py --host 0.0.0.0 --port 8787
```

客户端开发时可：

```bat
set VPET_PET_ID_API=http://127.0.0.1:8787
```

正式发版：在 `pet_id_cloud.py` 填入 `DEFAULT_PET_ID_API_URL`（如 Cloudflare Worker 地址）。

## 接口

- `GET /health`
- `POST /v1/register` `{machine_id}` → 自动发号或找回
