# Real-Time STag Detector

A lightweight Python tool for real-time detection and tracking of STag markers. It displays camera output with tag information overlaid live on the video stream. 

Instructions for first-time installation and use can be found [here](INSTRUCTIONS.txt).

### What are STags?

STags, designed by Manfred Stoiber, are used for motion tracking of animals.  This **real-time STag detector** (this repository) was developed as a tool to display detected tags in real-time, allowing for a **live view of the tags** rather than having to analyze them after the recording process.

## Demo

There are two types of STag detectors in this repository:
1. [With RecentId Colour Coding](https://rawcdn.githack.com/JulianKempenaers/real-time-tag-detector/main/assets/example_RICC.mp4)

<video controls width="600">
  <source src="https://rawcdn.githack.com/JulianKempenaers/real-time-tag-detector/main/assets/example_RICC.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

2. [Without RecentId Colour Coding](https://rawcdn.githack.com/JulianKempenaers/real-time-tag-detector/main/assets/example_nRICC.mp4)

 ## Compatibility Notes
- [Installer](run_installer.sh) currently tested on **Raspberry Pi OS** (Linux terminal).
- Built in **Python**
- Works with **Picam2** camera system
- Uses the **STag** library by **Manfred Stoiber** for marker detection

---
## License

- This project is licensed under the [MIT License](LICENSE). 
- Includes components from the 'stag-python' library (MIT-licensed).
