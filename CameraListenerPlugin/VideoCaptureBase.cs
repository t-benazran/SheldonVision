using System;
using System.Threading;
using System.Threading.Tasks;
using OpenCvSharp;
using Sigmund.CommonNetStandard;

namespace CameraListenerPlugin
{
    public abstract class VideoCaptureBase: IDisposable
    {
        protected readonly PluginBase.SigmundLogFunc mSendLog;
        private readonly Action<byte[]> mSendByteArrMessage;
        private CancellationTokenSource mCancellationTokenSource;
        private readonly bool mIsOpenDebugWindow;
        private int mDelayBetweenFramesMs;
        private const int MILLISECONDS_IN_SECOND = 1000;
        private readonly ManualResetEvent _pauseEvent = new ManualResetEvent(true);
        private readonly int mFrameHeight;
        private readonly int mFrameWidth;
        private readonly bool mImageResize;
        private readonly object mCaptureLock = new object();

        protected VideoCapture Capture { get; private set; }
        protected bool IsPlaying { get; private set; }

        protected readonly object mIsLoadedRequestLock = new object();
        protected bool mIsLoadedRequest;

        public int FramesCount;
        private Task _playingTask;

        public abstract void OnSliderValueChanged(int frame);
        public abstract void OnNextBtn();
        public abstract void OnPreviousBtn();
        public abstract void LoadRequest(string getStringMessage);
        public abstract void SendCurrentFrame();

        protected VideoCaptureBase(double fps, bool isOpenDebugWindow, PluginBase.SigmundLogFunc sendLog, Action<byte[]> sendByteArrMessage, CancellationTokenSource cancellationTokenSource, int imageHeight, int imageWidth, bool resizeImage)
        {
            mSendLog = sendLog;
            mSendByteArrMessage = sendByteArrMessage;
            mCancellationTokenSource = cancellationTokenSource;
            mDelayBetweenFramesMs = (int)(MILLISECONDS_IN_SECOND / fps);
            mIsOpenDebugWindow = isOpenDebugWindow;
            mFrameHeight = imageHeight;
            mFrameWidth = imageWidth;
            mImageResize = resizeImage;
        }

        protected bool IsCaptureAvilable => Capture != null;

        public void Init()
        {
            Capture = GetVideoCapture();
            FramesCount = Capture.FrameCount;
        }

        public void OnStopBtn()
        {
            IsPlaying = false;
            
            _pauseEvent.Set();
            mCancellationTokenSource.Cancel();

            if (_playingTask != null)
            {
                Task.WaitAll(_playingTask);
            }

            Capture?.Release();
            Capture = null;
            mCancellationTokenSource = new CancellationTokenSource();
        }

        public void StartPlaying()
        {
            _playingTask =  Task.Run(Start);
        }

        public double GetCurrentFramePosition()
        {
            return Capture.Get(VideoCaptureProperties.PosFrames);
        }

        public void Start()
        {
            // Prevent double init in case of loaded request
            lock (mIsLoadedRequestLock)
            {
                if (!mIsLoadedRequest)
                {
                    Init();
                }
            }

            if (!Capture.IsOpened())
            {
                Log(LogMessageTypeProto.Fatal, "Couldn't open video stream");
            }

            Log(LogMessageTypeProto.Info, "Start reading from video stream");
            while (!mCancellationTokenSource.IsCancellationRequested && Capture?.IsOpened() == true)
            {
                _pauseEvent.WaitOne();
                var encodedImage = GetCurrentFrame();
                SendMessage(encodedImage);
                Cv2.WaitKey(mDelayBetweenFramesMs); //Must
            }

            lock (mIsLoadedRequestLock)
            {
                mIsLoadedRequest = false;
            }
        }

        protected byte[] GetCurrentFrame()
        {
            var image = new Mat();
            lock (mCaptureLock)
            {
                Capture?.Read(image);
            }

            if (image.Empty() && IsCaptureAvilable)
            {
                Log(LogMessageTypeProto.Error, "Video stream return empty frame");
                OnPauseBtn();
                return null;
            }

            if (mIsOpenDebugWindow)
            {
                Cv2.ImShow("capture", image);
            }

            if (mImageResize)
            {
                var image_dst = new Mat(mFrameWidth, mFrameHeight, image.Type());
                Cv2.Resize(image, image_dst, new Size(mFrameWidth, mFrameHeight));
                Cv2.ImEncode(".jpeg", image_dst, out var encodedImage);
                return encodedImage;
            }
            else
            {
                Cv2.ImEncode(".jpeg", image, out var encodedImage);
                return encodedImage;
            }                                                             
        }

        protected abstract VideoCapture GetVideoCapture();

        private void Log(LogMessageTypeProto logType, string message)
        {
            mSendLog?.Invoke(logType, message);
        }

        protected virtual void SendMessage(byte[] message)
        {
            mSendByteArrMessage?.Invoke(message);
        }

        public void OnPlayBtn()
        {
            if (!IsPlaying)
            {
                IsPlaying = true;

                if (IsPaused)
                {
                    _pauseEvent.Set();
                }
            }
        }

        private bool IsPaused => !_pauseEvent.WaitOne(0);

        public void OnPauseBtn()
        {
            IsPlaying = false;
            _pauseEvent.Reset();
        }

        public virtual void Dispose()
        {
            Capture?.Dispose();
        }

        public void SetFPS(int fps)
        {
            mDelayBetweenFramesMs = (int)(MILLISECONDS_IN_SECOND / fps);
        }

        public int GetFPS()
        {
            return (int)Capture.Fps;
        }

        protected bool SetProperty(VideoCaptureProperties videoCaptureProperties,double val)
        {
            bool? isSet = false;
            lock (mCaptureLock)
            {
                isSet = Capture?.Set(videoCaptureProperties, val);
            }
            return isSet ?? false;
        }

        protected double GetProperty(VideoCaptureProperties videoCaptureProperties)
        {
            lock (mCaptureLock)
            {
                return Capture?.Get(videoCaptureProperties) ?? 0;
            }
        }
    }
}
