from src.manager.launcher.launcher_interface import ILauncher
from src.manager.docker_thread.docker_thread import DockerThread
from src.manager.vnc.vnc_server import Vnc_server
import time
import os
import stat

class LauncherGazeboView(ILauncher):
    display: str
    internal_port: str
    external_port: str
    height: int
    width: int
    running = False

    def run(self, callback):
        DRI_PATH = os.path.join("/dev/dri", os.environ.get("DRI_NAME", "card0"))
        ACCELERATION_ENABLED = self.check_device(DRI_PATH)

        CAMERA_PATH = os.path.join("/dev", os.environ.get("CAMERA_NAME", "video0"))
        CAMERA_ENABLED = self.check_device(CAMERA_PATH)

        print("\n******* [gazebo_view] DRI_PATH: " + str(DRI_PATH) + "\n")       # BORRAR
        print("\n******* [gazebo_view] CAMERA_PATH: " + str(CAMERA_PATH) + "\n")       # BORRAR

        gz_vnc = Vnc_server()
        
        if CAMERA_ENABLED:
            gz_vnc.start_vnc(self.display, self.internal_port, self.external_port)
            time.sleep(1)
            camera_node_cmd = (f"ros2 run usb_cam usb_cam_node_exe")
            rviz_cmd = (f"export DISPLAY=:0; rviz2")
            camera_thread = DockerThread(camera_node_cmd)
            rviz_thread = DockerThread(rviz_cmd)
            camera_thread.start()
            rviz_thread.start()
            self.running = True
        else:
            # Confi = gure browser screen width and height for gzclient
            gzclient_config_cmds = f"echo [geometry] > ~/.gazebo/gui.ini; echo x=0 >> ~/.gazebo/gui.ini; echo y=0 >> ~/.gazebo/gui.ini; echo width={self.width} >> ~/.gazebo/gui.ini; echo height={self.height} >> ~/.gazebo/gui.ini;"
            
            if ACCELERATION_ENABLED:
                gz_vnc.start_vnc_gpu(self.display, self.internal_port, self.external_port,DRI_PATH)
                time.sleep(6)

                # Write display config and start gzclient
                gzclient_cmd = (
                    f"export DISPLAY=:0; {gzclient_config_cmds} export VGL_DISPLAY={DRI_PATH}; vglrun gzclient --verbose")
            else:
                gz_vnc.start_vnc(self.display, self.internal_port, self.external_port)
                time.sleep(6)

                gzclient_cmd = (
                    f"export DISPLAY=:0; {gzclient_config_cmds} gzclient --verbose")
            
            gzclient_thread = DockerThread(gzclient_cmd)
            gzclient_thread.start()
            self.running = True

    def check_device(self, device_path):
        try:
            return stat.S_ISCHR(os.lstat(device_path)[stat.ST_MODE])
        except:
            return False
        
    def is_running(self):
        return self.running

    def terminate(self):
        pass

    def died(self):
        pass
