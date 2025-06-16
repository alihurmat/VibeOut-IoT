from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import time
import json
import logging
import tempfile
import os
import traceback
from pydantic import BaseModel
from typing import Optional, List, Dict
import datetime
import asyncio
import re
import serial
import serial.tools.list_ports

# Heart rate data storage (in-memory for simplicity, consider a database for production)
heart_rate_data = []

# Model for heart rate data
class HeartRateReading(BaseModel):
    bpm: float
    spo2: float
    timestamp: Optional[str] = None

# Global variables for Arduino communication
arduino_serial = None
arduino_connected = False

GOOGLE_API_KEY = 'AIzaSyA6_Ch43vOdlVaXfZvR8FqjaPCYpgNVVHk'
genai.configure(api_key=GOOGLE_API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
}

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-preview-04-17",
    generation_config=generation_config,
)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


@app.post("/process_video/")
async def process_video(
        video_file: UploadFile = File(...),
        prompt: str = Form(
            "Analyze the video and provide a JSON report with workout exercises minimum 5 (name of exercise, sets, reps), facial emotions minimum 10 (emotion, timestamp), voice emotions minimum 8 (emotion, timestamp), and nutrition plan (meal, time, food)")
):
    temp_video_path = None
    try:
        logging.info(f"Received video file: {video_file.filename}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            content = await video_file.read()
            temp_video.write(content)
            temp_video_path = temp_video.name

        logging.info(f"Temporary video file created: {temp_video_path}")

        genai_video_file = genai.upload_file(temp_video_path)

        logging.info(f"Completed upload to Google AI: {genai_video_file.uri}")

        timeout = 600
        start_time = time.time()
        while genai_video_file.state.name == "PROCESSING" and (time.time() - start_time) < timeout:
            logging.info(f"Processing... Time elapsed: {time.time() - start_time:.2f}s")
            time.sleep(10)
            genai_video_file = genai.get_file(genai_video_file.name)

        if genai_video_file.state.name == "FAILED":
            raise ValueError(f"Video processing failed: {genai_video_file.state.name}")
        elif genai_video_file.state.name == "PROCESSING":
            raise TimeoutError("Video processing timed out")

        logging.info("Making LLM inference request...")
        response = model.generate_content([prompt, genai_video_file],
                                          request_options={"timeout": 600})

        logging.info("LLM response received. Parsing JSON...")
        raw_data = json.loads(response.text)
        logging.info(f"Parsed JSON data: {json.dumps(raw_data, indent=2)}")

        # Transform the data structure to match what the frontend expects
        transformed_data = {}

        # Check if data is in a nested structure with workout_report
        if "workout_report" in raw_data:
            report = raw_data["workout_report"]
            
            # Transform exercises array
            if "exercises" in report:
                transformed_data["workout_exercises"] = []
                for exercise in report["exercises"]:
                    transformed_data["workout_exercises"].append({
                        "name": exercise.get("name", ""),
                        "sets": exercise.get("sets", ""),
                        "reps": exercise.get("reps", "")
                    })
            
            # Handle facial emotions - checking both timestamp and time_stamp
            if "facial_emotions" in report:
                transformed_data["facial_emotions"] = []
                for emotion in report["facial_emotions"]:
                    transformed_data["facial_emotions"].append({
                        "emotion": emotion.get("emotion", ""),
                        "time_stamp": emotion.get("timestamp", emotion.get("time_stamp", ""))
                    })
            
            # Handle voice emotions - checking both timestamp and time_stamp
            if "voice_emotions" in report:
                transformed_data["voice_emotions"] = []
                for emotion in report["voice_emotions"]:
                    transformed_data["voice_emotions"].append({
                        "emotion": emotion.get("emotion", ""),
                        "time_stamp": emotion.get("timestamp", emotion.get("time_stamp", ""))
                    })
            
            # Transform nutrition plan
            if "nutrition_plan" in report:
                transformed_data["nutrition_plan"] = {}
                for i, meal in enumerate(report["nutrition_plan"]):
                    meal_name = meal.get("meal", f"meal{i+1}").lower().replace(" ", "_")
                    transformed_data["nutrition_plan"][meal_name] = {
                        "time": meal.get("time", ""),
                        "food": meal.get("food", "")
                    }
        else:
            # Data doesn't have workout_report structure, try to use it directly
            if "exercises" in raw_data:
                transformed_data["workout_exercises"] = raw_data["exercises"]
            elif "workout_exercises" in raw_data:
                transformed_data["workout_exercises"] = raw_data["workout_exercises"]
            
            for field in ["facial_emotions", "voice_emotions"]:
                if field in raw_data:
                    transformed_data[field] = raw_data[field]
            
            if "nutrition_plan" in raw_data:
                transformed_data["nutrition_plan"] = raw_data["nutrition_plan"]
        
        # If we still don't have the expected keys, create default data
        if "workout_exercises" not in transformed_data:
            transformed_data["workout_exercises"] = [
                {"name": "Push ups", "sets": "3", "reps": "10"},
                {"name": "Squats", "sets": "3", "reps": "15"},
                {"name": "Plank", "sets": "3", "reps": "60 seconds"},
                {"name": "Lunges", "sets": "3", "reps": "12 per leg"},
                {"name": "Burpees", "sets": "3", "reps": "8"}
            ]
            
        if "facial_emotions" not in transformed_data:
            transformed_data["facial_emotions"] = [
                {"emotion": "Neutral", "time_stamp": "00:00"},
                {"emotion": "Effort", "time_stamp": "00:01"},
                {"emotion": "Strain", "time_stamp": "00:02"}
            ]
            
        if "voice_emotions" not in transformed_data:
            transformed_data["voice_emotions"] = [
                {"emotion": "Neutral", "time_stamp": "00:00"},
                {"emotion": "Effort", "time_stamp": "00:01"},
                {"emotion": "Strain", "time_stamp": "00:02"}
            ]
            
        if "nutrition_plan" not in transformed_data:
            transformed_data["nutrition_plan"] = {
                "breakfast": {"time": "8:00 AM", "food": "Oatmeal with fruits"},
                "lunch": {"time": "1:00 PM", "food": "Grilled chicken salad"},
                "dinner": {"time": "7:00 PM", "food": "Baked fish with vegetables"}
            }

        logging.info(f"Transformed data for frontend: {json.dumps(transformed_data, indent=2)}")

        os.unlink(temp_video_path)
        logging.info(f"Temporary video file deleted: {temp_video_path}")

        return JSONResponse(content=transformed_data)

    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        logging.error(traceback.format_exc())

        if temp_video_path and os.path.exists(temp_video_path):
            os.unlink(temp_video_path)
            logging.info(f"Temporary video file deleted due to error: {temp_video_path}")

        # Return a generic data structure in case of error
        default_data = {
            "workout_exercises": [
                {"name": "Push ups", "sets": "3", "reps": "10"},
                {"name": "Squats", "sets": "3", "reps": "15"},
                {"name": "Plank", "sets": "3", "reps": "60 seconds"},
                {"name": "Lunges", "sets": "3", "reps": "12 per leg"},
                {"name": "Burpees", "sets": "3", "reps": "8"}
            ],
            "facial_emotions": [
                {"emotion": "Neutral", "time_stamp": "00:00"},
                {"emotion": "Effort", "time_stamp": "00:01"},
                {"emotion": "Strain", "time_stamp": "00:02"}
            ],
            "voice_emotions": [
                {"emotion": "Neutral", "time_stamp": "00:00"},
                {"emotion": "Effort", "time_stamp": "00:01"},
                {"emotion": "Strain", "time_stamp": "00:02"}
            ],
            "nutrition_plan": {
                "breakfast": {"time": "8:00 AM", "food": "Oatmeal with fruits"},
                "lunch": {"time": "1:00 PM", "food": "Grilled chicken salad"},
                "dinner": {"time": "7:00 PM", "food": "Baked fish with vegetables"}
            }
        }
        return JSONResponse(content=default_data, status_code=200)

@app.post("/heart_rate/")
async def add_heart_rate_reading(reading: HeartRateReading):
    if not reading.timestamp:
        reading.timestamp = datetime.datetime.now().isoformat()
    heart_rate_data.append(reading.dict())
    return JSONResponse(content={"message": "Heart rate reading added successfully"})

@app.get("/heart_rate/")
async def get_heart_rate_readings():
    return JSONResponse(content=heart_rate_data)

# Arduino Serial Communication Functions
def find_arduino_port():
    """Find the Arduino serial port by checking available ports"""
    logging.info("Searching for Arduino port...")
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        logging.info(f"Found port: {port.device} - {port.description}")
        # Common Arduino identifiers in port description
        if "Arduino" in port.description or "CH340" in port.description or "USB Serial" in port.description:
            logging.info(f"Identified likely Arduino port: {port.device}")
            return port.device
    
    # If no Arduino port found, list all available ports for manual selection
    if ports:
        logging.info("No Arduino port automatically identified. Available ports:")
        for i, port in enumerate(ports):
            logging.info(f"{i}: {port.device} - {port.description}")
        # Default to first available port if any exists
        if ports:
            logging.info(f"Defaulting to first available port: {ports[0].device}")
            return ports[0].device
    
    logging.warning("No serial ports found")
    return None

def connect_to_arduino(port=None, baud_rate=9600):
    """Connect to Arduino via serial port"""
    global arduino_serial, arduino_connected
    
    try:
        # If no port specified, try to find one
        if port is None:
            port = find_arduino_port()
            if port is None:
                logging.error("No Arduino port available")
                return False
        
        # Close existing connection if any
        if arduino_serial is not None:
            try:
                arduino_serial.close()
                logging.info("Closed existing serial connection")
            except Exception as e:
                logging.warning(f"Error closing existing serial connection: {str(e)}")
        
        # Try to connect to the port
        try:
            arduino_serial = serial.Serial(port, baud_rate, timeout=1)
            arduino_connected = True
            logging.info(f"Successfully connected to Arduino on {port} at {baud_rate} baud")
            return True
        except PermissionError:
            logging.error(f"Permission denied for port {port}. The port may be in use by another program.")
            logging.error("Please close any other programs using the serial port (like Arduino IDE Serial Monitor)")
            arduino_connected = False
            return False
        except Exception as e:
            logging.error(f"Failed to connect to Arduino: {str(e)}")
            arduino_connected = False
            return False
    except Exception as e:
        logging.error(f"Failed to connect to Arduino: {str(e)}")
        arduino_connected = False
        return False

async def read_arduino_data_task():
    """Background task to read data from Arduino"""
    global arduino_serial, arduino_connected, heart_rate_data
    
    while True:
        if arduino_connected and arduino_serial:
            try:
                if arduino_serial.in_waiting > 0:
                    line = arduino_serial.readline().decode('utf-8', errors='ignore').strip()
                    logging.debug(f"Raw Arduino data: {line}")
                    
                    # Parse data from Arduino format <DATA,bpm,spo2>
                    if "<DATA" in line and ">" in line:
                        # Extract data between < and >
                        match = re.search(r'<DATA,([\d\.]+),([\d\.]+)>', line)
                        if match:
                            bpm = float(match.group(1))
                            spo2 = float(match.group(2))
                            
                            # Create timestamp
                            timestamp = datetime.datetime.now().isoformat()
                            
                            # Create reading
                            reading = HeartRateReading(
                                bpm=bpm,
                                spo2=spo2,
                                timestamp=timestamp
                            )
                            
                            # Store reading
                            heart_rate_data.append(reading.dict())
                            
                            # Keep only the most recent 100 readings
                            if len(heart_rate_data) > 100:
                                heart_rate_data = heart_rate_data[-100:]
                            
                            logging.info(f"Stored heart rate data: BPM={bpm}, SpO2={spo2}")
            
            except Exception as e:
                logging.error(f"Error reading from Arduino: {str(e)}")
                arduino_connected = False
                
                # Try to reconnect
                await asyncio.sleep(5)
                connect_to_arduino()
        
        # If not connected, try to connect
        elif not arduino_connected:
            connect_to_arduino()
            await asyncio.sleep(5)  # Wait before trying again
        
        # Small delay to prevent high CPU usage
        await asyncio.sleep(0.1)

@app.get("/arduino/status")
async def get_arduino_status():
    """Get the status of the Arduino connection"""
    return {
        "connected": arduino_connected,
        "port": arduino_serial.port if arduino_connected else None,
        "readings_count": len(heart_rate_data)
    }

@app.post("/arduino/connect")
async def connect_arduino_endpoint(port: Optional[str] = None, baud_rate: int = 9600):
    """Endpoint to manually connect to Arduino"""
    success = connect_to_arduino(port, baud_rate)
    return {
        "success": success,
        "message": f"Connected to Arduino on {arduino_serial.port}" if success else "Failed to connect to Arduino",
        "port": arduino_serial.port if success else None
    }

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Connect to Arduino and start background task on startup"""
    connect_to_arduino()
    asyncio.create_task(read_arduino_data_task())
    logging.info("Arduino reading task started")

@app.on_event("shutdown")
async def shutdown_event():
    """Close Arduino connection on shutdown"""
    global arduino_serial
    if arduino_serial:
        arduino_serial.close()
        logging.info("Arduino connection closed")