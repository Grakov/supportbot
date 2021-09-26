from ext.attachments.downloadable import DownloadableAttachment, FileSizeLimitExceededException, FileDownloadDisabledException, FreeSpaceLimitExceededException
from ext.attachments.photo import Photo
from telebot import types


class Video(DownloadableAttachment):
    attachment_type = 'video'

    # @TODO add file download
    def __init__(self, video: types.Video):
        self.file_id = video.file_id
        self.file_size = video.file_size
        self.video_width = video.width
        self.video_height = video.height
        self.video_duration = video.duration
        self.video_thumb = Photo(video.thumb)
        try:
            self.video_thumb.download()
        except (FileSizeLimitExceededException, FileDownloadDisabledException, FreeSpaceLimitExceededException):
            pass

        self.convert_to_dict()
        self.update({
            self.attachment_type: {
                "width": self.video_width,
                "height": self.video_height,
                "duration": self.video_duration,
                "thumb": self.video_thumb.dict()
            }
        })
