using OpenCvSharp;
using Plugin.AzureBlobStorage;
using Sigmund.CommonNetStandard;
using System;
using System.IO;
using System.Text.RegularExpressions;
using System.Threading;


namespace CameraListenerPlugin
{
    public class VideoFileCapture : VideoCaptureBase
    {
        private const string REGEX_VALID_URI_PATTERN = @"^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$";
        private string mPath;

        public VideoFileCapture(string path, double fps, bool isOpenDebugWindow, PluginBase.SigmundLogFunc sendLog, Action<byte[]> sendByteArrMessage, CancellationTokenSource cancellationToken, int imageHeight, int imageWidth, bool resizeImage) :
            base(fps, isOpenDebugWindow, sendLog, sendByteArrMessage, cancellationToken, imageHeight, imageWidth, resizeImage)
        {
            mPath = path;
        }

        private bool IsValidUri(string path)
        {
            var rgx = new Regex(REGEX_VALID_URI_PATTERN, RegexOptions.Compiled | RegexOptions.IgnoreCase);
            return rgx.IsMatch(path);
        }

        protected override VideoCapture GetVideoCapture()
        {
            if (string.IsNullOrEmpty(mPath))
            {
                return new VideoCapture();
            }

            // mPath is a local file
            if (File.Exists(mPath))
            {
                mSendLog(LogMessageTypeProto.Info, $"Loading video File {mPath}");
                return new VideoCapture(mPath);
            }

            // mPath is a URI
            AzureUtilities.SetLog(mSendLog);
            var sharedAccessSignature = AzureUtilities.GetServiceSasUriForBlob(mPath);
            mSendLog(LogMessageTypeProto.Info, $"Loading video from URI {mPath}");
            return new VideoCapture(sharedAccessSignature.ToString());
        }

        public override void OnNextBtn()
        {
            OnPauseBtn();

            if (IsFrameAvailable())
            {
                SendCurrentFrame();
                SetNextFrame();
            }
        }

        private void SetNextFrame()
        {
            var currentFrame = GetCurrentFramePosition();

            if (currentFrame > FramesCount)
            {
                return;
            }
            SetFrameByIndex(currentFrame + 1);
        }

        public override void OnPreviousBtn()
        {
            OnPauseBtn();

            if (!IsCaptureAvilable)
            {
                return;
            }

            if (SetPreviousFrame())
            {
                SendCurrentFrame();
            }
        }

        public override void SendCurrentFrame()
        {
            SendMessage(GetCurrentFrame());
        }

        private bool SetFrameByIndex(double frameToSet)
        {
            var wasPlaying = IsPlaying;
            OnPauseBtn();

            var res = SetProperty(VideoCaptureProperties.PosFrames, frameToSet);

            if (wasPlaying)
            {
                OnPlayBtn();
            }

            return res;
        }

        private bool SetPreviousFrame()
        {
            var currentFrame = GetCurrentFramePosition();

            if (currentFrame <= 0)
            {
                return false;
            }

            return SetFrameByIndex(currentFrame - 1);
        }

        public override void OnSliderValueChanged(int newFrame)
        {
            SetFrameByIndex(newFrame);
        }

        public bool IsFrameAvailable()
        {
            if (!IsCaptureAvilable)
            {
                return false;
            }

            return FramesCount > 0 &&
                   GetProperty(VideoCaptureProperties.PosFrames) < FramesCount;
        }

        public override void LoadRequest(string filePath)
        {
            if (File.Exists(filePath) || IsValidUri(filePath))
            {
                mPath = filePath;

                Init();
                lock (mIsLoadedRequestLock)
                {
                    mIsLoadedRequest = true;
                }
                // Pause recording
                OnPauseBtn();
                StartPlaying();
            }
            else
            {
                mSendLog(LogMessageTypeProto.Error, $"{filePath} Not exists, File or URI are invalid");
                throw new InvalidUriException();
            }
        }
    }
}
