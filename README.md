A lightweight Python tool for real-time detection and tracking of STag markers. It displays camera output with tag information overlaid live on the video stream. 

Instructions for first-time installation and use can be found [here](INSTRUCTIONS.txt).

### What are STags?

STags, designed by Manfred Stoiber, are used for motion tracking of animals.  This **real-time STag detector** (this repository) was developed as a tool to display detected tags in real-time, allowing for a **live view of the tags** rather than having to analyze them after the recording process.

## Demo

There are two types of STag detectors in this repository:
With RecentId Colour Coding | Without RecentId Colour Coding
:-: | :-:
![example_RICC](https://github.com/user-attachments/assets/39f25e92-64d8-450b-b841-7fe114bbed60) | ![example_nRICC](https://github.com/user-attachments/assets/6f79223b-624f-43e2-8c93-a4ae6fb85260)

 ## Compatibility Notes
- [Installer](run_installer.sh) currently tested on **Raspberry Pi OS** (Linux terminal).
- Built in **Python**
- Works with **Picam2** camera system
- Uses the **STag** library by **Manfred Stoiber** for marker detection

---
## License

- This project is licensed under the [MIT License](LICENSE). 
- Includes components from the 'stag-python' library (MIT-licensed).
