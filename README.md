<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary><h2 style="display: inline-block">Table of Contents</h2></summary>
  <ol>
    <li>
      <a href="#SheldonVision">SheldonVision</a>
    </li>
    <li>
      <a href="#project-scope">Project Scope</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#dependencies">Dependencies</a></li>
        <li><a href="#installing">Install</a></li>
      </ul>
    </li>
    <li><a href="#how-to-use">How to use</a>
      <ul>
        <li><a href="#load-local-files">Load local files</a></li>
        <li><a href="#load-from-cloud">Load from cloud</a></li>
        <li><a href="#features">Features</a></li>
      </ul>
    </li>
    <li>
      <a href="#high-level-requirements">High Level Requirements</a>
      <ul>
        <li><a href="#sheldonvisionui">Sheldon Vision UI</a></li>
        <li><a href="#camera-listener-plugin">Camera Listener Plugin</a></li>
        <li><a href="#tests">Tests</a></li>
      </ul>
    </li>
    <li><a href="#software-diagram">Software Diagram</a></li>
    <li><a href="#sigmund">Sigmund</a></li>
    <li><a href="#link-to-jira-roadmap">Link to JIRA roadmap</a></li>
  </ol>
</details>

<!-- SheldonVision -->
# SheldonVision

The SheldonVision project was developed in response to the needs of the Data Science team at my workplace, who required a user-friendly debugging tool for their algorithms. Its primary objective is to facilitate frame navigation, enhance algorithm accuracy through the analysis of specific frames, and incorporate additional layers of metadata. The intended beneficiaries of this project are data scientists, who can leverage its capabilities to improve their work.

![image](https://github.com/t-benazran/SheldonVision/assets/72923818/0167b3b4-2b8b-434d-9e9a-97d0e5b20764)


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
7. Copy the ``` results ``` folder to ``` C:\ ```

## How To Use
### Load Local Files
1. Click the ``` Video ``` button and load the sample video from ``` C:\results\Experiments\WOALOLTestSetP0 ```
2. Click the ``` Play ``` button

### Load From Cloud
1. Click the ``` Jump File ``` button and load the ``` All-unique-FN-unique.json ``` from ``` SheldonVisionExampleFiles ``` folder in this repository
2. Scroll down the page and choose the desired video to load

### Features
#### Bounding Box Metadata
Click the ``` MeataData Primary ``` or ``` Metadata Seconadry ``` button and load the ``` presence_log.json ```

1. Play - 

2. Rewind - 

3. Decimation - This button ensures that the flow of the video would be dictated by the applied layers instead of just passing frame by frame.


4. Jump File


5. Frame Features - Zoom In/Out, Capture, x,y,color of current pixel
Play: The "Play" button is a standard feature found in most video players. When pressed, it starts the playback of the video, allowing you to watch it from the current position to the end.

Rewind: The "Rewind" button allows you to quickly move backward in the video. When pressed, it rewinds the playback to a previous point, allowing you to review or revisit specific parts of the video.

Decimation: The "Decimation" button introduces a unique functionality to the video playback. By enabling this feature, the video's flow is determined by the applied layers instead of playing frame by frame in a linear manner. It provides the ability to manipulate and control the progression of the video based on the predefined layers, giving you more creative control over the visual experience.

Jump File: The "Jump File" button provides a convenient way to skip to a different part within the video player. When clicking this button a file browser opens enabling the user to choose the needed jump file.

Frame Features: This set of features enhances your ability to interact with individual frames of the video:

Zoom In/Out: This feature allows you to magnify or reduce the display size of the current frame. It enables you to focus on specific details or get an overview of the entire frame. 

Frame features (x,y,color of current pixel) -  These frame features provide information about the current pixel under the cursor. They display the coordinates (x, y) of the pixel and its corresponding color value, which can be useful for analysis, editing, or extracting specific color data from the video frame.


![image](https://github.com/t-benazran/SheldonVision/assets/72923818/99aee3d0-9ae2-435c-a1f9-271f9a170372)


## High Level Requirements
### SheldonVisionUI
SheldonVisionUI serves as the web-based user interface for our tool, offering a comprehensive platform for data scientists to load videos, setting files, and metadata in order to facilitate algorithm debugging. Its feature set encompasses various functionalities such as play/pause buttons, frame skipping (both forwards and backwards), decimation options, and the ability to jump to specific frames of interest. Additionally, users can leverage zoom in/out capabilities and access other relevant features. This UI empowers data scientists with an intuitive and powerful interface to effectively analyze and debug their algorithms.

### Camera Listener Plugin
The Camera Listener Plugin is a C# backend plugin designed to facilitate the playback of widely used video formats, such as .mp4 files. It leverages the capabilities of OpenCV for efficient handling of video frames. The plugin includes a range of essential features for video playback, including functions such as VideoPlayerPlay, VideoPlayerStop, VideoPlayerNextFrame, VideoPlayerPreviousFrame, VideoPlayerPause, and VideoPlayerSetFrame. These functionalities allow seamless control over the video playback, enabling users to play, stop, navigate to the next or previous frame, pause the video, and set a specific frame for analysis. The Camera Listener Plugin thus serves as a robust backend component, enhancing the video playback capabilities within the tool.

### Tests
The tests for the project are categorized into two main types: manual tests and unit tests. The manual tests focus on validating the functionality of the user interface (UI) and its various components. These tests include verifying the proper functioning of all UI features and buttons, loading videos and checking the displayed data, ensuring data retrieval accuracy from the first video, loading and verifying the list of videos and error handling on the UI, loading and displaying metadata, and validating metadata for the current frame.

On the other hand, the unit tests are specifically designed to cover the functionality of certain UI behaviors. These tests focus on testing individual units or components of the code to ensure their correctness and proper integration with the overall system. The unit tests will encompass scenarios that exercise specific UI behaviors and verify their expected outcomes.
By combining manual tests for UI validation and unit tests for specific UI behaviors, a comprehensive testing approach is employed to ensure the quality and reliability of the project.

## Software Diagram
![image](https://github.com/t-benazran/SheldonVision/assets/72923818/d1ee98dd-e619-4347-96ba-a9a533f5aacf)

![image](https://github.com/t-benazran/SheldonVision/assets/72923818/1dd68b02-acef-4a8c-b254-8d845dccc208)

## Sigmund
Flexible and scalable development environment that can be used for a wide range of applications. Sigmund is a distributed system built in micro-service architecture, using various plugins that are used to achieve different goals. Set of plugins are commonly called Network.
Plugin supported in C++, C# and Python. Using protocol buffer to build the data structures one time for all the languages. Leveraging ZeroMQ for communication layer.
The development environment includes Plugin base to minimize developer overhead.
We will use Sigmund in order to create a Network that contains CameraListenerPlugin and SheldonVisionUI. Each of them is a Plugin, registering to Sigmund and send/receives messages from/to it. This way we will create communication between the plugins.

Each Sigmund Plugin as independent component communicate with each other on top of network connection. The Plugins sending and listening to specific messages types without the need to know which component is registered to network. The only information that a Plugin needs to know is the IP address of Sigmund Core.

| ![image](https://github.com/t-benazran/SheldonVision/assets/72923818/4f8e84e3-50d4-44c7-bee6-d8482bff2edf) | 
|:--:| 
|   Sigmund network example:
Plugin A sends 'a' messages and doesn’t subscribe to any message.
Plugin B sends 'b' and 'x' messages and subscribes to 'a' messages.
Plugin C sends 'c' messages and subscribed to 'a' and 'b' messages. |

## Link to JIRA roadmap
https://talklein125.atlassian.net/jira/software/projects/FP/boards/1/roadmap


