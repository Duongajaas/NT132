# Service Discovery and Load Balancing

Thư mục này minh họa cách Kubernetes Service Discovery kết hợp với NGINX để định tuyến và cân bằng tải cho ChatApp.

## Các file

- `nginx.conf`: cấu hình reverse proxy chạy trong frontend pod.
- `whoami.yaml`: deployment thử nghiệm có 3 replica và Service `whoami`.
- `probe.yaml`: pod kiểm tra liên tục endpoint readiness qua Service `api-lb`.

## Service discovery

Trong `chat.yaml`, API có hai Service:

| Service | Loại | Mục đích |
|---|---|---|
| `api` | Headless (`clusterIP: None`) | DNS trả về IP của các API pod để NGINX có thể biết từng backend |
| `api-lb` | ClusterIP | Một địa chỉ ổn định để các workload trong cluster gọi API và để Kubernetes cân bằng request |

NGINX phân giải tên đầy đủ `api.chat.svc.cluster.local` bằng CoreDNS. Resolver trong `nginx.conf` là `10.43.0.10`, địa chỉ DNS service mặc định của k3s. DNS record được làm mới mỗi 5 giây (`valid=5s`), vì vậy danh sách pod backend có thể thay đổi khi rollout hoặc scale.

## Cân bằng tải tại NGINX

Hai upstream được cấu hình:

- `chat_http`: xử lý REST API và upload file.
- `chat_hubs`: xử lý SignalR/WebSocket.

Cả hai dùng `least_conn`, ưu tiên backend đang có ít kết nối hơn. Mỗi upstream có connection pool `keepalive 32` và loại backend sau tối đa hai lỗi trong khoảng `10s`.

SignalR có thêm:

- Header `Upgrade` và `Connection` để nâng cấp sang WebSocket.
- `proxy_buffering off`.
- `proxy_read_timeout 120s`.
- Cookie affinity `chat_route` cho đường dẫn `/hubs/`.

Các route chính:

| Route | Upstream / xử lý |
|---|---|
| `/api/files/upload` | `chat_http`, giới hạn riêng 9 MB |
| `/api/` | `chat_http` |
| `/hubs/` | `chat_hubs`, WebSocket/SignalR |
| `/assets/` | file tĩnh, cache immutable trong 1 năm |
| `/` | SPA fallback về `/index.html` |

HTTP tại cổng `8080` redirect sang HTTPS. HTTPS tại cổng `8443` dùng certificate được mount từ Secret `fe-tls`. Query string không được ghi log vì SignalR có thể truyền access token trong query string.

## Kiểm tra discovery và load balancing

Triển khai probe:

```powershell
kubectl apply -f .\config\chat.yaml
kubectl apply -f .\Service_Discovery_and_Load_Balancing\probe.yaml
kubectl -n chat logs -f pod/probe
```

Probe gọi:

```text
http://api-lb:8080/health/ready
```

Log `OK` cho biết Service đang chuyển được request đến API pod; `FAIL` cần kiểm tra readiness, endpoints và log API:

```powershell
kubectl -n chat get endpoints api api-lb
kubectl -n chat get pods -l app=api -o wide
kubectl -n chat describe svc api-lb
```

## Kiểm tra nhiều backend với `whoami`

```powershell
kubectl apply -f .\Service_Discovery_and_Load_Balancing\whoami.yaml
kubectl -n chat get pods -l app=whoami -o wide
kubectl -n chat get endpoints whoami
```

Service `whoami` phân phối request đến ba pod. Có thể tạo một pod tạm trong namespace `chat` để gọi Service nhiều lần:

```powershell
kubectl -n chat run curl --rm -it --restart=Never `
  --image=curlimages/curl -- sh -c "for i in 1 2 3 4 5; do curl -s http://whoami; echo; done"
```

## Scale và rollout

```powershell
kubectl -n chat scale deployment/api --replicas=3
kubectl -n chat rollout status deployment/api
kubectl -n chat get endpoints api api-lb -w
```

Khi pod mới đạt readiness, endpoint sẽ được thêm vào Service. Khi pod cũ bị loại khỏi readiness hoặc bị xóa, endpoint tương ứng được loại bỏ; NGINX sẽ nhận danh sách backend mới ở lần DNS refresh tiếp theo.
