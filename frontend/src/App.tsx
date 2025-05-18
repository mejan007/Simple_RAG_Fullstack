import React, { useState, useCallback } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
import './App.css'

function App() {
  // Three state variables to manage the app's functionality
  /*
    The first is a string variable to track and store the user’s query.

    The second is another string variable to hold and display the backend’s RAG chain response.

    Finally, we’ll use a boolean variable to track whether the application is currently streaming. 
    This ensures that no duplicate queries are submitted while the app is processing, 
    allowing the system to handle one stream at a time without issues.


    The query variable is passed into the value attribute of the <textarea>, enabling us to track and update the user’s input dynamically.

    The response variable is displayed in the response-container <div>, allowing the backend’s output to be shown in real-time

    The isStreaming variable is used in the disabled attribute of the <button>, ensuring the submit button is temporarily disabled while streaming is active, preventing duplicate submissions.

  */
  const [query, setQuery] = useState<string>('');
  const [response, setResponse] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState<boolean>(false);

  // New handlers to manage file upload functionality
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadStatus, setUploadStatus] = useState<string>('');
  const [isDragActive, setIsDragActive] = useState<boolean>(false);
  const [uploadedDocIds, setUploadedDocIds] = useState<string[]>([]);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

     // Get dropped files
    const files = e.dataTransfer.files;
    if (files.length === 0) return;
    
    // Process only the first file
    const file = files[0];
    
    // Check if it's a text file or a file we can read as text
    if (!file.type.includes('text') && 
        !file.type.includes('application/json') && 
        !file.type.includes('application/pdf') && 
        !file.name.endsWith('.txt') && 
        !file.name.endsWith('.md')) {
      setUploadStatus('Please upload a text file only.');
      return;
    }
    
    setIsUploading(true);
    setUploadStatus('Reading file...');
    
    try {
      // Read the file as text first
      const fileContent = await readFileAsText(file);
      
      // Convert to base64
      const base64Content = btoa(fileContent);
      
      // Call the upload API
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          file_data: base64Content
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setUploadStatus(`Successfully uploaded document with ${data.uploaded_ids.length} chunks.`);
        setUploadedDocIds(data.uploaded_ids);
      } else {
        setUploadStatus(`Error: ${data.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error uploading file:', error);

      const errorMessage =
        error instanceof Error
          ? error.message
          : typeof error === 'string'
            ? error
            : 'Unknown error';

      setUploadStatus(`Error uploading file: ${errorMessage}`)
    } finally {
      setIsUploading(false);
    }
  }, []);

  // Helper function to read file as text
  const readFileAsText = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        resolve(reader.result as string);
      };
      reader.onerror = () => {
        reject(new Error('Failed to read file'));
      };
      reader.readAsText(file);
    });
  };

  // Manual file input handler
  const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    const file = files[0];
    
    // Check if it's a text file
    if (!file.type.includes('text') && 
        !file.type.includes('application/json') && 
        !file.type.includes('application/pdf') && 
        !file.name.endsWith('.txt') && 
        !file.name.endsWith('.md')) {
      setUploadStatus('Please upload a text file only.');
      return;
    }
    
    setIsUploading(true);
    setUploadStatus('Reading file...');
    
    try {
      // Read the file as text
      const fileContent = await readFileAsText(file);
      
      // Convert to base64
      const base64Content = btoa(fileContent);
      
      // Call the upload API
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          file_data: base64Content
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setUploadStatus(`Successfully uploaded document with ${data.uploaded_ids.length} chunks.`);
        setUploadedDocIds(data.uploaded_ids);
      } else {
        setUploadStatus(`Error: ${data.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error uploading file:', error);

      const errorMessage =
        error instanceof Error
          ? error.message
          : typeof error === 'string'
            ? error
            : 'Unknown error';

      setUploadStatus(`Error uploading file: ${errorMessage}`);
    } finally {
      setIsUploading(false);
    }
  };
    
  // The first handler will track and update changes in the query <textarea>

  const handleQueryChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuery(event.target.value);
    /*
    This function, defined within the App component, will ensure that whenever the user types or modifies the 
    input in the <textarea>, the query state variable is updated via the setQuery function.
    */
  };

  // Query submission handler which allows React frontend to interact with FastAPI backend via WebSocket
  const handleQuerySubmit = () => {

    // Check if query is empty, if it is, return early and don't create a WebSocket connection

    if(!query.trim()) return;

    /*
    When the connection opens, we set isStreaming to true, preventing the user from submitting multiple queries simultaneously. 
    We also reset the response state to clear any previous results, ensuring a clean slate for the current query.
    
    */

    const websocket = new WebSocket('ws://localhost:8000/ws/stream');
    setIsStreaming(true);
    setResponse('');


    // To manage the WebSocket connection effectively, we create the four key event handlers:

    //Websocker On Open Action -> Triggered when WebScoket connection is successfully established
     websocket.onopen = () => {

    /*
    This is the moment when the client is ready to communicate with the backend. 
    
    At this point, the backend is waiting for an initial JSON payload containing the user's query. 
    This query will be used to execute the RAG pipeline and return a response.
    */
   console.log("WebSocker connection opened.");
    // Send query to the server
    websocket.send(JSON.stringify({query}));
    };

    // ON MESSAGE HANDLER -> Called whenever a new message (chunk of response) is received from the server.
    websocket.onmessage = (event) => {
      
      const data = event.data;
      console.log('data: ', data);

      // Check for the termination flag
      if (data == '<<END>>'){
        websocket.close();
        setIsStreaming(false);
        return;
      }
      // Check for no query Error flag
      if (data == '<<E:NO_QUERY>>') {
        console.log('ERROR: No Query, closing connection...')
        websocket.close();
        setIsStreaming(false);
        return;
      }
      // Update state directly with the new data
      setResponse((prevResponse) => prevResponse + data);
    };

    // Websocket Error Handler -> Handles errors that occur during the connection.
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      websocket.close();
      setIsStreaming(false);
    };

    // ON CLOSE Action -> Executes cleanup actions when the connection is closed, either normally or unexpectedly.
    websocket.onclose = () => {
      console.log('WebSocket connection closed.');
      setIsStreaming(false);
    };

  }


  return (
    <div className='main-div'>
      <div className='header-container'>
        <h1>Full Stack RAG w/ Streaming</h1>
        
        {/* File Upload Section */}
        <div 
          className={`drop-zone ${isDragActive ? 'active' : ''} ${isUploading ? 'uploading' : ''}`}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <div className="drop-zone-content">
            {isUploading ? (
              <div className="upload-progress">Uploading...</div>
            ) : (
              <>
                <p>Drag & drop your text file here</p>
                <p>or</p>
                <input 
                  type="file" 
                  id="file-input" 
                  onChange={handleFileInputChange} 
                  className="file-input"
                  accept=".txt,.md,.json,.pdf,text/*"
                />
                <label htmlFor="file-input" className="file-input-label">
                  Choose a file
                </label>
              </>
            )}
          </div>
        </div>
        
        {/* Upload Status */}
        {uploadStatus && (
          <div className={`upload-status ${uploadStatus.includes('Error') ? 'error' : 'success'}`}>
            {uploadStatus}
          </div>
        )}

        {/* Query Input Bar */}
        <div className='query-input-bar'>
          <textarea
            className='query-textarea'
            value={query}
            onChange={handleQueryChange}
            placeholder="Query your data here..."
            rows={5}
            cols={100}
            disabled={uploadedDocIds.length === 0 && !uploadStatus.includes('Successfully')}
          ></textarea>
          <button
            className='submit-btn'
            onClick={handleQuerySubmit}
            disabled={isStreaming || uploadedDocIds.length === 0}
          >
            Submit
          </button>
        </div>
      </div>

      <div className='response-container'>
        {response ? (
          <div className="response-text">{response}</div>
        ) : (
          <div className="response-placeholder">Your response will appear here after submitting a query.</div>
        )
      }
      </div>
    </div>
  )
}

export default App
