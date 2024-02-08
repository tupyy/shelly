#!/usr/bin/env python3
import argparse
from requests import get
from typing import Dict
from prometheus_client import CollectorRegistry, Gauge, generate_latest


NAMESPACE = "energy"
LABEL_NAMES = ["system"]


def get_data(shellyIP: str) -> Dict:
    url = f"http://{shellyIP}/rpc/PM1.GetStatus?id=0"
    result = get(url)
    if result.status_code != 200:
        raise ValueError(f"Unable to call shelly PM: {result.status_code}")
    data: Dict = {}
    data['current'] = result.json()['current']
    data['apower'] = result.json()['apower']
    data['aenergy'] = result.json()['aenergy']['total']

    return data


def collect_metrics(metric: Gauge, system: str, value: float) -> None:
    metric.labels(system=system).set(value)


def create_metrics(registry: CollectorRegistry) -> Dict:
    metrics = {}
    metrics['apower'] = Gauge(
        "apower",
        "Power",
        labelnames=LABEL_NAMES,
        namespace=NAMESPACE,
        registry=registry,
        unit="watt",
    )
    metrics['current'] = Gauge(
        "current",
        "Current",
        labelnames=LABEL_NAMES,
        namespace=NAMESPACE,
        registry=registry,
        unit="A",
    )
    metrics['aenergy'] = Gauge(
        "energy",
        "Enery",
        labelnames=LABEL_NAMES,
        namespace=NAMESPACE,
        registry=registry,
        unit="wh",
    )
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip', dest='shelly_ip', action='store',
                        help="Shelly MiniPM ip address")

    args = parser.parse_args()

    registry = CollectorRegistry()
    metrics = create_metrics(registry)

    try:
        data = get_data(args.shelly_ip)
        collect_metrics(metrics['apower'], "homelab", data['apower'])
        collect_metrics(metrics['current'], "homelab", data['current'])
        collect_metrics(metrics['aenergy'], "homelab", data['aenergy'])
        print(generate_latest(registry).decode(), end="")
    except (ValueError, ConnectionError) as e:
        print(e)


if __name__ == "__main__":
    main()
