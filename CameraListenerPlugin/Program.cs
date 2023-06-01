using Sigmund.CommonNetStandard;
using Sigmund.CommonNetStandard.Transport;

namespace CameraListenerPlugin
{
    public class Program
    {
        public static void Main(string[] args)
        {
            SigmundArgumentsParser<CameraListenerPluginOptions, CameraListenerPlugin>.ParseAndRun(args, RunCameraListenerPluginCommandLinePlayerWithOptions);
        }

        public static void RunCameraListenerPluginCommandLinePlayerWithOptions(CameraListenerPluginOptions opts) => RunPlugin(opts);

        public static void RunPlugin(CameraListenerPluginOptions opts, ISigmundTransport sigmundTransport= null)
        {
            var cameraListenerPlugin = new CameraListenerPlugin(opts, sigmundTransport);
            cameraListenerPlugin.Start();
        }
    }
}
