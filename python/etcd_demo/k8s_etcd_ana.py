#!/usr/bin/env python3
import etcd3
# import zip
import subprocess

if __name__ == "__main__":
    # host = "etcd.infcs.tob"
    # port = 4379
    kwargs = {}
    host = "127.0.0.1"
    port = 2379

    ca_cert = "/etc/ssl/etcd/ssl/ca.pem"
    cert_key = "/etc/ssl/etcd/ssl/admin-n180-036-016-key.pem"
    cert_cert = "/etc/ssl/etcd/ssl/admin-n180-036-016.pem"
    # kwargs["grpc_options"] = {'grpc.max_receive_message_length': 100 * 1024 * 1024,}
    # kwargs["ca_cert"] = "/etc/storage_etcd/ssl/ca.pem"
    # kwargs["cert_key"] = "/etc/storage_etcd/ssl/client-key.pem"
    # kwargs["cert_cert"] = "/etc/storage_etcd/ssl/client.pem"

    client = etcd3.Etcd3Client(host=host, port=port,
                               ca_cert=ca_cert,
                               cert_key=cert_key,
                               cert_cert=cert_cert,
                               grpc_options=[("grpc.max_receive_message_length", 1024 * 1024 * 100)], )

    # 获取 k8s 里的 前缀
    cmd = f'ETCDCTL_API=3 etcdctl --endpoints=https://{host}:{port} --cacert={ca_cert}  --cert={cert_cert} --key={cert_key} get --prefix=true --keys-only "/"'
    result = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True, text=True)
    stdout = result.stdout
    key_prefix_list = []
    for line in stdout.split("\n"):
        if line == "":
            continue
        # 保留前2级前缀，例如 line 是/registry/roles/kube-system/kubeadm:kubeadm-certs，那么 prefix 就是 /registry/roles
        prefix = "/".join(line.split("/")[:3])
        key_prefix_list.append(prefix)
    key_prefix_list = list(set(key_prefix_list))
    print(key_prefix_list)

    prefix_result = []
    for prefix in key_prefix_list:
        keys = client.get_prefix(prefix)
        size = 0
        i = 0
        for value, metadata in keys:
            key = metadata.key
            key_size = len(key)
            value_size = len(value)
            size += (key_size + value_size)
        prefix_result.append(size)
    print(list(zip(key_prefix_list, prefix_result)))
    print("total size:", sum(prefix_result))