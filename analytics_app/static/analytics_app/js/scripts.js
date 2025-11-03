// JS ֆայլ՝ հիմնական դինամիկ համարները

document.addEventListener('DOMContentLoaded', () => {
    console.log('Analytics website loaded');

    // Initialize group analysis if data is available
    const initGroupAnalysis = () => {
        const groupBySelect = document.getElementById('groupByField');
        const analyzeFieldsSelect = document.getElementById('analyzeFields');
        const aggregationSelect = document.getElementById('aggregationType');
        const chartsContainer = document.getElementById('groupAnalysisCharts');
        
        if (!groupBySelect || !analyzeFieldsSelect || !chartsContainer || !rawData || !rawData.length) {
            return;
        }

        // Get numeric fields
        const numericFields = getNumericColumns(rawData);
        
        // Populate group by select
        numericFields.forEach(field => {
            const option = document.createElement('option');
            option.value = field;
            option.textContent = field;
            groupBySelect.appendChild(option);
        });

        // Populate analyze fields select
        numericFields.forEach(field => {
            const option = document.createElement('option');
            option.value = field;
            option.textContent = field;
            analyzeFieldsSelect.appendChild(option);
        });

        // Function to create/update charts based on selections
        const updateGroupAnalysis = () => {
            const xField = groupBySelect.value;
            const selectedFields = Array.from(analyzeFieldsSelect.selectedOptions).map(opt => opt.value);
            const aggregationType = aggregationSelect.value;

            chartsContainer.innerHTML = ''; // Clear existing charts

            selectedFields.forEach(field => {
                const chartContainer = document.createElement('div');
                chartContainer.className = 'mb-4';
                chartContainer.innerHTML = `<h6 class="text-primary mb-2">${field} by ${xField}</h6>`;

                const canvas = document.createElement('canvas');
                chartContainer.appendChild(canvas);
                chartsContainer.appendChild(chartContainer);

                const ctx = canvas.getContext('2d');
                const aggregatedData = groupAndAggregate(rawData, xField, field, aggregationType);

                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: aggregatedData.map(item => item.x),
                        datasets: [{
                            label: field,
                            data: aggregatedData.map(item => item.y),
                            borderColor: '#0C4B8E',
                            backgroundColor: 'rgba(12,75,142,0.1)',
                            pointRadius: 2,
                            fill: true,
                            tension: 0.3
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            title: {
                                display: true,
                                text: `${field} by ${xField} (${aggregationType})`,
                                color: '#0C4B8E'
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const dataPoint = aggregatedData[context.dataIndex];
                                        return `${field}: ${context.formattedValue} (${dataPoint.count} items)`;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                title: {
                                    display: true,
                                    text: xField,
                                    color: '#0C4B8E'
                                }
                            },
                            y: {
                                title: {
                                    display: true,
                                    text: field,
                                    color: '#0C4B8E'
                                }
                            }
                        }
                    }
                });
            });
        };

        // Add event listeners
        groupBySelect.addEventListener('change', updateGroupAnalysis);
        analyzeFieldsSelect.addEventListener('change', updateGroupAnalysis);
        aggregationSelect.addEventListener('change', updateGroupAnalysis);

        // Initial update if fields are pre-selected
        if (groupBySelect.value && analyzeFieldsSelect.selectedOptions.length > 0) {
            updateGroupAnalysis();
        }
    };

    // Function to check if a value is numeric
    const isNumeric = (value) => {
        return !isNaN(value) && value !== null && value !== '';
    };

    // Function to get numeric columns from data
    const getNumericColumns = (data) => {
        const numericColumns = new Set();
        if (!data || !data.length) return [];
        
        Object.keys(data[0]).forEach(column => {
            // Check first few rows to determine if the column is numeric
            const isNumericColumn = data.slice(0, 10).every(row => isNumeric(row[column]));
            if (isNumericColumn) {
                numericColumns.add(column);
            }
        });
        return Array.from(numericColumns);
    };

    // Function to calculate grouped statistics
    const calculateGroupedStats = (data, xField, yField) => {
        const groups = {};
        
        // Group the data
        data.forEach(row => {
            const xValue = row[xField];
            const yValue = parseFloat(row[yField]);
            
            if (!groups[xValue]) {
                groups[xValue] = [];
            }
            
            if (!isNaN(yValue)) {
                groups[xValue].push(yValue);
            }
        });

        // Calculate statistics for each group
        const groupedStats = Object.entries(groups).map(([x, values]) => {
            const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
            const sorted = [...values].sort((a, b) => a - b);
            const median = sorted.length % 2 === 0 
                ? (sorted[sorted.length/2 - 1] + sorted[sorted.length/2]) / 2 
                : sorted[Math.floor(sorted.length/2)];
            const std = Math.sqrt(values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length);
            
            return {
                x: parseFloat(x),
                y: mean, // We'll show the mean value in the line chart
                count: values.length,
                stats: {
                    mean: mean,
                    median: median,
                    min: Math.min(...values),
                    max: Math.max(...values),
                    std: std
                }
            };
        });

        // Sort by x value
        return groupedStats.sort((a, b) => a.x - b.x);
    };

    // Function to create X-axis selector for a chart
    const createXAxisSelector = (chartContainer, data, currentField, chart) => {
        const numericColumns = getNumericColumns(data);
        
        // Get the existing selector that was created in the template
        const select = chartContainer.querySelector('select[data-chart]');
        if (!select) return;
        
        // Populate the select with numeric fields
        numericColumns.forEach(column => {
            if (column !== currentField) {  // Don't include the current field
                const option = document.createElement('option');
                option.value = column;
                option.textContent = column;
                select.appendChild(option);
            }
        });
        
        // Add event listener
        select.addEventListener('change', (e) => {
            const xField = e.target.value;
            updateLineChart(chart, data, xField, currentField);
        });
        
        // Initial chart update with first numeric column
        if (numericColumns.length > 0) {
            updateLineChart(chart, data, numericColumns[0], currentField);
        }
    };

    // Function to update line chart with new X-axis
    const updateLineChart = (chart, data, xField, yField) => {
        const groupedStats = calculateGroupedStats(data, xField, yField);
        
        chart.data.labels = groupedStats.map(item => item.x);
        chart.data.datasets[0].data = groupedStats.map(item => item.y);
        
        // Update tooltips to show detailed stats for each group
        chart.options.plugins.tooltip = {
            callbacks: {
                label: function(context) {
                    const stats = groupedStats[context.dataIndex].stats;
                    const count = groupedStats[context.dataIndex].count;
                    return [
                        `${yField} statistics for ${xField}=${context.label} (${count} items):`,
                        `Mean: ${stats.mean.toFixed(2)}`,
                        `Median: ${stats.median.toFixed(2)}`,
                        `Min: ${stats.min.toFixed(2)}`,
                        `Max: ${stats.max.toFixed(2)}`,
                        `Std: ${stats.std.toFixed(2)}`
                    ];
                }
            }
        };
        
        // Update chart title and axis labels
        chart.options.plugins.title.text = `${yField} Analysis by ${xField}`;
        chart.options.scales.x.title.text = xField;
        chart.options.scales.y.title.text = yField;
        
        chart.update();
    };

    // Navbar hover effect enhancement (optional)
    const navLinks = document.querySelectorAll('header nav ul.main-nav li a');

    navLinks.forEach(link => {
        link.addEventListener('mouseenter', () => {
            link.style.transform = 'scale(1.05)';
            link.style.transition = 'transform 0.2s';
        });
        link.addEventListener('mouseleave', () => {
            link.style.transform = 'scale(1)';
        });
    });

    // Smooth scroll for anchor links (if any)
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(link.getAttribute('href'));
            if(target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // File input alert on upload page (optional)
    const uploadInput = document.querySelector('input[type="file"]');
    if(uploadInput) {
        uploadInput.addEventListener('change', () => {
            const fileName = uploadInput.files[0]?.name;
            if(fileName) {
                alert(`Selected file: ${fileName}`);
            }
        });
    }

    // Initialize group analysis
    initGroupAnalysis();
});    // Handle chart creation and display
    const createChart = (container, data, field) => {
        const chartContainer = document.createElement('div');
        chartContainer.className = 'chart-container mb-4';
        
        const canvas = document.createElement('canvas');
        container.appendChild(chartContainer);
        chartContainer.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: field,
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: ''
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: field
                        }
                    }
                }
            }
        });

        // Add X-axis selector and initialize chart
        createXAxisSelector(chartContainer, data, field, chart);
        
        return chart;
    };

    // Initialize charts when analysis results are available
    const initializeCharts = () => {
        const analysisResults = window.analysisResults; // This should be set by your Django template
        if (!analysisResults) return;

        const chartsContainer = document.querySelector('#analysis-charts-container');
        if (!chartsContainer) return;

        Object.keys(analysisResults).forEach(field => {
            if (typeof analysisResults[field] === 'object' && analysisResults[field].data) {
                createChart(chartsContainer, analysisResults[field].data, field);
            }
        });
    };

    // Call initialization when DOM is loaded
    initializeCharts();
});
