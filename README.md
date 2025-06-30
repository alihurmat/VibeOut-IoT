# VibeOut-IoT: Your Emotion-Aware Fitness Companion 🌟

![VibeOut Logo](https://img.shields.io/badge/VibeOut-IoT-brightgreen)

Welcome to **VibeOut-IoT**, an innovative fitness platform that tailors workouts based on your physical metrics and emotional state. By leveraging ESP32 technology, heart rate monitoring, and AI emotion detection, VibeOut creates a personalized fitness experience that adapts to your needs.

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
4. [Usage](#usage)
5. [Technical Details](#technical-details)
6. [Contributing](#contributing)
7. [License](#license)
8. [Contact](#contact)
9. [Releases](#releases)

## Introduction

In today’s fast-paced world, understanding your emotional state while working out can enhance your fitness journey. VibeOut combines heart rate and SpO2 monitoring with AI-driven emotion detection to offer a unique approach to fitness. This project aims to make workouts more effective and sustainable by aligning them with both your physical and emotional health.

## Features

- **Real-Time Monitoring**: Track heart rate and SpO2 levels continuously.
- **Emotion Detection**: Utilize AI to analyze emotional states.
- **Personalized Workouts**: Adapt workouts based on your metrics and emotions.
- **User-Friendly Interface**: Built with ReactJS for an intuitive experience.
- **Cloud Integration**: Store and analyze data using FastAPI and ThingSpeak.
- **Analytics Dashboard**: View real-time data and workout analysis.

## Getting Started

To begin using VibeOut-IoT, follow these steps to set up your environment.

### Prerequisites

Before you start, ensure you have the following:

- An ESP32 development board
- MAX30102 heart rate and SpO2 sensor
- Arduino IDE installed
- Python 3.x installed
- Node.js and npm for ReactJS

### Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/alihurmat/VibeOut-IoT.git
   cd VibeOut-IoT
   ```

2. **Set Up the Arduino Environment**:

   - Open the Arduino IDE.
   - Install the ESP32 board package via the Board Manager.
   - Install the necessary libraries for the MAX30102 sensor.

3. **Upload the Code**:

   - Open the Arduino sketch located in the `arduino` folder.
   - Connect your ESP32 board to your computer.
   - Select the correct port and upload the code.

4. **Set Up the Backend**:

   - Navigate to the `backend` folder.
   - Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

   - Run the FastAPI server:

   ```bash
   uvicorn main:app --reload
   ```

5. **Set Up the Frontend**:

   - Navigate to the `frontend` folder.
   - Install the necessary npm packages:

   ```bash
   npm install
   ```

   - Start the React application:

   ```bash
   npm start
   ```

Now you can access the application on your browser.

## Usage

Once everything is set up, you can start using VibeOut-IoT. 

1. **Connect the Sensor**: Ensure your MAX30102 sensor is properly connected to the ESP32 board.
2. **Launch the Application**: Open your web browser and navigate to the address where your React app is running (usually `http://localhost:3000`).
3. **Start Monitoring**: Begin your workout. The application will monitor your heart rate and SpO2 levels in real-time.
4. **View Analytics**: After your workout, you can analyze your performance and emotional state through the dashboard.

## Technical Details

### Hardware Components

- **ESP32**: A low-cost, low-power system on a chip with integrated Wi-Fi and Bluetooth.
- **MAX30102**: A heart rate and SpO2 sensor that uses photoplethysmography.

### Software Components

- **Arduino**: Used for programming the ESP32.
- **FastAPI**: A modern web framework for building APIs with Python.
- **ReactJS**: A JavaScript library for building user interfaces.
- **ThingSpeak**: An IoT analytics platform that allows you to visualize and analyze data.

### Data Flow

1. The ESP32 reads data from the MAX30102 sensor.
2. The data is sent to the FastAPI backend.
3. The backend processes the data and sends it to the React frontend for visualization.
4. Users can interact with the dashboard to view their performance metrics.

## Contributing

We welcome contributions to improve VibeOut-IoT. If you have ideas or suggestions, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes and push to your fork.
4. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or feedback, please reach out:

- **Ali Hurmat**: [GitHub Profile](https://github.com/alihurmat)

## Releases

To download the latest release of VibeOut-IoT, visit the [Releases section](https://github.com/alihurmat/VibeOut-IoT/releases). You can find the necessary files to download and execute.

For updates and new features, always check the Releases section. 

---

With VibeOut-IoT, you can take control of your fitness journey in a way that respects both your body and your mind. Join us in redefining fitness through technology!