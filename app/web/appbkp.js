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

    const [selectedOption, setSelectedOption] = React.useState("");
    const [formData, setFormData] = React.useState({});
    const [submittedData, setSubmittedData] = React.useState(null);

    // States to control flow views
    const [showForm, setShowForm] = useState(false);
    const [showPreview, setShowPreview] = useState(false);

    // Form fields (can be empty)
    const [formInput1, setFormInput1] = useState('');
    const [formInput2, setFormInput2] = useState('');
    const [formInput3, setFormInput3] = useState('');


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
            // Reset view states on re-upload
            setShowForm(false);
            setShowPreview(false);
            setChunks([]);
        }
    };

    const removeFile = () => {
        setFile(null);
        setFileName('');
        setResponseMessage('');
        setShowForm(false);
        setShowPreview(false);
        setChunks([]);
    };

    // When file is selected and "Next" is clicked, call uploadFile API then show form view
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
                setShowForm(true);
                // Reset any previous chunk states
                setShowPreview(false);
                setChunks([]);
            } else {
                setResponseMessage(result.message || 'Error uploading file.');
            }
        } catch (error) {
            setResponseMessage('Error uploading file.');
        }
    };

    // Preview chunks: send filename and form data to getChunks API
    const handlePreviewChunks = async () => {
        if (!fileName) {
            alert('No file uploaded.');
            return;
        }
        const data = {
            file_path: fileName,
            chunkingMechanism: fileName,
            input1: formInput1,
            input2: formInput2,
            input3: formInput3
        }

        try {
            const response = await fetch(`${apiUrl}/getChunks1`, {
                method: 'POST',
                body: JSON.stringify(data),
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

    // Call uploadChunks endpoint with chunks and form data
    const handleSubmitChunks = async () => {
        if (chunks.length === 0) {
            alert('No chunks available to submit.');
            return;
        }
        try {
            const response = await fetch(`${apiUrl}/uploadChunks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    chunks,
                    username,
                    input1: formInput1 || "",
                    input2: formInput2 || "",
                    input3: formInput3 || ""
                }),
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

    React.useEffect(() => {
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
            <div className="login-container">
                <h2>Please Enter Username</h2>
                <input
                    type="text"
                    value={username}
                    onChange={handleUsernameChange}
                    onKeyPress={handleKeyPress}
                    placeholder="Enter your username"
                />
                <button onClick={handleLogin}>Login</button>
            </div>
        );
    }

    return (
        <div>
            <div className="menu-bar">
                <div
                    className={`menu-item ${currentTab === 'index' ? 'active' : ''}`}
                    onClick={() => handleTabChange('index')}
                >
                    Index
                </div>
                <div
                    className={`menu-item ${currentTab === 'search' ? 'active' : ''}`}
                    onClick={() => handleTabChange('search')}
                >
                    Search
                </div>
                <div className="menu-item logout">
                    <button onClick={handleLogout}>Logout</button>
                </div>
            </div>

            {currentTab === 'index' && (
                <div className="form-container">
                    <h3>Upload File</h3>
                    <div>
                        <input
                            id="file-input"
                            type="file"
                            accept="*/*"
                            style={{ display: 'none' }}
                            onChange={handleFileUpload}
                        />
                        <button onClick={() => document.getElementById('file-input').click()}>
                            Upload File
                        </button>
                    </div>
                    {fileName && (
                        <div className="file-info">
                            <span>{fileName}</span>
                            <button onClick={removeFile}>Remove</button>
                            <button onClick={handleShowForm}>Next</button>
                        </div>
                    )}

                    {showForm && (
                        <div className="form-section">
                            <h3>Additional Data</h3>
                            <input
                                type="text"
                                placeholder="Input 1"
                                value={formInput1}
                                onChange={(e) => setFormInput1(e.target.value)}
                            />
                            <input
                                type="text"
                                placeholder="Input 2"
                                value={formInput2}
                                onChange={(e) => setFormInput2(e.target.value)}
                            />
                            <input
                                type="text"
                                placeholder="Input 3"
                                value={formInput3}
                                onChange={(e) => setFormInput3(e.target.value)}
                            />
                            <div>
                                <button type="button" onClick={handlePreviewChunks}>
                                    Preview Chunks
                                </button>
                                <button type="button" onClick={handleSubmitChunks}>
                                    Submit
                                </button>
                                <button type="button" onClick={() => setShowForm(false)}>
                                    Back
                                </button>
                            </div>
                        </div>
                    )}

                    {responseMessage && <span>{responseMessage}</span>}

                    {showPreview && chunks.length > 0 && (
                        <div className="chunks-preview" style={{ position: 'relative' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <h4>Chunks Preview:</h4>
                                <button
                                    onClick={() => setChunksCollapsed(!chunksCollapsed)}
                                    style={{
                                        border: 'none',
                                        background: 'transparent',
                                        fontSize: '20px',
                                        cursor: 'pointer',
                                        color: chunksCollapsed ? 'red' : 'black',
                                    }}
                                >
                                {chunksCollapsed ? '▼' : 'X'}
                                </button>
                            </div>
                            {!chunksCollapsed && (
                                <div >
                                    {chunks.map((chunk, index) => (
                                        <div key={index} className="chunk-item">
                                            <strong>ChunkId: {index}</strong>
                                            <br />
                                            <strong>Chunk:</strong>
                                            <br />
                                            <span>{chunk}</span>
                                        </div>
                                    ))}        
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {currentTab === 'search' && (
                <form onSubmit={handleSubmit} className="form-container">
                    {loading && <div className="loading-message">Loading options...</div>}
                    {error && <div className="error-message">Error: {error}</div>}
                    {!loading && !error && (
                        <div className="checkbox-group">
                            {options.map((option) => (
                                <label key={option.value} className="checkbox-label">
                                    <input
                                        type="checkbox"
                                        value={option.value}
                                        onChange={handleOptionChange}
                                        checked={selectedOptions.includes(option.value)}
                                    />
                                    {option.label}
                                </label>
                            ))}
                        </div>
                    )}
                    <div>
                        <label>Search Query:</label>
                        <input
                            type="text"
                            placeholder="Enter your search query"
                            onChange={(e) => setInputValue(e.target.value)}
                        />
                    </div>
                    <button type="submit" disabled={loading || error}>
                        Submit
                    </button>
                </form>
            )}

            {currentTab === 'search' && responseData && responseData.data && (
                <div className="results-container">
                    {Object.keys(responseData.data).map((option) => (
                        <div key={option} className="result-card">
                            <h3>{option}</h3>
                            <h4>totalhits: {responseData.totalHits[option]}</h4>
                            {Array.isArray(responseData.data[option]) ? (
                                responseData.data[option].map((item, index) => (
                                    <div key={index} className="result-item bordered-box">
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

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
