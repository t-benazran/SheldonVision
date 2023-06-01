using OpenCvSharp;
using Sigmund.CommonNetStandard;
using System;
using System.IO;
using System.Threading;

namespace CameraListenerPlugin
{
    public class CameraCapture : VideoCaptureBase
    {
        private readonly int mFrameWidth;
        private readonly int mFrameHeight;
        private readonly bool mAutoFocus;
        private readonly double mFps;
        private readonly int mMaxClipLength;
        private VideoWriter mVideoWriter;
        private int mRecordedFrames;
        public string mOutputFilePath;
        private readonly Action<string> mSendCameraClipPath;
        private readonly Action<string, string> mSendCameraError;

        public CameraCapture(
            int frameWidth,
            int frameHeight,
            bool autoFocus,
            double fps,
            bool isOpenDebugWindow,
            bool pauseMode,
            string outputFilePath,
            int? maxClipDuration,
            PluginBase.SigmundLogFunc sendLog,
            Action<byte[]> sendByteArrMessage,
            Action<string> sendCameraClipPath,
            Action<string, string> sendCameraError,
            CancellationTokenSource cancellationToken,
            bool imageResize
        ) : base(fps, isOpenDebugWindow, sendLog, sendByteArrMessage, cancellationToken, frameHeight, frameWidth, imageResize)
        {
            mFrameWidth = frameWidth;
            mFrameHeight = frameHeight;
            mAutoFocus = autoFocus;
            mFps = fps;
            mSendCameraError = sendCameraError;

            if (!string.IsNullOrEmpty(outputFilePath))
            {
                var fixedPath = Path.GetFullPath(outputFilePath);
                mSendCameraClipPath = sendCameraClipPath;
                mMaxClipLength = maxClipDuration ?? 0;
                mOutputFilePath = fixedPath;
                if (!pauseMode)
                {
                    StartRecording();   
                }
            }
        }

        public override void Dispose()
        {
            mVideoWriter?.Dispose();
            base.Dispose();
        }

        protected override VideoCapture GetVideoCapture()
        {
            Environment.SetEnvironmentVariable("OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS", "0");
            var capture = new VideoCapture(0, VideoCaptureAPIs.MSMF)
            {
                FrameWidth = mFrameWidth,
                FrameHeight = mFrameHeight,
                AutoFocus = mAutoFocus,
                Fps = mFps
            };
            if (!capture.IsOpened())
            {
                mSendCameraError("Failed to open camera", mOutputFilePath);
            }

            return capture;
        }

        protected override void SendMessage(byte[] frame)
        {
            var image = new Mat();
            Capture?.Read(image);
            if (image.Empty() && IsCaptureAvilable)
            {
                mSendCameraError("Failed to open camera", "");
            }
            else if (mVideoWriter != null && mVideoWriter.IsOpened())
            {
                var mat = Cv2.ImDecode(frame, ImreadModes.Unchanged);

                var resized = new Mat();
                Cv2.Resize(mat, resized, new Size(mFrameWidth, mFrameHeight));
                mVideoWriter.Write(resized);

                if (mMaxClipLength > 0)
                {
                    mRecordedFrames++;
                    if (mRecordedFrames / (int)mFps == mMaxClipLength)
                    {
                        mRecordedFrames = 0;
                        StopRecording();
                        StartRecording();
                    }
                }
            }

            base.SendMessage(frame);
        }

        public override void LoadRequest(string getStringMessage)
        {
            throw new NotImplementedException();
        }

        public override void SendCurrentFrame()
        {
            throw new NotImplementedException();
        }

        public override void OnNextBtn()
        {
            throw new NotImplementedException();
        }

        public override void OnPreviousBtn()
        {
            throw new NotImplementedException();
        }

        public override void OnSliderValueChanged(int frame)
        {
            throw new NotImplementedException();
        }
        
        public void StopCamera()
        {
            OnStopBtn();
            mSendLog(LogMessageTypeProto.Info, "Stop Camera - closing plugin");
            StopRecording();
        }

        public void StartRecording()
        {
            var defaultFileName = $"{Path.GetFileNameWithoutExtension(mOutputFilePath)}_" +
                                  $"{DateTime.Now:HHmmss-ddMMyyyy}{Path.GetExtension(mOutputFilePath)}";
            var newFilePath = Path.Join(Path.GetDirectoryName(mOutputFilePath), defaultFileName);

            mVideoWriter = new VideoWriter(newFilePath,
                CovertCodecToFourCc(Path.GetExtension(newFilePath)),
                mFps,
                new Size(mFrameWidth, mFrameHeight));
        }

        public void StopRecording()
        {
            if (mVideoWriter != null && mVideoWriter.IsOpened())
            {
                mVideoWriter?.Release();
                mSendCameraClipPath?.Invoke(mVideoWriter?.FileName);
            }
        }
        
        private static int CovertCodecToFourCc(string codec)
        {
            return codec switch
            {
                "mp4" => VideoWriter.FourCC('m', 'j', 'p', 'g'),
                "avi" => VideoWriter.FourCC('d','i','v', 'x'),
                _ => VideoWriter.FourCC('m', 'p', '4', 'v')
            };
        }
    }
}