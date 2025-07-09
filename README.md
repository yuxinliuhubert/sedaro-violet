# Violet Sedaro Platform

A comprehensive web-based interface for managing and simulating Sedaro agent templates with advanced property tracking, real-time simulation monitoring, and detailed statistics analysis.

## 🚀 Features

### Core Functionality
- **Agent Template Management**: Connect to and manage Sedaro agent templates
- **Real-time Simulation**: Start, monitor, and control simulations with live progress tracking
- **Property Tracking**: Track and manage template properties through an intuitive spreadsheet interface
- **Statistics Analysis**: View detailed simulation statistics grouped by agents and blocks
- **Block ID Mapping**: Automatic mapping of block IDs to readable names for better organization

### Advanced Features
- **Auto-Simulation**: Automatically trigger simulations when tracked properties change
- **State Persistence**: Save and restore application state across sessions
- **Property Mutability Detection**: Visual indicators for editable vs read-only properties
- **Grouped Statistics Display**: Hierarchical view of simulation statistics by agent → block → property
- **Interactive Property Explorer**: Browse and edit template properties with search functionality

## 🏗️ Architecture

### Backend (Flask)
- **API Endpoints**: RESTful API for template management, simulation control, and statistics
- **Sedaro Integration**: Direct integration with Sedaro API for agent template operations
- **Block Discovery**: Automatic discovery and categorization of template blocks
- **Simulation Management**: Comprehensive simulation lifecycle management

### Frontend (JavaScript/HTML/CSS)
- **Responsive UI**: Modern, responsive interface with purple/gray/white brand colors
- **Real-time Updates**: Live progress monitoring and status updates
- **State Management**: Local storage-based state persistence
- **Property Mapping**: Intelligent block ID to name mapping system

## 📋 Prerequisites

- Python 3.7+
- Sedaro API access
- Valid API key and workspace configuration

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd sedaro-violet
   ```

2. **Install dependencies**:
   ```bash
   pip install flask sedaro
   ```

3. **Configure API credentials**:
   Update the following constants in `app.py`:
   ```python
   API_KEY = "your-sedaro-api-key"
   TEMP_AGENT_REPO_BRANCH_ID = "your-template-branch-id"
   SCENARIO_BRANCH_VERSION_ID = "your-scenario-branch-id"
   WORKSPACE_ID = "your-workspace-id"
   ```

4. **Run the application**:
   ```bash
   python3 app.py
   ```

5. **Access the platform**:
   Open your browser and navigate to `http://localhost:5000`

## 🎯 Usage Guide

### 1. Template Management

#### Connecting to Templates
- Use the **"🔄 Refresh Template"** button to connect to your agent template
- The system automatically discovers all blocks and properties
- Block IDs are mapped to readable names for better organization

#### Template Explorer
- **Search Components**: Use the searchable dropdown to find specific components
- **Property Editing**: Click on components to view and edit their properties
- **Mutability Indicators**: Visual indicators show which properties are editable
- **Property Tracking**: Use the "📊 Track" button to add properties to the spreadsheet

### 2. Simulation Control

#### Starting Simulations
1. Click **"🚀 Start Simulation"** to begin a new simulation
2. Monitor progress in real-time with the progress bar
3. View detailed progress information including current time and time step
4. Use **"Abort"** to stop running simulations

#### Simulation Monitoring
- **Live Progress**: Real-time progress updates every 2 seconds
- **Status Tracking**: Current status, completion percentage, and time information
- **Auto-Recovery**: Automatically restores monitoring for interrupted simulations
- **Timeout Protection**: Stops polling after 30 minutes to prevent infinite loops

### 3. Property Tracking Spreadsheet

#### Adding Properties
1. **Manual Entry**: Type property names and values directly
2. **Template Selection**: Click the property selector to choose from available template properties
3. **Auto-Tracking**: Enable auto-trigger to automatically apply changes and start simulations

#### Property Organization
- **Block Grouping**: Properties are automatically grouped by their associated blocks
- **Root Properties**: Template-level properties are separated from block properties
- **Visual Hierarchy**: Clear visual distinction between different property types

#### Auto-Simulation Features
- **Change Detection**: Automatically detects when tracked properties change
- **Batch Updates**: Applies multiple property changes efficiently
- **Simulation Triggering**: Automatically starts simulations after successful updates
- **Error Handling**: Graceful handling of update failures

### 4. Statistics Analysis

#### Fetching Statistics
1. Click **"📈 Statistics"** to open the statistics section
2. Enter a simulation ID or leave empty for the latest simulation
3. Toggle "Wait for Stats" if you want to wait for statistics to be ready
4. Click **"📊 Fetch Statistics"** to retrieve detailed statistics

#### Statistics Display
- **Hierarchical Organization**: Statistics grouped by Agent → Block → Property
- **Root Properties**: Agent-level properties displayed separately
- **Block Properties**: Properties organized by their associated blocks
- **Readable Names**: Block IDs automatically mapped to readable names

#### Statistics Types
- **Absolute Average**: Average of absolute values
- **Maximum/Minimum**: Peak and minimum values
- **Standard Deviation**: Statistical variance
- **Integral**: Cumulative values over time
- **Variance**: Statistical variance measures

### 5. Advanced Features

#### State Persistence
- **Automatic Saving**: Application state saved every 5 seconds
- **Session Recovery**: Restores previous state when reopening the application
- **Simulation Continuity**: Maintains simulation monitoring across sessions
- **Spreadsheet Data**: Preserves all tracked properties and their values

#### Block ID Mapping
- **Automatic Discovery**: Discovers all blocks in the template
- **Name Resolution**: Maps cryptic block IDs to readable names
- **Type Information**: Includes block type and path information
- **Fallback Handling**: Graceful handling of unknown blocks

#### Property Mutability
- **Visual Indicators**: Clear indication of editable vs read-only properties
- **Update Validation**: Prevents updates to immutable properties
- **Error Feedback**: Clear error messages for failed updates
- **Success Confirmation**: Visual confirmation of successful updates

## 🔧 API Reference

### Template Management
- `GET /api/template_structure` - Get complete template structure
- `POST /api/refresh_template` - Refresh template connection
- `GET /api/blocks` - Get all discovered blocks
- `GET /api/block/<id>/properties` - Get properties of specific block

### Property Management
- `POST /api/update_property` - Update block property
- `POST /api/update_root_property` - Update root-level property
- `GET /api/mutability` - Check property mutability

### Simulation Control
- `POST /api/simulate` - Start new simulation
- `GET /api/simulation_status` - Get simulation status and progress
- `POST /api/abort_simulation` - Abort running simulation
- `GET /api/results` - Get simulation results

### Statistics
- `POST /api/simulation_statistics` - Get simulation statistics
- `GET /api/available_streams` - Get available data streams

## 🎨 UI Components

### Color Scheme
- **Primary**: `#c3adff` (Purple)
- **Secondary**: `#6c757d` (Gray)
- **Background**: `#ffffff` (White)
- **Accent**: `#a78bfa` (Darker Purple)

### Interactive Elements
- **Buttons**: Purple gradient with hover effects
- **Progress Bars**: Animated progress indicators
- **Dropdowns**: Searchable component selectors
- **Tables**: Responsive data tables with hover effects
- **Modals**: Overlay dialogs for property editing

### Visual Hierarchy
- **Agent Sections**: Top-level grouping with purple headers
- **Block Subsections**: Secondary grouping with gray backgrounds
- **Property Items**: Individual property rows with clear labels
- **Status Indicators**: Color-coded status badges and icons

## 🐛 Debugging

### Console Functions
The application includes several debug functions accessible from the browser console:

```javascript
// Test block mapping functionality
debugBlockMapping()

// Get summary of all blocks by type
getBlockSummary()

// Test statistics grouping (requires statistics data)
debugStatisticsGrouping(statisticsData)
```

### Common Issues

#### Template Connection Issues
- Verify API key and workspace configuration
- Check network connectivity to Sedaro API
- Ensure template branch ID is correct

#### Simulation Problems
- Verify scenario branch configuration
- Check simulation parameters and constraints
- Monitor simulation logs for error details

#### Property Update Failures
- Check property mutability status
- Verify property names and values
- Ensure block IDs are valid

## 🔒 Security Considerations

- **API Key Protection**: Store API keys securely and rotate regularly
- **Input Validation**: All user inputs are validated before processing
- **Error Handling**: Sensitive information is not exposed in error messages
- **Session Management**: State persistence uses local storage only

## 🚀 Performance Optimization

- **Lazy Loading**: Components and properties loaded on demand
- **Caching**: Block mapping and template structure cached locally
- **Polling Optimization**: Efficient simulation status polling with timeout protection
- **Batch Operations**: Multiple property updates processed efficiently

## 📈 Future Enhancements

- **Multi-Template Support**: Manage multiple agent templates simultaneously
- **Advanced Filtering**: Filter properties and statistics by type, value range, etc.
- **Export Functionality**: Export statistics and property data to various formats
- **Collaboration Features**: Share templates and simulation results
- **Advanced Analytics**: Statistical analysis and trend visualization
- **API Rate Limiting**: Intelligent handling of API rate limits
- **Offline Mode**: Basic functionality without network connectivity

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the debugging section above
- Review the API documentation
- Contact the development team
- Submit issues through the repository

---

**Violet Sedaro Platform** - Empowering satellite simulation and analysis with intuitive, powerful tools. 