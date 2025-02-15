# 3D Print Dose Customization Tool

A graphical tool for arranging and customizing components for 3D printing with different exposure settings.

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
   - Delete selected components with Delete key

3. **Creating Patterns**

   - Use Component > Tile create to make repeated patterns
   - Specify start position, spacing, and number of components

4. **Saving Work**
   - Save layouts using File > Save Layout
   - Load existing layouts with File > Open Layout
   - Generate final print file using File > Generate print file

## Keyboard Shortcuts

- `Insert`: Add new component
- `Delete`: Remove selected component(s)
- `Ctrl+=`: Zoom in
- `Ctrl+-`: Zoom out
- `Ctrl+G`: Create new group
- `Ctrl+S`: Save layout
- `Ctrl+O`: Open layout

## Notes

- Components cannot overlap in the final layout
- Each group should be named with a numeric value representing exposure settings
- The canvas maintains aspect ratio when zooming
- Component dimensions are set to the image dimensions in the component zip file
