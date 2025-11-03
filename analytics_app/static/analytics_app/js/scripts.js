// JS ֆայլ՝ հիմնական դինամիկ համարները

document.addEventListener('DOMContentLoaded', () => {
    console.log('Analytics website loaded');

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

    // Function to create X-axis selector for a chart
    const createXAxisSelector = (chartContainer, data, currentField, chart) => {
        const numericColumns = getNumericColumns(data);
        
        const selectorContainer = document.createElement('div');
        selectorContainer.className = 'x-axis-selector mb-3';
        
        const label = document.createElement('label');
        label.textContent = 'Select X-axis: ';
        label.className = 'me-2';
        
        const select = document.createElement('select');
        select.className = 'form-select form-select-sm d-inline-block w-auto';
        
        numericColumns.forEach(column => {
            if (column !== currentField) {  // Don't include the current field
                const option = document.createElement('option');
                option.value = column;
                option.textContent = column;
                select.appendChild(option);
            }
        });
        
        select.addEventListener('change', (e) => {
            const xField = e.target.value;
            updateLineChart(chart, data, xField, currentField);
        });
        
        selectorContainer.appendChild(label);
        selectorContainer.appendChild(select);
        chartContainer.insertBefore(selectorContainer, chart.canvas);
        
        // Initial chart update with first numeric column
        if (numericColumns.length > 0) {
            updateLineChart(chart, data, numericColumns[0], currentField);
        }
    };

    // Function to update line chart with new X-axis
    const updateLineChart = (chart, data, xField, yField) => {
        const sortedData = [...data].sort((a, b) => a[xField] - b[xField]);
        
        chart.data.labels = sortedData.map(row => row[xField]);
        chart.data.datasets[0].data = sortedData.map(row => row[yField]);
        chart.options.scales.x.title.text = xField;
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

    // Handle chart creation and display
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
