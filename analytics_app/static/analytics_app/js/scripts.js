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

    // Function to group and aggregate data
    const groupAndAggregate = (data, xField, yField, aggregationType = 'avg') => {
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

        // Calculate aggregates for each group
        const aggregated = Object.entries(groups).map(([x, values]) => {
            let aggregatedValue;
            switch (aggregationType) {
                case 'avg':
                    aggregatedValue = values.reduce((sum, val) => sum + val, 0) / values.length;
                    break;
                case 'sum':
                    aggregatedValue = values.reduce((sum, val) => sum + val, 0);
                    break;
                case 'min':
                    aggregatedValue = Math.min(...values);
                    break;
                case 'max':
                    aggregatedValue = Math.max(...values);
                    break;
                case 'count':
                    aggregatedValue = values.length;
                    break;
                default:
                    aggregatedValue = values.reduce((sum, val) => sum + val, 0) / values.length;
            }
            return { x: parseFloat(x), y: aggregatedValue, count: values.length };
        });

        // Sort by x value
        return aggregated.sort((a, b) => a.x - b.x);
    };

    // Function to create X-axis selector and aggregation controls for a chart
    const createXAxisSelector = (chartContainer, data, currentField, chart) => {
        const numericColumns = getNumericColumns(data);
        
        const controlsContainer = document.createElement('div');
        controlsContainer.className = 'chart-controls mb-3';
        
        // Create group by selector
        const groupByContainer = document.createElement('div');
        groupByContainer.className = 'd-inline-block me-3';
        
        const groupByLabel = document.createElement('label');
        groupByLabel.textContent = 'Group by:';
        groupByLabel.className = 'me-2';
        
        const groupBySelect = document.createElement('select');
        groupBySelect.className = 'form-select form-select-sm d-inline-block w-auto me-3';
        
        numericColumns.forEach(column => {
            if (column !== currentField) {
                const option = document.createElement('option');
                option.value = column;
                option.textContent = column;
                groupBySelect.appendChild(option);
            }
        });

        // Create aggregation type selector
        const aggregationContainer = document.createElement('div');
        aggregationContainer.className = 'd-inline-block';
        
        const aggregationLabel = document.createElement('label');
        aggregationLabel.textContent = 'Aggregate by:';
        aggregationLabel.className = 'me-2';
        
        const aggregationSelect = document.createElement('select');
        aggregationSelect.className = 'form-select form-select-sm d-inline-block w-auto';
        
        const aggregationTypes = [
            { value: 'avg', label: 'Average' },
            { value: 'sum', label: 'Sum' },
            { value: 'min', label: 'Minimum' },
            { value: 'max', label: 'Maximum' },
            { value: 'count', label: 'Count' }
        ];

        aggregationTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type.value;
            option.textContent = type.label;
            aggregationSelect.appendChild(option);
        });

        // Add event listeners
        const updateChart = () => {
            const xField = groupBySelect.value;
            const aggregationType = aggregationSelect.value;
            updateLineChart(chart, data, xField, currentField, aggregationType);
        };

        groupBySelect.addEventListener('change', updateChart);
        aggregationSelect.addEventListener('change', updateChart);
        
        // Assemble the controls
        groupByContainer.appendChild(groupByLabel);
        groupByContainer.appendChild(groupBySelect);
        aggregationContainer.appendChild(aggregationLabel);
        aggregationContainer.appendChild(aggregationSelect);
        
        controlsContainer.appendChild(groupByContainer);
        controlsContainer.appendChild(aggregationContainer);
        
        chartContainer.insertBefore(controlsContainer, chart.canvas);
        
        // Initial chart update
        if (numericColumns.length > 0) {
            updateLineChart(chart, data, numericColumns[0], currentField, 'avg');
        }
    };

    // Function to update line chart with new X-axis and aggregation
    const updateLineChart = (chart, data, xField, yField, aggregationType) => {
        const aggregatedData = groupAndAggregate(data, xField, yField, aggregationType);
        
        chart.data.labels = aggregatedData.map(item => item.x);
        chart.data.datasets[0].data = aggregatedData.map(item => item.y);
        
        // Update tooltips to show count of items in each group
        chart.options.plugins.tooltip = {
            callbacks: {
                label: function(context) {
                    const dataPoint = aggregatedData[context.dataIndex];
                    const value = context.formattedValue;
                    return `${yField}: ${value} (${dataPoint.count} items)`;
                }
            }
        };
        
        // Update chart title and axis labels
        const aggTypeLabel = {
            'avg': 'Average',
            'sum': 'Sum',
            'min': 'Minimum',
            'max': 'Maximum',
            'count': 'Count'
        }[aggregationType] || 'Average';

        chart.options.plugins.title.text = `${yField} by ${xField} (${aggTypeLabel})`;
        chart.options.scales.x.title.text = xField;
        chart.options.scales.y.title.text = `${aggTypeLabel} of ${yField}`;
        
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
