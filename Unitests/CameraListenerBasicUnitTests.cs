using CameraListenerPlugin;
using Sigmund.CommonNetStandard;
using NUnit.Framework;
using System.IO;
using System.Threading;
using System.Linq;
using Plugin.RecordingInfra;
using System;

namespace Sigmund.PluginsTestProject.CameraListener
{
    class CameraListenerBasicUnitTests : SigmundUnitTestBase
    {
        private const string MP4_VIDEO_FILE_PATH = @"cat.mp4";
        private const int PLAY_RECORDING_TIMEOUT_MS = 30000;
        private const int NUMBER_OF_FRAMES_ON_VIDEO = 151;
        private const string CAMERA_FRAMES_MESSAGE_TYPE = "CameraFrame";
        private const string TEST_PLUGIN_NAME = "TestPlugin";

        public CameraListenerBasicUnitTests()
        {
            _pluginName = "CameraListenerPlugin";
        }

        private CameraListenerPluginOptions GetDefaultOptions(string videoRecordingFilePath="")
        {
            return new CameraListenerPluginOptions
            {
                PluginName = "CameraListenerPlugin",
                VideoPath = videoRecordingFilePath == string.Empty ? string.Empty : Path.GetFullPath(videoRecordingFilePath) 
            };
        }

        [Test]
        public void InitSuccessTestMethod()
        {
            var opts = GetDefaultOptions();
            var cameraListenerPlugin = new CameraListenerPlugin.CameraListenerPlugin(opts, _transport);

            InitSuccessTest(cameraListenerPlugin);
        }

        [Test, Timeout(PLAY_RECORDING_TIMEOUT_MS)]
        [TestCase(MP4_VIDEO_FILE_PATH)]
        public void PlayRecordingSuccessTestMethod(string videoRecordingFilePath)
        {
            var opts = GetDefaultOptions(videoRecordingFilePath);
            var cameraListenerPlugin = new CameraListenerPlugin.CameraListenerPlugin(opts, _transport);

            Assert.IsTrue(File.Exists(videoRecordingFilePath));
            // Send registration Ack message
            SendRegistrationAckMessage();

            _transport.AddSleepBetweenMessagesMessage(3000);
            SendStopMessage();
            cameraListenerPlugin.Start();

            var cameraListenerMessages = _transport.GetOutputMessages();

            Assert.AreEqual(NUMBER_OF_FRAMES_ON_VIDEO, cameraListenerMessages.Count(x => x.Type == CAMERA_FRAMES_MESSAGE_TYPE));
        }

        [Test, Timeout(PLAY_RECORDING_TIMEOUT_MS)]
        [TestCase(MP4_VIDEO_FILE_PATH)]
        public void PauseRecordingTestMethod(string videoRecordingFilePath)
        {
            var opts = GetDefaultOptions(videoRecordingFilePath);
            opts.PauseMode = true;
            var cameraListenerPlugin = new CameraListenerPlugin.CameraListenerPlugin(opts, _transport);

            Assert.IsTrue(File.Exists(videoRecordingFilePath));
            // Send registration Ack message
            SendRegistrationAckMessage();

            // Run Plugin and check registration
            _transport.SendMessageToPlugin(new SigmundMsg(PlayerPlugin.PLAY_MESSAGE, TEST_PLUGIN_NAME, ""));
            _transport.AddSleepBetweenMessagesMessage(3000);

            SendStopMessage();
            cameraListenerPlugin.Start();

            var cameraListenerMessages = _transport.GetOutputMessages();

            Assert.AreEqual(NUMBER_OF_FRAMES_ON_VIDEO, cameraListenerMessages.Count(x => x.Type == CAMERA_FRAMES_MESSAGE_TYPE));
        }

        [Test, Timeout(PLAY_RECORDING_TIMEOUT_MS)]
        [TestCase(MP4_VIDEO_FILE_PATH)]
        public void NextFrameTestMethod(string videoRecordingFilePath)
        {
            var NUMBER_OF_FRAMES_ON_NEXT = 1;
            var opts = GetDefaultOptions(videoRecordingFilePath);
            opts.PauseMode = true;
            var cameraListenerPlugin = new CameraListenerPlugin.CameraListenerPlugin(opts, _transport);

            Assert.IsTrue(File.Exists(videoRecordingFilePath));
            // Send registration Ack message
            SendRegistrationAckMessage();

            // Run Plugin and check registration
            _transport.SendMessageToPlugin(new SigmundMsg(PlayerPlugin.NEXT_FRAME_MESSAGE, TEST_PLUGIN_NAME, ""));

            SendStopMessage();
            cameraListenerPlugin.Start();

            var cameraListenerMessages = _transport.GetOutputMessages();

            Assert.AreEqual(NUMBER_OF_FRAMES_ON_NEXT, cameraListenerMessages.Count(x => x.Type == CAMERA_FRAMES_MESSAGE_TYPE));
        }

        [Test, Timeout(PLAY_RECORDING_TIMEOUT_MS)]
        [TestCase(MP4_VIDEO_FILE_PATH)]
        public void PreviousFrameTestMethod(string videoRecordingFilePath)
        {
            var NUMBER_OF_FRAMES_ON_PERVIOUS = 1; // When setting a frame and when asking for previous
            var opts = GetDefaultOptions(videoRecordingFilePath);
            opts.PauseMode = true;
            var cameraListenerPlugin = new CameraListenerPlugin.CameraListenerPlugin(opts, _transport);

            Assert.IsTrue(File.Exists(videoRecordingFilePath));
            // Send registration Ack message
            SendRegistrationAckMessage();

            // Run Plugin and check registration
            _transport.AddSleepBetweenMessagesMessage(1000);
            _transport.SendMessageToPlugin(new SigmundMsg(PlayerPlugin.SET_FRAME_MESSAGE, TEST_PLUGIN_NAME, "3"));
            _transport.SendMessageToPlugin(new SigmundMsg(PlayerPlugin.PREVIOUS_FRAME_MESSAGE, TEST_PLUGIN_NAME, ""));

            SendStopMessage();
            cameraListenerPlugin.Start();

            var cameraListenerMessages = _transport.GetOutputMessages();

            Assert.AreEqual(NUMBER_OF_FRAMES_ON_PERVIOUS, cameraListenerMessages.Count(x => x.Type == CAMERA_FRAMES_MESSAGE_TYPE));
        }

        [Test, Timeout(PLAY_RECORDING_TIMEOUT_MS)]
        public void PauseModeWithCameraFailureTestMethod()
        {
            var opts = GetDefaultOptions();
            opts.PauseMode = true;
            var cameraListenerPlugin = new CameraListenerPlugin.CameraListenerPlugin(opts, _transport);

            // Send registration Ack message
            SendRegistrationAckMessage();

            SendStopMessage();
            
            cameraListenerPlugin.Start();

            var cameraListenerMessages = _transport.GetOutputMessages();
            Assert.AreEqual(
                cameraListenerMessages.First(x => x.Type == Constants.SIGMUND_MSG_TYPE).Msg, 
                Constants.SIGMUND_PLUGIN_CLOSING);
        }
    }
}
