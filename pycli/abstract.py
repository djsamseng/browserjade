import numpy as np

class AbstractMemoryRawPixelSeen:
    """Remember if I've ever seen a given raw pixel
    """
    def __init__(self) -> None:
        self.pixelsSeen = dict()
    def tick(self, webcam_video, webcam_audio):
        for pixel in webcam_video:
            self.pixelsSeen = True

class AbstractMemoryRawPixelPersistPosition:
    """Remember if this pixel was the same color from t1 to t2
    """
    def __init__(self) -> None:
        self.pixelsPersist = dict()
        self.lastImg = np.zeros((800, 600))
    def tick(self, webcam_video, webcam_audio):
        for i in range(webcam_video.shape[0]):
            if self.lastImg[i] == webcam_video[i]:
                self.pixelsPersist[self.lastImg] = True
        self.lastImg = webcam_video

class AbstractMemoryPixelGroupPersistPosition:
    """Remember if this group of pixels 
    of a given color persists from t1 to t2
    """
    def __init__(self) -> None:
        self.pixelGroupsPersist = dict()
        self.lastImg = np.zeros((800, 600))
    def tick(self, webcam_video, webcam_audio):
        cur_pixel_groups = self.__get_pixel_groups(webcam_video)
        last_pixel_groups = self.__get_pixel_groups(self.lastImg)
        for cur_group in cur_pixel_groups:
            for last_group in last_pixel_groups:
                if cur_group == last_group:
                    self.pixelGroupsPersist[cur_group] = True

    def __get_pixel_groups(self, frame):
        pixel_groups = []
        i = 0
        cur_pixel_group=[]
        cur_pixel_group_color = frame[0].color
        while i < len(frame):
            if frame[i].color == cur_pixel_group_color:
                cur_pixel_group.append(frame[i])
            else:
                pixel_groups.append(cur_pixel_group)
                cur_pixel_group = []
                cur_pixel_group_color = frame[i].color
                cur_pixel_group.append(frame[i])
            i += 1

class AbstractMemoryPixelGroupMoveObserver:
    """Watch how this group of pixels
    of a given color move from t1 to t2
    """
    def __init__(self) -> None:
        pass
        

