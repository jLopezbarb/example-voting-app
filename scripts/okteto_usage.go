package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"

	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	metricstype "k8s.io/metrics/pkg/apis/metrics/v1beta1"
	"k8s.io/metrics/pkg/client/clientset/versioned"
	metricsclientset "k8s.io/metrics/pkg/client/clientset/versioned"
)

type Pod struct {
	name               string
	cpuUsage           string
	memoryUsage        string
	numberOfContainers int
}

func (p Pod) String() string {
	nameLength := strings.Repeat(" ", len(p.name))
	return fmt.Sprintf("%s => Number of containers in pod: %d\n%s ╚> Memory: %s\n%s ╚> CPU: %s",
		p.name, p.numberOfContainers, nameLength, p.memoryUsage, nameLength, p.cpuUsage)
}

func main() {
	// Definition of variables to use later
	var config *rest.Config
	var namespace string
	var pods metricstype.PodMetricsList

	config = getConfig()
	namespace = "jlopezbarb"

	pods = getRawMetrics(config, namespace)

	for _, pod := range pods.Items {
		name := pod.ObjectMeta.Name
		cpuUsage, memoryUsage := getUsages(pod.Containers)

		var p Pod
		p.name = name
		p.cpuUsage = cpuUsage.String()
		p.memoryUsage = memoryUsage.String()
		p.numberOfContainers = len(pod.Containers)
		fmt.Println(p.String())
	}
}

func getUsages(containers []metricstype.ContainerMetrics) (resource.Quantity, resource.Quantity) {
	var totalCpuUsage resource.Quantity
	var totalMemoryUsage resource.Quantity
	for idx, container := range containers {
		var cpu resource.Quantity
		cpu = *container.Usage.Cpu()

		var memory resource.Quantity
		memory = *container.Usage.Memory()
		if idx == 0 {
			totalCpuUsage = cpu
			totalMemoryUsage = memory
		} else {
			totalCpuUsage.Add(cpu)
			totalMemoryUsage.Add(memory)
		}
	}
	return totalCpuUsage, totalMemoryUsage
}

func getRawMetrics(config *rest.Config, namespace string) metricstype.PodMetricsList {
	clientset, err := metricsclientset.NewForConfig(config)
	if err != nil {
		log.Fatal(err)
	}
	podMetricsList, err := clientset.MetricsV1beta1().PodMetricses(namespace).List(context.TODO(), metav1.ListOptions{})
	if err != nil {
		log.Fatal(err)
	}

	pods := *podMetricsList
	return pods
}

func getConfig() *rest.Config {
	kubeconfig := filepath.Join(
		os.Getenv("HOME"), ".kube", "config",
	)
	config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
	if err != nil {
		log.Fatal(err)
	}
	return config
}

func getNumberOfRunningPods(namespace string, config *rest.Config) int {
	clientset, _ := kubernetes.NewForConfig(config)
	pods, _ := clientset.CoreV1().Pods(namespace).List(context.TODO(), metav1.ListOptions{})
	return len(pods.Items)
}

func getMetricsClient(config *rest.Config) *versioned.Clientset {
	metricsClient, err := metricsclientset.NewForConfig(config)
	if err != nil {
		log.Fatal(err)
	}
	return metricsClient
}
