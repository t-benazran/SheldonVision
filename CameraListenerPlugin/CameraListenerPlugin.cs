using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Google.Protobuf;
using Plugin.RecordingInfra;
using Sigmund.CommonNetStandard;
using Sigmund.CommonNetStandard.Transport;

namespace CameraListenerPlugin
{
    public class CameraListenerPlugin : PluginBase
    {
        private enum PathStatus
        {
            Valid,
            Invalid
        }

        private const string CAMERA_FRAME_MSG_NAME = "CameraFrame";
        private const string GET_TOTAL_VIDEO_FRAMES_MSG_NAME = "GetTotalVideoFrames";
        private const string PATH_STATUS_MSG = "PathStatus";
        private const string LOAD_REQUESTS_MESSAGE = "LoadRequest";
        private const string FPS_STATUS_MESSAGE = "FpsStatus";
        private const string TOTAL_VIDEO_FRAMES_MSG_NAME = "TotalVideoFrames";
        private const string GET_CURRENT_FRAME_MESSAGE = "GetCurrentFrame";
        private const string START_RECORDING_CAMERA = "StartRecordingCamera";
        private const string STOP_RECORDING_CAMERA = "StopRecordingCamera";
        private const string ON_CAMERA_CLIP_CLOSED = "OnCameraClipClosed";
        private const string SET_FRAME_PER_SECOND = "SetFramePerSecond";
        private const string GET_FRAME_PER_SECOND = "GetFramePerSecond";
        private const string CAMERA_ACTION = "CameraAction";
        public const double DEFAULT_FRAMES_PER_SECOND_CAMERA = 10;
        public const double DEFAULT_FRAMES_PER_SECOND_VIDEO = 100;

        private readonly CameraListenerPluginOptions mOptions;
        private readonly CancellationTokenSource mTokenSource = new CancellationTokenSource();
        private VideoCaptureBase _videoCapture;
        private Task _videoCaptureTask;


        public CameraListenerPlugin(CameraListenerPluginOptions options, ISigmundTransport sigmundTransport = null) : base(options, sigmundTransport)
        {
            mOptions = options;
            InputTypes.UnionWith(new List<string>
            {
                PlayerPlugin.PLAY_MESSAGE,
                PlayerPlugin.STOP_MESSAGE,
                PlayerPlugin.NEXT_FRAME_MESSAGE,
                PlayerPlugin.PREVIOUS_FRAME_MESSAGE,
                PlayerPlugin.PAUSE_MESSAGE,
                PlayerPlugin.SET_FRAME_MESSAGE,
                GET_TOTAL_VIDEO_FRAMES_MSG_NAME,
                LOAD_REQUESTS_MESSAGE ,
                GET_CURRENT_FRAME_MESSAGE,
                START_RECORDING_CAMERA,
                STOP_RECORDING_CAMERA,
                GET_FRAME_PER_SECOND,
                SET_FRAME_PER_SECOND,
                CAMERA_ACTION
            });
            OutputTypes.UnionWith(new List<string>
            {
                CAMERA_FRAME_MSG_NAME,
                TOTAL_VIDEO_FRAMES_MSG_NAME,
                CAMERA_ACTION
            });
        }

        protected override void OnInit()
        {
            if (!mOptions.Fps.HasValue)
            {
                var isCamera = string.IsNullOrWhiteSpace(mOptions.VideoPath);
                mOptions.Fps = isCamera
                    ? DEFAULT_FRAMES_PER_SECOND_CAMERA
                    : DEFAULT_FRAMES_PER_SECOND_VIDEO;
            }

            try
            {
                _videoCapture = string.IsNullOrWhiteSpace(mOptions.VideoPath)
                    ? (VideoCaptureBase)new CameraCapture(
                        mOptions.FrameWidth,
                        mOptions.FrameHeight,
                        !mOptions.IsDisableAutoFocus,
                        mOptions.Fps.Value,
                        mOptions.IsShowDebugWindow,
                        mOptions.PauseMode,
                        mOptions.OutputVideoPath,
                        mOptions.MaxClipDurationInSec,
                        SendLog,
                        SendFrame,
                        SendCameraClip,
                        SendCameraError,
                        mTokenSource,
                        mOptions.ResizeImage)
                    : new VideoFileCapture(
                        mOptions.VideoPath,
                        mOptions.Fps.Value,
                        mOptions.IsShowDebugWindow,
                        SendLog,
                        SendFrame,
                        mTokenSource,
                        mOptions.FrameHeight,
                        mOptions.FrameWidth,
                        mOptions.ResizeImage);

            }
            catch (Exception e)
            {
                SendLog(LogMessageTypeProto.Fatal, $"Failed to initialize video capture - {e.Message}");
                Stop();
            }

            if (mOptions.WaitingMode)
            {
                mOptions.Fps = DEFAULT_FRAMES_PER_SECOND_VIDEO;
                _videoCapture = new VideoFileCapture(null, mOptions.Fps.Value, mOptions.IsShowDebugWindow, SendLog, SendFrame, mTokenSource, mOptions.FrameHeight, mOptions.FrameWidth, mOptions.ResizeImage);
                SendLog(LogMessageTypeProto.Info, $"Waiting for {LOAD_REQUESTS_MESSAGE} message");

                return;
            }

            // If pauseMode flag is enable, pause recording and wait for Play message
            if (mOptions.PauseMode && _videoCapture is VideoFileCapture)
            {
                _videoCapture.Init();
                // Pause recording
                _videoCapture.OnPauseBtn();
                _videoCapture.StartPlaying();
                SendLog(LogMessageTypeProto.Info, $"Waiting for Play message");
            }
            else
            {
                _videoCaptureTask = Task.Factory.StartNew(_videoCapture.Start);
                Task.Factory.StartNew(WaitAndStop);
            }
        }

        public override void PluginLogic()
        {
            var msg = GetNextMsg();
            try
            {
                switch (msg.Type)
                {
                    case PlayerPlugin.PLAY_MESSAGE:
                        SendLog(LogMessageTypeProto.Info, $"{PlayerPlugin.PLAY_MESSAGE} message received");
                        _videoCapture.OnPlayBtn();
                        break;
                    case GET_TOTAL_VIDEO_FRAMES_MSG_NAME:
                        SendLog(LogMessageTypeProto.Info, $"{GET_TOTAL_VIDEO_FRAMES_MSG_NAME} message received");

                        if (_videoCapture is VideoFileCapture)
                        {
                            SendMessage(TOTAL_VIDEO_FRAMES_MSG_NAME, _videoCapture.FramesCount.ToString());
                        }
                        else
                        {
                            SendLog(LogMessageTypeProto.Error, $"Getting total frames from live camera capturing is not supported");
                        }

                        break;
                    case PlayerPlugin.STOP_MESSAGE:
                        SendLog(LogMessageTypeProto.Info, $"{PlayerPlugin.STOP_MESSAGE} message received");
                        _videoCapture.OnStopBtn();
                        break;
                    case PlayerPlugin.NEXT_FRAME_MESSAGE:
                        SendLog(LogMessageTypeProto.Info, $"{PlayerPlugin.NEXT_FRAME_MESSAGE} message received");
                        _videoCapture.OnNextBtn();
                        break;
                    case PlayerPlugin.PREVIOUS_FRAME_MESSAGE:
                        SendLog(LogMessageTypeProto.Info, $"{PlayerPlugin.PREVIOUS_FRAME_MESSAGE} message received");
                        _videoCapture.OnPreviousBtn();
                        break;
                    case PlayerPlugin.PAUSE_MESSAGE:
                        SendLog(LogMessageTypeProto.Info, $"{PlayerPlugin.PAUSE_MESSAGE} message received");
                        _videoCapture.OnPauseBtn();
                        break;
                    case PlayerPlugin.SET_FRAME_MESSAGE:
                        var frame = Convert.ToDouble(msg.Msg);
                        SendLog(LogMessageTypeProto.Info, $"{PlayerPlugin.SET_FRAME_MESSAGE} to frame {frame} message received");
                        _videoCapture.OnSliderValueChanged((int)frame);
                        break;
                    case LOAD_REQUESTS_MESSAGE:
                        SendLog(LogMessageTypeProto.Info, $"{LOAD_REQUESTS_MESSAGE} message received");
                        try
                        {
                            _videoCapture.LoadRequest(msg.GetStringMessage());
                            SendMessage(PATH_STATUS_MSG, PathStatus.Valid.ToString());
                        }
                        catch (Plugin.AzureBlobStorage.InvalidUriException)
                        {
                            SendMessage(PATH_STATUS_MSG, PathStatus.Invalid.ToString());
                        }
                        catch (Azure.RequestFailedException)
                        {
                            SendLog(LogMessageTypeProto.Error, $"Invalid URI inserted, please enter a URI to the container");
                            SendMessage(PATH_STATUS_MSG, PathStatus.Invalid.ToString());
                        }
                        break;
                    case GET_CURRENT_FRAME_MESSAGE:
                        SendLog(LogMessageTypeProto.Info, $"{GET_CURRENT_FRAME_MESSAGE} message received");
                        _videoCapture.SendCurrentFrame();
                        break;
                    case SET_FRAME_PER_SECOND:
                        var fps = Convert.ToInt32(msg.Msg);
                        _videoCapture.SetFPS(fps);
                        break;
                    case GET_FRAME_PER_SECOND:
                        var fps_value = _videoCapture.GetFPS();
                        SendLog(LogMessageTypeProto.Info, $"Running with FPS {fps_value}");
                        SendMessage(FPS_STATUS_MESSAGE, fps_value.ToString());
                        break;
                    case CAMERA_ACTION:
                        HandleCameraAction(CameraAction.Parser.ParseFrom(msg.GetByteArrayMessage()));
                        break;
                }
            }
            catch(Exception e)
            {
                SendLog(LogMessageTypeProto.Error, $"{msg.Type} handling cause some error: {e.Message}{Environment.NewLine}{e.StackTrace}");
                _telemetryClient.TrackException(e);
            }
        }

        protected override void OnStop()
        {
            mTokenSource?.Cancel();
            _videoCapture?.Dispose();
        }

        private void WaitAndStop()
        {
            _videoCaptureTask.Wait();
            SendClosePlugin(PluginName);
        }

        private void SendFrame(byte[] frame)
        {
            SendMessage(CAMERA_FRAME_MSG_NAME, frame, _videoCapture.GetCurrentFramePosition().ToString());
            SendLog(LogMessageTypeProto.Debug, $"Sent frame {_videoCapture.GetCurrentFramePosition()}, Time In Ms {DateTimeOffset.Now.ToUnixTimeMilliseconds()}");
        }

        private void SendCameraClip(string filePath)
        {
            SendMessage(ON_CAMERA_CLIP_CLOSED, filePath);
            SendLog(LogMessageTypeProto.Debug, $"Sent camera clip - {filePath}");
        }

        private void HandleCameraAction(CameraAction action)
        {
            try
            {
                var videoCameraCapture = _videoCapture as CameraCapture;

                if (videoCameraCapture == null)
                {
                    return;
                }
                switch (action.Action)
                {
                    case CameraActionType.CameraActionStart:
                        //Not implemented
                        break;
                    case CameraActionType.CameraActionStop:
                        videoCameraCapture.StopCamera(); //Stop the camera and close the plugin
                        break;
                    case CameraActionType.CameraActionStartRecording:
                        videoCameraCapture.mOutputFilePath = action.RecordingPath ?? videoCameraCapture.mOutputFilePath;
                        videoCameraCapture.StartRecording();
                        break;
                    case CameraActionType.CameraActionStopRecording:
                        videoCameraCapture.StopRecording();
                        break;
                }
            }
            catch (Exception ex)
            {
                SendCameraError(ex.ToString(), action.RecordingPath);
                _telemetryClient.TrackException(ex);
            }
        }

        private void SendCameraError(string error, string recordingPath = "")
        {
            var cameraError = new CameraAction();
            cameraError.Action = CameraActionType.CameraActionError;
            cameraError.RecordingPath = recordingPath ?? "";
            cameraError.ErrorMsg = error;
            SendMessage(CAMERA_ACTION, cameraError.ToByteArray());
            SendLog(LogMessageTypeProto.Error, $"Sent camera action error - {error}");
        }
    }
}
