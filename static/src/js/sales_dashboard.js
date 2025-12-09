/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class SalesDashboard extends Component {
    static template = "bi_sales_prediction.DashboardTemplate";

    setup() {
        this.orm = useService("orm");
        this.revenueChartRef = useRef("revenueChart");
        this.statusChartRef = useRef("statusChart");
        this.predictionChartRef = useRef("predictionChart");
        
        this.charts = {};
        this.Chart = null;

        this.state = useState({
            months: 6,
            loading: true,
            error: null,
            kpis: {
                total_revenue: 0,
                monthly_revenue: 0,
                yearly_revenue: 0,
                total_orders: 0,
                monthly_orders: 0,
                total_customers: 0,
                avg_order_value: 0,
            },
            topProducts: [],
            topCustomers: [],
            monthlyRevenueChart: { labels: [], data: [] },
            ordersByStatus: [],
        });

        onMounted(async () => {
            await this.loadChartJS();
            await this.fetchDashboardData();
            await this.fetchPrediction();
        });
        
        onWillUnmount(() => {
            Object.values(this.charts).forEach(chart => {
                if (chart) chart.destroy();
            });
        });
    }

    async loadChartJS() {
        if (window.Chart) {
            this.Chart = window.Chart;
            return;
        }
        
        return new Promise((resolve, reject) => {
            const script = document.createElement("script");
            script.src = "/web/static/lib/Chart/Chart.js";
            script.onload = () => {
                this.Chart = window.Chart;
                resolve();
            };
            script.onerror = () => {
                const script2 = document.createElement("script");
                script2.src = "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js";
                script2.onload = () => {
                    this.Chart = window.Chart;
                    resolve();
                };
                script2.onerror = reject;
                document.head.appendChild(script2);
            };
            document.head.appendChild(script);
        });
    }

    formatCurrency(value) {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(value || 0);
    }

    formatNumber(value) {
        return new Intl.NumberFormat("en-US").format(value || 0);
    }

    async fetchDashboardData() {
        this.state.loading = true;
        this.state.error = null;

        try {
            const data = await this.orm.call(
                "bi.sales.predictor",
                "get_dashboard_data",
                []
            );
            
            this.state.kpis = data.kpis;
            this.state.topProducts = data.top_products;
            this.state.topCustomers = data.top_customers;
            this.state.monthlyRevenueChart = data.monthly_revenue_chart;
            this.state.ordersByStatus = data.orders_by_status;
            
            this.state.loading = false;
            
            await new Promise(resolve => setTimeout(resolve, 100));
            this.renderRevenueChart();
            this.renderStatusChart();
        } catch (error) {
            console.error("Error fetching dashboard data:", error);
            this.state.error = error.message || "Failed to load dashboard data";
            this.state.loading = false;
        }
    }

    async fetchPrediction() {
        try {
            const data = await this.orm.call(
                "bi.sales.predictor",
                "get_prediction_data",
                [parseInt(this.state.months)]
            );
            
            if (data.error) {
                console.error("Prediction error:", data.error);
                return;
            }
            
            await new Promise(resolve => setTimeout(resolve, 100));
            this.renderPredictionChart(data);
        } catch (error) {
            console.error("Error fetching prediction data:", error);
        }
    }

    renderRevenueChart() {
        if (!this.revenueChartRef.el || !this.Chart) return;
        
        if (this.charts.revenue) {
            this.charts.revenue.destroy();
        }

        const ctx = this.revenueChartRef.el.getContext("2d");
        this.charts.revenue = new this.Chart(ctx, {
            type: "bar",
            data: {
                labels: this.state.monthlyRevenueChart.labels,
                datasets: [{
                    label: "Revenue",
                    data: this.state.monthlyRevenueChart.data,
                    backgroundColor: "rgba(54, 162, 235, 0.8)",
                    borderColor: "rgb(54, 162, 235)",
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                    },
                },
            },
        });
    }

    renderStatusChart() {
        if (!this.statusChartRef.el || !this.Chart) return;
        
        if (this.charts.status) {
            this.charts.status.destroy();
        }

        const colors = [
            "rgba(255, 99, 132, 0.8)",
            "rgba(54, 162, 235, 0.8)",
            "rgba(255, 206, 86, 0.8)",
            "rgba(75, 192, 192, 0.8)",
            "rgba(153, 102, 255, 0.8)",
        ];

        const ctx = this.statusChartRef.el.getContext("2d");
        this.charts.status = new this.Chart(ctx, {
            type: "doughnut",
            data: {
                labels: this.state.ordersByStatus.map(s => s.status),
                datasets: [{
                    data: this.state.ordersByStatus.map(s => s.count),
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: "#fff",
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                    },
                },
            },
        });
    }

    renderPredictionChart(data) {
        if (!this.predictionChartRef.el || !this.Chart) return;
        
        if (this.charts.prediction) {
            this.charts.prediction.destroy();
        }

        const ctx = this.predictionChartRef.el.getContext("2d");
        this.charts.prediction = new this.Chart(ctx, {
            type: "line",
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: "Historical Sales",
                        data: data.historical,
                        borderColor: "rgb(54, 162, 235)",
                        backgroundColor: "rgba(54, 162, 235, 0.1)",
                        fill: true,
                        tension: 0.3,
                    },
                    {
                        label: "Predicted Sales",
                        data: data.predicted,
                        borderColor: "rgb(255, 99, 132)",
                        backgroundColor: "rgba(255, 99, 132, 0.1)",
                        borderDash: [5, 5],
                        fill: true,
                        tension: 0.3,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "top",
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                    },
                },
            },
        });
    }
}

registry.category("actions").add("bi_sales_prediction.dashboard", SalesDashboard);
