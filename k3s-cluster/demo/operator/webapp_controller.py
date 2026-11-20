
import json
import ssl
import time
import urllib.request
import urllib.error
from pathlib import Path

NAMESPACE = "k8s-demo"
GROUP = "lab.nt132.example"
VERSION = "v1"

API = "https://kubernetes.default.svc"

SA = Path("/var/run/secrets/kubernetes.io/serviceaccount")
SSL_CONTEXT = ssl.create_default_context(
    cafile=str(SA / "ca.crt")
)

CR_PATH = (
    f"/apis/{GROUP}/{VERSION}"
    f"/namespaces/{NAMESPACE}/webapps"
)

DEPLOY_PATH = (
    f"/apis/apps/v1/namespaces/"
    f"{NAMESPACE}/deployments"
)


def request(method, path, body=None, patch=False):
    headers = {
        "Authorization": "Bearer " + (SA / "token").read_text().strip(),
        "Content-Type": (
            "application/strategic-merge-patch+json"
            if patch else "application/json"
        )
    }

    data = json.dumps(body).encode() if body is not None else None

    req = urllib.request.Request(
        API + path,
        data=data,
        headers=headers,
        method=method
    )

    with urllib.request.urlopen(
        req, context=SSL_CONTEXT, timeout=10
    ) as response:
        return json.load(response)


def reconcile(webapp):
    meta = webapp["metadata"]

    if meta.get("deletionTimestamp"):
        return

    name = meta["name"]
    uid = meta["uid"]

    replicas = webapp["spec"]["replicas"]
    image = webapp["spec"]["image"]

    deployment_name = f"webapp-{name}"
    labels = {"webapp": name}

    path = f"{DEPLOY_PATH}/{deployment_name}"

    desired = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": deployment_name,
            "namespace": NAMESPACE,
            "ownerReferences": [{
                "apiVersion": f"{GROUP}/{VERSION}",
                "kind": "WebApp",
                "name": name,
                "uid": uid,
                "controller": True
            }]
        },
        "spec": {
            "replicas": replicas,
            "selector": {
                "matchLabels": labels
            },
            "template": {
                "metadata": {
                    "labels": labels
                },
                "spec": {
                    "nodeSelector": {
                        "workload": "chatapp"
                    },
                    "automountServiceAccountToken": False,
                    "containers": [{
                        "name": "web",
                        "image": image,
                        "ports": [{
                            "containerPort": 80
                        }]
                    }]
                }
            }
        }
    }

    try:
        current = request("GET", path)

    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise

        request("POST", DEPLOY_PATH, desired)

        print(
            f"CREATE {deployment_name}: "
            f"replicas={replicas}, image={image}",
            flush=True
        )
        return

    owners = current["metadata"].get("ownerReferences", [])

    if not any(owner.get("uid") == uid for owner in owners):
        print(f"SKIP {deployment_name}: ownership conflict", flush=True)
        return

    actual_replicas = current["spec"].get("replicas", 1)

    containers = current["spec"]["template"]["spec"]["containers"]

    actual_image = next(
        (c["image"] for c in containers if c["name"] == "web"),
        None
    )

    changes = {}

    if actual_replicas != replicas:
        changes["replicas"] = replicas

    if actual_image != image:
        changes["template"] = {
            "spec": {
                "containers": [{
                    "name": "web",
                    "image": image
                }]
            }
        }

    if changes:
        request(
            "PATCH",
            path,
            {"spec": changes},
            patch=True
        )

        print(
            f"RECONCILE {deployment_name}: "
            f"replicas {actual_replicas} -> {replicas}; "
            f"image {actual_image} -> {image}",
            flush=True
        )


print("WebApp Operator started", flush=True)

while True:
    try:
        webapps = request("GET", CR_PATH)

        for webapp in webapps["items"]:
            try:
                reconcile(webapp)
            except Exception as error:
                print(f"RECONCILE ERROR: {error}", flush=True)

    except Exception as error:
        print(f"API ERROR: {error}", flush=True)

    time.sleep(5)
