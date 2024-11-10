// Global variables and initialization
let currentMapping = null;
let generatedDocument = null;

// Initialize Mermaid
mermaid.initialize({ 
    startOnLoad: true,
    theme: 'default',
    flowchart: {
        useMaxWidth: true,
        htmlLabels: true,
        curve: 'basis'
    },
    securityLevel: 'loose'
});

// Utility Functions
function debugLog(message, data = null) {
    console.log(`[Debug] ${message}`, data || '');
}

function handleError(error, context) {
    console.error(`[Error in ${context}]:`, error);
    showAlert(`Error: ${error.message || 'Unknown error occurred'}`, 'error');
}

function showAlert(message, type = 'info', duration = 5000) {
    debugLog(`Showing alert: ${message} (${type})`);
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) return;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" class="text-gray-500 hover:text-gray-700">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
        </button>
    `;
    alertContainer.appendChild(alert);
    if (duration) {
        setTimeout(() => {
            if (alert.parentElement) alert.remove();
        }, duration);
    }
}

function setLoading(loading, message = 'Processing...') {
    debugLog(`Setting loading state: ${loading} with message: ${message}`);
    const spinner = document.getElementById('loadingSpinner');
    const loadingText = document.getElementById('loadingText');
    if (loadingText) loadingText.textContent = message;
    if (spinner) spinner.classList.toggle('hidden', !loading);
}

function setDocumentGenerationLoading(isLoading) {
    const generateBtn = document.getElementById('generateDocBtn');
    if (!generateBtn) return;

    if (isLoading) {
        generateBtn.disabled = true;
        generateBtn.innerHTML = `
            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Generating Document...
        `;
    } else {
        generateBtn.disabled = false;
        generateBtn.innerHTML = 'Generate Document';
    }
}

// Tab Switching
function switchTab(tabId) {
    const contents = document.querySelectorAll('.tab-content');
    const buttons = document.querySelectorAll('.tab-button');
    
    contents.forEach(content => content.classList.add('hidden'));
    buttons.forEach(button => button.classList.remove('active'));
    
    const selectedContent = document.getElementById(`${tabId}-content`);
    const selectedButton = document.querySelector(`[data-tab="${tabId}"]`);
    
    if (selectedContent) selectedContent.classList.remove('hidden');
    if (selectedButton) selectedButton.classList.add('active');
}

// File handling utilities
function getFileNameFromPath(path) {
    return path.split('\\').pop().split('/').pop();
}

function updateFileLabel(fileName) {
    const fileLabel = document.getElementById('fileLabel');
    if (fileLabel) {
        fileLabel.textContent = fileName || 'Choose a file';
    }
}

// Form Handling and XML Analysis
async function handleFormSubmit(e) {
    debugLog('Form submission started');
    e.preventDefault();

    const xmlInput = document.getElementById('xmlInput');
    if (!xmlInput) return;

    const xmlContent = xmlInput.value;
    debugLog('XML Content length:', xmlContent.length);

    if (!xmlContent.trim()) {
        showAlert('Please provide XML content', 'error');
        return;
    }

    setLoading(true, 'Analyzing mapping...');

    try {
        debugLog('Sending XML to server');
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ xml: xmlContent }),
        });
        
        debugLog('Server response received', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server error: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        debugLog('Parsed response data', data);

        if (data.error) {
            throw new Error(data.error);
        }

        currentMapping = data;
        const resultsElement = document.getElementById('results');
        if (resultsElement) resultsElement.classList.remove('hidden');
        
        renderMappingResults(data);
        showAlert('Mapping analysis completed successfully', 'success');
        switchTab('overview');
    } catch (error) {
        handleError(error, 'handleFormSubmit');
    } finally {
        setLoading(false);
    }
}

// Document Generation
async function generateDocument() {
    if (!currentMapping) {
        showAlert('Please analyze a mapping first', 'error');
        return;
    }

    setDocumentGenerationLoading(true);
    showAlert('Starting document generation...', 'info');

    try {
        const response = await fetch('/generate_document', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(currentMapping)
        });

        if (!response.ok) {
            throw new Error('Failed to generate document');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `design_document_${new Date().toISOString().slice(0,19).replace(/[:]/g, '')}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showAlert('Document generated successfully!', 'success');
    } catch (error) {
        console.error('Error:', error);
        showAlert('Error generating document', 'error');
    } finally {
        setDocumentGenerationLoading(false);
    }
}

// File Upload Handling
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        const xmlInput = document.getElementById('xmlInput');
        if (xmlInput) xmlInput.value = e.target.result;
        updateFileLabel(file.name);
    };
    reader.readAsText(file);
}

// Rendering Functions
function renderMappingResults(data) {
    renderOverview(data);
    renderTransformations(data);
    renderDataFlow(data);
    renderExpressions(data);
    renderSQLQueries(data);
    mermaid.init();
}

function generateMermaidFlow(mapping) {
    let mermaidCode = 'flowchart LR\n';
    
    // Define styles
    mermaidCode += `    classDef source fill:#dbeafe,stroke:#3b82f6\n`;
    mermaidCode += `    classDef target fill:#dcfce7,stroke:#22c55e\n`;
    mermaidCode += `    classDef transformation fill:#f3e8ff,stroke:#a855f7\n\n`;
    
    // Add nodes
    mapping.sources.forEach(source => {
        const safeId = source.replace(/[^a-zA-Z0-9]/g, '_');
        mermaidCode += `    ${safeId}[\"${source}\"]:::source\n`;
    });

    mapping.transformations.forEach(transform => {
        const safeId = transform.name.replace(/[^a-zA-Z0-9]/g, '_');
        mermaidCode += `    ${safeId}[\"${transform.name}<br/>${transform.type}\"]:::transformation\n`;
    });

    mapping.targets.forEach(target => {
        const safeId = target.replace(/[^a-zA-Z0-9]/g, '_');
        mermaidCode += `    ${safeId}[\"${target}\"]:::target\n`;
    });

    // Add connections
    mapping.connectors.forEach(conn => {
        const fromId = conn.frominstance.replace(/[^a-zA-Z0-9]/g, '_');
        const toId = conn.toinstance.replace(/[^a-zA-Z0-9]/g, '_');
        const fieldLabel = conn.fromfield.replace(/[^a-zA-Z0-9_]/g, '_');
        mermaidCode += `    ${fromId} --> |${fieldLabel}| ${toId}\n`;
    });

    return mermaidCode;
}

function renderOverview(data) {
    const overviewElement = document.getElementById('mappingOverview');
    if (!overviewElement) return;

    const { mapping } = data;
    overviewElement.innerHTML = `
        <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h3 class="font-semibold mb-2">Basic Information</h3>
                    <dl class="space-y-2">
                        <div class="flex">
                            <dt class="w-24 text-gray-500">Name:</dt>
                            <dd class="font-medium">${mapping.name || 'N/A'}</dd>
                        </div>
                        <div class="flex">
                            <dt class="w-24 text-gray-500">Description:</dt>
                            <dd class="font-medium">${mapping.description || 'No description available'}</dd>
                        </div>
                    </dl>
                </div>
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h3 class="font-semibold mb-2">Statistics</h3>
                    <dl class="space-y-2">
                        <div class="flex">
                            <dt class="w-32 text-gray-500">Sources:</dt>
                            <dd class="font-medium">${mapping.sources.length}</dd>
                        </div>
                        <div class="flex">
                            <dt class="w-32 text-gray-500">Targets:</dt>
                            <dd class="font-medium">${mapping.targets.length}</dd>
                        </div>
                        <div class="flex">
                            <dt class="w-32 text-gray-500">Transformations:</dt>
                            <dd class="font-medium">${mapping.transformations.length}</dd>
                        </div>
                    </dl>
                </div>
            </div>
            <div class="mt-8">
                <h3 class="font-semibold mb-4">Data Flow Diagram</h3>
                <div class="mermaid">
                    ${generateMermaidFlow(mapping)}
                </div>
            </div>
        </div>
    `;
}

function renderTransformations(data) {
    const transformationsElement = document.getElementById('transformationsContent');
    if (!transformationsElement) return;

    const { mapping } = data;
    transformationsElement.innerHTML = mapping.transformations.map(transform => `
        <div class="bg-white p-6 rounded-lg shadow-md mb-6">
            <div class="flex justify-between items-start">
                <div>
                    <h3 class="text-lg font-semibold">${transform.name}</h3>
                    <p class="text-gray-600">${transform.type}</p>
                </div>
                <span class="px-2 py-1 rounded-full text-sm ${transform.reusable === 'YES' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">
                    ${transform.reusable === 'YES' ? 'Reusable' : 'Non-reusable'}
                </span>
            </div>
            
            ${transform.description ? `
                <p class="mt-2 text-gray-700">${transform.description}</p>
            ` : ''}

            <div class="mt-4">
                <h4 class="font-medium mb-2">Fields</h4>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead>
                            <tr class="bg-gray-50">
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Expression</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-200">
                            ${transform.fields.map(field => `
                                <tr class="hover:bg-gray-50">
                                    <td class="px-4 py-2">${field.name}</td>
                                    <td class="px-4 py-2">${field.datatype}</td>
                                    <td class="px-4 py-2">
                                        ${field.expression ? `
                                            <pre class="text-sm bg-gray-100 p-2 rounded overflow-x-auto">${field.expression}</pre>
                                        ` : 'N/A'}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `).join('');
}

function renderDataFlow(data) {
    const dataFlowElement = document.getElementById('dataFlowContent');
    if (!dataFlowElement) return;

    const { mapping } = data;
    dataFlowElement.innerHTML = `
        <div class="space-y-6">
        ${mapping.connectors.map(conn => `
            <div class="bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200">
                <div class="flex items-center space-x-4">
                    <div class="flex-1">
                        <div class="font-medium">${conn.frominstance}</div>
                        <div class="text-sm text-gray-500">${conn.frominstancetype}</div>
                        <div class="text-sm font-medium text-blue-600">${conn.fromfield}</div>
                    </div>
                    <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/>
                    </svg>
                    <div class="flex-1">
                        <div class="font-medium">${conn.toinstance}</div>
                        <div class="text-sm text-gray-500">${conn.toinstancetype}</div>
                        <div class="text-sm font-medium text-green-600">${conn.tofield}</div>
                    </div>
                </div>
            </div>
        `).join('')}
    </div>
`;
}

function renderExpressions(data) {
const expressionsElement = document.getElementById('expressionsContent');
if (!expressionsElement) return;

const { mapping } = data;
const expressionsHtml = mapping.transformations
    .filter(transform => transform.fields.some(field => field.expression))
    .map(transform => `
        <div class="bg-white p-6 rounded-lg shadow-md mb-6">
            <h3 class="text-lg font-semibold mb-4">${transform.name}</h3>
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead>
                        <tr class="bg-gray-50">
                            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Field</th>
                            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Expression</th>
                            <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">
                        ${transform.fields
                            .filter(field => field.expression)
                            .map(field => `
                                <tr class="hover:bg-gray-50">
                                    <td class="px-4 py-2 font-medium">${field.name}</td>
                                    <td class="px-4 py-2">
                                        <pre class="text-sm bg-gray-100 p-2 rounded overflow-x-auto">${field.expression}</pre>
                                    </td>
                                    <td class="px-4 py-2">${field.expressiontype || 'N/A'}</td>
                                </tr>
                            `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `).join('');

expressionsElement.innerHTML = expressionsHtml || '<p class="text-gray-500 p-4">No expressions found in the mapping.</p>';
}

function renderSQLQueries(data) {
    const sqlElement = document.getElementById('sqlContent');
    if (!sqlElement) return;

    const { mapping } = data;
    let sqlContentHtml = '';

    function formatSQLQuery(sql) {
        return sql.split('\n')
            .map(line => line.trim())
            .filter(line => line)
            .join('\n');
    }

    mapping.transformations.forEach(transform => {
        const sqlQueries = transform.attributes.filter(attr => 
            ['Sql Query', 'Pre SQL', 'Post SQL', 'Lookup Sql Override'].includes(attr.name) && attr.value
        );

        if (sqlQueries.length > 0) {
            sqlContentHtml += `
                <div class="bg-white p-6 rounded-lg shadow-md mb-6">
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <h3 class="text-lg font-semibold">${transform.name}</h3>
                            <p class="text-gray-600">${transform.type}</p>
                        </div>
                    </div>
                    
                    <div class="space-y-4">
                        ${sqlQueries.map(sql => `
                            <div class="sql-query-section">
                                <h4 class="font-medium text-gray-700 mb-2">${sql.name}</h4>
                                <div class="bg-gray-50 p-4 rounded-lg">
                                    <pre class="text-sm overflow-x-auto whitespace-pre-wrap">${formatSQLQuery(sql.value)}</pre>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
    });

    sqlElement.innerHTML = sqlContentHtml || `
        <div class="text-center text-gray-500 py-8">
            No SQL queries found in this mapping.
        </div>
    `;
}

// Initialize Event Listeners
document.addEventListener('DOMContentLoaded', () => {
debugLog('Initializing event listeners');

// Form submission
const uploadForm = document.getElementById('uploadForm');
if (uploadForm) {
    uploadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        handleFormSubmit(e);
    });
}

// Analyze button
const analyzeButton = document.getElementById('analyzeButton');
if (analyzeButton) {
    analyzeButton.addEventListener('click', handleFormSubmit);
    debugLog('Analyze button event listener attached');
}

// File input
const fileInput = document.getElementById('fileInput');
const uploadFileBtn = document.getElementById('uploadFileBtn');
if (fileInput && uploadFileBtn) {
    uploadFileBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileUpload);
}

// Tab switching
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => switchTab(button.dataset.tab));
});

// Generate document
const generateDocBtn = document.getElementById('generateDocBtn');
if (generateDocBtn) {
    generateDocBtn.addEventListener('click', generateDocument);
}

// Clear button
const clearButton = document.getElementById('clearButton');
if (clearButton) {
    clearButton.addEventListener('click', () => {
        const xmlInput = document.getElementById('xmlInput');
        if (xmlInput) xmlInput.value = '';
        
        const results = document.getElementById('results');
        if (results) results.classList.add('hidden');
        
        currentMapping = null;
        generatedDocument = null;
        updateFileLabel('No file chosen');
    });
}

debugLog('Initialization complete');
});
