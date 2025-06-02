# Real-time tag detector
A lightweight Python tool for real-time detection and tracking of STag markers. It displays camera output with tag information overlaid live on the video stream. 

### What are STags?

STags, designed by Manfred Stoiber, are used for motion tracking of animals.  This **real-time STag detector** (this repository) was developed as a tool to display detected tags in real-time, allowing for a **live view of the tags** rather than having to analyze them after the recording process.

 ## Compatibility Notes
- [Installer](run_installer.sh) currently tested on **Raspberry Pi OS** (Linux terminal).
- Built in **Python**
- Works with **Picam2** camera system
- Uses the **STag** library by **Manfred Stoiber** for marker detection

## Installation and Instructions
Instructions for first-time installation and use can be found [here](INSTRUCTIONS.txt).

## Available tools:
There are two types of STag detectors in this repository:
[With RecentId Colour Coding (RICC)](assets/example_RICC.mp4) | [Without RecentId Colour Coding(nRICC)](assets/example_nRICC.mp4)
:-: | :-:
![example_RICC](https://github.com/user-attachments/assets/39f25e92-64d8-450b-b841-7fe114bbed60) | ![example_nRICC](https://github.com/user-attachments/assets/6f79223b-624f-43e2-8c93-a4ae6fb85260)
This code keeps track of the n most recently detected tags and colour codes them. This means that even if they move out of frame for a few seconds, they will still have the same colour when they return. This is currently limited to 21 tags per frame.| This code does not keep track of the most recently detected tags. Therefore, it can handle >21 tags per frame. Use this if you do not require colour coding of STags.

Both RICC and nRICC exist as two distinct versions:
1. Real-time view of detected tags 
2. Record a video of detected tags and save the video.

After running the installer, the four tools can be ran using the executable .sh files:
Tools (executable .sh files) | Recent Id Colour Coding? | real-time view | Record and save video | Number of cameras | Notes
:-- | :- | :-| :- | :- | :--
RecentIdColourCoding.sh | Yes | Yes | No |  1 or 2 | Number of cameras detected automatically. Always restart the Raspberry Pi after plugging in or removing cameras.
RecentIdColourCoding_video.sh | Yes | No | Yes | 1 |
without_RecentIdColourCoding.sh | No | Yes | No | 1 |
without_RecentIdColourCoding_video.sh| No | No | Yes | 1 |

---
## License

- This project is licensed under the [MIT License](LICENSE). 
- Includes components from the 'stag-python' library (MIT-licensed).
