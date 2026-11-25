# NT132 - ChatApp và triển khai K3s

Dự án gồm ứng dụng chat trực tuyến ChatApp và các kịch bản thực hành vận hành ứng dụng trên cụm K3s/Kubernetes.

## Cấu trúc ứng dụng

### Backend

Backend nằm trong `ChatApp/`, xây dựng bằng ASP.NET Core/.NET 10 và cung cấp REST API cùng SignalR cho nhắn tin, presence và gọi. Các thành phần chính:

- `Controllers/`: các endpoint HTTP cho xác thực, người dùng, bạn bè, hội thoại, nhóm và tin nhắn.
- `Services/`, `Calls/`, `Messages/`, `Notifications/`: nghiệp vụ và xử lý tính năng.
- `Hubs/`, `Realtime/`, `Presence/`: kết nối thời gian thực, SignalR và trạng thái online.
- `Data/`, `Models/`, `Migrations/`: truy cập PostgreSQL, mô hình dữ liệu và migration.
- Redis được sử dụng cho shared state và presence khi chạy nhiều instance; background worker xử lý các tác vụ nền.

### Frontend

Frontend nằm trong `chat-app-web/`, dùng React, TypeScript và Vite; image production phục vụ ứng dụng bằng NGINX.

- `src/pages/`: các trang chat, đăng nhập, đăng ký, bạn bè và hồ sơ.
- `src/components/`: các thành phần giao diện dùng lại.
- `src/api/`: các hàm giao tiếp với backend.
- `src/realtime/`, `src/store/`: kết nối thời gian thực và state của ứng dụng.

## Triển khai và demo 8 chức năng K3s

Manifest và kịch bản demo nằm trong `k3s-cluster/`. Các chức năng dưới đây minh họa những khả năng điều phối ứng dụng của Kubernetes trên K3s:

1. **Automated Rollouts and Rollbacks** - Dùng `Deployment` và chiến lược `RollingUpdate` để cập nhật pod dần dần. Cấu hình API trong `config/chat.yaml` đặt `maxUnavailable: 0`; có thể theo dõi rollout và quay lại revision trước bằng `kubectl rollout status` và `kubectl rollout undo`.
2. **Service Discovery and Load Balancing** - CoreDNS và Kubernetes `Service` cung cấp tên DNS và địa chỉ dịch vụ ổn định. Demo có `api-lb` kiểu ClusterIP để cân bằng request đến các API pod; NGINX làm reverse proxy cho REST API và SignalR/WebSocket. Xem `Service_Discovery_and_Load_Balancing/`.
3. **Declarative Configuration / Desired State Management** - Khai báo namespace, Deployment, Service và cấu hình bằng YAML; áp dụng manifest để K3s duy trì số replica và trạng thái mong muốn. Xem `vinh-kubernetes/01-desired-state/`.
4. **Storage Orchestration** - Demo với Local Path Provisioner, `StorageClass`, `PersistentVolumeClaim` và pod sử dụng volume; kiểm tra cấp phát volume, dữ liệu còn sau khi tạo lại pod và ràng buộc lưu trữ theo node. Xem `storage-orchestration/`.
5. **Self-healing** - `Deployment` duy trì số pod khai báo (demo 3 replica); khi pod bị xóa hoặc dừng, Kubernetes tạo pod thay thế để trở về trạng thái mong muốn. Xem `Self-healing/`.
6. **Autoscaling** - Minh họa scale theo CPU bằng HPA (mục tiêu 50%, từ 1 đến 5 replica) và scale theo lịch bằng KEDA (0 đến 3 replica). Xem `Autoscaling/`.
7. **Configuration and Secret Management** - `ConfigMap` chứa cấu hình không nhạy cảm; thông tin như chuỗi kết nối và khóa JWT được đưa vào Kubernetes `Secret` và nạp vào container qua biến môi trường. Không lưu giá trị secret thật trong manifest công khai. Xem `ConfigMaps_Secrets-Extensibility/` và `config/`.
8. **Extensibility** - Mở rộng Kubernetes bằng CRD `WebApp` và operator Python. Người dùng khai báo image/replica trong custom resource; operator theo dõi và reconcile thành `Deployment`. Xem `ConfigMaps_Secrets-Extensibility/operator/`.

### Các thành phần triển khai ChatApp

`k3s-cluster/config/chat.yaml` khai báo các workload và dịch vụ Redis, API, worker, frontend; frontend được phục vụ bởi NGINX và kết nối vào API. `migrate.yaml` chạy database migration bằng Kubernetes Job. Cấu hình không bí mật nằm trong ConfigMap, còn thông tin nhạy cảm được cấp riêng qua Secret. Các kịch bản demo từng chức năng nằm trong các thư mục con được liệt kê ở trên.

## Video demo

[Xem video demo các chức năng K3s](https://drive.google.com/drive/folders/1B_gzi1rqN-Qqc2NoF3QYlb_JwkndWZAx?hl=vi)

## Phân công công việc

| STT | Họ và tên | Nhiệm vụ | Mức độ hoàn thành |
|---:|---|---|---:|
| 1 | Lê Quốc Dương | Triển khai cụm K3s, demo tính năng Rolling Updates/Rollbacks và Service Discovery and Load Balancing | 100% |
| 2 | Hồ Nhật Duy | Triển khai cụm K3s, demo tính năng Configuration/Secret Management và Extensibility | 100% |
| 3 | Huỳnh Thanh Hoàng | Triển khai cụm K3s, demo tính năng Self-healing và Autoscaling | 100% |
| 4 | Lê Quang Vinh | Triển khai cụm K3s, demo tính năng Declarative Configuration/Desired State Management và Storage Orchestration | 100% |