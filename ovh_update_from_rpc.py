"""
$ pip install ovh
$ pip install nano-python
"""
import json
import ovh
import nano
import ipaddress

from config import *

# config.py needs these entries
# application_key = "xxxxxxxx"
# application_secret = "xxxxxxxx"
# consumer_key = "xxxxxxxx"
# domain = "example.com"
# subdomain = "peering"

rpc = nano.rpc.Client("http://localhost:7076")

node_peers = rpc.peers()

# print(json.dumps(node_peers, indent=4))

print(f"Found {len(node_peers)} node peers")


def convert_to_ipv4_address(peer):
    ip, separator, port = peer.rpartition(":")
    assert separator  # separator (`:`) must be present
    port = int(port)  # convert to integer
    ip = ipaddress.ip_address(
        ip.strip("[]")
    )  # convert to `IPv4Address` or `IPv6Address`

    # print(ip.version)  # print ip version: `4` or `6`
    assert ip.version == 6

    # print(ip.ipv4_mapped)
    return str(ip.ipv4_mapped)


peer_ips = [convert_to_ipv4_address(peer) for peer in node_peers.keys()]

# print(json.dumps(peer_ips, indent=4))


# Instanciate an OVH Client.
# You can generate new credentials with full access to your account on
# the token creation page
client = ovh.Client(
    # Endpoint of API OVH Europe (List of available endpoints)
    endpoint="ovh-eu",
    application_key=application_key,  # Application Key
    application_secret=application_secret,  # Application Secret
    consumer_key=consumer_key,  # Consumer Key
)

record_ids = client.get(
    f"/domain/zone/{domain}/record",
    fieldType="A",
    subDomain=subdomain,
)

# print(json.dumps(record_ids, indent=4))


def get_record(record_id):
    result = client.get(f"/domain/zone/{domain}/record/{record_id}")
    return result


raw_records = [get_record(id) for id in record_ids]

existing_targets = [record["target"] for record in raw_records]

existing_targets_mapping = {record["target"]: record["id"] for record in raw_records}

print(f"Found {len(existing_targets)} existing records")


new_peers = [peer_ip for peer_ip in peer_ips if peer_ip not in existing_targets]


print(f"Found {len(new_peers)} new peer ips")


dead_peers = [
    existing_target
    for existing_target in existing_targets
    if existing_target not in peer_ips
]

print(f"Found {len(dead_peers)} dead peer ips")


def add_record(ip):
    print(f"Adding record for: {ip}")

    result = client.post(
        f"/domain/zone/{domain}/record",
        fieldType="A",
        subDomain=subdomain,
        target=ip,
        ttl=None,
    )

    # Pretty print
    # print(json.dumps(result, indent=4))


def delete_record(ip):
    print(f"Deleteing record for: {ip}")

    id = existing_targets_mapping[ip]
    result = client.delete(f"/domain/zone/{domain}/record/{id}")


def refresh_zone():
    print(f"Refreshing zone")
    result = client.post(f"/domain/zone/{domain}/refresh")


for new_peer in new_peers:
    add_record(new_peer)

for dead_peer in dead_peers:
    delete_record(dead_peer)


refresh_zone()
