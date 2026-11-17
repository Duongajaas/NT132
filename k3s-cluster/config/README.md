# Kubernetes configuration

Thư mục này chứa các manifest triển khai ChatApp trong namespace `chat`.

## Thành phần

### `chat.yaml`

Manifest tạo các tài nguyên chính:

- `ConfigMap/app-config`: cấu hình không bí mật cho API và worker.
- `Deployment/redis` và `Service/redis`: Redis dùng cho shared state, presence và các tính năng cần giao tiếp giữa nhiều instance.
- `Deployment/api`: ChatApp API, mặc định một replica, lắng nghe cổng `8080`.
- `Service/api`: headless Service (`clusterIP: None`) để NGINX có thể phân giải đến IP của từng API pod.
- `Service/api-lb`: ClusterIP Service thông thường, dùng để cân bằng request nội bộ đến các API pod.
- `Deployment/worker`: background worker với `Runtime__Role=worker`. Chiến lược `Recreate` đảm bảo không chạy đồng thời hai worker trong lúc rollout.
- `Deployment/frontend` và `Service/frontend`: frontend NGINX, TLS certificate lấy từ Secret `fe-tls`.
- `IngressRouteTCP/chat`: Traefik chuyển tiếp kết nối TLS đến frontend bằng TLS passthrough.

API và worker dùng chung `app-config` cùng Secret `app-secret`. Secret này phải tồn tại trước khi tạo pod:

```powershell
kubectl -n chat create secret generic app-secret `
  --from-literal=ConnectionStrings__DefaultConnection="..." `
  --from-literal=Jwt__SecretKey="..."
```

Không ghi secret thật vào file manifest hoặc tài liệu.

### `migrate.yaml`

Tạo một Kubernetes Job tên `migrate`. Job chạy `/app/efbundle` bằng cùng image API để áp dụng database migration một lần.

Job sử dụng `app-config` và `app-secret`, có `backoffLimit: 2` và không tự khởi động lại sau khi kết thúc. Hãy chạy migration trước khi rollout API/worker.

## Triển khai

```powershell
kubectl create namespace chat
kubectl apply -f .\config\chat.yaml
kubectl -n chat wait --for=condition=available deployment/redis --timeout=120s
kubectl apply -f .\config\migrate.yaml
kubectl -n chat wait --for=condition=complete job/migrate --timeout=180s
kubectl -n chat rollout status deployment/api
kubectl -n chat rollout status deployment/worker
kubectl -n chat rollout status deployment/frontend
```

Nếu `app-secret`, `fe-tls` hoặc image private registry chưa được chuẩn bị, các pod tương ứng sẽ không thể khởi động đầy đủ.

## Kiểm tra

```powershell
kubectl -n chat get deploy,pod,svc,job
kubectl -n chat get endpoints api api-lb
kubectl -n chat logs job/migrate
kubectl -n chat describe pod -l app=api
```

API readiness dùng endpoint `/health/ready`. Startup probe cho API cho phép tối đa khoảng 90 giây để ứng dụng khởi động; readiness probe kiểm tra mỗi 5 giây và loại pod khỏi Service sau hai lần thất bại.

## Cập nhật image

Các Deployment hiện tham chiếu image:

```text
192.168.56.10:5000/chat-be:v1
192.168.56.10:5000/chat-fe:v1
```

Khi phát hành phiên bản mới, cập nhật tag trong manifest rồi áp dụng lại. API dùng RollingUpdate với `maxUnavailable: 0`; worker dùng `Recreate` để giữ một worker hoạt động tại một thời điểm.
