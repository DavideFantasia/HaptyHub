[🇬🇧 eng](README_en.md) | [🇮🇹 ita](README.md)

---
# HaptyHub
HaptyHub is a desktop application that uses Artificial Intelligence (LLM x Computer Vision) to translate two-dimensional diagrams, maps, and graphs (found in slides or notes) into tactile 3D models (`.scad` files).
In addition to generating the 3D model, the software interfaces with external hardware to **make the 3D models interactive**: by touching the nodes of the printed model, the application recognizes the touch and reads the node's description out loud via Text-to-Speech, or through the use of a Tablet with the companion app installed: [HaptyApp](https://github.com/StefanoPea/HaptyApp).

The main goal is to promote study accessibility for blind or low-vision students (Low Vision), allowing for the rapid 3D printing of educational material and interactive haptic exploration.

---
## Table of Contents
- [Installation and Setup](#installation-and-setup)
  - [1. Clone the repository](#1-clone-the-repository)
  - [2. Run automatic installation](#2-run-automatic-installation)
  - [3. API Key Configuration](#3-api-key-configuration)
- [User Guide](#user-guide)
  - [Creating 3D models from photos](#creating-3d-models-from-photos)
  - [Calibration and Association (Haptic Graphs)](#calibration-and-association-haptic-graphs)
  - [Interactive Reading of the Haptic Graph](#interactive-reading-of-the-haptic-graph)
- [Development and Architecture Notes](#development-and-architecture-notes)
  - [Project Structure](#project-structure)
  - [Debug Mode](#debug-mode)
  - [Multithreading and Hardware](#multithreading-and-hardware)
  - [Extensibility (Strategy Pattern)](#extensibility-strategy-pattern)
- [Uninstallation](#uninstallation)

---

# Installation and Setup
To run the software, you must have [Python 3](https://www.python.org/downloads/) installed on your system. The project includes automatic installation scripts that create a virtual environment, install dependencies, and create desktop shortcuts.

## 1. Clone the repository
```bash
git clone git@github.com:DavideFantasia/HaptyHub.git
cd HaptyHub
```
Alternatively, you can download the project in `.zip` format and extract it.

## 2. Run automatic installation

### On Windows:
Run the `install.bat` file (via double click or from the terminal). If Windows displays a security warning, right-click and run as administrator.
Subsequent launches of the application can be done via the shortcut created on the Desktop or by running `HaptyHub.bat`.

### On Linux/macOS:
Open the terminal and run the bash script (you will be asked for your password to configure the `udev` rules necessary for reading the USB port):
```bash
chmod +x install.sh
./install.sh
```
Subsequent launches can be done by searching for the application among your programs or by running `HaptyHub.sh`.

### 3. API Key Configuration
The software uses the Google Gemini API. After installation, a file named `.env` will be generated in the main folder.
You can enter your key in two ways:
1. By starting the program and going to the top menu: `Options -> API Key`.
2. By opening the `.env` file with a text editor and pasting the key: `GEMINI_API_KEY=your_key`

Your Gemini key can be obtained for free at the following [link](https://aistudio.google.com/api-keys)

---

# User Guide
The software is divided into three main workflows, accessible from the UI:

## Creating 3D models from photos
This function translates a 2D image into 3D code.

**1.** Launch the application (double click on the icon created on the Desktop or on the executable created in the working folder).
**2.** Select the Desired Function
  **a.** If you want to create a 3D model: drag an image (e.g., Flow Chart, Graph) into the **PREVIEW IMG** area on the left, or click on it to select a file.
  **b.** Select the diagram type from the **Template menu** at the top (e.g., _Direct Graph_, _Flow Chart_).
  **c.** Fill in the required parameters based on the operation, such as `Options->Add Device/Load Device` for generating Tablet Overlays
**6.** If you want to generate a 3D model, simply click the Send button at the bottom right. The AI will process the image and automatically save the generated file in the `output/` folder, displaying the 3D model in the side 3D viewer at the end of the process.

## Calibration and Association (Haptic Graphs)
This function is used to "teach" the software to recognize touches on the 3D printed model by saving the resonant frequencies.

1. Connect the hardware sensor board (e.g., _NanoVNA_) via USB.
2. Go to the menu **Tactile -> Sensor Calibration** or select the corresponding function on the homepage.
3. The software will establish an environmental baseline (**do not touch the sensor** in this phase).
4. Follow the on-screen instructions: **physically touch a node** on the 3D model and hold it down.
5. When the software detects and stabilizes the peak, release and fill in the ID and Description of the node related to the Peak where you notice the biggest change.
6. Repeat for all nodes. When finished, click on **Finish and Export** to save the entire tactile map in a `.json` file.

## Interactive Reading of the Haptic Graph
This is the usage mode for the end user. It allows the exploration of the printed 3D model with voice feedback.

1. Go to the menu **Tactile -> Tactile Graph Reading** or select the corresponding function on the homepage.
2. From the new window's menu, click on **File -> Import Graph (JSON)** and select the previously created calibration file.
3. The software will calculate a _new baseline_ (to adapt to current environmental conditions).
4. Touch any node on the physical model: the software will calculate the Mean Squared Error (MSE) of the frequencies in real time, identify the corresponding node, and read it out loud using native voice synthesis (Windows SAPI5 or Linux espeak/mbrola).

---

# Development and Architecture Notes
The project is built to be modular, reactive, and extensible.

## Project Structure
```text
HaptyHub/
├── assets/                     # Application icons and graphic resources
├── src/                        # Main source code
│   ├── api_client.py           # Handles communication with the Gemini API
│   ├── models/                 # Data structures (e.g., Graph and Node representation)
│   ├── prompts/                # LLM prompt templates divided by type
│   │   ├── basic/              # Prompts for basic 3D models (Flowcharts, Graphs, Sets)
│   │   └── interactive/        # Prompts for advanced interactive models
│   ├── ui/                     # Graphical User Interface components (PyQt6)
│   │   ├── HaptyHub.py                 # Main dashboard
│   │   ├── android_model_window.py     # Window for generating Tablet overlays
│   │   ├── circuit_model_window.py     # Window for interactive base generation (NanoVNA)
│   │   ├── basic_haptic_modeler.py     # Window for generating embossed diagrams (no interaction)
│   │   ├── calibration_window.py       # Sensor calibration and association window
│   │   ├── hapticReader_window.py      # Reading window with voice feedback (TTS)
│   │   └── panels.py                   # Collection of UI Panels
│   └── utils/                  # Utility scripts and processing engines
│       ├── run_elk.js                  # ELK spatial routing engine (Node.js)
│       ├── json_to_scad*.py            # Converters for spatial coordinates into OpenSCAD
│       ├── gemini_worker.py            # Asynchronous thread for LLM calls
│       ├── sensor_*.py                 # Serial communication logic with NanoVNA
│       ├── tts_worker.py               # Text-to-Speech engine for audio feedback
│       ├── stl_viewer.py               # 3D renderer integrated into the GUI
│       └── ...                         # Secondary Utility files
├── config.py                     # Global parameters, paths, and configuration settings
├── main.py                       # Application entry point
├── requirements.txt              # Required Python dependencies
├── install.sh / install.bat      # Automated installation scripts (Linux/Windows)
└── uninstall.sh / uninstall.bat  # Automated uninstallation scripts (Linux/Windows)
```

## Debug Mode

In the `config.py` file, there is a `DEBUG_MODE` variable (also modifiable at runtime from the **Options -> Debug Mode menu**).

- If **ENABLED**, the app uses the `TestClient`. It will simulate sending and receiving data without contacting Google's servers. It is essential to use it during interface development or layout creation to avoid consuming the API quota.
- If **DISABLED**, real calls to Gemini will be made.

## Multithreading and Hardware
To avoid graphic interface "freezes":
- API calls are handled asynchronously via `GeminiWorker`.
- The hardware (Serial) is read in a loop by a separate `SensorWorker`. Raw readings are algorithmically stabilized to reduce noise and false positives during reading.
- Voice synthesis uses a `TTSWorker` based on a thread-safe **Queue** structure. This prevents **pyttsx3**/COM engine crashes and UI freezes, ensuring a smooth experience even if the user touches nodes quickly.
- The conversion from `.scad` files to `.stl` files for in-App viewing and subsequent printing is handled by `STLCompilerWorker`.

## Extensibility (Strategy Pattern)
To add support for a new type of diagram to be processed with AI:
- **Create Prompts**: Create a new folder in `src/prompts/`, distinguishing between interactive or non-interactive (e.g., `/basic/NewSchema/` or `/interactive/NewSchema/`), and add two files: `phase1.txt` (Vision-to-Text) and `phase2.txt` (Text-to-SCAD). It is recommended to refer to the prompts already present in the same folder as a reference.
- **Create Prompt Logic**: In `src/prompts/templates.py`, create a class that inherits from `BaseTemplate`. Implement the `get_phase_1()` and `get_phase_2()` methods to inject user parameters into the text.
- **Create UI Panel**: In `src/ui/panels.py`, create a class that inherits from `BaseTemplatePanel`. Create the form here (text fields, spinboxes) to collect specific data from the frontend.
- **Register the Template**: In `src/ui/landing_window.py`, add the new panel to the `QStackedWidget` in the right column and add a new checkable action in the top menu ("Template").

## Uninstallation
If you wish to remove the software and clean your system (including virtual environments and USB rules on Linux):
- **Windows**: Run `uninstall.bat`.
- **Linux**: Run `./uninstall.sh`.
