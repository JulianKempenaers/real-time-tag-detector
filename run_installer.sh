#!/bin/bash

#use the current user's home directory 
USER_HOME=$HOME

#search for the live_qr_scanner_folder folder 
LIVE_QR_SCANNER_DIR=$(find "$USER_HOME" -type d -name "live_qr_scanner_folder" 2>/dev/null)
#check if the folder was found

#check if the folder was found
if [ ! -d "$LIVE_QR_SCANNER_DIR" ]; then
	echo "live_qr_scanner_folder folder not found. Please make sure the folder exists in the Documents folder"
	exit 1
fi


# Install system-wide dependencies
sudo apt update
sudo apt install -y python3-picamera2  # Install picamera2 system-wide

# Define venv folder name
VENV_DIR="$LIVE_QR_SCANNER_DIR/live_qr_scanner"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv --system-site-packages "$VENV_DIR"  # Creates the virtual environment
else
    rm -rf "$VENV_DIR" #remove existing environment
    python3 -m venv --system-site-packages "$VENV_DIR"   #recreate the environment
	echo "Virtual environment already exists, likely due to copying folder from other computer. Recreating environment for this computer."
fi



# Activate virtual environment
source $VENV_DIR/bin/activate

# Upgrade pip
pip install --upgrade pip

# Check if 'requirements.txt' exists and install dependencies
if [ -f "$LIVE_QR_SCANNER_DIR/requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r "$LIVE_QR_SCANNER_DIR/requirements.txt"
else
    echo "'requirements.txt' not found. Please ensure it's in the project directory."
fi


# Install libcamera dependencies if needed
echo "Installing libcamera dependencies..."
sudo apt-get update
sudo apt-get install -y python3-libcamera

# Verify libcamera installation
if ! python -c "import libcamera" &> /dev/null; then
    echo "libcamera is not installed in Python. Installing Python bindings..."
    pip install libcamera
fi


#generate a run_stag.sh file
RUN_SCRIPT="$LIVE_QR_SCANNER_DIR/run_stag_with_RecentIdColourCoding.sh"
cat <<EOF > "$RUN_SCRIPT"
#!/bin/bash
cd "$LIVE_QR_SCANNER_DIR"
source live_qr_scanner/bin/activate
python live_stag_scanner_RICC.py
EOF

chmod +x "$RUN_SCRIPT" #make it executable
echo ""
echo "Created launcher script at $RUN_SCRIPT"
echo "You can now run the program anytime with:"
echo "'bash $RUN_SCRIPT' or by double clicking this file and executing in terminal" 


#generate a run_stag.sh file
RUN_SCRIPT="$LIVE_QR_SCANNER_DIR/run_stag_without_RecentIdColourCoding.sh"
cat <<EOF > "$RUN_SCRIPT"
#!/bin/bash
cd "$LIVE_QR_SCANNER_DIR"
source live_qr_scanner/bin/activate
python live_stag_scanner_nRICC.py
EOF

chmod +x "$RUN_SCRIPT" #make it executable
echo ""
echo "Created launcher script at $RUN_SCRIPT"
echo "You can now run the program anytime with:"
echo "'bash $RUN_SCRIPT' or by double clicking this file and executing in terminal" 




echo ""
echo "Setup complete."
