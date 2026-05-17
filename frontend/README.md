# Code Reuse - Frontend

A clean, minimalist web interface for the Context-Aware Code Generation system.

## 🎨 Features

### 1. **Landing Page**
- Clean input for GitHub repository URLs
- Feature cards showcasing system capabilities
- Gradient background with modern design

### 2. **Processing Page**
- Real-time progress visualization
- Step-by-step analysis display:
  - Repository cloning
  - AST parsing
  - Dependency graph building
  - Embedding generation
- Live statistics counter

### 3. **Dependency Graph Visualization**
- Interactive D3.js force-directed graph
- Color-coded nodes by type (services, utils, models)
- Draggable nodes for exploration
- Graph statistics display
- "Proceed to Coding" button

### 4. **IDE Interface**
- **Left Panel - AI Agent:**
  - Query input textarea
  - Generate code button
  - Real-time processing log with timestamps
  - Color-coded log entries (info, success, warning, error)
  
- **Right Panel - Code Display:**
  - Syntax-highlighted code viewer
  - Line numbers
  - Copy to clipboard functionality
  - Iteration counter
  
- **Metrics Panel:**
  - Namespace Reuse Score with progress bar
  - Structural Similarity Check
  - Overall Quality Score
  - Real-time metric updates

## 🚀 Quick Start

### Option 1: Direct File Opening
Simply open `index.html` in your web browser:
```bash
# Windows
start frontend/index.html

# macOS
open frontend/index.html

# Linux
xdg-open frontend/index.html
```

### Option 2: Local Server (Recommended)
Using Python's built-in HTTP server:
```bash
cd frontend
python -m http.server 8000
```
Then open: http://localhost:8000

### Option 3: Live Server (VS Code)
1. Install "Live Server" extension in VS Code
2. Right-click `index.html`
3. Select "Open with Live Server"

## 📁 File Structure

```
frontend/
├── index.html          # Main HTML structure
├── styles.css          # Complete styling (minimalist design)
├── app.js             # JavaScript logic and interactions
└── README.md          # This file
```

## 🎯 User Flow

1. **Enter GitHub URL** → User pastes repository link
2. **Processing** → System analyzes repository (AST, dependencies, embeddings)
3. **View Graph** → Interactive visualization of code dependencies
4. **Generate Code** → Enter query in IDE interface
5. **View Results** → See generated code with quality metrics

## 🎨 Design Philosophy

- **Minimalist**: Clean, uncluttered interface
- **Modern**: Gradient backgrounds, smooth animations
- **Intuitive**: Clear visual hierarchy and flow
- **Responsive**: Works on desktop and tablet devices
- **Professional**: IDE-like interface for developers

## 🔧 Customization

### Colors
Edit CSS variables in `styles.css`:
```css
:root {
    --primary: #667eea;
    --secondary: #764ba2;
    --accent: #f093fb;
    /* ... more colors */
}
```

### Graph Visualization
Modify graph settings in `app.js`:
```javascript
const simulation = d3.forceSimulation(data.nodes)
    .force('link', d3.forceLink(data.links).distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    // ... more forces
```

## 📊 Current Implementation

### Status: ✅ Frontend Complete (Mock Data)

The frontend is fully functional with simulated data. It demonstrates:
- ✅ All UI components
- ✅ Page transitions
- ✅ Graph visualization
- ✅ Processing animations
- ✅ Metrics display
- ⏳ Backend API integration (pending)

### Mock Data Flow
Currently uses simulated data to demonstrate functionality:
- Repository analysis: 6 files, 51 functions, 16 imports
- Graph: 10 nodes, 9 edges
- Code generation: Pre-defined example
- Metrics: Sample scores (66.7% namespace, 80% quality)

## 🔌 Backend Integration (Next Steps)

To connect to the actual backend API, update `app.js`:

```javascript
// Replace simulation functions with actual API calls

async function startAnalysis(repoUrl) {
    const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl })
    });
    const data = await response.json();
    // Handle response...
}

async function generateCode(query) {
    const response = await fetch('http://localhost:8000/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            query: query,
            repo_url: state.repoUrl 
        })
    });
    const data = await response.json();
    // Handle response...
}
```

## 🌐 Browser Compatibility

- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari
- ⚠️ IE11 (not supported)

## 📦 Dependencies

- **D3.js v7** - Graph visualization (loaded from CDN)
- **Google Fonts** - Inter font family (loaded from CDN)

No build process required! Pure HTML, CSS, and JavaScript.

## 🎬 Demo Flow

1. **Landing Page**
   - Paste: `https://github.com/username/repo`
   - Click "Analyze Repository"

2. **Processing Page** (auto-advances)
   - Watch steps complete
   - See statistics update

3. **Graph Page**
   - Explore dependency visualization
   - Click "Proceed to Coding"

4. **IDE Page**
   - Enter query: "Add email validation"
   - Click "Generate Code"
   - View processing log
   - See generated code and metrics

## 🎨 Screenshots

### Landing Page
Clean input with gradient background and feature cards

### Processing Page
Step-by-step progress with live statistics

### Graph Visualization
Interactive D3.js force-directed graph

### IDE Interface
Split-panel design with agent log and code display

## 📝 Notes

- All animations use CSS transitions for smooth performance
- Graph is fully interactive (drag nodes, zoom, pan)
- Log entries auto-scroll to bottom
- Code can be copied with one click
- Responsive design adapts to screen size

## 🚧 Future Enhancements

- [ ] WebSocket support for real-time updates
- [ ] Syntax highlighting for multiple languages
- [ ] Export generated code to file
- [ ] Dark/light theme toggle
- [ ] Graph export as image
- [ ] Code diff viewer for iterations
- [ ] Search functionality in logs
- [ ] Keyboard shortcuts

## 📄 License

Part of the IBM Code Reuse project.