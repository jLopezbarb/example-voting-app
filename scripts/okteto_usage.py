import re
from typing import Tuple, Iterable
import sys
from kubernetes.config import load_kube_config
from kubernetes.client import CustomObjectsApi


class CPUQuantity(object):

    def __init__(self, quantity: int = 0, unit: str = "n"):
        self.quantity = quantity
        self.unit = unit

    def convert_to_cpus(self):
        conversor_rate = {"n": 1000000000, "m": 1000}
        self.quantity = self.quantity / conversor_rate.get(self.unit)
        self.unit = "CPU"
        return self

    def __add__(self, other):
        if self.unit == other.unit:
            return CPUQuantity(self.quantity + other.quantity)
        else:
            raise ValueError()

    def __iadd__(self, other):
        if self.unit == other.unit:
            self.quantity += other.quantity
            return self
        else:
            raise ValueError()

    def __str__(self):
        return f"{self.quantity}{self.unit}"


class MemoryQuantity(object):

    def __init__(self, quantity: int = 0, unit: str = "Ki"):
        self.quantity = quantity
        self.unit = unit

    def convert_to_Mb(self):
        conversor_rate = {"Ki": 1024}
        self.quantity = self.quantity / conversor_rate.get(self.unit)
        self.unit = "MiB"
        return self

    def __add__(self, other):
        if self.unit == other.unit:
            return MemoryQuantity(self.quantity + other.quantity, self.unit)
        else:
            raise ValueError()

    def __iadd__(self, other):
        if self.unit == other.unit:
            self.quantity += other.quantity
            return self
        else:
            raise ValueError()

    def __str__(self):
        return f"{self.quantity}{self.unit}"


class PodMetrics(object):

    def __init__(self, name: str, memory_usage: MemoryQuantity, cpu_usage: CPUQuantity, number_of_containers: int):
        self.name = name
        self.memory_usage = memory_usage.convert_to_Mb()
        self.cpu_usage = cpu_usage.convert_to_cpus()
        self.number_of_containers = number_of_containers

    def __str__(self):
        return f"{self.name} => Number of containers in pod: {self.number_of_containers}" \
               f"\n{' ' * len(self.name)} ╚> Memory: {str(self.memory_usage)}\n" \
               f"{' ' * len(self.name)} ╚> CPU: {str(self.cpu_usage)}\n"


def __split_quantity_and_unit_from_string(string: str) -> Tuple[int, str]:
    temp = re.compile("([0-9]+)([a-zA-Z]+)")
    quantity, unit = temp.match(string).groups()
    return int(quantity), unit


def __get_cpu_usage_from_string(usage_string: str) -> CPUQuantity:
    quantity, unit = __split_quantity_and_unit_from_string(usage_string)
    return CPUQuantity(quantity, unit)


def __get_memory_usage_from_string(usage_string: str) -> MemoryQuantity:
    quantity, unit = __split_quantity_and_unit_from_string(usage_string)
    return MemoryQuantity(quantity, unit)


def __get_pods_metrics_from_response(results: dict) -> Iterable[PodMetrics]:
    for pod in results["items"]:
        pod_name = pod["metadata"]["name"]
        total_cpu = CPUQuantity()
        total_memory = MemoryQuantity()
        containers = pod["containers"]
        for container in containers:
            total_cpu += __get_cpu_usage_from_string(container["usage"]["cpu"])
            total_memory += __get_memory_usage_from_string(container["usage"]["memory"])
        yield PodMetrics(pod_name, total_memory, total_cpu, len(containers))


if __name__ == '__main__':
    load_kube_config()
    custom_api = CustomObjectsApi()
    results = custom_api.list_namespaced_custom_object('metrics.k8s.io', 'v1beta1', sys.argv[1], 'pods')
    for pod in __get_pods_metrics_from_response(results):
        print(pod)
