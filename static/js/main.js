document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const scrapeForm = document.getElementById('scrape-form');
    const urlInput = document.getElementById('url');
    const scrapeTypeSelect = document.getElementById('scrape-type');
    const selectorInput = document.getElementById('selector');
    const advancedOptionsToggle = document.getElementById('advanced-options-toggle');
    const advancedOptions = document.getElementById('advanced-options');
    const userAgentInput = document.getElementById('user-agent');
    const timeoutInput = document.getElementById('timeout');
    const scrapeButton = document.getElementById('scrape-button');
    const sampleCards = document.querySelectorAll('.sample-card');
    
    // Add event listeners to sample cards for auto-filling the form
    sampleCards.forEach(card => {
        card.addEventListener('click', function() {
            // Get data attributes
            const url = this.getAttribute('data-url');
            const type = this.getAttribute('data-type');
            const selector = this.getAttribute('data-selector');
            
            // Fill form fields
            urlInput.value = url;
            
            // Select the right option
            for (let i = 0; i < scrapeTypeSelect.options.length; i++) {
                if (scrapeTypeSelect.options[i].value === type) {
                    scrapeTypeSelect.selectedIndex = i;
                    break;
                }
            }
            
            // Set selector if provided
            selectorInput.value = selector || '';
            
            // Highlight the form
            scrapeForm.classList.add('border-primary');
            setTimeout(() => {
                scrapeForm.classList.remove('border-primary');
            }, 1500);
            
            // Scroll to form
            scrapeForm.scrollIntoView({ behavior: 'smooth' });
        });
        
        // Add hover effect
        card.classList.add('cursor-pointer');
    });
    
    const resultsPlaceholder = document.getElementById('results-placeholder');
    const resultsContainer = document.getElementById('results-container');
    const resultsLoading = document.getElementById('results-loading');
    const resultsContent = document.getElementById('results-content');
    
    const exportJsonBtn = document.getElementById('export-json');
    const exportCsvBtn = document.getElementById('export-csv');
    const copyResultsBtn = document.getElementById('copy-results');
    
    const remainingRequestsDisplay = document.getElementById('remaining-requests');
    
    // Store the last results
    let lastResults = null;
    
    // Toggle advanced options
    advancedOptionsToggle.addEventListener('change', function() {
        if (this.checked) {
            advancedOptions.classList.remove('d-none');
        } else {
            advancedOptions.classList.add('d-none');
        }
    });
    
    // Handle form submission
    scrapeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Disable the submit button
        scrapeButton.disabled = true;
        scrapeButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Scraping...';
        
        // Show loading state
        resultsPlaceholder.classList.add('d-none');
        resultsContainer.classList.remove('d-none');
        resultsContent.classList.add('d-none');
        resultsLoading.classList.remove('d-none');
        
        // Build request data
        const requestData = {
            url: urlInput.value,
            scrape_type: scrapeTypeSelect.value,
            selector: selectorInput.value || null,
            config: {}
        };
        
        // Add advanced options if provided
        if (userAgentInput.value) {
            requestData.config.user_agent = userAgentInput.value;
        }
        
        if (timeoutInput.value) {
            requestData.config.timeout = parseInt(timeoutInput.value);
        }
        
        // Make API request
        fetch('/api/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            // Update rate limit display
            checkRateLimit();
            
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(errorData.message || 'An error occurred');
                });
            }
            return response.json();
        })
        .then(data => {
            // Store results for export
            lastResults = data;
            
            // Display results
            displayResults(data);
            
            // Enable export buttons
            exportJsonBtn.disabled = false;
            exportCsvBtn.disabled = false;
        })
        .catch(error => {
            // Display a formal error message instead of the raw error
            resultsContent.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Request Error:</strong> 
                    <p>You have used all available request credits for this session. Please try again later.</p>
                    <p class="small mb-0 mt-2">If this problem persists, please check your internet connection or contact support.</p>
                </div>
            `;
        })
        .finally(() => {
            // Hide loading state
            resultsLoading.classList.add('d-none');
            resultsContent.classList.remove('d-none');
            
            // Re-enable the submit button
            scrapeButton.disabled = false;
            scrapeButton.innerHTML = '<i class="fas fa-spider me-2"></i> Scrape Data';
        });
    });
    
    // Display results based on the type
    function displayResults(data) {
        let html = '';
        
        if (!data.success) {
            html = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Error:</strong> ${data.message || 'An error occurred'}
                </div>
            `;
        } else {
            // Metadata
            html += `
                <div class="mb-3">
                    <small class="text-muted">
                        <i class="fas fa-globe me-1"></i> 
                        <a href="${data.url}" target="_blank">${data.url}</a>
                    </small>
                    <br>
                    <small class="text-muted">
                        <i class="fas fa-clock me-1"></i> 
                        ${new Date(data.data.timestamp).toLocaleString()}
                    </small>
                </div>
            `;
            
            // Content based on scrape type
            const scrapeType = data.data.scrape_type;
            const resultData = data.data.data;
            
            if (scrapeType === 'text') {
                if (typeof resultData === 'string') {
                    html += `<div class="card card-body bg-dark results-text">${formatText(resultData)}</div>`;
                } else if (Array.isArray(resultData)) {
                    html += '<div class="list-group">';
                    resultData.forEach((text, i) => {
                        html += `
                            <div class="list-group-item">
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1">Item ${i + 1}</h6>
                                </div>
                                <p class="mb-1 results-text">${formatText(text)}</p>
                            </div>
                        `;
                    });
                    html += '</div>';
                }
            } else if (scrapeType === 'tables') {
                if (resultData.length === 0) {
                    html += '<div class="alert alert-info">No tables found on the page</div>';
                } else {
                    resultData.forEach((table, i) => {
                        html += `<h5>Table ${i + 1}</h5>`;
                        html += '<div class="table-responsive">';
                        html += '<table class="table table-striped table-hover">';
                        
                        // Headers
                        html += '<thead><tr>';
                        table.headers.forEach(header => {
                            html += `<th>${header}</th>`;
                        });
                        html += '</tr></thead>';
                        
                        // Data rows
                        html += '<tbody>';
                        table.data.forEach(row => {
                            html += '<tr>';
                            table.headers.forEach(header => {
                                html += `<td>${row[header] !== undefined ? row[header] : ''}</td>`;
                            });
                            html += '</tr>';
                        });
                        html += '</tbody></table></div>';
                    });
                }
            } else if (scrapeType === 'links') {
                if (resultData.length === 0) {
                    html += '<div class="alert alert-info">No links found on the page</div>';
                } else {
                    html += '<div class="list-group">';
                    resultData.forEach(link => {
                        html += `
                            <a href="${link.url}" target="_blank" class="list-group-item list-group-item-action">
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1">${link.text || '(No text)'}</h6>
                                    <small class="text-muted">${link.title || ''}</small>
                                </div>
                                <small class="text-primary">${link.url}</small>
                            </a>
                        `;
                    });
                    html += '</div>';
                }
            } else if (scrapeType === 'images') {
                if (resultData.length === 0) {
                    html += '<div class="alert alert-info">No images found on the page</div>';
                } else {
                    html += '<div class="row">';
                    resultData.forEach(image => {
                        html += `
                            <div class="col-md-6 col-lg-4 mb-3">
                                <div class="card h-100">
                                    <div class="card-body">
                                        <p class="card-text">
                                            <small class="text-muted">${image.alt || '(No alt text)'}</small>
                                        </p>
                                        <p class="card-text">
                                            <a href="${image.src}" target="_blank" class="text-truncate d-inline-block" style="max-width: 100%;">
                                                ${image.src}
                                            </a>
                                        </p>
                                        <p class="card-text">
                                            <small class="text-muted">
                                                ${image.width ? image.width + '×' + (image.height || '?') : 'Dimensions unknown'}
                                            </small>
                                        </p>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    html += '</div>';
                }
            } else if (scrapeType === 'full') {
                // Text content section
                html += '<h5><i class="fas fa-align-left me-2"></i> Text Content</h5>';
                html += '<div class="card card-body bg-dark mb-4 results-text">';
                if (typeof resultData.text === 'string') {
                    html += formatText(resultData.text);
                } else if (Array.isArray(resultData.text)) {
                    resultData.text.forEach((text, i) => {
                        html += `<p>Item ${i + 1}: ${formatText(text)}</p>`;
                    });
                }
                html += '</div>';
                
                // Tables section
                html += '<h5><i class="fas fa-table me-2"></i> Tables</h5>';
                if (!resultData.tables || resultData.tables.length === 0) {
                    html += '<div class="alert alert-info mb-4">No tables found on the page</div>';
                } else {
                    html += '<div class="mb-4">';
                    resultData.tables.forEach((table, i) => {
                        html += `<h6>Table ${i + 1}</h6>`;
                        html += '<div class="table-responsive">';
                        html += '<table class="table table-sm table-striped">';
                        
                        // Headers
                        html += '<thead><tr>';
                        table.headers.forEach(header => {
                            html += `<th>${header}</th>`;
                        });
                        html += '</tr></thead>';
                        
                        // Data rows (show max 5 rows)
                        html += '<tbody>';
                        const maxRows = Math.min(5, table.data.length);
                        for (let i = 0; i < maxRows; i++) {
                            html += '<tr>';
                            table.headers.forEach(header => {
                                html += `<td>${table.data[i][header] !== undefined ? table.data[i][header] : ''}</td>`;
                            });
                            html += '</tr>';
                        }
                        html += '</tbody></table></div>';
                        
                        if (table.data.length > 5) {
                            html += `<p><small class="text-muted">${table.data.length - 5} more rows not shown</small></p>`;
                        }
                    });
                    html += '</div>';
                }
                
                // Links section
                html += '<h5><i class="fas fa-link me-2"></i> Links</h5>';
                if (!resultData.links || resultData.links.length === 0) {
                    html += '<div class="alert alert-info mb-4">No links found on the page</div>';
                } else {
                    html += '<div class="list-group mb-4">';
                    // Show max 10 links
                    const maxLinks = Math.min(10, resultData.links.length);
                    for (let i = 0; i < maxLinks; i++) {
                        const link = resultData.links[i];
                        html += `
                            <a href="${link.url}" target="_blank" class="list-group-item list-group-item-action">
                                <div class="d-flex w-100 justify-content-between">
                                    <span>${link.text || '(No text)'}</span>
                                    <small class="text-muted">${link.title || ''}</small>
                                </div>
                                <small class="text-primary">${link.url}</small>
                            </a>
                        `;
                    }
                    html += '</div>';
                    
                    if (resultData.links.length > 10) {
                        html += `<p><small class="text-muted">${resultData.links.length - 10} more links not shown</small></p>`;
                    }
                }
                
                // Images section
                html += '<h5><i class="fas fa-image me-2"></i> Images</h5>';
                if (!resultData.images || resultData.images.length === 0) {
                    html += '<div class="alert alert-info">No images found on the page</div>';
                } else {
                    html += '<div class="row">';
                    // Show max 6 images
                    const maxImages = Math.min(6, resultData.images.length);
                    for (let i = 0; i < maxImages; i++) {
                        const image = resultData.images[i];
                        html += `
                            <div class="col-md-6 col-lg-4 mb-3">
                                <div class="card h-100">
                                    <div class="card-body">
                                        <p class="card-text">
                                            <small class="text-muted">${image.alt || '(No alt text)'}</small>
                                        </p>
                                        <p class="card-text">
                                            <a href="${image.src}" target="_blank" class="text-truncate d-inline-block" style="max-width: 100%;">
                                                ${image.src}
                                            </a>
                                        </p>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                    html += '</div>';
                    
                    if (resultData.images.length > 6) {
                        html += `<p><small class="text-muted">${resultData.images.length - 6} more images not shown</small></p>`;
                    }
                }
            }
        }
        
        // Update the results container
        resultsContent.innerHTML = html;
    }
    
    // Format text for display
    function formatText(text) {
        if (!text) return '(No content)';
        
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;')
            .replace(/\n/g, '<br>');
    }
    
    // Handle JSON export
    exportJsonBtn.addEventListener('click', function() {
        if (!lastResults) return;
        
        const jsonStr = JSON.stringify(lastResults, null, 2);
        downloadFile(jsonStr, 'scraped_data.json', 'application/json');
    });
    
    // Handle CSV export
    exportCsvBtn.addEventListener('click', function() {
        if (!lastResults) return;
        
        const resultData = lastResults.data.data;
        const scrapeType = lastResults.data.scrape_type;
        let csv = '';
        
        if (scrapeType === 'text') {
            // Text data - just output as is
            if (typeof resultData === 'string') {
                csv = resultData;
            } else if (Array.isArray(resultData)) {
                csv = resultData.join('\n');
            }
        } else if (scrapeType === 'tables' && resultData.length > 0) {
            // Use the first table
            const table = resultData[0];
            
            // Headers
            csv += table.headers.join(',') + '\n';
            
            // Rows
            table.data.forEach(row => {
                csv += table.headers.map(header => {
                    const cell = row[header] !== undefined ? row[header] : '';
                    // Escape commas and quotes
                    return '"' + ('' + cell).replace(/"/g, '""') + '"';
                }).join(',') + '\n';
            });
        } else if (scrapeType === 'links' && resultData.length > 0) {
            // Link data
            csv = 'text,url,title\n';
            resultData.forEach(link => {
                const text = `"${(link.text || '').replace(/"/g, '""')}"`;
                const url = `"${(link.url || '').replace(/"/g, '""')}"`;
                const title = `"${(link.title || '').replace(/"/g, '""')}"`;
                csv += `${text},${url},${title}\n`;
            });
        } else if (scrapeType === 'images' && resultData.length > 0) {
            // Image data
            csv = 'src,alt,title,width,height\n';
            resultData.forEach(image => {
                const src = `"${(image.src || '').replace(/"/g, '""')}"`;
                const alt = `"${(image.alt || '').replace(/"/g, '""')}"`;
                const title = `"${(image.title || '').replace(/"/g, '""')}"`;
                const width = `"${(image.width || '').replace(/"/g, '""')}"`;
                const height = `"${(image.height || '').replace(/"/g, '""')}"`;
                csv += `${src},${alt},${title},${width},${height}\n`;
            });
        } else if (scrapeType === 'full') {
            // Full data - just use the text part
            csv = resultData.text || '';
        }
        
        downloadFile(csv, 'scraped_data.csv', 'text/csv');
    });
    
    // Handle copy results
    copyResultsBtn.addEventListener('click', function() {
        if (!lastResults) return;
        
        const jsonStr = JSON.stringify(lastResults, null, 2);
        
        navigator.clipboard.writeText(jsonStr).then(
            function() {
                alert('Results copied to clipboard!');
            },
            function(err) {
                console.error('Could not copy text: ', err);
                alert('Failed to copy to clipboard');
            }
        );
    });
    
    // Download file helper function
    function downloadFile(content, fileName, contentType) {
        const a = document.createElement('a');
        const file = new Blob([content], {type: contentType});
        a.href = URL.createObjectURL(file);
        a.download = fileName;
        a.click();
        URL.revokeObjectURL(a.href);
    }
    
    // Check rate limit status
    function checkRateLimit() {
        fetch('/api/rate-limit')
            .then(response => response.json())
            .then(data => {
                remainingRequestsDisplay.textContent = data.remaining_requests;
                
                // Update color based on remaining requests
                const rateDisplay = document.getElementById('rate-limit-display');
                if (data.remaining_requests <= 2) {
                    rateDisplay.className = 'badge bg-danger py-2 px-3';
                } else if (data.remaining_requests <= 5) {
                    rateDisplay.className = 'badge bg-warning text-dark py-2 px-3';
                } else {
                    rateDisplay.className = 'badge bg-success py-2 px-3';
                }
            })
            .catch(error => {
                // Display a more formal message when rate limit check fails
                console.log('Rate limit check unavailable: Service may be busy');
                remainingRequestsDisplay.textContent = '--';
                // Update to a neutral color when status is unknown
                const rateDisplay = document.getElementById('rate-limit-display');
                rateDisplay.className = 'badge bg-secondary py-2 px-3';
            });
    }
    
    // Check rate limit on page load
    checkRateLimit();
    
    // Set up polling to update rate limit periodically
    setInterval(checkRateLimit, 30000); // check every 30 seconds
});