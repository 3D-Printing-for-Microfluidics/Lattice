# Lattice: A Python utility for position-specific exposure control in 3D printing

Lattice is a graphical layout and design tool for high-throughput 3D printing that enables the simultaneous printing of many devices in a single print run by providing a way to easily arrange devices in the print area and control exposure settings for each one individually. 

Run with `python -m app.app`

## Features

- **Component Management**

  - Load component files (zip format)
  - Add, delete, and position components on canvas
  - Tile creation for repeated patterns
  - Drag and drop positioning
  - Multi-select with shift-click
  - Zoom in/out functionality

- **Group Organization**

  - Create exposure groups with custom colors
  - Assign components to groups
  - Each group represents different exposure settings
  - Rename and delete groups
  - Change group colors

- **Layout Tools**
  - Align components (left, right, top, bottom)
  - Set precise X/Y coordinates
  - Drag selection for multiple components
  - Save and load component layouts
  - Automatic overlap detection

## How to Use

1. **Getting Started**

   - Launch the application
   - Load a component file using Component > Load component
   - Create a group using Group > New Group
   - Add components using Component > Add, Insert key, or Component > Tile create

2. **Component Manipulation**

   - Click and drag to move components
   - Shift+click to select multiple components
   - Use Arrange > Set X and Arrange > Set Y for precise positioning
   - Use Arrange > align left, right, top, bottom to align selected components
   - Delete selected components with Delete key

3. **Creating Patterns**

   - Use Component > Tile create to make repeated patterns
   - Specify start position, spacing, and number of components

4. **Saving Work**
   - Save layouts using File > Save Layout
   - Load existing layouts with File > Open Layout
   - Generate final print file using File > Generate print file

## Keyboard Shortcuts

### Component Management

- `Insert`: Add new component
- `Delete`: Remove selected component(s)
- `Ctrl+L`: Load component file

### File Operations

- `Ctrl+S`: Save layout
- `Ctrl+O`: Open layout

### View Controls

- `Ctrl+=`: Zoom in
- `Ctrl+-`: Zoom out

### Group Management

- `Ctrl+G`: Create new group
- `Ctrl+C`: Change selected components to current group

### Alignment (of currently selected components)

- `Ctrl+←`: Align left
- `Ctrl+→`: Align right
- `Ctrl+↑`: Align top
- `Ctrl+↓`: Align bottom
- `Ctrl+X`: Set X position
- `Ctrl+Y`: Set Y position

### Selection

- `Shift+Click`: Select multiple components
- `Click+Drag`: Select with selection box

## Testing

### Running Tests

- Run all tests with: `pytest`
- Run a specific test file: `pytest tests/test_file.py`
- Run tests in watch mode: `pytest-watch`
- Run tests with detailed output: `pytest -v`
- Run tests matching a specific name: `pytest -k "test_name"`

### Test Coverage

To generate and view test coverage reports:

1. Generate coverage report: `pytest --cov=app tests/`
2. Generate detailed HTML report: `pytest --cov=app --cov-report=html tests/`
3. View the HTML report in `htmlcov/index.html`

## Notes

- Components cannot overlap in the final layout
- Each group should be named with a numeric value representing exposure settings
- The canvas maintains aspect ratio when zooming
- Component dimensions are set to the image dimensions in the component zip file
