const App = () => {
    const apiUrl = 'http://localhost:5000';
    const { useState, useEffect } = React;
    const [chunksCollapsed, setChunksCollapsed] = useState(false);
    const [currentTab, setCurrentTab] = useState('index');
    const [file, setFile] = useState(null);
    const [fileName, setFileName] = useState('');
    const [responseMessage, setResponseMessage] = useState('');
    const [selectedOptions, setSelectedOptions] = useState([]);
    const [responseData, setResponseData] = useState(null);
    const [options, setOptions] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [username, setUsername] = useState('');
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [chunks, setChunks] = useState([]);
    const [buttonVisible, setButtonVisible] = useState(false);
    // States to control flow views
    const [showForm, setShowForm] = useState(false);
    const [showPreview, setShowPreview] = useState(false);

    // Static form fields removed in favor of dynamic form only
    // Dynamic form states
    const [chosenOption, setChosenOption] = useState("");
    const [formValues, setFormValues] = useState({});
    const [submittedValues, setSubmittedValues] = useState(null);

    const formConfigs = {
        regex: {
            fields: [
                { name: "pattern", label: "Pattern", type: "text", required: true },
                { name: "max_tokens", label: "Max tokens", type: "number", required: true },
                { name: "overlap_tokens", label: "Overlap Tokens", type: "number", required: true }
            ]
        },
        semantic: {
            fields: [
                { name: "max_tokens", label: "Max tokens", type: "number", required: true },
                { name: "sim_threshold", label: "Similarity Threshold", type: "number", required: true },
                { name: "overlap", label: "Number of sentences to Overlap", type: "number", required: true }
            ]
        },
        sentence: {
            fields: [
                { name: "orderId", label: "Order ID", type: "text", required: true },
                { name: "quantity", label: "Quantity", type: "number", required: true },
                { name: "deliveryDate", label: "Delivery Date", type: "date", required: false }
            ]
        }
    };

    const handleTabChange = (tab) => {
        if (isLoggedIn) {
            setCurrentTab(tab);
            if (tab === 'index') {
                setResponseData(null);
            }
        }
    };

    const handleLogin = () => {
        if (username.trim()) {
            setIsLoggedIn(true);
        } else {
            alert('Please enter a username');
        }
    };

    const handleLogout = () => {
        setIsLoggedIn(false);
        setUsername('');
        setCurrentTab('index');
        setResponseData(null);
        setFile(null);
        setFileName('');
        setResponseMessage('');
        setSelectedOptions([]);
        setShowForm(false);
        setShowPreview(false);
        setChunks([]);
        setChosenOption("");
        setFormValues({});
        setSubmittedValues(null);
    };

    const handleUsernameChange = (e) => {
        setUsername(e.target.value);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleLogin();
        }
    };

    // File upload
    const handleFileUpload = (event) => {
        const uploadedFile = event.target.files[0];
        if (uploadedFile) {
            setFile(uploadedFile);
            setFileName(uploadedFile.name);
            setResponseMessage('');
            setButtonVisible(true);
            // setButtonVisible(true);
            // Reset views on re-upload
            setShowForm(false);
            setShowPreview(false);
            setChunks([]);
            setChosenOption("");
            setFormValues({});
            setSubmittedValues(null);
        }
    };

    const removeFile = () => {
        setFile(null);
        setFileName('');
        setButtonVisible(false);
        setResponseMessage('');
        setShowForm(false);
        setShowPreview(false);
        setChunks([]);
        setChosenOption("");
        setFormValues({});
        setSubmittedValues(null);
    };

    // When file is selected and "Upload file" is clicked, call uploadFile API then show form view
    const handleShowForm = async () => {
        if (!file) {
            alert('Please select a file first.');
            return;
        }
        const formData = new FormData();
        formData.append('file', file);
        try {
            const response = await fetch(`${apiUrl}/uploadFile`, {
                method: 'POST',
                body: formData,
            });
            const result = await response.json();
            if (response.ok) {
                setResponseMessage(result.message);
                setButtonVisible(false);
                setShowForm(true);
                setShowPreview(false);
                setChunks([]);
                
            } else {
                setResponseMessage(result.message || 'Error uploading file.');
            }
        } catch (error) {
            setResponseMessage('Error uploading file.');
        }
    };

    // Preview chunks: send filename and dynamic form data to getChunks API
    const handlePreviewChunks = async () => {
        if (!fileName) {
            alert('No file uploaded.');
            return;
        }
        // Use dynamic form data in payload since we removed static form
        const payload = {
            file_path: fileName,
            chunkingMechanism: chosenOption,
            parameters: formValues
        };
        console.log(payload);
        try {
            // const response = await fetch(`${apiUrl}/getChunks1`, {
                const response = await fetch(`${apiUrl}/getChunksWithMechanism`, {
                method: 'POST',
                body: JSON.stringify(payload),
                headers: { 'Content-Type': 'application/json' }
            });
            const result = await response.json();
            if (response.ok) {
                setResponseMessage(result.message);
                if (result.chunks) {
                    setChunks(result.chunks);
                    setShowPreview(true);
                } else {
                    setChunks([]);
                    setShowPreview(false);
                }
            } else {
                setResponseMessage(result.message || 'Error fetching chunks.');
            }
        } catch (error) {
            setResponseMessage('Error fetching chunks.');
        }
    };

    // Back button from preview view: go back to form view
    const handleBackFromPreview = () => {
        setShowPreview(false);
    };

    // Call uploadChunks endpoint with chunks and combined dynamic form data
    const handleSubmitChunks = async () => {
        if (chunks.length === 0) {
            alert('No chunks available to submit.');
            return;
        }
        try {
            const payload = {
                chunks,
                username,
                dynamicFormData: chosenOption ? formValues : null
            };

            const response = await fetch(`${apiUrl}/uploadChunks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (response.ok) {
                alert('Chunks successfully indexed! ' + (result.message || ''));
            } else {
                alert(result.message || 'Error indexing chunks.');
            }
        } catch (error) {
            alert('Error indexing chunks.');
        }
    };

    const handleOptionChange = (e) => {
        const value = e.target.value;
        setSelectedOptions((prev) =>
            prev.includes(value)
                ? prev.filter((item) => item !== value)
                : [...prev, value]
        );
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (selectedOptions.length === 0) {
            alert('Please select at least one option.');
            return;
        }
        try {
            const response = await fetch(`${apiUrl}/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ranking_profiles: selectedOptions, query: inputValue, username }),
            });
            const data = await response.json();
            setResponseData(data);
        } catch (error) {
            setError('An error occurred while submitting the form.');
        }
    };

    // Dynamic form handlers
    const handleDynamicOptionChange = (e) => {
        setChosenOption(e.target.value);
        setFormValues({});
        setSubmittedValues(null);
    };

    const handleDynamicInputChange = (e) => {
        const { name, value } = e.target;
        setFormValues((prev) => ({ ...prev, [name]: value }));
    };

    // Instead of a separate dynamic submit, we will use the fixed button "Preview Chunks"
    // so we remove any internal dynamic submit button.
    const renderField = (field) => {
        switch (field.type) {
            case "textarea":
                return (
                    <textarea
                        name={field.name}
                        value={formValues[field.name] || ""}
                        onChange={handleDynamicInputChange}
                        required={field.required}
                        className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                        placeholder={field.label}
                    />
                );
            default:
                return (
                    <input
                        type={field.type}
                        name={field.name}
                        value={formValues[field.name] || ""}
                        onChange={handleDynamicInputChange}
                        required={field.required}
                        className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                        placeholder={field.label}
                    />
                );
        }
    };

    useEffect(() => {
        if (currentTab === 'search' && isLoggedIn) {
            const fetchOptions = async () => {
                try {
                    const response = await fetch(`${apiUrl}/ranking_profiles`, {
                        method: 'GET',
                        headers: { 'Content-Type': 'application/json' },
                    });
                    if (!response.ok) {
                        throw new Error('Failed to fetch options');
                    }
                    const data = await response.json();
                    setOptions(data);
                    setLoading(false);
                } catch (err) {
                    setError(err.message);
                    setLoading(false);
                }
            };
            fetchOptions();
        }
    }, [currentTab, isLoggedIn]);

    if (!isLoggedIn) {
        return (
            <div className="login-container max-w-md mx-auto mt-10 p-6 bg-white rounded-lg shadow-md">
                <h2 className="text-2xl font-bold mb-4">Please Enter Username</h2>
                <input
                    type="text"
                    value={username}
                    onChange={handleUsernameChange}
                    onKeyPress={handleKeyPress}
                    placeholder="Enter your username"
                    className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                />
                <button
                    onClick={handleLogin}
                    className="mt-4 w-full bg-blue-500 text-white p-2 rounded-md hover:bg-blue-600"
                >
                    Login
                </button>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto mt-10 p-6 bg-white rounded-lg shadow-md">
            <div className="menu-bar flex justify-between mb-6">
                <div
                    className={`menu-item px-4 py-2 cursor-pointer ${currentTab === 'index' ? 'bg-blue-500 text-white rounded-md' : ''}`}
                    onClick={() => handleTabChange('index')}
                >
                    Index
                </div>
                <div
                    className={`menu-item px-4 py-2 cursor-pointer ${currentTab === 'search' ? 'bg-blue-500 text-white rounded-md' : ''}`}
                    onClick={() => handleTabChange('search')}
                >
                    Search
                </div>
                <div className="menu-item logout">
                    <button
                        onClick={handleLogout}
                        className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
                    >
                        Logout
                    </button>
                </div>
            </div>

            {currentTab === 'index' && (
                <div className="form-container">
                    <h3 className="text-xl font-semibold mb-4">Upload File</h3>
                    <div>
                        <input
                            id="file-input"
                            type="file"
                            accept="*/*"
                            style={{ display: 'none' }}
                            onChange={handleFileUpload}
                        />
                        
                            <button
                            onClick={() => document.getElementById('file-input').click()}
                            className="bg-blue-500 text-white p-2 rounded-md hover:bg-blue-600"
                        >
                            Select File
                        </button>
                    </div>
                    {fileName && (
                        <div className="file-info flex items-center mt-4">
                            <span className="mr-4">{fileName}</span>
                            <button
                                onClick={removeFile}
                                className="mr-2 bg-red-500 text-white p-2 rounded-md hover:bg-red-600"
                            >
                                Remove
                            </button>

                        {buttonVisible && (
                            <button
                            onClick={handleShowForm}
                            className="bg-green-500 text-white p-2 rounded-md hover:bg-green-600"
                            >    
                            Upload File
                            </button>
                        )}

                            {/* <button
                                onClick={handleShowForm}
                                className="bg-green-500 text-white p-2 rounded-md hover:bg-green-600"
                            >
                                Upload File
                            </button> */}
                        </div>
                    )}

                    {showForm && (
                        <div className="form-section mt-6">
                            <h3 className="text-xl font-semibold mb-4">Chunking Mechanism</h3>
                            <select
                                value={chosenOption}
                                onChange={handleDynamicOptionChange}
                                className="w-full border border-gray-300 rounded-md p-2 mb-4"
                            >
                                <option value="">Select an option</option>
                                {Object.keys(formConfigs).map((key) => (
                                    <option key={key} value={key}>
                                        {key.charAt(0).toUpperCase() + key.slice(1)}
                                    </option>
                                ))}
                            </select>

                            {chosenOption && (
                                <div>
                                    <h4 className="text-lg font-semibold mb-4">
                                        {chosenOption.charAt(0).toUpperCase() + chosenOption.slice(1)} Form
                                    </h4>
                                    {formConfigs[chosenOption].fields.map((field) => (
                                        <div key={field.name} className="mb-4">
                                            <label className="block text-sm font-medium text-gray-700">
                                                {field.label}
                                            </label>
                                            {renderField(field)}
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Fixed button group for dynamic form only */}
                            <div className="flex space-x-2 mt-4">
                                <button
                                    type="button"
                                    onClick={handlePreviewChunks}
                                    className="bg-blue-500 text-white p-2 rounded-md hover:bg-blue-600"
                                >
                                    Preview Chunks
                                </button>
                                <button
                                    type="button"
                                    onClick={handleSubmitChunks}
                                    className="bg-green-500 text-white p-2 rounded-md hover:bg-green-600"
                                >
                                    Index Chunks
                                </button>
                                <button
                                    type="button"
                                    onClick={() => {
                                        setShowForm(false)
                                        setShowPreview(false);
                                        setChunks([]);
                                        setButtonVisible(true);
                                    }}
                                    className="bg-gray-500 text-white p-2 rounded-md hover:bg-gray-600"
                                >
                                    Back
                                </button>
                            </div>
                        </div>
                    )}

                    {responseMessage && (
                        <span className="block mt-4 text-gray-700">{responseMessage}</span>
                    )}

                    {showPreview && chunks.length > 0 && (
                        <div className="chunks-preview mt-6" style={{ position: 'relative' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <h4 className="text-lg font-semibold">Chunks Preview:</h4>
                                <button
                                    onClick={() => setChunksCollapsed(!chunksCollapsed)}
                                    style={{
                                        border: 'none',
                                        background: 'transparent',
                                        fontSize: '20px',
                                        cursor: 'pointer',
                                        color: chunksCollapsed ? 'red' : 'black'
                                    }}
                                >
                                    {chunksCollapsed ? '▼' : 'X'}
                                </button>
                            </div>
                            {!chunksCollapsed && (
                                <div>
                                    {chunks.map((chunk, index) => (
                                        <div key={index} className="chunk-item mt-4 p-4 bg-gray-100 rounded-md">
                                            <strong>ChunkId: {chunk.index}</strong>
                                            <br />
                                            <strong>Chunk:</strong>
                                            <br />
                                            <span>{chunk.content}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {currentTab === 'search' && (
                <form onSubmit={handleSubmit} className="form-container mt-6">
                    {loading && <div className="loading-message text-gray-700">Loading options...</div>}
                    {error && <div className="error-message text-red-500">Error: {error}</div>}
                    {!loading && !error && (
                        <div className="checkbox-group">
                            {options.map((option) => (
                                <label key={option.value} className="checkbox-label block mb-2">
                                    <input
                                        type="checkbox"
                                        value={option.value}
                                        onChange={handleOptionChange}
                                        checked={selectedOptions.includes(option.value)}
                                        className="mr-2"
                                    />
                                    {option.label}
                                </label>
                            ))}
                        </div>
                    )}
                    <div className="mt-4">
                        <label className="block text-sm font-medium text-gray-700">Search Query:</label>
                        <input
                            type="text"
                            placeholder="Enter your search query"
                            onChange={(e) => setInputValue(e.target.value)}
                            className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                        />
                    </div>
                    <button
                        onClick={handleSubmit}
                        disabled={loading || error}
                        className="mt-4 w-full bg-blue-500 text-white p-2 rounded-md hover:bg-blue-600 disabled:bg-gray-400"
                    >
                        Submit
                    </button>
                </form>
            )}

            {currentTab === 'search' && responseData && responseData.data && (
                <div className="results-container mt-6">
                    {Object.keys(responseData.data).map((option) => (
                        <div key={option} className="result-card p-4 bg-gray-100 rounded-md mb-4">
                            <h3 className="text-lg font-semibold">{option}</h3>
                            <h4>totalhits: {responseData.totalHits[option]}</h4>
                            {Array.isArray(responseData.data[option]) ? (
                                responseData.data[option].map((item, index) => (
                                    <div key={index} className="result-item bordered-box p-4 bg-white rounded-md mt-2">
                                        {Object.entries(item).map(([key, value]) => (
                                            <div key={key}>
                                                <strong>{key}:</strong>{' '}
                                                {typeof value === 'object' ? (
                                                    <ul style={{ paddingLeft: '15px', margin: 0 }}>
                                                        {Object.entries(value).map(([subKey, subValue]) => (
                                                            <li key={subKey}>
                                                                <strong>{subKey}:</strong> {subValue}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                ) : (
                                                    value
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                ))
                            ) : (
                                <p>{responseData.data[option]}</p>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
