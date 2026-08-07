from pycaw.pycaw import AudioUtilities

# Get system volume interface using modern pycaw syntax
devices = AudioUtilities.GetSpeakers()
volume = devices.EndpointVolume


def volume_up(step=0.05):
    current = volume.GetMasterVolumeLevelScalar()
    volume.SetMasterVolumeLevelScalar(min(1.0, current + step), None)
    print("Volume increased")


def volume_down(step=0.05):
    current = volume.GetMasterVolumeLevelScalar()
    volume.SetMasterVolumeLevelScalar(max(0.0, current - step), None)
    print("Volume decreased")


def set_volume(level):
    # level: 0-100
    scalar = max(0, min(100, level)) / 100
    volume.SetMasterVolumeLevelScalar(scalar, None)
    print(f"Volume set to {level}%")


def mute():
    volume.SetMute(1, None)
    print("Muted")


def unmute():
    volume.SetMute(0, None)
    print("Un-muted")