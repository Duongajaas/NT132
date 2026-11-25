# Storage Orchestration

## Overview

This project demonstrates Persistent Storage Orchestration
in Kubernetes using the K3s Local Path Provisioner.

## Components

- Namespace: data
- StorageClass: local-path
- PersistentVolumeClaim: demo-pvc
- Pod: storage-demo
- Test Pod: shared-pod

## Scenarios

### Scenario 1: Persistent Volume Provisioning

Create a Namespace, PersistentVolumeClaim and Pod
to demonstrate automatic persistent volume provisioning.

### Scenario 2: Data Persistence

Write data to the persistent volume, delete the Pod,
recreate the Pod and verify that the data remains.

### Scenario 3: Local Storage Node Constraint

Test the limitation of local storage by scheduling
a Pod on another node and examining volume node affinity.

## Configuration Files

- namespace.yaml
- pvc.yaml
- storage-pod.yaml
- shared-pod.yaml
