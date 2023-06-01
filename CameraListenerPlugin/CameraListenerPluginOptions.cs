using Sigmund.CommonNetStandard;
using CommandLine;

namespace CameraListenerPlugin
{
    public class CameraListenerPluginOptions : PluginOptionsBase
    {
        public const int DEFAULT_FRAME_WIDTH = 1920;
        public const int DEFAULT_FRAME_HEIGHT = 1280;

        [Option('w', "width", Required = false, Default = DEFAULT_FRAME_WIDTH, HelpText = "Frame Width (camera mode)")]
        public int FrameWidth { get; set; }

        [Option('h', "height", Required = false, Default = DEFAULT_FRAME_HEIGHT, HelpText = "Frame Height (camera mode)")]
        public int FrameHeight { get; set; }

        [Option("disableAutoFocus", Required = false, Default = false, HelpText = "Disable Auto Focus (camera mode)")]
        public bool IsDisableAutoFocus { get; set; }

        [Option('f', "fps", Required = false, HelpText = "Frame per sec (camera mode)")]
        public double? Fps { get; set; }

        [Option('p', "videoPath", Required = false, Default = null, HelpText = "Video file to stream (file mode)")]
        public string VideoPath { get; set; }

        [Option("showDebugWindow", Required = false, Default = false, HelpText = "Show debug window (displays frames)")]
        public bool IsShowDebugWindow { get; set; }

        [Option("pauseMode", Required = false, Default = false, HelpText = "Pause mode, the player wait for playing request")]
        public bool PauseMode { get; set; }

        [Option("waitingMode", Required = false, Default = false, HelpText = "Waiting mode, the player wait for loading request")]
        public bool WaitingMode { get; set; }
        
        [Option("outputVideoPath", Required = false, Default = null, HelpText = "Output file to write camera stream to (camera mode)")]
        public string OutputVideoPath { get; set; }

        [Option("maxClipDuration", Required = false, HelpText = "Max recorded video chunk duration in seconds. 0 - unlimited (camera mode)")]
        public int? MaxClipDurationInSec { get; set; }

        [Option("resizeImage", Required = false, Default = false, HelpText = "Is image resize required? (use --width and --height for size setting)")]
        public bool ResizeImage { get; set; }
    }
}
