# Module Uniformity Documentation

## Overview
All modules in the Attempy-DAA system now have consistent authentication, navigation, and styling.

## Modules

### 1. Index Page (`/index.html`)
- **Purpose**: Landing page with navigation to all modules
- **Authentication**: Required (redirects to login if not authenticated)
- **Navigation**: Links to all modules with consistent icons and styling
- **Features**: 
  - Python Compiler
  - C++ Compiler  
  - Visualizer
  - Agent
  - Simulator

### 2. Python Compiler (`/compiler.html`)
- **Purpose**: Execute Python code in isolated containers
- **Authentication**: Required (uses unified navigation)
- **Navigation**: Links to C++ Compiler, Visualizer, and Agent
- **Features**:
  - Code editor with syntax highlighting
  - Algorithm name and input size tracking
  - Runtime measurement and database storage
  - Real-time output display

### 3. C++ Compiler (`/cpp_compiler.html`)
- **Purpose**: Compile and execute C++ code in isolated containers
- **Authentication**: Required (uses unified navigation)
- **Navigation**: Links to Python Compiler, Visualizer, and Agent
- **Features**:
  - C++ code editor with GCC compilation
  - Algorithm name and input size tracking
  - Runtime measurement and database storage
  - Real-time output display

### 4. Visualizer (`/visualization.html`)
- **Purpose**: Analyze and visualize algorithm performance data
- **Authentication**: Required (uses unified navigation)
- **Navigation**: Links to Python Compiler, C++ Compiler, and Agent
- **Features**:
  - Performance overview statistics
  - Interactive charts (line, bar, scatter)
  - Performance data table
  - Backend-generated plots

### 5. Agent (`http://localhost:8000/dev-ui/`)
- **Purpose**: AI-powered code assistance and analysis
- **Authentication**: External system
- **Navigation**: Referenced from all modules
- **Features**: AI agent functionality

## Unified Features

### Authentication System
- **Token Storage**: `localStorage.getItem('token')`
- **User Storage**: `localStorage.getItem('user')`
- **Auto-redirect**: Redirects to `/login.html` if not authenticated
- **Logout**: Consistent logout functionality across all modules

### Navigation System
- **Unified Navigation**: All modules use `/static/navigation.js`
- **Consistent Icons**: Font Awesome icons for each module
- **Dynamic Links**: Only shows links to other modules (not current page)
- **Responsive Design**: Works on all screen sizes

### Styling
- **Consistent CSS**: All modules use `/static/styles.css`
- **Font Awesome**: Consistent icon library
- **Inter Font**: Consistent typography
- **Color Scheme**: Consistent button and element colors

### API Integration
- **Authentication Headers**: Consistent `Authorization: Bearer <token>` headers
- **Error Handling**: Consistent error handling across modules
- **Database Integration**: All modules can save data to Supabase

## File Structure
```
static/
├── index.html              # Landing page
├── compiler.html           # Python compiler
├── cpp_compiler.html       # C++ compiler
├── visualization.html      # Performance visualizer
├── navigation.js           # Unified navigation system
├── script.js              # Python compiler logic
├── visualization.js       # Visualization logic
└── styles.css             # Unified styling
```

## Benefits of Uniformity
1. **Consistent User Experience**: Same navigation and authentication across all modules
2. **Maintainability**: Single source of truth for navigation and authentication
3. **Scalability**: Easy to add new modules with consistent structure
4. **User-Friendly**: Intuitive navigation between modules
5. **Security**: Consistent authentication checks across all modules 