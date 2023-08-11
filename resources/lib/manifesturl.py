import ipaddress
import random
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ManifestUrl:
    url: str
    manifest_type: str
    headers: Optional[dict] = None
    debug_source_name: Optional[str] = None


def random_elisa_ipv4():
    return str(random_ip(ipaddress.ip_network('91.152.0.0/13')))


def random_ip(ip_network):
    # Convert to an int range, because sampling from a range is efficient
    ip_range_start = ip_network.network_address + 1
    ip_range_end = ip_network.broadcast_address - 1
    int_ip_range = range(int(ip_range_start), int(ip_range_end) + 1)
    return ipaddress.ip_address(random.choice(int_ip_range))
