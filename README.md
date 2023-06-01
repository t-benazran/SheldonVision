# SheldonVision

The SheldonVision project was developed in response to the needs of the Data Science team at my workplace, who required a user-friendly debugging tool for their algorithms. Its primary objective is to facilitate frame navigation, enhance algorithm accuracy through the analysis of specific frames, and incorporate additional layers of metadata. The intended beneficiaries of this project are data scientists, who can leverage its capabilities to improve their work.

![image](https://github.com/t-benazran/SheldonVision/assets/112501531/acd40c1a-3dfa-442a-8806-4b88f496daa3)

## Project Scope

The project scope entails the development of a user-friendly web UI interface, specifically designed for data scientists to effortlessly load their videos and facilitate easy debugging. The backend functionality will be responsible for retrieving the requested frames and addressing user queries, but this process will remain transparent to the user. Key features of the interface include the ability to navigate to the next or previous frames, implement decimation techniques, switch between video files, and incorporate additional functionalities as needed. The primary goal is to provide data scientists with a seamless and efficient platform for video analysis and algorithm debugging.


### Prerequisites

* Python 3.10.6
* .NET (6.0+ is preferable)

### Dependencies

* SheldonDependencies folder which is part of this repository

### Installing
1. Install ``` Python 3.10.6 ``` 

  ![image](https://github.com/t-benazran/SheldonVision/assets/112501531/150aa904-0a21-4bb3-843c-b89c9d2de3e3)

2. Download the zip for this repository or use git on the termianl. The terminal command is:
```
git clone https://github.com/t-benazran/SheldonVision.git
```

3. Move the ``` Sigmund ``` folder to ``` C:\Tools\ ```
4. Open Terminal or CMD and change directory to ``` SheldonDependencies ``` folder in this repository
5. run ``` pip install -r requirements.txt ```
6. Change directory to ``` C:\Tools\Sigmund\PluginSheldonVision\Networks ``` and run ``` RunSheldonVisionUiNetwork.bat ```
7. Copy the ``` results/Experiments/WOALOLTestSetP0 ``` folder to ``` C:\ ```

## High Level Requirements
### SheldonVisionUI
SheldonVisionUI serves as the web-based user interface for our tool, offering a comprehensive platform for data scientists to load videos, setting files, and metadata in order to facilitate algorithm debugging. Its feature set encompasses various functionalities such as play/pause buttons, frame skipping (both forwards and backwards), decimation options, and the ability to jump to specific frames of interest. Additionally, users can leverage zoom in/out capabilities and access other relevant features. This UI empowers data scientists with an intuitive and powerful interface to effectively analyze and debug their algorithms.

### Camera Listener Plugin
The Camera Listener Plugin is a C# backend plugin designed to facilitate the playback of widely used video formats, such as .mp4 files. It leverages the capabilities of OpenCV for efficient handling of video frames. The plugin includes a range of essential features for video playback, including functions such as VideoPlayerPlay, VideoPlayerStop, VideoPlayerNextFrame, VideoPlayerPreviousFrame, VideoPlayerPause, and VideoPlayerSetFrame. These functionalities allow seamless control over the video playback, enabling users to play, stop, navigate to the next or previous frame, pause the video, and set a specific frame for analysis. The Camera Listener Plugin thus serves as a robust backend component, enhancing the video playback capabilities within the tool.

### Tests
The tests for the project are categorized into two main types: manual tests and unit tests. The manual tests focus on validating the functionality of the user interface (UI) and its various components. These tests include verifying the proper functioning of all UI features and buttons, loading videos and checking the displayed data, ensuring data retrieval accuracy from the first video, loading and verifying the list of videos and error handling on the UI, loading and displaying metadata, and validating metadata for the current frame.

On the other hand, the unit tests are specifically designed to cover the functionality of certain UI behaviors. These tests focus on testing individual units or components of the code to ensure their correctness and proper integration with the overall system. The unit tests will encompass scenarios that exercise specific UI behaviors and verify their expected outcomes.
By combining manual tests for UI validation and unit tests for specific UI behaviors, a comprehensive testing approach is employed to ensure the quality and reliability of the project.

## SW Diagram
![image](https://github.com/t-benazran/SheldonVision/assets/112501531/2bd920c5-d1e0-47ec-be8b-7065b91c0299)

![image](https://github.com/t-benazran/SheldonVision/assets/112501531/1bbc4dcb-069e-493a-b9ae-81e42a13d627)

## Sigmund
Flexible and scalable development environment that can be used for a wide range of applications. Sigmund is a distributed system built in micro-service architecture, using various plugins that are used to achieve different goals. Set of plugins are commonly called Network.
Plugin supported in C++, C# and Python. Using protocol buffer to build the data structures one time for all the languages. Leveraging ZeroMQ for communication layer.
The development environment includes Plugin base to minimize developer overhead.
We will use Sigmund in order to create a Network that contains CameraListenerPlugin and SheldonVisionUI. Each of them is a Plugin, registering to Sigmund and send/receives messages from/to it. This way we will create communication between the plugins.

Each Sigmund Plugin as independent component communicate with each other on top of network connection. The Plugins sending and listening to specific messages types without the need to know which component is registered to network. The only information that a Plugin needs to know is the IP address of Sigmund Core.

![image](https://github.com/t-benazran/SheldonVision/assets/112501531/5d9adaa9-5f6e-487d-b3fc-2147c76a038e) 

Sigmund network example:
Plugin A sends 'a' messages and doesn’t subscribe to any message.
Plugin B sends 'b' and 'x' messages and subscribes to 'a' messages.
Plugin C sends 'c' messages and subscribed to 'a' and 'b' messages.
