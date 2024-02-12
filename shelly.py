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
    data: Dict = dict(
        current=result.json()['current'],
        apower=result.json()['apower'],
        energy=result.json()['aenergy']['total'],
    )
    return data


def reset_counters(shellyIP: str) -> None:
    url = f"http://{shellyIP}/rpc/PM1.ResetCounters?id=0&type=[\"aenergy\",\"ret_aenergy\"]"
    result = get(url)
    if result.status_code != 200:
        raise ValueError("Unable to reset counters")


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
    metrics['energy'] = Gauge(
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
    parser.add_argument('-e', '--energy', dest='energy', action='store_true', default=False)
    parser.add_argument('-r', '--reset', dest='reset', action='store_true', default=False)

    args = parser.parse_args()

    registry = CollectorRegistry()
    metrics = create_metrics(registry)

    try:
        data = get_data(args.shelly_ip)
        if not args.energy:
            collect_metrics(metrics['apower'], "homelab", data['apower'])
            collect_metrics(metrics['current'], "homelab", data['current'])
        else:
            collect_metrics(metrics['energy'], "homelab", data['energy'])
        print(generate_latest(registry).decode(), end="")
    except (ValueError, ConnectionError) as e:
        print(e)

    if args.reset:
        reset_counters(args.shelly_ip)


if __name__ == "__main__":
    main()
